"""Backward-compatible entry point.

The API moved to ``app.main`` in v2.  Keeping this module means old commands
such as ``uvicorn api:app`` still work.
"""

from app.main import app  # noqa: F401
