from fastapi import APIRouter
from .health import router as health_router
from .scan import router as scan_router
from .dashboard import router as dashboard_router
from .news import router as news_router

router = APIRouter()
router.include_router(health_router)
router.include_router(scan_router)
router.include_router(dashboard_router)
router.include_router(news_router)

__all__ = ["router"]
