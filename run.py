import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
from dotenv import load_dotenv
from os import getenv
from handlers import main_router as router


load_dotenv()
bot = Bot(token=getenv('BOT_TOKEN'))
dp = Dispatcher()
dp.include_router(router)


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s: %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level=logging.INFO
    )
    try:
        print('started')
        asyncio.run(main())
    except KeyboardInterrupt:
        print('exit')