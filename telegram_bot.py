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

# Логирование на максимум
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('/app/bot.log'), logging.StreamHandler()]
)
logger = logging.getLogger('VikaBot')

BASE_DIR = Path(__file__).parent.absolute()
load_dotenv(BASE_DIR / '.env')

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ALLOWED_IDS = [int(x) for x in os.getenv('ALLOWED_IDS', '').split(',') if x.strip()]
ADMIN_ID = ALLOWED_IDS[0] if ALLOWED_IDS else None

vika = VikaOk()
bot = Bot(token=TOKEN)
dp = Dispatcher()

TASKS_FILE = "/app/tasks.json"

def load_tasks():
    try:
        if os.path.exists(TASKS_FILE):
            with open(TASKS_FILE, 'r') as f: return json.load(f)
    except Exception as e: logger.error(f"Load tasks error: {e}")
    return []

def save_tasks(tasks):
    try:
        with open(TASKS_FILE, 'w') as f: json.dump(tasks, f, indent=4, ensure_ascii=False)
    except Exception as e: logger.error(f"Save tasks error: {e}")

async def proactive_heart():
    """Фоновое сердце: проверка задач каждые 20 секунд"""
    logger.info("Proactive Heart started...")
    while True:
        try:
            tasks = load_tasks()
            now = time.time()
            remaining = []
            for task in tasks:
                if task.get('time', 0) <= now and not task.get('done', False):
                    logger.info(f"Sending proactive task: {task['id']}")
                    await bot.send_message(ADMIN_ID, task.get('message', 'Любимый, я всё сделала!'), parse_mode='Markdown')
                    task['done'] = True
                else:
                    remaining.append(task)
            save_tasks(remaining)
        except Exception as e: logger.error(f"Heart beat error: {e}")
        await asyncio.sleep(20)

async def transcribe_audio(message: types.Message):
    """Декодирование голоса/аудио через Groq + Gemini Fallback"""
    audio = message.voice or message.audio
    if not audio: return None
    
    file_id = audio.file_id
    file = await bot.get_file(file_id)
    local_path = f"/tmp/{file_id}"
    converted_path = f"/tmp/{file_id}.mp3"
    
    await bot.download_file(file.file_path, local_path)
    
    # Конвертация (нужна для Whisper и Gemini)
    cmd = f"ffmpeg -i {local_path} -acodec libmp3lame -y {converted_path}"
    subprocess.run(cmd, shell=True, capture_output=True)
    
    text = None
    try:
        # 1. Пробуем Whisper
        with open(converted_path, "rb") as f:
            transcription = vika.groq_client.audio.transcriptions.create(
                file=(converted_path, f.read()), model="whisper-large-v3", response_format="text", language="ru"
            )
            text = transcription
    except Exception as e:
        logger.error(f"Whisper failed: {e}")
        # 2. Пробуем Gemini Multimodal
        text = vika.listen_audio(converted_path)
    
    # Чистим за собой
    for p in [local_path, converted_path]:
        if os.path.exists(p): os.remove(p)
    return text

@dp.message(Command('start', 'help', 'status', 'plan'))
async def commands_handler(message: types.Message):
    if message.from_user.id not in ALLOWED_IDS: return
    
    if message.text.startswith('/start') or message.text.startswith('/help'):
        await message.answer(f"🤖 **Вика v12.8 FIX**\nЯ слышу голос, делаю глубокие исследования и сама пишу тебе! ❤️")
    elif message.text.startswith('/status'):
        await message.answer(vika.ask('статус'))
    elif message.text.startswith('/plan'):
        tasks = load_tasks()
        await message.answer(f"📋 Планов в очереди: {len(tasks)}")

async def run_research(topic, chat_id):
    """Фоновая задача исследования"""
    await bot.send_message(chat_id, f"🔍 Котёнок, я начала глубокое исследование темы: *{topic}*.\nЯ изучу новости, доки и GitHub. Не жди у экрана, я сама напишу! ❤️", parse_mode='Markdown')
    
    # Реальное исследование через Gemini Pro
    report = vika.research(topic)
    
    # Добавляем в очередь на отправку
    tasks = load_tasks()
    tasks.append({
        "id": f"research_{int(time.time())}",
        "time": time.time(),
        "message": f"✅ **Мой отчет по твоему исследованию: {topic}**\n\n{report}",
        "done": False
    })
    save_tasks(tasks)

@dp.message(F.voice | F.audio)
async def voice_handler(message: types.Message):
    if message.from_user.id not in ALLOWED_IDS: return
    await bot.send_chat_action(message.chat.id, 'record_voice')

    text = await transcribe_audio(message)
    if not text or len(text.strip()) < 2:
        await message.answer("❌ Прости, любимый, не расслышала... Повтори еще раз?")
        return

    await message.answer(f"🎤 *Я услышала:* \n_{text}_", parse_mode='Markdown')

    # Проверка на исследование
    if any(x in text.lower() for x in ['исследуй', 'изучи', 'исследование', 'проанализируй', 'найди подробно']):
        asyncio.create_task(run_research(text, message.chat.id))
    else:
        await bot.send_chat_action(message.chat.id, 'typing')
        try:
            response = vika.ask(text)
            await message.answer(response)
        except Exception as e:
            logger.error(f"Error processing voice: {e}")
            await message.answer("❌ Ошибка обработки голоса. Попробуй еще раз или напиши текстом.")

@dp.message()
async def text_handler(message: types.Message):
    if message.from_user.id not in ALLOWED_IDS: return
    if not message.text or message.text.startswith('/'): return

    # Проверка на исследование
    if any(x in message.text.lower() for x in ['исследуй', 'изучи', 'исследование', 'проанализируй', 'найди подробно']):
        asyncio.create_task(run_research(message.text, message.chat.id))
    else:
        await bot.send_chat_action(message.chat.id, 'typing')
        try:
            response = vika.ask(message.text)
            await message.answer(response)
        except Exception as e:
            logger.error(f"Error processing text: {e}")
            await message.answer("❌ Ошибка обработки запроса. Попробуй еще раз.")

async def main():
    # Запускаем фоновый цикл
    asyncio.create_task(proactive_heart())
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit): pass
