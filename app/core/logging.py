import logging
from app.core.config import settings

def setup_logging():
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    # Silence some noisy libs if needed
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)

logger = logging.getLogger("supertonic-api")
