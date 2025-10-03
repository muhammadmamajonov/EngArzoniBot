from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

# Oddiy foydalanuvchi uchun
user_main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Avtomabil sotish")],
        [KeyboardButton(text="Boshqa e'lon")],
        [KeyboardButton(text="📄 Mening e'lonlarim")],
    ],
    resize_keyboard=True,
)

# Admin uchun
admin_main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="E'lon joylash")],
        [KeyboardButton(text="🚗 Avtomobillar"), KeyboardButton(text="Boshqa e'lonlar")],
        [KeyboardButton(text="📊 Statistika", web_app=WebAppInfo(url="https://engarzoni.netlify.app"))]
    ],
    resize_keyboard=True,
)

# Viloyat tanlash uchun keyboard
region_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Andijon"),
            KeyboardButton(text="Namangan"),
            KeyboardButton(text="Farg'ona"),
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)

yaqunlash_button = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Yakunlash")]],
    resize_keyboard=True)