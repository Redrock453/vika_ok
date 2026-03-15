import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from agent import VikaOk
from dotenv import load_dotenv

# Загрузка настроек
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID") # Для безопасности, чтобы только ты мог ей командовать

logging.basicConfig(level=logging.INFO)

# Мозги Вики
vika = VikaOk()

# Инициализация бота
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if ADMIN_ID and str(message.from_user.id) != ADMIN_ID:
        await message.answer("Доступ запрещен. Я работаю только на БАС.")
        return
    await message.answer("Вика_Ok v5.2 в строю. Командуй, Вячеслав.")

@dp.message()
async def handle_message(message: types.Message):
    if ADMIN_ID and str(message.from_user.id) != ADMIN_ID:
        return

    # Показываем, что Вика думает
    await bot.send_chat_action(message.chat.id, "typing")
    
    # Запрос к мозгам
    query = message.text
    response = vika.ask(query)
    
    # Если ответ слишком длинный (например, дамп системы), режем на куски
    if len(response) > 4000:
        for x in range(0, len(response), 4000):
            await message.answer(response[x:x+4000])
    else:
        await message.answer(response)

async def main():
    print(f"\n[!] VIKA TELEGRAM BOT STARTED")
    if not ADMIN_ID:
        print("[WARN] ADMIN_ID не установлен! Бот будет отвечать ВСЕМ.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
