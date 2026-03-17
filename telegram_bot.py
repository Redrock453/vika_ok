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

# Логи в минимум
logging.basicConfig(level=logging.WARNING)

# Мозги Вики (версия v9.1)
vika = VikaOk()

# Инициализация бота
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message()
async def handle_message(message: types.Message):
    text = message.text.strip()
    
    # Визуальный статус
    await bot.send_chat_action(message.chat.id, "typing")
    
    # Запрос к ядру (v9.1)
    response = vika.ask(text)
    
    # Отправка ответа
    await message.answer(response)

async def main():
    print(f"\n==================================================")
    print(f"   🤖 VIKA_OK TG-BOT v9.1 — DOMINATOR ACTIVE")
    print(f"==================================================\n")
    
    # Бесконечный цикл, чтобы перебивать старого бота
    while True:
        try:
            await dp.start_polling(bot)
        except Exception as e:
            print(f"[!] Ошибка: {e}. Перезапуск через 5 сек...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n👋 Бот выключен.\n")
