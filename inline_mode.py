import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineQuery, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from models import Elon

from db import async_session

BOT_TOKEN = "6663857422:AAFM9C0m1mnlpr1W9oIBoJ845Ane__vgZwY"

dp = Dispatcher()
bot = Bot(BOT_TOKEN)


@dp.message(CommandStart())
async def command_start_handler(message: Message):
    await message.answer(f"Assalomu alaykum, {message.from_user.full_name}!\n"
                         f"E'lonlarni qidirish uchun /search buyrug'ini bosing.")

@dp.message(Command("search"))
async def search_handler(message: Message):
    print(message.content_type, "--------------------")
    """Foydalanuvchiga inline rejimga o'tish tugmalarini yuboradi."""
    builder = InlineKeyboardBuilder()
    
    # 1-tugma: "Avto"
    builder.button(
        text="Avto",
        # Bu parametr bosilganda yozish maydoniga @bot_nomi avto deb yozadi
        switch_inline_query_current_chat="avto" 
    )
    
    # 2-tugma: "Boshqa"
    builder.button(
        text="Boshqa",
        # Bu parametr bosilganda yozish maydoniga @bot_nomi boshqa deb yozadi
        switch_inline_query_current_chat="boshqa"
    )
    
    builder.adjust(2) # Tugmalarni bir qatorda 2 tadan joylashtiradi

    await message.answer(
        "Qaysi turdagi e'lonlarni qidiramiz?",
        reply_markup=builder.as_markup()
    )


@dp.inline_query()
async def inline_handler(inline_query: InlineQuery):
    """
    Inline so'rovni qayta ishlaydi.
    Kelgan so'rovga (avto/boshqa) qarab ma'lumotlarni filterlaydi.
    """
    db = async_session()
    # Foydalanuvchi yozgan matnni olamiz (masalan, "avto" yoki "boshqa")
    query = inline_query.query.strip().lower() 
    print(f"Inline query received: {query}")
    # Ma'lumotlar bazasidan faqat kerakli turdagi ma'lumotlarni olamiz
    organizations = await db.execute(select(Elon).where(Elon.type_ == query).order_by(Elon.id.desc()).limit(50))
    organizations = organizations.scalars().all()

    results = []
    if query == "avto":
        for elon in organizations:
            results.append(
                InlineQueryResultArticle(
                    id=str(elon.id),
                    title=f"{elon.description} {elon.plate_number}",
                    input_message_content=InputTextMessageContent(
                        message_text=f"{elon.plate_number}"
                    )
                )
            )
    elif query == "boshqa":
        for elon in organizations:
            results.append(
                InlineQueryResultArticle(
                    id=str(elon.id),
                    title=elon.description,
                    description=f"{elon.viloyat} | {elon.phone_number}",
                    input_message_content=InputTextMessageContent(
                        message_text=f"{elon.id}"
                    )
                )
            )

    await inline_query.answer(results, cache_time=1)


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())