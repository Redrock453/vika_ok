"""Vika_Ok Telegram Bot — production entrypoint."""
import logging
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.config import config
from src.handlers.telegram import create_bot

# Configure logging with level from config
logging.basicConfig(
    level=config.log_level,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(config.log_file),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("vika")


async def main():
    # Validate config first
    is_valid, errors = config.validate()
    if not is_valid:
        logger.error("Configuration validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        logger.error("Fix these issues in .env and restart.")
        sys.exit(1)

    bot, dp = create_bot()
    logger.info(f"Vika_Ok v13.1 starting... (log level: {config.log_level})")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.exception("Fatal error")
        sys.exit(1)
