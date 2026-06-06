import logging
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

logger = logging.getLogger("api.news")

router = APIRouter()

BLOG_FILE = Path(__file__).resolve().parent.parent / "blog" / "index.html"


@router.get("/blog", response_class=HTMLResponse)
async def get_blog():
    logger.info("GET /blog")
    if not BLOG_FILE.exists():
        return HTMLResponse(
            "<h1>Blog pas encore généré</h1>"
            "<p>Lance d'abord <code>python run_agent.py</code> pour générer le blog.</p>",
            status_code=404,
        )
    return HTMLResponse(BLOG_FILE.read_text(encoding="utf-8"))
