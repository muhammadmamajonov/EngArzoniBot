import os
from aiogram import Router, F, Bot
from aiogram.types import VideoNote, Video, ContentType
from sqlalchemy import select
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import Message, InlineQuery, InlineQueryResultArticle, InputTextMessageContent

from models import Elon
from states import ElonJoylashState

admin_elon_joylash_router = Router()
ADMINS_ID = [int(i) for i in os.getenv("ADMIN_ID").split(",")]
CHANNEL_ID = os.getenv("CHANNEL_ID")



@admin_elon_joylash_router.message(F.from_user.id.in_(ADMINS_ID), F.text == "E'lon joylash")
async def elon_joylash(message: Message, state: FSMContext):
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
        "Qaysi turdagi e'lon joylaymiz?",
        reply_markup=builder.as_markup()
    )
    await state.set_state(ElonJoylashState.elon_tanlash)


@admin_elon_joylash_router.inline_query()
async def inline_handler(inline_query: InlineQuery, session: AsyncSession, state: FSMContext):
    print(await state.get_state())
    """
    Inline so'rovni qayta ishlaydi.
    Kelgan so'rovga (avto/boshqa) qarab ma'lumotlarni filterlaydi.
    """
 
    query = inline_query.query.strip().lower() 
    # Ma'lumotlar bazasidan faqat kerakli turdagi ma'lumotlarni olamiz
    elonlar = await session.execute(select(Elon).where(Elon.type_ == query, Elon.posted == False).order_by(Elon.id.desc()).limit(50))
    elonlar = elonlar.scalars().all()

    results = []
    if len(elonlar) == 0:
        result = [InlineQueryResultArticle(
            id="1",
            title="Hozircha yangi murojatlar yo'q",
            input_message_content=InputTextMessageContent(
                message_text=f"Hozircha yangi murojatlar yo'q"
            )
        )]
        await inline_query.answer(result, cache_time=1)
        return

    if query == "avto":
        for elon in elonlar:
            results.append(
                InlineQueryResultArticle(
                    id=str(elon.id),
                    title=f"{elon.plate_number}",
                    description=elon.description,
                    input_message_content=InputTextMessageContent(
                        message_text=f"{elon.id}"
                    )
                )
            )
    elif query == "boshqa":
        for elon in elonlar:
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


@admin_elon_joylash_router.message(F.from_user.id.in_(ADMINS_ID), ElonJoylashState.elon_tanlash)
async def get_elon_id(message: Message, state: FSMContext):
    print(message.text)
    if message.text.isdigit():
        await message.answer("Video yuboring")
        await state.update_data(elon_id=message.text)
        await state.set_state(ElonJoylashState.video_joylash)


@admin_elon_joylash_router.message(
    F.from_user.id.in_(ADMINS_ID),
    (F.content_type == ContentType.VIDEO_NOTE) | (F.content_type == ContentType.VIDEO),
    ElonJoylashState.video_joylash
)
async def get_video_note(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    print(message.content_type)
    data = await state.get_data()
    elon_id = data["elon_id"]
    
    # Ma'lumotlar bazasidan e'lonni topish
    query = select(Elon).where(
        Elon.id == elon_id, Elon.posted == False
    )
    result = await session.execute(query)
    elon = result.scalar_one_or_none()

    if not elon:
        await message.answer(
            f"❗️'{elon_id}' idli yoki hali joylanmagan e'lon topilmadi. "
            f"idni tekshirib, qayta yuboring."
        )
        return
    
    # Kanalga post joylash
    try:
        if message.content_type == ContentType.VIDEO_NOTE:
            video_note_id = message.video_note.file_id
            sent_video = await bot.send_video_note(CHANNEL_ID, video_note_id)
            description_text = (
                f" Avtomobil: {elon.description}\n"
                f" Murojaat uchun: {elon.phone_number}\n"
            )
            sent_description = await bot.send_message(CHANNEL_ID, description_text)
            elon.video_id = sent_video.video_note.file_id
            elon.description_id = sent_description.message_id
        elif message.content_type == ContentType.VIDEO:
            video_id = message.video.file_id
            description_text = (
                f" {elon.description}\n"
                f" Murojaat uchun: {elon.phone_number}\n"
            )
            sent_video = await bot.send_video(CHANNEL_ID, video_id, caption=description_text)
            elon.video_id = sent_video.video.file_id
            elon.description_id = sent_video.message_id
        
        elon.posted = True
        await session.commit()

        await message.answer(
            f" E'lon kanalga muvaffaqiyatli joylandi.",
        )
        await state.clear()

    except Exception as e:
        await message.answer(f" Xatolik yuz berdi: {e}")
        await state.clear()

# @admin_elon_joylash_router.message()
# async def echo(message: Message, state: FSMContext):
#     print(await state.get_state())
#     print(message.text, message.from_user.first_name)
#     await message.reply(message.text)

# @admin_elon_joylash_router.message(F.from_user.in_(ADMINS_ID), PostCreation.waiting_for_plate)
# async def post_to_channel(
#     message: Message, state: FSMContext, session: AsyncSession, bot: Bot
# ):
#     plate_number = message.text.upper()
#     data = await state.get_data()
#     video_note_id = data["video_note_id"]

#     # Ma'lumotlar bazasidan e'lonni topish
#     query = select(Elon).where(
#         Elon.plate_number == plate_number, Elon.posted == False
#     )
#     result = await session.execute(query)
#     elon = result.scalar_one_or_none()

#     if not elon:
#         await message.answer(
#             f"❗️'{plate_number}' raqamli yoki hali joylanmagan e'lon topilmadi. "
#             f"Raqamni tekshirib, qayta yuboring."
#         )
#         return

#     # Kanalga post joylash
#     try:
#         sent_video = await bot.send_video_note(CHANNEL_ID, video_note_id)
#         description_text = (
#             f" Avtomobil: {elon.description}\n"
#             f" Murojaat uchun: {elon.phone_number}\n"
#         )
#         sent_description = await bot.send_message(CHANNEL_ID, description_text)

#         # DBni yangilash
#         elon.video_id = sent_video.video_note.file_id
#         elon.description_id = sent_description.message_id
#         elon.posted = True
#         await session.commit()

#         await message.answer(
#             f" E'lon kanalga muvaffaqiyatli joylandi.",
#         )
#         await state.clear()

#     except Exception as e:
#         await message.answer(f" Xatolik yuz berdi: {e}")
#         await state.clear()
