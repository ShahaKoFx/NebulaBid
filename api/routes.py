from fastapi import APIRouter
from engine.analyzer import analyze
from engine.market import fetch

router = APIRouter()

@router.get("/api/analyze/{pair}")
async def analyze_pair(pair: str):
    try:
        sig = analyze(pair.upper())
        return sig or {"signal": None}
    except Exception as e:
        return {"error": str(e)}

@router.get("/api/price/{pair}")
async def price(pair: str):
    try:
        df = fetch(pair.upper(), "15m", "1d")
        if df.empty: return {"error": "no data"}
        return {"price": float(df["close"].iloc[-1])}
    except Exception as e:
        return {"error": str(e)}
