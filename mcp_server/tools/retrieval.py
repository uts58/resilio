import json

from mcp.server.fastmcp import Context, FastMCP

from ..knowledge_base import KnowledgeBase


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    def retrieve_cyber_context(query: str, ctx: Context) -> str:
        """Retrieve NIST/CIS controls or guidance for a given cybersecurity topic."""
        kb: KnowledgeBase = ctx.request_context.lifespan_context["kb"]
        return json.dumps(kb.retrieve(query), indent=2)