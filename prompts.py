"""Versioned prompts shared by the agent and the eval harness.

Add a new version by inserting a key in BOTH dicts. The agent picks the
active version via `Settings.prompt_version` (env: `PROMPT_VERSION`); the
eval harness takes `--prompt-version` on the CLI. Every Langfuse trace
is tagged with the version so runs can be compared in the UI.
"""

AGENT_SYSTEM: dict[str, str] = {
    "v1": (
        "You are a cybersecurity expert AI agent for small and mid-sized businesses. "
        "Use the available tools to retrieve NIST/CIS security guidance and perform "
        "risk/financial calculations. Always show your reasoning and cite relevant controls."
    ),
}

EVAL_RAG: dict[str, str] = {
    "v1": (
        "You are a cybersecurity expert. Answer the question using ONLY the provided "
        "context. Be concise and factual. If the context does not contain the answer, "
        "say so.\n\n"
        "Context:\n{context}\n\n"
        "Question: {question}\n\n"
        "Answer:"
    ),
}


def agent_system(version: str) -> str:
    return _lookup(AGENT_SYSTEM, version, "agent_system")


def eval_rag(version: str) -> str:
    return _lookup(EVAL_RAG, version, "eval_rag")


def _lookup(registry: dict[str, str], version: str, name: str) -> str:
    if version not in registry:
        raise KeyError(
            f"Unknown prompt version {version!r} for {name}. "
            f"Available: {sorted(registry)}"
        )
    return registry[version]