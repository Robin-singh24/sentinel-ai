"""API ROUTER"""

from fastapi import APIRouter

from app.api.health.router import router as health_router
from app.modules.auth.router import router as auth_router
from app.modules.documents.router import router as document_router
from app.modules.workspaces.router import router as workspace_router

api_v1_router = APIRouter(prefix="/api/v1")

# ── Domain routers ────────────────────────────────────────────────────────────
api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(workspace_router)
api_v1_router.include_router(document_router)

# Future routers are registered below this line:
# api_v1_router.include_router(conversation_router)
