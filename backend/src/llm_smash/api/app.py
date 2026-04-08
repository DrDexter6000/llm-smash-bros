"""FastAPI application factory."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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

    frontend_dist = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "..", "frontend", "dist"
    )
    if os.path.exists(frontend_dist):
        app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")

    return app
