import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SIGNAL_INTERVAL_SEC = int(os.getenv("SIGNAL_INTERVAL_SEC", "300"))

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
scheduler = AsyncIOScheduler()

from bot.handlers import router as bot_router
dp.include_router(bot_router)

from engine.generator import scan_and_send

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Bazani ishga tushirish
    from bot.db import init_db
    await init_db()
    
    # 2. Eski webhookni o'chirish va Pollingni boshlash
    await bot.delete_webhook(drop_pending_updates=True)
    polling_task = asyncio.create_task(dp.start_polling(bot))
    print("✅ Bot polling rejimida ishga tushdi")
    
    # 3. Signal yuboruvchi taymerni ishga tushirish
    scheduler.add_job(scan_and_send, "interval", seconds=SIGNAL_INTERVAL_SEC, args=[bot])
    scheduler.start()
    print("✅ Scheduler started")
    
    yield
    
    # O'chirish jarayoni
    polling_task.cancel()
    scheduler.shutdown()
    await bot.session.close()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API yo'llarini ulash (Mini App uchun)
from api.routes import router as api_router
app.include_router(api_router)

# Render va boshqa tekshiruvlar uchun yagona Health Check
@app.get("/")
@app.head("/")
@app.get("/health")
async def health():
    return {"status": "ok", "app": "NebulaBid AI", "mode": "polling"}
