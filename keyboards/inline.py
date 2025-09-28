from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def sold_button(elon_id: int):
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="✅ Sotildi", callback_data=f"sold_{elon_id}")
    )
    return builder.as_markup()


def payment_type_buttons(elon_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🧾 Chek yuborish", callback_data=f"send_check_{elon_id}"
        ),
        InlineKeyboardButton(
            text="💵 Naqd pulda to'ladim", callback_data=f"cash_payment_{elon_id}"
        ),
    )
    return builder.as_markup()


def confirm_sold_button(elon_id: int):
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="✅ Sotildi deb belgilash", callback_data=f"confirm_sold_{elon_id}"
        )
    )
    return builder.as_markup()