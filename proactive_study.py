import os
import asyncio
import logging
from aiogram import Bot
from agent import VikaOk
from dotenv import load_dotenv

async def main():
    load_dotenv()
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('ALLOWED_IDS').split(',')[0]
    bot = Bot(token=token)
    vika = VikaOk()

    print('[INFO] Вика начинает изучение репозитория...')
    
    # Реальное изучение файлов
    files = os.listdir('/root/vika_ok/')
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
