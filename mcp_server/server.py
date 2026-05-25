from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import asyncio

from mcp.server.fastmcp import FastMCP

from .config import Settings
from .knowledge_base import init_knowledge_base
from .tools import calculators, retrieval


@asynccontextmanager
async def _lifespan(server: FastMCP) -> AsyncIterator[dict]:
    settings = Settings()
    kb = await asyncio.to_thread(init_knowledge_base, settings)
    yield {"kb": kb}


def create_app() -> FastMCP:
    settings = Settings()
    app = FastMCP(
        "resilio-tools",
        host="0.0.0.0",
        port=settings.mcp_port,
        lifespan=_lifespan,
    )
    calculators.register(app)
    retrieval.register(app)
    return app


mcp = create_app()