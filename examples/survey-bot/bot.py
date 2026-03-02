import os
import sys

from dotenv import load_dotenv
from loguru import logger

from botty import AppBuilder

# Load environment variables
load_dotenv()


def configure_logging(level: str = "INFO"):
    logger.remove()
    logger.add(
        sys.stderr,
        level=level,
        colorize=True,
        format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
    )


def main():
    configure_logging(os.getenv("LOG_LEVEL", "INFO"))

    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN not set in .env")
        sys.exit(1)

    logger.info("Starting Survey Bot...")
    app = AppBuilder().token(token).build()
    app.launch()


if __name__ == "__main__":
    main()
