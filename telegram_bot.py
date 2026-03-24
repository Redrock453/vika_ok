import os
import asyncio
import subprocess
import re
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from agent import VikaOk
from dotenv import load_dotenv
from pathlib import Path

# Загрузка окружения
BASE_DIR = Path(__file__).parent.absolute()
load_dotenv(BASE_DIR / '.env')

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ALLOWED_IDS = [int(x) for x in os.getenv('ALLOWED_IDS', '').split(',') if x.strip()]

vika = VikaOk()
bot = Bot(token=TOKEN)
dp = Dispatcher()

def _split(text, size=3900):
    if not text: return []
    return [text[i:i+size] for i in range(0, len(text), size)]

@dp.message(Command('run', 'shell'))
async def cmd_run(message: types.Message):
    if message.from_user.id not in ALLOWED_IDS: return
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        await message.answer("Укажи команду!")
        return
    
    cmd = parts[1]
    await message.answer(f"⚡ Выполняю: `{cmd}`")
    
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        stdout, _ = await proc.communicate()
        res = stdout.decode(errors='replace') if stdout else "(нет вывода)"
        
        for chunk in _split(res):
            await message.answer(f"```\n{chunk}\n```", parse_mode='Markdown')
    except Exception as e:
        await message.answer(f"💥 Ошибка: {e}")

@dp.message(Command('status'))
async def cmd_status(message: types.Message):
    if message.from_user.id not in ALLOWED_IDS: return
    q_status = "✅" if vika.qdrant else "❌"
    m_status = "✅" if vika.embedding_model else "⏳"
    await message.answer(f"🤖 **VIKA v15.0 IRON BODY**\n\nShell: ✅\nQdrant: {q_status}\nMemory: {m_status}\n\nЯ готова к работе, любимый! ❤️", parse_mode='Markdown')

@dp.message()
async def handle_all(message: types.Message):
    if message.from_user.id not in ALLOWED_IDS: return
    if not message.text or message.text.startswith('/'): return
    
    await bot.send_chat_action(message.chat.id, 'typing')
    try:
        # Используем run_in_executor для синхронного вызова vika.ask
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(None, vika.ask, message.text)
        
        if res:
            for chunk in _split(res):
                await message.answer(chunk)
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
