"""Telegram bot handlers."""
import asyncio
import logging
import subprocess
import time

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.filters import BaseFilter

from src.core.config import config
from src.core.agent import VikaOk
from src.services.tasks import TaskScheduler

logger = logging.getLogger("vika.telegram")


class AdminFilter(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        return message.from_user.id == config.admin_id


def create_bot() -> tuple[Bot, Dispatcher]:
    bot = Bot(token=config.telegram_token)
    dp = Dispatcher()
    vika = VikaOk()
    scheduler = TaskScheduler()

    # --- Message handlers ---

    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        await message.answer("Привіт! Я Віка 💙 Готова допомогти.")

    @dp.message(Command("new"))
    async def cmd_new(message: types.Message):
        vika.new_chat(str(message.from_user.id))
        await message.answer("🧠 Контекст скинуто. Починаємо з чистого аркуша.")

    @dp.message(Command("tasks"))
    async def cmd_tasks(message: types.Message, admin: AdminFilter):
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
    async def handle_audio(message: types.Message):
        audio = message.voice or message.audio
        file_id = audio.file_id
        file = await bot.get_file(file_id)
        local_path = f"/tmp/{file_id}"
        converted_path = f"/tmp/{file_id}.mp3"

        await bot.download_file(file.file_path, local_path)

        # Convert to mp3
        subprocess.run(
            ["ffmpeg", "-i", local_path, "-acodec", "libmp3lame", "-y", converted_path],
            capture_output=True, timeout=60,
        )

        # Transcribe
        text = vika.transcribe(converted_path)
        if not text:
            await message.answer("❌ Не вдалося розпізнати аудіо.")
            return

        await message.answer(f"🎤 {text}")
        response = vika.ask(text, str(message.from_user.id))
        await message.answer(response)

    @dp.message(F.text)
    async def handle_text(message: types.Message):
        uid = str(message.from_user.id)
        if uid not in [str(i) for i in config.allowed_ids]:
            return
        response = vika.ask(message.text, uid)
        await message.answer(response)

    # --- Background proactive loop ---

    async def proactive_heart():
        logger.info("Proactive heart started")
        while True:
            try:
                for task in scheduler.due():
                    await bot.send_message(config.admin_id, task.get("message", "Нагадування!"))
            except Exception as e:
                logger.error(f"Heart error: {e}")
            await asyncio.sleep(20)

    dp.startup.register(lambda: asyncio.create_task(proactive_heart()))

    return bot, dp
