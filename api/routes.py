from fastapi import APIRouter
import random

router = APIRouter()

@router.get("/api/analyze/{pair}")
async def analyze_pair(pair: str):
    # VAQTINCHALIK TEST KODI
    return {
        "direction": "buy",
        "confirmations": 8,
        "confidence": 85,
        "entry": 2350.50,
        "tp": 2365.00,
        "sl": 2340.00,
        "reasons": ["EMA Trend yuqoriga", "RSI 55 (Neytral)", "MACD kesishdi", "ADX kuchli"]
    }

@router.get("/api/price/{pair}")
async def price(pair: str):
    # VAQTINCHALIK TEST KODI
    return {"price": 2350.50 + random.uniform(-2, 2)}
