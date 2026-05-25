import re

import streamlit as st


def sanitize_text(text: str):
    """
    Escapes single, unescaped '$' signs (not part of $$...$$ or math contexts).
    If the '$' is already escaped (i.e., '\$'), it is left untouched.
    """
    # Match a single $ that is:
    # - not preceded by '\' (so it's not already escaped)
    # - not part of a $$...$$ pair
    return re.sub(r'(?<![\\$])\$(?!\$)', r'\\$', text)


def render_llm_output(text: str):
    """
    Hybrid renderer for LLM outputs with both markdown and LaTeX.
    Automatically detects block math (\[...\], $$...$$) and inline math (\(...\)).
    Also escapes lone '$' signs to prevent unintended LaTeX parsing.
    """

    text = sanitize_text(text)

    # --- Handle display math: \[...\] or $$...$$ ---
    block_math = re.findall(r"(?:\\\[|\$\$)(.*?)(?:\\\]|\$\$)", text, re.DOTALL)
    parts = re.split(r"(?:\\\[.*?\\\]|\$\$.*?\$\$)", text, flags=re.DOTALL)

    for i, part in enumerate(parts):
        # Render regular markdown segments
        if part.strip():
            st.markdown(part, unsafe_allow_html=True)

        # Render math blocks
        if i < len(block_math):
            st.latex(block_math[i].strip())

    # --- Handle inline LaTeX (\(...\)) ---
    inline_math = re.findall(r"\\\((.*?)\\\)", text)
    for expr in inline_math:
        st.latex(expr.strip())
