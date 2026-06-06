import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)

from fastapi import FastAPI
from .api import router

app = FastAPI(title="Rabbit Scan", version="0.3.0")
app.include_router(router)
