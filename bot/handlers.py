from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import os
from bot.db import upsert_user

router = Router()
WEBAPP_URL = os.getenv("WEBAPP_URL", "")

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

@router.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext):
    await state.set_state(Flow.lang)
    await msg.answer(
        "👋 Xush kelibsiz, <b>NebulaBid AI</b>!\n\n🌐 Tilni tanlang:",
        reply_markup=lang_kb()
    )

@router.callback_query(F.data.startswith("lang:"))
async def pick_lang(cb: CallbackQuery, state: FSMContext):
    lang = cb.data.split(":")[1]
    await upsert_user(cb.from_user.id, lang=lang)
    await state.update_data(lang=lang, pairs=set())
    await state.set_state(Flow.phone)
    await cb.message.answer(
        "📱 Iltimos, telefon raqamingizni tasdiqlang:",
        reply_markup=phone_kb()
    )
    await cb.answer()

@router.message(F.contact)
async def got_phone(msg: Message, state: FSMContext):
    await upsert_user(msg.from_user.id, phone=msg.contact.phone_number)
    await msg.answer("✅ Raqam tasdiqlandi!", reply_markup=ReplyKeyboardMarkup(keyboard=[], resize_keyboard=True))
    await state.set_state(Flow.pairs)
    await msg.answer(
        "📊 Qaysi juftliklar bo'yicha signal olishni xohlaysiz?\n\n<i>Bir nechta tanlashingiz mumkin.</i>",
        reply_markup=pairs_kb(set())
    )

@router.callback_query(F.data.startswith("pair:"))
async def toggle_pair(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = set(data.get("pairs", set()))
    code = cb.data.split(":")[1]
    if code in selected: selected.discard(code)
    else: selected.add(code)
    await state.update_data(pairs=selected)
    await cb.message.edit_reply_markup(reply_markup=pairs_kb(selected))
    await cb.answer()

@router.callback_query(F.data == "pairs_done")
async def pairs_done(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("pairs", set())
    if not selected:
        await cb.answer("Kamida bitta juftlik tanlang", show_alert=True)
        return
    names = ", ".join(PAIRS[c] for c in selected)
    await upsert_user(cb.from_user.id, pairs=",".join(selected))
    await state.clear()
    await cb.message.answer(f"✅ Tanlandi: {names}")
    await cb.message.answer("🚀 Mini App'ni ochish uchun pastdagi tugmani bosing:", reply_markup=main_kb())
    await cb.answer()
