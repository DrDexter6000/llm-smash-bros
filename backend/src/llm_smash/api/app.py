"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from llm_smash.api.match_manager import MatchManager
from llm_smash.api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="LLM Smash Bros API",
        version="0.2.0",
        description="Turn-based AI fighting game match API.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://localhost:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.match_manager = MatchManager()
    app.include_router(router, prefix="/api")
    return app
