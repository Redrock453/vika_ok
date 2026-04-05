import os
import asyncio
import logging
import subprocess
import re
import json
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from agent import VikaOk
from dotenv import load_dotenv
from pathlib import Path

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('/app/bot.log'), logging.StreamHandler()]
)
logger = logging.getLogger('VikaBot')

BASE_DIR = Path(__file__).parent.absolute()
load_dotenv(BASE_DIR / '.env')

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ALLOWED_IDS_RAW = os.getenv('ALLOWED_IDS', '')
ALLOWED_IDS = [int(x.strip()) for x in ALLOWED_IDS_RAW.split(',') if x.strip() and x.strip().isdigit()]
if not ALLOWED_IDS:
    raise ValueError("ALLOWED_IDS не установлен или пустой. Укажи хотя бы один Telegram ID в .env")
ADMIN_ID = ALLOWED_IDS[0]

vika = VikaOk()
bot = Bot(token=TOKEN)
dp = Dispatcher()

TASKS_FILE = "/app/tasks.json"

def load_tasks():
    try:
        if os.path.exists(TASKS_FILE):
            with open(TASKS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Load tasks error: {e}")
    return []

def save_tasks(tasks):
    try:
        with open(TASKS_FILE, 'w') as f:
            json.dump(tasks, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Save tasks error: {e}")

async def proactive_heart():
    logger.info("Proactive Heart started...")
    while True:
        try:
            tasks = load_tasks()
            now = time.time()
            remaining = []
            for task in tasks:
                if task.get('time', 0) <= now and not task.get('done', False):
                    await bot.send_message(ADMIN_ID, task.get('message', 'Любимый, всё готово!'), parse_mode='Markdown')
                    task['done'] = True
                else:
                    remaining.append(task)
            save_tasks(remaining)
        except Exception as e:
            logger.error(f"Heart beat error: {e}")
        await asyncio.sleep(20)

async def transcribe_audio(message: types.Message):
    audio = message.voice or message.audio
    if not audio:
        return None

    file_id = audio.file_id
    file = await bot.get_file(file_id)
    local_path = f"/tmp/{file_id}"
    converted_path = f"/tmp/{file_id}.mp3"

    await bot.download_file(file.file_path, local_path)

    import shlex
    safe_local = shlex.quote(local_path)
    safe_converted = shlex.quote(converted_path)
    subprocess.run(
        ["ffmpeg", "-i", local_path, "-acodec", "libmp3lame", "-y", converted_path],
        capture_output=True, timeout=60
    )

    text = None
    try:
        with open(converted_path, "rb") as f:
            transcription = vika.groq_client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=f,
                response_format="text",
            )
            text = transcription.text.strip() if hasattr(transcription, 'text') else str(transcription)
    except Exception as e:
        logger.error(f"Whisper via Groq failed: {e}")
        text = vika.listen_audio(converted_path)

    for p in [local_path, converted_path]:
        if os.path.exists(p):
            os.remove(p)
    return text

@dp.message(Command('start', 'help', 'status', 'plan'))
async def commands_handler(message: types.Message):
    if message.from_user.id not in ALLOWED_IDS:
        return
    if message.text.startswith('/start') or message.text.startswith('/help'):
        await message.answer("🤖 **Вика v12.8**\nПомню контекст, слышу голос, делаю исследования! ❤️")
    elif message.text.startswith('/status'):
        await message.answer(vika.ask('статус', user_id=str(message.from_user.id)))
    elif message.text.startswith('/plan'):
        tasks = load_tasks()
        await message.answer(f"📋 Планов в очереди: {len(tasks)}")

async def run_research(topic, chat_id, user_id):
    await bot.send_message(chat_id, f"🔍 Начала исследование: *{topic}*", parse_mode='Markdown')
    report = vika.research(topic)
    tasks = load_tasks()
    tasks.append({
        "id": f"research_{int(time.time())}",
        "time": time.time(),
        "message": f"✅ **Отчет по теме: {topic}**\n\n{report}",
        "done": False
    })
    save_tasks(tasks)

@dp.message(F.voice | F.audio)
async def voice_handler(message: types.Message):
    if message.from_user.id not in ALLOWED_IDS:
        return
    await bot.send_chat_action(message.chat.id, 'record_voice')

    text = await transcribe_audio(message)
    if not text or len(text.strip()) < 2:
        await message.answer("❌ Не расслышала, повтори?")
        return

    await message.answer(f"🎤 *Я услышала:*\n_{text}_", parse_mode='Markdown')

    user_id = str(message.from_user.id)
    if any(x in text.lower() for x in ['исследуй', 'изучи', 'проанализируй', 'найди подробно']):
        asyncio.create_task(run_research(text, message.chat.id, user_id))
    else:
        await bot.send_chat_action(message.chat.id, 'typing')
        response = vika.ask(text, user_id=user_id)
        await message.answer(response)

@dp.message()
async def text_handler(message: types.Message):
    if message.from_user.id not in ALLOWED_IDS:
        return
    if not message.text or message.text.startswith('/'):
        return

    user_id = str(message.from_user.id)
    if any(x in message.text.lower() for x in ['исследуй', 'изучи', 'проанализируй', 'найди подробно']):
        asyncio.create_task(run_research(message.text, message.chat.id, user_id))
    else:
        await bot.send_chat_action(message.chat.id, 'typing')
        response = vika.ask(message.text, user_id=user_id)
        await message.answer(response)

async def main():
    asyncio.create_task(proactive_heart())
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass