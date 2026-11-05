import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

# BotFather bergan uzun tokenni shu yerga qo'shtirnoq ichiga yozasiz
API_TOKEN = '74839201:AAHjg_misol_uchun' # <--- O'zingizning Tokeningizni qo'ying

# Log tizimini sozlash
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# 1. Til tanlash menyusi
lang_markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
lang_markup.add(KeyboardButton("🇺🇿 O'zbekcha"), KeyboardButton("🇷🇺 Русский"))

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.answer("Xush kelibsiz! Tilni tanlang / Dobro pojalovat! Vyberite yazyk:", reply_markup=lang_markup)

# 2. Telefon raqamni so'rash
@dp.message_handler(lambda message: message.text in ["🇺🇿 O'zbekcha", "🇷🇺 Русский"])
async def ask_phone(message: types.Message):
    phone_markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    phone_markup.add(KeyboardButton("📱 Raqamni yuborish / Otpravit nomer", request_contact=True))
    await message.answer("Ro'yxatdan o'tish uchun telefon raqamingizni yuboring:", reply_markup=phone_markup)

# 3. Raqamni qabul qilish va Mini App tugmasini ko'rsatish
@dp.message_handler(content_types=['contact'])
async def contact_received(message: types.Message):
    # Sizning tayyor Mini App havolangiz
    web_app_url = "https://github.io" 
    
    app_markup = ReplyKeyboardMarkup(resize_keyboard=True)
    app_markup.add(KeyboardButton("🚀 NebulaBid App", web_app_info=WebAppInfo(url=web_app_url)))
    
    await message.answer("Muvaffaqiyatli ro'yxatdan o'tdingiz! Mini App-ni oching va savdo juftligini tanlang:", reply_markup=app_markup)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
