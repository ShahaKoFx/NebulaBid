import yfinance as yf
import pandas as pd
import requests

YF = {
    "XAUUSD": "GC=F", "EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X",
    "USDJPY": "USDJPY=X", "BTCUSD": "BTC-USD",
}

def fetch(pair, interval="15m", period="5d"):
    symbol = YF.get(pair.upper(), "GC=F")
    
    # Brauzer kabi ko'rinish (Yahoo bloklab qo'ymasligi uchun)
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    try:
        ticker = yf.Ticker(symbol, session=session)
        # timeout=10 qo'shildi, shunda server qotib qolmaydi
        df = ticker.history(interval=interval, period=period, timeout=10)
        
        if df.empty: 
            return pd.DataFrame()
            
        df = df.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"})
        return df.dropna()
    except Exception as e:
        print(f"YFinance xatosi: {e}")
        return pd.DataFrame()
