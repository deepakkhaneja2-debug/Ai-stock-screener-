import yfinance as yf
import pandas as pd
from data_engine import DataEngine

def rsi(s, p=14):
    d = s.diff()
    u = d.clip(lower=0)
    l = -d.clip(upper=0)
    rs = u.rolling(p).mean() / l.rolling(p).mean()
    return 100 - 100 / (1 + rs)

# Use the single source of truth for symbols
engine = DataEngine()
stocks = engine.load_symbols()

rows = []
for st in stocks:
    df = yf.download(st, period="6mo", progress=False, auto_adjust=True)
    if df.empty:
        continue
    c = df["Close"].squeeze()
    e20 = c.ewm(span=20).mean().iloc[-1]
    e50 = c.ewm(span=50).mean().iloc[-1]
    rv = rsi(c).iloc[-1]
    sig = "BUY" if c.iloc[-1] > e20 > e50 else "SELL" if c.iloc[-1] < e20 < e50 else "WATCH"
    rows.append([st, round(c.iloc[-1], 2), round(e20, 2), round(e50, 2), round(rv, 2), sig])

out = pd.DataFrame(rows, columns=["Stock", "Price", "EMA20", "EMA50", "RSI", "Signal"])
print(out)
out.to_excel("NSE_Scanner.xlsx", index=False)