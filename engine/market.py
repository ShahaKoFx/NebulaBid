import yfinance as yf
import pandas as pd

YF = {
    "XAUUSD": "GC=F", "EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X",
    "USDJPY": "USDJPY=X", "BTCUSD": "BTC-USD",
}

def fetch(pair, interval="15m", period="5d"):
    df = yf.download(YF[pair], interval=interval, period=period, progress=False, auto_adjust=False)
    if df.empty: return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"})
    return df.dropna()
