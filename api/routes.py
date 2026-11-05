from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool
from engine.analyzer import analyze
from engine.market import fetch

router = APIRouter()

@router.get("/api/analyze/{pair}")
async def analyze_pair(pair: str):
    try:
        # Tahlilni orqa fonda ishlatamiz (serverni qotirmasligi uchun)
        sig = await run_in_threadpool(analyze, pair.upper())
        return sig or {"signal": None}
    except Exception as e:
        return {"error": str(e)}

@router.get("/api/price/{pair}")
async def price(pair: str):
    try:
        # Narxni orqa fonda olamiz
        df = await run_in_threadpool(fetch, pair.upper(), "15m", "1d")
        if df.empty: 
            return {"error": "Ma'lumot topilmadi (Yahoo bloklagan bo'lishi mumkin)"}
        return {"price": float(df["close"].iloc[-1])}
    except Exception as e:
        return {"error": str(e)}
