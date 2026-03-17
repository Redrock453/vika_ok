import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from agent import VikaOk
from dotenv import load_dotenv
from pathlib import Path

# Загрузка настроек
BASE_DIR = Path(__file__).parent.absolute()
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# Твои два ID
ALLOWED_IDS = [8685889273, 8793880458]

# Логи в минимум
logging.basicConfig(level=logging.WARNING)

# Мозги Вики
vika = VikaOk()

# Инициализация бота
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message()
async def handle_message(message: types.Message):
    # ПРОВЕРКА ХОЗЯИНА
    if message.from_user.id not in ALLOWED_IDS:
        print(f"[SECURITY] Попытка доступа от левого юзера: {message.from_user.id}")
        return

    # Защита от пустых сообщений (картинки, стикеры без подписи)
    if not message.text:
        return

    text = message.text.strip()
    
    # Визуальный статус
    await bot.send_chat_action(message.chat.id, "typing")
    
    # Запрос к ядру
    response = vika.ask(text)
    
    # Отправка ответа
    await message.answer(response)

async def main():
    print(f"\n==================================================")
    print(f"   🤖 VIKA_OK TG-BOT v9.4 — PRIVATE MODE ACTIVE")
    print(f"   ДОСТУП РАЗРЕШЕН ДЛЯ: {ALLOWED_IDS}")
    print(f"==================================================\n")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n👋 Бот выключен.\n")
