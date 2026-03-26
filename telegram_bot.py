import os
import asyncio
import subprocess
import re
import json
import tempfile
from pathlib import Path
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from agent import VikaOk
from dotenv import load_dotenv
import edge_tts

# Загрузка окружения
BASE_DIR = Path(__file__).parent.absolute()
load_dotenv(BASE_DIR / '.env')

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ALLOWED_IDS = [int(x) for x in os.getenv('ALLOWED_IDS', '').split(',') if x.strip()]

vika = VikaOk()
bot = Bot(token=TOKEN)
dp = Dispatcher()

VOICE = "ru-RU-SvetlanaNeural"

def _split(text, size=3900):
    if not text: return []
    return [text[i:i+size] for i in range(0, len(text), size)]

async def text_to_speech(text, output_path):
    """Синтез текста в речь через edge-tts"""
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output_path)

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

@dp.message(F.voice)
async def handle_voice(message: types.Message):
    if message.from_user.id not in ALLOWED_IDS: return
    
    await bot.send_chat_action(message.chat.id, 'record_voice')
    
    with tempfile.TemporaryDirectory() as tmpdir:
        ogg_path = os.path.join(tmpdir, "voice.ogg")
        wav_path = os.path.join(tmpdir, "voice.wav")
        
        # Скачиваем голос
        file_info = await bot.get_file(message.voice.file_id)
        await bot.download_file(file_info.file_path, ogg_path)
        
        # Конвертируем в wav через ffmpeg для Whisper
        subprocess.run(['ffmpeg', '-i', ogg_path, '-ar', '16000', wav_path, '-y'], check=True, capture_output=True)
        
        try:
            # Используем Whisper через DO-AI клиент
            with open(wav_path, "rb") as audio_file:
                transcript = vika.do_client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file
                )
            text = transcript.text
        except Exception as e:
            await message.answer(f"❌ Ошибка распознавания: {e}")
            return

        # Процессим текст через Вику
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(None, vika.ask, text)
        
        if res:
            # Генерируем голос в ответ
            reply_voice_path = os.path.join(tmpdir, "reply.mp3")
            await text_to_speech(res, reply_voice_path)
            
            await message.reply_voice(types.FSInputFile(reply_voice_path))
            if len(res) > 200:
                await message.answer(res)

@dp.message()
async def handle_text(message: types.Message):
    if message.from_user.id not in ALLOWED_IDS: return
    if not message.text or message.text.startswith('/'): return
    
    await bot.send_chat_action(message.chat.id, 'typing')
    try:
        loop = asyncio.get_event_loop()
        res = await loop.run_in_executor(None, vika.ask, message.text)
        
        if res:
            # Для текста тоже добавим возможность голосового ответа
            for chunk in _split(res):
                await message.answer(chunk)
            
            # Включаем озвучку для ВСЕХ ответов
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                await text_to_speech(res, f.name)
                await message.answer_voice(types.FSInputFile(f.name))
                os.unlink(f.name)

    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
# VOICE MODE - додати перед if __name__
