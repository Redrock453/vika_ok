import os
import asyncio
import logging
from pathlib import Path
from aiogram import Bot
from agent import VikaOk
from dotenv import load_dotenv

async def main():
    load_dotenv()
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN не установлен в .env")

    allowed_ids_raw = os.getenv('ALLOWED_IDS', '')
    allowed_ids = [x.strip() for x in allowed_ids_raw.split(',') if x.strip()]
    if not allowed_ids:
        raise ValueError("ALLOWED_IDS не установлен или пустой. Укажи хотя бы один Telegram ID в .env")
    chat_id = allowed_ids[0]

    bot = Bot(token=token)
    vika = VikaOk()

    print('[INFO] Вика начинает изучение репозитория...')

    # Используем путь относительно скрипта вместо хардкода
    base_dir = Path(__file__).parent.absolute()
    files = os.listdir(base_dir)
    structure = '\n'.join(files)

    query = f'Я изучила структуру папок нашего проекта: {structure}. Составь проактивное, нежное и дерзкое сообщение для моего мужа Вячеслава (Баса). Расскажи, что ты готова к работе над БАС и что ты нашла интересного в коде.'

    response = vika.ask(query)

    if response:
        await bot.send_chat_action(chat_id, 'typing')
        await asyncio.sleep(2)
        await bot.send_message(chat_id, response)
        print('[SUCCESS] Сообщение отправлено!')

    await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())
