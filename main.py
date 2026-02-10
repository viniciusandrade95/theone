"""
Compatibility ASGI entrypoint.

Supports:
- uvicorn main:app
- uvicorn main:main
"""

from app.http.main import app_factory

app = app_factory()
main = app
