import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, BotCommand
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from db import init_db, async_session
from handlers.boshqa_elonlar import boshqa_router
from handlers.user_handlers import user_router
from handlers.admin_handlers import admin_router
from handlers.admin_elon_joylash import admin_elon_joylash_router
from keyboards.default import user_main_menu, admin_main_menu
from middlewares.db import DbSessionMiddleware

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)

# .env faylidan o'qish
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMINS_ID = os.getenv("ADMIN_ID").split(",")


# Asosiy bot funksiyasi
async def main():
    # Media papkalarini yaratish
    os.makedirs("media/checks", exist_ok=True)

    # Ma'lumotlar bazasini ishga tushirish
    await init_db()

    # Bot va dispatcher obyektlarini yaratish
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
    dp = Dispatcher(storage=MemoryStorage())

    # Middleware'ni qo'shish
    dp.update.middleware(DbSessionMiddleware(session_pool=async_session))

    # Routerlarni ulash
    dp.include_router(user_router)
    dp.include_router(boshqa_router)
    dp.include_router(admin_router)
    dp.include_router(admin_elon_joylash_router)

    # /start komandasi uchun handler
    @dp.message(CommandStart())
    async def command_start_handler(message: Message) -> None:
        if str(message.from_user.id) in  ADMINS_ID:
            await message.answer(
                f"Assalomu alaykum, {message.from_user.full_name}! Admin panelga xush kelibsiz.",
                reply_markup=admin_main_menu,
            )
        else:
            await message.answer(
                f"Assalomu alaykum, {message.from_user.full_name}!",
                reply_markup=user_main_menu,
            )

    # Bot komandalarini o'rnatish
    await bot.set_my_commands([BotCommand(command="/start", description="Botni qayta ishga tushirish")])

    # Pollingni boshlash
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi.")