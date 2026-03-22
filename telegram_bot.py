import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from agent import VikaOk
from dotenv import load_dotenv
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('VikaBot')

BASE_DIR = Path(__file__).parent.absolute()
load_dotenv(BASE_DIR / '.env')

TOKEN       = os.getenv('TELEGRAM_BOT_TOKEN')
ALLOWED_IDS = list(map(int, os.getenv('ALLOWED_IDS', '').split(','))) if os.getenv('ALLOWED_IDS') else []

vika = VikaOk()

bot = Bot(token=TOKEN)
dp  = Dispatcher()


@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    if not _allowed(message): return
    await message.answer(
        f'🤖 Вика_Ok {vika.VERSION if hasattr(vika, "VERSION") else ""} запущена!\n'
        'Просто пиши — я помню весь разговор сессии.\n'
        '/clear — очистить историю | /status — статус'
    )


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
    if not message.text:      return

    query = message.text.strip()
    logger.info(f'Query [{message.from_user.id}]: {query[:80]}')

    await bot.send_chat_action(message.chat.id, 'typing')

    try:
        loop     = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, vika.ask, query)

        if not response:
            response = '[!] Пустой ответ.'

        for chunk in _split(response, 4000):
            await message.answer(chunk)

        logger.info('Response sent OK.')

    except Exception as e:
        logger.error(f'Error: {e}')
        await message.answer(f'❌ Ошибка: {e}')


def _allowed(message: types.Message) -> bool:
    if not ALLOWED_IDS:
        return True
    if message.from_user.id not in ALLOWED_IDS:
        logger.warning(f'Access denied: {message.from_user.id}')
        return False
    return True


def _split(text: str, size: int) -> list:
    if len(text) <= size:
        return [text]
    chunks = []
    while text:
        if len(text) <= size:
            chunks.append(text)
            break
        pos = text.rfind('\n', 0, size)
        if pos == -1:
            pos = text.rfind(' ', 0, size)
        if pos == -1:
            pos = size
        chunks.append(text[:pos])
        text = text[pos:].lstrip()
    return chunks


async def main():
    logger.info('Starting Vika Bot...')
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info('Bot stopped.')
