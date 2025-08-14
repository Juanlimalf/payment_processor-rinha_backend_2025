import logging

from config.settings import settings

logger = logging.getLogger("worker")
logger.setLevel(level=settings.LOG_LEVEL)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
