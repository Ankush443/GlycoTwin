"""Uvicorn entry point for local GlycoTwin API development."""

from .app import create_app

app = create_app()
