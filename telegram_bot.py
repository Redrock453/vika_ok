import os
import asyncio
import logging
import subprocess
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from agent import VikaOk
from dotenv import load_dotenv
from pathlib import Path

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(name)s %(levelname)s %(message)s", handlers=[logging.FileHandler("/app/bot.log"), logging.StreamHandler()])
logger = logging.getLogger('VikaBot')
BASE_DIR = Path(__file__).parent.absolute()
load_dotenv(BASE_DIR / '.env')
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ALLOWED_IDS = [int(x) for x in os.getenv('ALLOWED_IDS', '').split(',') if x.strip()]
vika = VikaOk()
yolo_mode = False
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command('start', 'help'))
async def cmd_start(message: types.Message):
    if not _allowed(message): return
    await message.answer('🤖 Вика_Ok\n/shell <cmd>\n/ps\n/clear\n/status\n/yolo — режим без подтверждений')

@dp.message(Command('yolo'))
async def cmd_yolo(message: types.Message):
    global yolo_mode
    if not _allowed(message): return
    yolo_mode = not yolo_mode
    await message.answer(f'🔥 YOLO-режим: {"ВКЛ ⚡" if yolo_mode else "ВЫКЛ"}')

@dp.message(Command('shell'))
async def cmd_shell(message: types.Message):
    global yolo_mode
    if not _allowed(message): return
    parts = message.text.split(None, 1)
    cmd = parts[1].strip() if len(parts) > 1 else ''
    if not cmd:
        await message.answer('Использование: /shell <команда>')
        return
    if not yolo_mode:
        await message.answer(f'⚠️ Выполнить: `{cmd}`?\nОтправь /yolo чтобы включить авторежим или повтори команду.', parse_mode='Markdown')
        return
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        output = (result.stdout + result.stderr).strip() or '(пусто)'
        for chunk in _split(f'$ {cmd}\n{output}', 3900):
            await message.answer(f'```\n{chunk}\n```', parse_mode='Markdown')
    except subprocess.TimeoutExpired:
        await message.answer('⏱ Таймаут 30с')
    except Exception as e:
        await message.answer(f'❌ {e}')

@dp.message(Command('ps'))
async def cmd_ps(message: types.Message):
    if not _allowed(message): return
    result = subprocess.run('ps aux | grep -E "python|bot" | grep -v grep', shell=True, capture_output=True, text=True)
    await message.answer(f'```\n{result.stdout.strip() or "пусто"}\n```', parse_mode='Markdown')

@dp.message(Command('clear'))
async def cmd_clear(message: types.Message):
    if not _allowed(message): return
    vika.clear_history()
    await message.answer('🧹 История очищена.')

@dp.message(Command('status'))
async def cmd_status(message: types.Message):
    if not _allowed(message): return
    await message.answer(vika.ask('статус'))

@dp.message()
async def handle_message(message: types.Message):
    if not _allowed(message): return
    if not message.text: return
    await bot.send_chat_action(message.chat.id, 'typing')
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, vika.ask, message.text.strip())
        for chunk in _split(response or '[!] Пустой ответ.', 4000):
            await message.answer(chunk)
    except Exception as e:
        await message.answer(f'❌ {e}')

def _allowed(message: types.Message) -> bool:
    if not ALLOWED_IDS: return True
    if message.from_user.id not in ALLOWED_IDS:
        logger.warning(f'Access denied: {message.from_user.id}')
        return False
    return True

def _split(text, size):
    if len(text) <= size: return [text]
    chunks = []
    while text:
        if len(text) <= size: chunks.append(text); break
        pos = text.rfind('\n', 0, size)
        if pos == -1: pos = text.rfind(' ', 0, size)
        if pos == -1: pos = size
        chunks.append(text[:pos])
        text = text[pos:].lstrip()
    return chunks

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
