from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.core.config import settings
from app.models.user import User
from app.services.llm_service import list_available_models

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "env": settings.APP_ENV,
    }


@router.get("/api/v1/settings/models")
async def available_llm_models(current_user: User = Depends(get_current_user)) -> dict:
    models = await list_available_models()
    return {"current_model": settings.OLLAMA_MODEL, "available_models": models}
