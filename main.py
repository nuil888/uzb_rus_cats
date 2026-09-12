import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKENf
from database import init_db
from handlers import router
from middlewares import RegistrationCheckMiddleware

logging.basicConfig(level=logging.INFO)

async def main() -> None:
    if not BOT_TOKEN:
        logging.error("КРИТИЧЕСКАЯ ОШИБКА: Переменная BOT_TOKEN не установлена!")
        return

    await init_db()
    logging.info("Инициализация базы данных завершена.")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.middleware(RegistrationCheckMiddleware())
    dp.callback_query.middleware(RegistrationCheckMiddleware())

    dp.include_router(router)

    logging.info("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
