"""
Top-level API router for Sentinel AI.

All domain routers are registered here and mounted with the `/api/v1` prefix
in `main.py`. Adding a new domain module requires only a single `include_router`
call in this file — no changes to `main.py` are needed.

Versioning strategy:
  - Current version prefix: /api/v1
  - Future versions will register an `api_v2_router` alongside this one.
"""

from fastapi import APIRouter

from app.api.health.router import router as health_router

api_v1_router = APIRouter(prefix="/api/v1")

# ── Domain routers ────────────────────────────────────────────────────────────
api_v1_router.include_router(health_router)

# Future routers are registered below this line:
# api_v1_router.include_router(auth_router)
# api_v1_router.include_router(workspace_router)
# api_v1_router.include_router(document_router)
# api_v1_router.include_router(conversation_router)
