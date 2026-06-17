from fastapi import APIRouter

from app.core.responses import success_response

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check() -> dict:
    return success_response(data={"status": "healthy"})

