import os
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Elon
from keyboards.default import user_main_menu, region_keyboard
from .boshqa_elonlar import BoshqaElonStates
from keyboards.inline import sold_button, payment_type_buttons, confirm_sold_button

user_router = Router()
ADMIN_ID = os.getenv("ADMIN_ID")


class NewApplication(StatesGroup):
    region = State()
    phone_number = State()
    description = State()
    plate_number = State()


@user_router.message(F.text == "Avtomabil sotish")
async def new_application_start(message: Message, state: FSMContext):
    await message.answer("Viloyatni tanlang:", reply_markup=region_keyboard)

    await state.set_state(NewApplication.region)

# Viloyat tanlangach, manzil kiritish
@user_router.message(NewApplication.region)
async def get_region(message: Message, state: FSMContext):
	region = message.text
	if region not in ["Andijon", "Namangan", "Farg'ona"]:
		await message.answer("Iltimos, viloyatni tugmalardan birini tanlang.")
		return
	await state.update_data(region=region)
	await message.answer("Murojaat uchun telefon raqamingizni yuboring, agar mir nechta raqam yozmoqchi bo'lsangiz ',' bilan ajratib yozing (masalan: +998901234567,+998337654321):")
	await state.set_state(NewApplication.phone_number)


@user_router.message(NewApplication.phone_number)
async def get_phone_number(message: Message, state: FSMContext):
    await state.update_data(phone_number=message.text)
    await message.answer("Avtomobilingiz qanday, qisqa yozing! \nMisol uchun: Gentra 2018 AT")
    await state.set_state(NewApplication.description)


@user_router.message(NewApplication.description)
async def get_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Avtomobil davlat raqamini kiriting (masalan: 01A123BC). Bu adminlar uchun kerak kanalda ko'rinmaydi:")
    await state.set_state(NewApplication.plate_number)


@user_router.message(NewApplication.plate_number)
async def get_plate_number(
    message: Message, state: FSMContext, session: AsyncSession, bot: Bot
):
    await state.update_data(plate_number=message.text.upper())
    data = await state.get_data()

    new_elon = Elon(
        owner_id=message.from_user.id,
        phone_number=data["phone_number"],
        description=data["description"],
        plate_number=data["plate_number"],
        type_="avto",
        viloyat=data["region"],
    )
    session.add(new_elon)
    await session.commit()

    await message.answer(
        "✅ Murojaatingiz qabul qilindi! Tez orada admin siz bilan bog'lanadi.",
        reply_markup=user_main_menu,
    )

    # Adminga xabar yuborish
    admin_message = (
        f"🆕 Yangi murojaat!\n\n"
        f"👤 Foydalanuvchi: {message.from_user.full_name}\n"
        f"📞 Telefon: {data['phone_number']}\n"
        f"📝 Ma'lumot: {data['description']}\n"
        f"🔢 Davlat raqami: {data['plate_number']}"
    )
    await bot.send_message(ADMIN_ID, admin_message)
    await state.clear()


@user_router.message(F.text == "📄 Mening e'lonlarim")
async def my_applications(message: Message, session: AsyncSession):
    user_elons = await session.execute(
        select(Elon).where(
            Elon.owner_id == message.from_user.id, Elon.posted == True
        )
    )
    elons = user_elons.scalars().all()

    if not elons:
        await message.answer("Sizda hali e'lonlar mavjud emas.")
        return

    for elon in elons:
        if elon.type_ == "avto":
            text = f"🔢 Davlat raqami: {elon.plate_number}\n📝 Tavsif: {elon.description}"
        else:
            text = f"{elon.description.split('|')[-1]} \n📝 Tavsif: {elon.description}"
        if elon.sold:
            text += "\n\n<b>✅ SOTILGAN</b>"
            await message.answer(text)
        else:
            await message.answer(text, reply_markup=sold_button(elon.id))


# --- Sotish jarayoni ---
class SoldProcess(StatesGroup):
    waiting_for_check = State()


@user_router.callback_query(F.data.startswith("sold_"))
async def sold_process_start(query: CallbackQuery, state: FSMContext):
    elon_id = int(query.data.split("_")[1])
    await query.message.edit_text(
        "E'lonni sotilgan deb belgilash uchun to'lov turini tanlang:",
        reply_markup=payment_type_buttons(elon_id),
    )
    await query.answer()


@user_router.callback_query(F.data.startswith("send_check_"))
async def wait_for_check(query: CallbackQuery, state: FSMContext):
    elon_id = int(query.data.split("_")[-1])
    print(query.data.split("_"))
    await state.update_data(elon_id=elon_id)
    await query.message.edit_text(
        "Xizmat uchun to'lov chekini rasm shaklida yuboring."
    )
    await state.set_state(SoldProcess.waiting_for_check)
    await query.answer()


@user_router.message(SoldProcess.waiting_for_check, F.photo)
async def get_check_photo(
    message: Message, state: FSMContext, session: AsyncSession, bot: Bot
):
    data = await state.get_data()
    elon_id = data["elon_id"]

    photo = message.photo[-1]
    file_path = f"media/checks/{photo.file_id}.jpg"
    await bot.download(file=photo.file_id, destination=file_path)

    elon = await session.get(Elon, elon_id)
    if elon:
        elon.check_photo = file_path
        elon.sold = True
        await session.commit()

        await message.answer("✅ Rahmat! Chekingiz qabul qilindi. E'loningiz 'Sotildi' deb belgilanadi.")

        # Adminga xabar
        admin_message = (
            f"✅ E'lon sotildi (chek yuborildi)!\n\n"
            f"🔢 Davlat raqami: {elon.plate_number}\n"
            f"📝 Ma'lumot: {elon.description}\n"
            f"📞 Telefon: {elon.phone_number}"
        )
        await bot.send_video_note(ADMIN_ID, elon.video_id)
        await bot.send_photo(
            ADMIN_ID,
            photo.file_id,
            caption=admin_message,
            reply_markup=confirm_sold_button(elon.id),
        )

    await state.clear()


@user_router.callback_query(F.data.startswith("cash_payment_"))
async def cash_payment(query: CallbackQuery, session: AsyncSession, bot: Bot):
    elon_id = int(query.data.split("_")[2])
    elon = await session.get(Elon, elon_id)
    if elon:
        elon.pay_with_cash = True
        elon.sold = True
        await session.commit()

        await query.message.edit_text(
            "✅ Ma'lumot qabul qilindi. E'loningiz 'Sotildi' deb belgilanadi."
        )

        # Adminga xabar
        admin_message = (
            f"✅ E'lon sotildi (naqd pulda)!\n\n"
            f"🔢 Davlat raqami: {elon.plate_number}\n"
            f"📝 Ma'lumot: {elon.description}\n"
            f"📞 Telefon: {elon.phone_number}"
        )
        await bot.send_video_note(ADMIN_ID, elon.video_id)
        await bot.send_message(
            ADMIN_ID, admin_message, reply_markup=confirm_sold_button(elon.id)
        )
    await query.answer()