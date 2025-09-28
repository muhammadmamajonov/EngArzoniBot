from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

# Oddiy foydalanuvchi uchun
user_main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🆕 Yangi murojaat")],
        [KeyboardButton(text="📄 Mening e'lonlarim")],
    ],
    resize_keyboard=True,
)

# Admin uchun
admin_main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📬 Murojaatlar")],
        [KeyboardButton(text="📊 Statistika", web_app=WebAppInfo(url="https://engarzoni.netlify.app"))]
    ],
    resize_keyboard=True,
)