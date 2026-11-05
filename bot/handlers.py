from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import os
from bot.db import upsert_user, get_user

router = Router()

WEBAPP_URL = os.getenv("WEBAPP_URL", "")
CHANNEL_ID = os.getenv("CHANNEL_ID", "")
CHANNEL_URL = os.getenv("CHANNEL_URL", "")

class Flow(StatesGroup):
    lang = State()
    phone = State()
    pairs = State()

PAIRS = {
    "XAUUSD": "XAU/USD (Oltin)",
    "EURUSD": "EUR/USD",
    "GBPUSD": "GBP/USD",
    "USDJPY": "USD/JPY",
    "BTCUSD": "BTC/USD",
}

# ============ SUBSCRIPTION CHECK ============
async def check_sub(bot: Bot, user_id: int) -> bool:
    if not CHANNEL_ID:
        return True  # Kanal sozlanmagan bo'lsa — ruxsat
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception as e:
        print(f"check_sub error: {e}")
        return False

def join_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=CHANNEL_URL)],
        [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")],
    ])

# ============ KEYBOARDS ============
def lang_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang:uz")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en")],
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru")],
        [InlineKeyboardButton(text="🇹🇷 Türkçe", callback_data="lang:tr")],
    ])

def phone_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📞 Raqamni yuborish", request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )

def pairs_kb(selected):
    rows = []
    for code, name in PAIRS.items():
        mark = "✅" if code in selected else "⬜"
        rows.append([InlineKeyboardButton(text=f"{mark} {name}", callback_data=f"pair:{code}")])
    rows.append([InlineKeyboardButton(text="➡️ Davom etish", callback_data="pairs_done")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🚀 Mini App'ni ochish", web_app=WebAppInfo(url=WEBAPP_URL))]],
        resize_keyboard=True
    )

# ============ START ============
@router.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext, bot: Bot):
    # 1. Kanalga a'zolikni tekshir
    if not await check_sub(bot, msg.from_user.id):
        await msg.answer(
            "👋 Xush kelibsiz!\n\n"
            "Botdan foydalanish uchun avval kanalga a'zo bo'ling:",
            reply_markup=join_kb()
        )
        return
    
    # 2. Ro'yxatdan o'tganmi?
    user = await get_user(msg.from_user.id)
    if user and user.get("phone") and user.get("pairs"):
        # Allaqachon ro'yxatdan o'tgan — to'g'ridan-to'g'ri menyu
        await state.clear()
        await msg.answer(
            f"🏠 Xush kelibsiz, <b>{msg.from_user.first_name}</b>!\n\n"
            "Mini App'ni ochish uchun pastdagi tugmani bosing:",
            reply_markup=main_kb()
        )
        return
    
    # 3. Yangi foydalanuvchi — til so'rash
    await state.set_state(Flow.lang)
    await msg.answer(
        "👋 Xush kelibsiz, <b>NebulaBid AI</b>!\n\n"
        "🌐 Tilni tanlang:",
        reply_markup=lang_kb()
    )

# ============ CHECK SUBSCRIPTION ============
@router.callback_query(F.data == "check_sub")
async def check_sub_cb(cb: CallbackQuery, state: FSMContext, bot: Bot):
    if not await check_sub(bot, cb.from_user.id):
        await cb.answer("❌ Siz hali kanalga a'zo bo'lmadingiz!", show_alert=True)
        return
    
    await cb.message.delete()
    
    user = await get_user(cb.from_user.id)
    if user and user.get("phone") and user.get("pairs"):
        await cb.message.answer(
            f"🏠 Xush kelibsiz, <b>{cb.from_user.first_name}</b>!",
            reply_markup=main_kb()
        )
        await cb.answer()
        return
    
    await state.set_state(Flow.lang)
    await cb.message.answer(
        "✅ A'zolik tasdiqlandi!\n\n🌐 Tilni tanlang:",
        reply_markup=lang_kb()
    )
    await cb.answer()

# ============ LANGUAGE ============
@router.callback_query(F.data.startswith("lang:"))
async def pick_lang(cb: CallbackQuery, state: FSMContext, bot: Bot):
    if not await check_sub(bot, cb.from_user.id):
        await cb.answer("⚠️ Kanalga a'zo bo'ling!", show_alert=True)
        return
    
    lang = cb.data.split(":")[1]
    await upsert_user(cb.from_user.id, lang=lang)
    await state.update_data(lang=lang, pairs=set())
    
    # Til tanlangach — juftliklar
    await state.set_state(Flow.pairs)
    await cb.message.edit_text(
        "📊 Qaysi juftliklar bo'yicha signal olishni xohlaysiz?\n\n"
        "<i>Bir nechta tanlashingiz mumkin.</i>",
        reply_markup=pairs_kb(set())
    )
    await cb.answer()

# ============ PAIRS ============
@router.callback_query(F.data.startswith("pair:"))
async def toggle_pair(cb: CallbackQuery, state: FSMContext, bot: Bot):
    if not await check_sub(bot, cb.from_user.id):
        await cb.answer("⚠️ Kanalga a'zo bo'ling!", show_alert=True)
        return
    
    data = await state.get_data()
    selected = set(data.get("pairs", set()))
    code = cb.data.split(":")[1]
    if code in selected:
        selected.discard(code)
    else:
        selected.add(code)
    await state.update_data(pairs=selected)
    await cb.message.edit_reply_markup(reply_markup=pairs_kb(selected))
    await cb.answer()

@router.callback_query(F.data == "pairs_done")
async def pairs_done(cb: CallbackQuery, state: FSMContext, bot: Bot):
    if not await check_sub(bot, cb.from_user.id):
        await cb.answer("⚠️ Kanalga a'zo bo'ling!", show_alert=True)
        return
    
    data = await state.get_data()
    selected = data.get("pairs", set())
    if not selected:
        await cb.answer("Kamida bitta juftlik tanlang", show_alert=True)
        return
    
    names = ", ".join(PAIRS[c] for c in selected)
    await upsert_user(cb.from_user.id, pairs=",".join(selected))
    
    # Juftliklardan keyin — telefon
    await state.set_state(Flow.phone)
    await cb.message.edit_text(f"✅ Tanlandi: {names}")
    await cb.message.answer(
        "📱 Iltimos, telefon raqamingizni tasdiqlang:",
        reply_markup=phone_kb()
    )
    await cb.answer()

# ============ PHONE ============
@router.message(F.contact)
async def got_phone(msg: Message, state: FSMContext, bot: Bot):
    if not await check_sub(bot, msg.from_user.id):
        await msg.answer("⚠️ Kanalga a'zo bo'ling:", reply_markup=join_kb())
        return
    
    await upsert_user(msg.from_user.id, phone=msg.contact.phone_number)
    await msg.answer(
        "✅ Raqam tasdiqlandi!",
        reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True)
    )
    await state.clear()
    await msg.answer(
        "🎉 Ro'yxatdan o'tdingiz!\n\n"
        "🚀 Mini App'ni ochish uchun pastdagi tugmani bosing:",
        reply_markup=main_kb()
    )
