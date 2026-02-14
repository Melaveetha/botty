"""
Task Manager Bot - Example Botty Application

A personal task manager bot demonstrating all Botty framework features.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

from botty import AppBuilder, SQLiteProvider

# Load environment variables
load_dotenv()


def configure_logging(log_level: str = "INFO"):
    """Configure logging with loguru."""
    logger.remove()  # Remove default handler

    # Console handler with colors
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True,
    )

    # File handler for errors
    logger.add(
        "logs/bot_errors.log",
        level="ERROR",
        rotation="10 MB",
        retention="1 month",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )

    # File handler for all logs
    logger.add(
        "logs/bot.log",
        level="DEBUG",
        rotation="10 MB",
        retention="1 week",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )


def validate_environment():
    """Validate required environment variables."""
    bot_token = os.getenv("BOT_TOKEN")

    if not bot_token:
        logger.error("BOT_TOKEN environment variable is not set")
        print("\n❌ Error: BOT_TOKEN is required!")
        print("📝 Please create a .env file with your bot token:")
        print("\n   BOT_TOKEN=your_token_here\n")
        print("💡 Get a token from @BotFather on Telegram")
        sys.exit(1)

    return bot_token


def main():
    """Main entry point for the bot."""
    # Configure logging
    log_level = os.getenv("LOG_LEVEL", "INFO")
    configure_logging(log_level)

    logger.info("=" * 60)
    logger.info("Starting Task Manager Bot")
    logger.info("=" * 60)

    try:
        # Validate environment
        bot_token = validate_environment()

        # Get database path
        db_path = os.getenv("DATABASE_PATH", "tasks.db")
        logger.info(f"Using database: {db_path}")

        # Create logs directory
        Path("logs").mkdir(exist_ok=True)

        # Build and configure the bot
        logger.info("Building bot application...")
        app = AppBuilder().token(bot_token).database(SQLiteProvider(db_path)).build()

        logger.info("✅ Bot application built successfully")
        logger.info("🚀 Starting bot polling...")

        # Print startup info
        print("\n" + "=" * 60)
        print("🤖 Task Manager Bot Started Successfully!")
        print("=" * 60)
        print("📊 Database:", db_path)
        print("📝 Log Level:", log_level)
        print("🔗 Press Ctrl+C to stop")
        print("=" * 60 + "\n")

        # Start the bot
        app.launch()

    except KeyboardInterrupt:
        logger.info("Received shutdown signal (Ctrl+C)")
        print("\n\n👋 Bot stopped by user")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
