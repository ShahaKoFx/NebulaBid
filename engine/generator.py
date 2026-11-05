from bot.db import get_all_users
from engine.analyzer import analyze

PIP = {"XAUUSD":0.1,"EURUSD":0.0001,"GBPUSD":0.0001,"USDJPY":0.01,"BTCUSD":1.0}
NAME = {"XAUUSD":"XAU/USD (Oltin)","EURUSD":"EUR/USD","GBPUSD":"GBP/USD","USDJPY":"USD/JPY","BTCUSD":"BTC/USD"}

def fmt(sig):
    p=PIP[sig["pair"]]
    e,tp,sl=sig["entry"],sig["tp"],sig["sl"]
    tp_pips=round(abs(tp-e)/p,1)
    sl_pips=round(abs(sl-e)/p,1)
    bar="█"*sig["confirmations"]+"░"*(10-sig["confirmations"])
    d="🟢 SOTIB OLISH (BUY)" if sig["direction"]=="buy" else "🔴 SOTISH (SELL)"
    lines=[
        f"⭐ <b>NEBULABID AI</b> • {d} • {NAME[sig['pair']]} • M15",
        f"💪 Signal kuchi: {bar} {sig['confidence']}% ({sig['confirmations']} tasdiq)",
        "",
        f"📍 Kirish narxi: ${e:.2f}",
        f"🎯 TP: ${tp:.2f} (+{tp_pips} pips)",
        f"🛑 SL: ${sl:.2f} (-{sl_pips} pips)",
        "",
        "🧠 Nega shu signal:",
    ]
    for r in sig["reasons"]: lines.append(f"• {r}")
    lines += ["", "⚠️ Moliyaviy maslahat emas. Foyda kafolatlanmaydi."]
    return "\n".join(lines)

async def scan_and_send(bot):
    users = await get_all_users()
    if not users: return
    pairs = set()
    for u in users:
        for p in (u["pairs"] or "").split(","):
            if p: pairs.add(p)
    for pair in pairs:
        try:
            sig = analyze(pair)
        except Exception as e:
            print(f"analyze fail {pair}: {e}")
            continue
        if not sig: continue
        for u in users:
            if pair not in (u["pairs"] or "").split(","): continue
            try:
                await bot.send_message(u["tg_id"], fmt(sig), parse_mode="HTML")
            except Exception as e:
                print(f"send fail {u['tg_id']}: {e}")
