import os
import asyncio
import logging
import subprocess
import re
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from agent import VikaOk
from dotenv import load_dotenv
from pathlib import Path

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('VikaBot')

BASE_DIR = Path(__file__).parent.absolute()
load_dotenv(BASE_DIR / '.env')

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ALLOWED_IDS = [int(x) for x in os.getenv('ALLOWED_IDS', '').split(',') if x.strip()]

vika = VikaOk()
yolo_mode = True  # авто-подтверждение для /run

bot = Bot(token=TOKEN)
dp = Dispatcher()

def _allowed(message: types.Message) -> bool:
    if not ALLOWED_IDS: return True
    if message.from_user.id not in ALLOWED_IDS:
        logger.warning(f'Access denied: {message.from_user.id}')
        return False
    return True

def _split(text, size=3900):
    if not text: return []
    if len(text) <= size: return [text]
    chunks = []
    while text:
        pos = text.rfind('\n', 0, size)
        if pos == -1: pos = text.rfind(' ', 0, size)
        if pos == -1: pos = size
        chunks.append(text[:pos])
        text = text[pos:].lstrip()
    return chunks

async def _stream_exec(message: types.Message, cmd: str, analyze: bool = False):
    await message.answer(f'⚡ Выполняю: `{cmd}`', parse_mode='Markdown')
    full_output = []
    
    try:
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        
        buffer = []
        
        while True:
            line = await process.stdout.readline()
            if not line: break
            
            text = line.decode('utf-8', errors='replace').rstrip()
            full_output.append(text)
            buffer.append(text)
            
            # Потоковый вывод каждые 5 строк
            if len(buffer) >= 5:
                chunk = '\n'.join(buffer)
                await message.answer(f'```\n{chunk}\n```', parse_mode='Markdown')
                buffer = []
                await asyncio.sleep(0.1)

        if buffer:
            await message.answer(f'```\n' + '\n'.join(buffer) + '\n```', parse_mode='Markdown')
            
        return_code = await process.wait()
        
        output_str = '\n'.join(full_output)
        
        if analyze:
            await message.answer('🔍 Анализирую вывод...')
            query = f'Команда `{cmd}` завершилась с кодом {return_code}. Вывод:\n{output_str[-2000:]}\n\nПроанализируй результат.'
            response = await asyncio.get_event_loop().run_in_executor(None, vika.ask, query)
            for chunk in _split(response):
                await message.answer(chunk)
        elif return_code != 0:
            await message.answer(f'❌ Ошибка (код {return_code})')
            
    except Exception as e:
        await message.answer(f'💥 Ошибка выполнения: {str(e)}')

@dp.message(Command('start', 'help'))
async def cmd_start(message: types.Message):
    if not _allowed(message): return
    await message.answer(
        '🤖 **Вика_Ok v11.5**\n'
        '/run <cmd> — выполнить bash\n'
        '/shell <cmd> — алиас /run\n'
        '/runlog <cmd> — выполнение + анализ\n'
        '/logs — последние 20 строк лога\n'
        '/ps — процессы\n'
        '/clear — очистить историю\n'
        '/status — статус системы\n'
        '/yolo — переключить авто-режим',
        parse_mode='Markdown'
    )

@dp.message(Command('yolo'))
async def cmd_yolo(message: types.Message):
    global yolo_mode
    if not _allowed(message): return
    yolo_mode = not yolo_mode
    await message.answer(f'🔥 YOLO-режим: {"ВКЛ ⚡" if yolo_mode else "ВЫКЛ"}')

@dp.message(Command('run', 'shell'))
async def cmd_run(message: types.Message):
    if not _allowed(message): return
    parts = message.text.split(None, 1)
    cmd = parts[1].strip() if len(parts) > 1 else ''
    if not cmd:
        await message.answer('Укажите команду.')
        return
    await _stream_exec(message, cmd)

@dp.message(Command('runlog'))
async def cmd_runlog(message: types.Message):
    if not _allowed(message): return
    parts = message.text.split(None, 1)
    cmd = parts[1].strip() if len(parts) > 1 else ''
    if not cmd:
        await message.answer('Укажите команду для анализа.')
        return
    await _stream_exec(message, cmd, analyze=True)

@dp.message(Command('logs'))
async def cmd_logs(message: types.Message):
    if not _allowed(message): return
    res = subprocess.run('tail -n 20 /app/bot.log', shell=True, capture_output=True, text=True)
    await message.answer(f'```\n{res.stdout or "(пусто)"}\n```', parse_mode='Markdown')

@dp.message(Command('ps'))
async def cmd_ps(message: types.Message):
    if not _allowed(message): return
    res = subprocess.run('ps aux | grep -E "python|bot" | grep -v grep', shell=True, capture_output=True, text=True)
    await message.answer(f'```\n{res.stdout or "пусто"}\n```', parse_mode='Markdown')

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
    
    # Более надежное обнаружение команд
    if message.text.startswith(('/run', '/shell', '/logs', '/ps', '/clear', '/status', '/yolo', '/runlog')):
        return

    await bot.send_chat_action(message.chat.id, 'typing')
    try:
        response = await asyncio.get_event_loop().run_in_executor(None, vika.ask, message.text.strip())
        if response:
            for chunk in _split(response):
                await message.answer(chunk)
    except Exception as e:
        await message.answer(f'❌ {e}')

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
