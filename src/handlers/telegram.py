"""Telegram bot handlers with security improvements."""
import asyncio
import hashlib
import logging
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, BaseFilter
from aiogram.types import BufferedInputFile

from src.core.config import config
from src.core.agent import VikaOk
from src.services.tasks import TaskScheduler

logger = logging.getLogger("vika.telegram")


class AdminFilter(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        return message.from_user.id == config.admin_id


class AllowedUsersFilter(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        return message.from_user.id in config.allowed_ids


def _safe_file_path(file_id: str, suffix: str = "") -> Path:
    """Generate safe file path from file_id to prevent path traversal."""
    hash_digest = hashlib.md5(file_id.encode()).hexdigest()
    return Path(config.audio_temp_dir) / f"{hash_digest}{suffix}"


async def _download_audio(bot: Bot, file_id: str) -> Optional[Path]:
    """Download audio file safely."""
    try:
        file_info = await bot.get_file(file_id)
        local_path = _safe_file_path(file_id, Path(file_info.file_path).suffix)
        await bot.download_file(file_info.file_path, str(local_path))
        return local_path
    except Exception as e:
        logger.error(f"Audio download failed: {e}")
        return None


async def _convert_to_mp3(input_path: Path) -> Optional[Path]:
    """Convert audio to MP3 using ffmpeg."""
    output_path = _safe_file_path(input_path.stem, ".mp3")
    try:
        result = subprocess.run(
            ["ffmpeg", "-i", str(input_path), "-acodec", "libmp3lame", "-y", str(output_path)],
            capture_output=True,
            timeout=60,
            check=False,
        )
        if result.returncode == 0:
            return output_path
        logger.error(f"FFmpeg conversion failed: {result.stderr.decode()}")
        return None
    except subprocess.TimeoutExpired:
        logger.error("FFmpeg conversion timeout")
        return None
    except Exception as e:
        logger.error(f"Audio conversion error: {e}")
        return None


def _cleanup_file(path: Optional[Path]) -> None:
    """Safely remove temporary file."""
    if path and path.exists():
        try:
            path.unlink()
        except Exception as e:
            logger.warning(f"Failed to cleanup {path}: {e}")


def create_bot() -> tuple[Bot, Dispatcher]:
    bot = Bot(token=config.telegram_token)
    dp = Dispatcher()
    vika = VikaOk()
    scheduler = TaskScheduler()

    # Apply rate limiting
    from aiogram.utils import RateLimiter
    dp.rate_limiter = RateLimiter(limit=config.rate_limit, period=config.rate_limit_period)

    # --- Message handlers ---

    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        await message.answer("Привіт! Я Віка 💙 Готова допомогти.")

    @dp.message(Command("new"))
    @dp.message(AllowedUsersFilter())
    async def cmd_new(message: types.Message):
        vika.new_chat(str(message.from_user.id))
        await message.answer("🧠 Контекст скинуто. Починаємо з чистого аркуша.")

    @dp.message(Command("tasks"))
    @dp.message(AdminFilter())
    async def cmd_tasks(message: types.Message):
        pending = scheduler.list_pending()
        if not pending:
            await message.answer("📋 Немає завдань.")
            return
        text = "📋 Завдання:\n"
        for i, t in enumerate(pending, 1):
            ts = time.strftime("%H:%M %d.%m", time.localtime(t["time"]))
            text += f"{i}. {t['message'][:60]} — {ts}\n"
        await message.answer(text)

    @dp.message(F.voice | F.audio)
    @dp.message(AllowedUsersFilter())
    async def handle_audio(message: types.Message):
        audio = message.voice or message.audio
        if not audio:
            return

        await bot.send_chat_action(message.chat.id, "record_voice")

        file_id = audio.file_id
        local_path = await _download_audio(bot, file_id)
        if not local_path:
            await message.answer("❌ Не вдалося завантажити аудіо.")
            return

        converted_path = await _convert_to_mp3(local_path)
        _cleanup_file(local_path)

        if not converted_path:
            await message.answer("❌ Не вдалося конвертувати аудіо.")
            return

        try:
            text = vika.transcribe(str(converted_path))
            if not text or len(text.strip()) < 2:
                await message.answer("❌ Не вдалося розпізнати аудіо.")
                return

            await message.answer(f"🎤 _{text}_", parse_mode="Markdown")
            response = vika.ask(text, str(message.from_user.id))
            await message.answer(response)
        finally:
            _cleanup_file(converted_path)

    @dp.message(F.text)
    @dp.message(AllowedUsersFilter())
    async def handle_text(message: types.Message):
        uid = str(message.from_user.id)
        await bot.send_chat_action(message.chat.id, "typing")
        response = vika.ask(message.text, uid)
        await message.answer(response)

    # --- Background proactive loop ---

    async def proactive_heart():
        logger.info("Proactive heart started")
        while True:
            try:
                for task in scheduler.due():
                    await bot.send_message(
                        config.admin_id,
                        task.get("message", "Нагадування!"),
                        parse_mode="Markdown"
                    )
            except Exception as e:
                logger.error(f"Heart error: {e}")
            await asyncio.sleep(20)

    @dp.startup()
    async def on_startup():
        # Validate config
        is_valid, errors = config.validate()
        if not is_valid:
            logger.error(f"Configuration errors: {', '.join(errors)}")
            return

        asyncio.create_task(proactive_heart())
        logger.info("Bot started successfully")

    @dp.shutdown()
    async def on_shutdown():
        logger.info("Bot shutting down")

    return bot, dp
