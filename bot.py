import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# Bot Tokeningizni shu yerga yozing
API_TOKEN = '9013600582:AAHYCUtaTSA_eJYWpGZuDsBZzWZq__G1on4' # <--- O'zingizning Tokeningizni qo'ying

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# 1. Til tanlash menyusi (Oddiy tugmalar)
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

# 3. Raqamni qabul qilish va INLINE (Telegram ichida ochiladigan) Mini App tugmasini ko'rsatish
@dp.message_handler(content_types=['contact'])
async def contact_received(message: types.Message):
    web_app_url = "https://github.io" 
    
    # Xabar tagida chiqadigan maxsus Inline tugma
    app_inline_markup = InlineKeyboardMarkup()
    app_inline_markup.add(
        InlineKeyboardButton("🚀 NebulaBid App", web_app_info=WebAppInfo(url=web_app_url))
    )
    
    # Eski oddiy tugmalarni o'chirish uchun ReplyKeyboardRemove ishlatamiz
    await message.answer("Ro'yxatdan muvaffaqiyatli o'tdingiz!", reply_markup=types.ReplyKeyboardRemove())
    
    # Inline tugma bilan Mini App ni yuboramiz
    await message.answer("Mini App-ni ochish va savdo juftligini tanlash uchun pastdagi tugmani bosing:", reply_markup=app_inline_markup)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
