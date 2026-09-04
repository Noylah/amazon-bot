import asyncio
import logging

from aiogram import Bot, Dispatcher

import database as db
from config import BOT_TOKEN, CEO_USERNAME
from handlers import router


async def main() -> None:
    db.init_db()
    db.apply_ceo_username(CEO_USERNAME)
    bot = Bot(token=BOT_TOKEN)
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
