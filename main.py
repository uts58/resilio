import os

import streamlit as st

from agent.agent import MCPAgent
from helper.helper import render_llm_output, sanitize_text


@st.cache_resource
def initialize_agent() -> MCPAgent:
    with st.spinner("Starting MCP server and loading knowledge base..."):
        return MCPAgent()


def main():
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    st.set_page_config(
        page_title="Cyber Resilience AI Agent",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown("#### AI-powered cybersecurity advisor for small and mid-sized businesses")

    agent = initialize_agent()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    with st.sidebar:
        st.header("️🛡️ Cyber Resilience AI Agent")
        st.markdown("""
        This AI agent helps with:
        - 🔒 NIST/CIS security controls
        - 💰 IT budget calculations
        - 📊 Risk assessment (ALE, ROSI)
        - 🎯 Security recommendations
        """)
        st.divider()

        st.header("Example Questions")
        examples = [
            "Top 5 NIST controls for SMBs",
            "Calculate IT budget for $2M revenue",
            "How to implement MFA?",
            "Calculate ALE: ARO=0.5, SLE=$100k",
            "ROSI if Exposure × Loss Reduction=$80k and cost=$50k?",
        ]
        for i, example in enumerate(examples):
            if st.button(sanitize_text(example), key=f"example_{i}", use_container_width=True):
                st.session_state.pending_query = example

        st.divider()
        if st.button("🔄 Clear Conversation", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            render_llm_output(message["content"])

    if "pending_query" in st.session_state:
        user_input = st.session_state.pop("pending_query")
        process_query = True
    else:
        user_input = st.chat_input("Ask me anything about cybersecurity...")
        process_query = user_input is not None

    if process_query and user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            render_llm_output(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    output = agent.invoke(list(st.session_state.messages))
                    render_llm_output(output)
                    st.session_state.messages.append({"role": "assistant", "content": output})
                except Exception as e:
                    error_msg = f"Error: {e}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})


if __name__ == "__main__":
    main()