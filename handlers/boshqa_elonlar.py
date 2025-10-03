
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.default import region_keyboard, user_main_menu

from models import Elon
from sqlalchemy.ext.asyncio import AsyncSession
import os

ADMINS_ID = [int(i) for i in os.getenv("ADMIN_ID").split(",")] if os.getenv("ADMIN_ID") else []


boshqa_router = Router()

# FSM States
class BoshqaElonStates(StatesGroup):
	region = State()
	address = State()
	product = State()
	phone_numbers = State()
	

# Boshqa e'lon boshlanishi
@boshqa_router.message(F.text == "Boshqa e'lon")
async def start_boshqa_elon(message: Message, state: FSMContext):
	await message.answer("Viloyatni tanlang:", reply_markup=region_keyboard)
	await state.set_state(BoshqaElonStates.region)	

# Viloyat tanlangach, manzil kiritish
@boshqa_router.message(BoshqaElonStates.region)
async def get_region(message: Message, state: FSMContext):
	region = message.text
	if region not in ["Andijon", "Namangan", "Farg'ona"]:
		await message.answer("Iltimos, viloyatni tugmalardan birini tanlang.")
		return
	await state.update_data(region=region)
	await message.answer("Manzilni kiriting(tuman/shaxar):", reply_markup=None)
	await state.set_state(BoshqaElonStates.address)

# Manzil kiritilgach, mahsulot nomini so'rash
@boshqa_router.message(BoshqaElonStates.address)
async def get_address(message: Message, state: FSMContext):
	address = message.text
	await state.update_data(address=address)
	await message.answer("Nimani sotmoqchisiz? (Mahsulot nomini yozing):")
	await state.set_state(BoshqaElonStates.product)


# Mahsulot nomi kiritilgach, telefon raqam(lar) so'rash
@boshqa_router.message(BoshqaElonStates.product)
async def get_product(message: Message, state: FSMContext):
	product = message.text
	await state.update_data(product=product)
	await state.update_data(phone_numbers=[])  # Bo'sh ro'yxat
	await message.answer("Murojaat uchun telefon raqam kiriting. Agar bir nechta raqam kiritmoqchi bo'lsangiz ',' bilan ajratib yozing:")
	await state.set_state(BoshqaElonStates.phone_numbers)


@boshqa_router.message(BoshqaElonStates.phone_numbers)
async def get_phone_numbers(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
	text = message.text.strip()
	data = await state.get_data()
	
	# Barcha ma'lumotlarni olish
	data = await state.get_data()
	region = data.get("region")
	address = data.get("address")
	product = data.get("product")
	phone_str = text
	owner_id = message.from_user.id

	# Bazaga saqlash uchun model (Elon) moslashtirish
	new_elon = Elon(
		owner_id=owner_id,
		phone_number=phone_str,
		viloyat=region,
		description=f"{region}, {address} | {product}",
		plate_number="BOSHQA E'lon",
		type_="boshqa",
	)
	session.add(new_elon)
	await session.commit()

	# Adminlarga yuborish
	admin_text = (
		f"<b>Yangi boshqa e'lon!</b>\n"
		f"<b>Viloyat:</b> {region}\n"
		f"<b>Manzil:</b> {address}\n"
		f"<b>Mahsulot:</b> {product}\n"
		f"<b>Telefon:</b> {phone_str}\n"
		f"<b>Foydalanuvchi ID:</b> {owner_id}"
	)
	for admin_id in ADMINS_ID:
		try:
			await bot.send_message(admin_id, admin_text)
		except Exception:
			pass

	await message.answer("E'loningiz qabul qilindi! Tez orada adminlar siz bilan bog'lanishadi.", reply_markup=user_main_menu)
	await state.clear()
	return
	



