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


@admin_router.message(F.from_user.id.in_(ADMINS_ID), F.text == "🚗 Avtomobillar")
async def show_applications(message: Message, session: AsyncSession):
    unposted_elons = await session.execute(
        select(Elon).where(Elon.posted == False, Elon.type_ == "avto").order_by(Elon.id.asc())
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


@admin_router.message(F.from_user.id.in_(ADMINS_ID), F.text == "Boshqa e'lonlar")
async def boshqa_elonlar(message: Message, session: AsyncSession):
    unposted_elons = await session.execute(
        select(Elon).where(Elon.posted == False, Elon.type_ == "boshqa")
    )
    elons = unposted_elons.scalars().all()

    if not elons:
        await message.answer(" Hozircha yangi murojaatlar yo'q.")
        return

    response = "📬 Yangi e'lonlar:\n\n"
    for elon in elons:
        response += (
            f"🆔 E'lon ID: {elon.id}\n"
            f"👤 Yuboruvchi ID: {elon.owner_id}\n"
            f"📞 Telefon: {elon.phone_number}\n"
            f"📝 Tavsif: {elon.description}\n"
            f"---------------------\n"
        )
    await message.answer(response)



@admin_router.callback_query(
    F.from_user.id.in_(ADMINS_ID), F.data.startswith("confirm_sold_")
)
async def mark_as_sold_in_channel(query: CallbackQuery, session: AsyncSession, bot: Bot):
    elon_id = int(query.data.split("_")[2])
    elon = await session.get(Elon, elon_id)

    if not elon or not elon.description_id:
        await query.answer("❗️ E'lon yoki uning xabar IDsi topilmadi.", show_alert=True)
        return

    try:
       
        # Telefon raqamlarni olib tashlash uchun regex
        # new_text = re.sub(r"📞 Murojaat uchun: .*?\n", "", elon.description)
        if elon.type_ == 'avto':
            final_text = (
                f"Avtomobil: {elon.description}\n"
                f"<b>SOTILDI</b> \n\n"
            )
        else:
            final_text = f"{elon.description} \n <b>SOTILDI</b>"
            
        try:
            await bot.edit_message_text(
                text=final_text,
                chat_id=CHANNEL_ID,
                message_id=elon.description_id,
            )
        except:
            print("exept")
            await bot.edit_message_caption(
                chat_id=CHANNEL_ID,
                message_id=elon.description_id,
                caption=final_text
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