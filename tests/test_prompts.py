import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import prompts


def test_v1_agent_system_is_registered():
    assert "v1" in prompts.AGENT_SYSTEM
    assert prompts.agent_system("v1") == prompts.AGENT_SYSTEM["v1"]


def test_v1_eval_rag_is_registered_and_formats():
    assert "v1" in prompts.EVAL_RAG
    rendered = prompts.eval_rag("v1").format(context="CTX", question="Q?")
    assert "CTX" in rendered and "Q?" in rendered


def test_unknown_version_raises_with_available_listed():
    with pytest.raises(KeyError, match="Available"):
        prompts.agent_system("v99")
    with pytest.raises(KeyError, match="Available"):
        prompts.eval_rag("v99")