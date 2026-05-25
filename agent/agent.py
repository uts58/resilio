import asyncio
import threading

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain_mcp_adapters.client import MultiServerMCPClient
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler as LangfuseHandler

import prompts

from .config import Settings

_MODEL = "llama-3.3-70b-versatile"


class MCPAgent:
    """LangGraph ReAct agent connected to a remote MCP HTTP server."""

    def __init__(self):
        self._settings = Settings()
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()
        self._graph = None
        asyncio.run_coroutine_threadsafe(self._init(), self._loop).result(timeout=60)

    async def _init(self):
        s = self._settings
        llm = ChatGroq(
            model=_MODEL,
            temperature=0.3,
            groq_api_key=s.groq_api_key,
        )
        client = MultiServerMCPClient(
            {
                "resilio-tools": {
                    "url": s.mcp_server_url,
                    "transport": "streamable_http",
                }
            }
        )
        tools = await client.get_tools()
        self._graph = create_agent(llm, tools)

        if s.langfuse_enabled:
            Langfuse(
                public_key=s.langfuse_public_key,
                secret_key=s.langfuse_secret_key,
                host=s.langfuse_host,
            )

    def invoke(self, messages: list[dict]) -> str:
        """Synchronous entry point — safe to call from any thread."""
        future = asyncio.run_coroutine_threadsafe(self._run(messages), self._loop)
        return future.result(timeout=120)

    async def _run(self, messages: list[dict]) -> str:
        version = self._settings.prompt_version
        system_prompt = prompts.agent_system(version)
        lc_messages = [SystemMessage(content=system_prompt)]
        for m in messages:
            if m["role"] == "user":
                lc_messages.append(HumanMessage(content=m["content"]))
            elif m["role"] == "assistant":
                lc_messages.append(AIMessage(content=m["content"]))

        config = {"metadata": {"prompt_version": version}}
        if self._settings.langfuse_enabled:
            config["callbacks"] = [LangfuseHandler()]

        result = await self._graph.ainvoke({"messages": lc_messages}, config=config)
        return result["messages"][-1].content
