"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI

from llm_smash.api.match_manager import MatchManager
from llm_smash.api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="LLM Smash Bros API",
        version="0.2.0",
        description="Turn-based AI fighting game match API.",
    )
    app.state.match_manager = MatchManager()
    app.include_router(router, prefix="/api")
    return app
