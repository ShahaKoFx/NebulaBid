import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Update
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
SIGNAL_INTERVAL_SEC = int(os.getenv("SIGNAL_INTERVAL_SEC", "300"))

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
scheduler = AsyncIOScheduler()

from bot.handlers import router as bot_router
dp.include_router(bot_router)

from engine.generator import scan_and_send

@asynccontextmanager
async def lifespan(app: FastAPI):
    from bot.db import init_db
    await init_db()
    try:
        await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
        print(f"✅ Webhook set: {WEBHOOK_URL}")
    except Exception as e:
        print(f"❌ Webhook error: {e}")
    scheduler.add_job(scan_and_send, "interval", seconds=SIGNAL_INTERVAL_SEC, args=[bot])
    scheduler.start()
    print("✅ Bot started")
    yield
    scheduler.shutdown()
    await bot.session.close()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from api.routes import router as api_router
app.include_router(api_router)

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot, update)
    return {"ok": True}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"app": "NebulaBid AI", "status": "running"}
