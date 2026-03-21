import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from agent import VikaOk
from dotenv import load_dotenv
from pathlib import Path

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('VikaBot')

# Загрузка настроек
BASE_DIR = Path(__file__).parent.absolute()
load_dotenv(BASE_DIR / '.env')

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ALLOWED_IDS = [8685889273, 8793880458]

# Мозги Вики
vika = VikaOk()

# Инициализация бота
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message()
async def handle_message(message: types.Message):
    if message.from_user.id not in ALLOWED_IDS:
        logger.warning(f'Access denied for user {message.from_user.id}')
        return

    if not message.text:
        return

    query = message.text.strip()
    logger.info(f'Received query from {message.from_user.id}: {query[:50]}...')

    # Визуальный статус 'Печатает...'
    await bot.send_chat_action(message.chat.id, 'typing')

    try:
        # Запускаем тяжелый расчет в отдельном потоке, чтобы не вешать бота
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, vika.ask, query)
        
        if not response:
            response = '[!] Бот вернул пустой ответ.'
            
        # Если ответ очень длинный, Телеграм может его не принять. Режем до 4000 симв.
        if len(response) > 4000:
            response = response[:4000] + '... [Текст обрезан]'
            
        await message.answer(response)
        logger.info('Response sent successfully.')

    except Exception as e:
        logger.error(f'Error handling message: {e}')
        await message.answer(f'❌ Ошибка при обработке: {e}')

async def main():
    logger.info('Starting Vika Bot v10.1...')
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info('Bot stopped.')
