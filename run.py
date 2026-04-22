"""Vika_Ok Telegram Bot — production entrypoint."""
import logging
import asyncio

from src.core.config import config
from src.handlers.telegram import create_bot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler("/app/bot.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("vika")


async def main():
    if not config.telegram_token:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        return
    if not config.allowed_ids:
        logger.error("ALLOWED_IDS not set!")
        return

    bot, dp = create_bot()
    logger.info("Vika_Ok v13.0 starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
