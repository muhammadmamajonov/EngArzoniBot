import os
import re
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models import Elon
from keyboards.default import admin_main_menu

admin_router = Router()
ADMINS_ID = [int(i) for i in os.getenv("ADMIN_ID").split(",")]
CHANNEL_ID = os.getenv("CHANNEL_ID")



class PostCreation(StatesGroup):
    waiting_for_plate = State()


@admin_router.message(F.from_user.id.in_(ADMINS_ID), F.text == "📬 Murojaatlar")
async def show_applications(message: Message, session: AsyncSession):
    unposted_elons = await session.execute(
        select(Elon).where(Elon.posted == False)
    )
    elons = unposted_elons.scalars().all()

    if not elons:
        await message.answer(" Hozircha yangi murojaatlar yo'q.")
        return

    response = "📬 Yangi Murojaatlar:\n\n"
    for elon in elons:
        response += (
            f"🆔 Murojaat ID: {elon.id}\n"
            f"🔢 Raqami: {elon.plate_number}\n"
            f"👤 Yuboruvchi ID: {elon.owner_id}\n"
            f"📞 Telefon: {elon.phone_number}\n"
            f"📝 Tavsif: {elon.description}\n"
            f"---------------------\n"
        )
    await message.answer(response)


@admin_router.message(F.from_user.id.in_(ADMINS_ID), F.video_note)
async def get_video_note(message: Message, state: FSMContext):
    await state.update_data(video_note_id=message.video_note.file_id)
    await message.answer(
        "Video qabul qilindi. Endi shu avtomobilning davlat raqamini yuboring:"
    )
    await state.set_state(PostCreation.waiting_for_plate)


@admin_router.message(F.from_user.in_(ADMINS_ID), PostCreation.waiting_for_plate)
async def post_to_channel(
    message: Message, state: FSMContext, session: AsyncSession, bot: Bot
):
    plate_number = message.text.upper()
    data = await state.get_data()
    video_note_id = data["video_note_id"]

    # Ma'lumotlar bazasidan e'lonni topish
    query = select(Elon).where(
        Elon.plate_number == plate_number, Elon.posted == False
    )
    result = await session.execute(query)
    elon = result.scalar_one_or_none()

    if not elon:
        await message.answer(
            f"❗️'{plate_number}' raqamli yoki hali joylanmagan e'lon topilmadi. "
            f"Raqamni tekshirib, qayta yuboring."
        )
        return

    # Kanalga post joylash
    try:
        sent_video = await bot.send_video_note(CHANNEL_ID, video_note_id)
        description_text = (
            f" Avtomobil: {elon.description}\n"
            f" Murojaat uchun: {elon.phone_number}\n"
        )
        sent_description = await bot.send_message(CHANNEL_ID, description_text)

        # DBni yangilash
        elon.circled_video_id = sent_video.video_note.file_id
        elon.description_id = sent_description.message_id
        elon.posted = True
        await session.commit()

        await message.answer(
            f" E'lon ({plate_number}) kanalga muvaffaqiyatli joylandi.",
            reply_markup=admin_main_menu,
        )
        await state.clear()

    except Exception as e:
        await message.answer(f" Xatolik yuz berdi: {e}")
        await state.clear()


@admin_router.callback_query(
    F.from_user.in_(ADMINS_ID), F.data.startswith("confirm_sold_")
)
async def mark_as_sold_in_channel(query: CallbackQuery, session: AsyncSession, bot: Bot):
    elon_id = int(query.data.split("_")[2])
    elon = await session.get(Elon, elon_id)

    if not elon or not elon.description_id:
        await query.answer("❗️ E'lon yoki uning xabar IDsi topilmadi.", show_alert=True)
        return

    try:
       
        # Telefon raqamlarni olib tashlash uchun regex
        new_text = re.sub(r"📞 Murojaat uchun: .*?\n", "", elon.description)
        final_text = (
            f"<b>SOTILDI</b> \n\n"
            f"Avtomobil: {new_text}\n"
        )

        await bot.edit_message_text(
            text=final_text,
            chat_id=CHANNEL_ID,
            message_id=elon.description_id,
        )
        if query.message.caption:
            await query.message.edit_caption(
                caption=query.message.caption + "\n\n<b> KANALDA 'SOTILDI' DEB BELGILANDI</b>",
                reply_markup=None,
            )
        else:
            await query.message.edit_text(
                text=query.message.text + "\n\n<b> KANALDA 'SOTILDI' DEB BELGILANDI</b>",
                reply_markup=None,
            )
        await query.answer(" E'lon kanalda 'Sotildi' deb belgilandi.")

    except Exception as e:
        await query.answer(f" Xatolik: {e}", show_alert=True)