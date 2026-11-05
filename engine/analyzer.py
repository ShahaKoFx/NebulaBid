import pandas as pd, numpy as np
from engine.market import fetch

def ema(s, p): return s.ewm(span=p, adjust=False).mean()

def rsi(s, p=14):
    d = s.diff()
    g = d.where(d>0,0).rolling(p).mean()
    l = -d.where(d<0,0).rolling(p).mean()
    return 100 - 100/(1+g/l)

def macd(s):
    m = ema(s,12) - ema(s,26)
    sg = ema(m,9)
    return m, sg, m-sg

def atr(h,l,c,p=14):
    tr = pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    return tr.rolling(p).mean()

def adx(h,l,c,p=14):
    up=h.diff(); dn=-l.diff()
    pdm=np.where((up>dn)&(up>0),up,0.0)
    mdm=np.where((dn>up)&(dn>0),dn,0.0)
    tr=pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    a=tr.rolling(p).mean()
    pdi=100*pd.Series(pdm,index=h.index).rolling(p).mean()/a
    mdi=100*pd.Series(mdm,index=h.index).rolling(p).mean()/a
    dx=100*(pdi-mdi).abs()/(pdi+mdi)
    return dx.rolling(p).mean(), pdi, mdi

def bollinger(s,p=20,k=2):
    ma=s.rolling(p).mean(); sd=s.rolling(p).std()
    return ma+k*sd, ma, ma-k*sd

def keltner(h,l,c,p=20,k=2):
    ma=ema(c,p); a=atr(h,l,c,p)
    return ma+k*a, ma, ma-k*a

def stochastic(h,l,c,p=14):
    low=l.rolling(p).min(); high=h.rolling(p).max()
    return 100*(c-low)/(high-low)

def analyze(pair):
    m15 = fetch(pair, "15m", "5d")
    h1  = fetch(pair, "1h", "1mo")
    if m15.empty or h1.empty or len(m15)<50 or len(h1)<50: return None

    c=m15["close"]; h=m15["high"]; l=m15["low"]; hc=h1["close"]
    ema20=ema(c,20).iloc[-1]; ema50=ema(c,50).iloc[-1]
    rsi_v=rsi(c).iloc[-1]
    _,_,hist=macd(c); hist=hist.iloc[-1]
    adx_v,pdi,mdi=adx(h,l,c); adx_v=adx_v.iloc[-1]
    bb_u,bb_m,bb_l=bollinger(c)
    kc_u,kc_m,kc_l=keltner(h,l,c)
    stoch=stochastic(h,l,c).iloc[-1]
    atr_v=atr(h,l,c).iloc[-1]
    price=c.iloc[-1]
    vol_ma=m15["volume"].rolling(20).mean().iloc[-1]
    vol_now=m15["volume"].iloc[-1]

    h1_ema50=ema(hc,50).iloc[-1]
    h1_ema200=ema(hc,200).iloc[-1] if len(hc)>=200 else h1_ema50
    h1_trend="up" if h1_ema50>h1_ema200 else "down"

    confs=[]
    confs.append(("EMA20 > EMA50", "buy" if ema20>ema50 else "sell"))
    confs.append((f"RSI {rsi_v:.0f}", "buy" if rsi_v>50 else "sell"))
    confs.append(("MACD hist +", "buy" if hist>0 else "sell"))
    if adx_v>25:
        confs.append((f"ADX {adx_v:.0f}", "buy" if pdi.iloc[-1]>mdi.iloc[-1] else "sell"))
    confs.append(("Bollinger", "buy" if price>bb_m.iloc[-1] else "sell"))
    if price>kc_u.iloc[-1]: confs.append(("Keltner yuqori", "buy"))
    elif price<kc_l.iloc[-1]: confs.append(("Keltner past", "sell"))
    confs.append((f"Stoch {stoch:.0f}", "buy" if stoch>50 else "sell"))
    if vol_now>vol_ma: confs.append(("Hajm", "buy" if price>c.iloc[-2] else "sell"))
    confs.append((f"H1 {h1_trend}", "buy" if h1_trend=="up" else "sell"))
    confs.append(("Price action", "buy" if c.iloc[-1]>c.iloc[-5] else "sell"))

    buys=sum(1 for _,d in confs if d=="buy")
    sells=sum(1 for _,d in confs if d=="sell")
    direction="buy" if buys>=sells else "sell"
    n=max(buys,sells)
    conf=int(n/len(confs)*100)

    if n<7: return None

    if direction=="buy":
        tp=price+atr_v*2; sl=price-atr_v*1
    else:
        tp=price-atr_v*2; sl=price+atr_v*1

    reasons=[r for r,d in confs if d==direction][:6]
    return {
        "pair":pair,"direction":direction,
        "entry":float(price),"tp":float(tp),"sl":float(sl),
        "confidence":conf,"confirmations":n,"reasons":reasons,
    }
