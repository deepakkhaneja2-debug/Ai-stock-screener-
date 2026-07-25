import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="AI Stock Screener", layout="wide")

st.title("📈 AI Stock Screener")
st.write("Professional NSE Stock Scanner")

stocks = [
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS",
    "SBIN.NS",
    "LT.NS",
    "ITC.NS",
    "BHARTIARTL.NS",
    "AXISBANK.NS",
    "KOTAKBANK.NS",
    "BAJFINANCE.NS",
    "BAJAJFINSV.NS",
    "MARUTI.NS",
    "TITAN.NS",
    "SUNPHARMA.NS",
    "ASIANPAINT.NS",
    "ULTRACEMCO.NS",
    "NTPC.NS",
    "POWERGRID.NS",
    "NESTLEIND.NS",
    "INDUSINDBK.NS",
    "WIPRO.NS",
    "TATAMOTORS.NS",
    "TATASTEEL.NS",
    "HINDALCO.NS",
    "ONGC.NS",
    "COALINDIA.NS",
    "ADANIPORTS.NS",
    "ADANIENT.NS",
    "GRASIM.NS",
    "EICHERMOT.NS",
    "JSWSTEEL.NS",
    "BPCL.NS",
    "BRITANNIA.NS",
    "CIPLA.NS",
    "DRREDDY.NS",
    "HEROMOTOCO.NS",
    "HINDUNILVR.NS",
    "TECHM.NS"
]
def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

rows = []

for stock in stocks:
    try:
        print(f"Checking: {stock}")

        df = yf.download(
            stock,
            period="6mo",
            progress=False,
            auto_adjust=True
        )

        if df.empty:
            print(f"No data: {stock}")
            continue

        close = df["Close"]

        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]

        ema20 = close.ewm(span=20).mean().iloc[-1]
        ema50 = close.ewm(span=50).mean().iloc[-1]
        last_price = float(close.iloc[-1])
        last_rsi = float(rsi(close).iloc[-1])

        if last_price > ema20 and ema20 > ema50:
            signal = "BUY ✅"
        elif last_price < ema20 and ema20 < ema50:
            signal = "SELL ❌"
        else:
            signal = "WATCH 👀"

        rows.append([
            stock,
            round(last_price, 2),
            round(float(ema20), 2),
            round(float(ema50), 2),
            round(last_rsi, 2),
            signal
        ])

    except Exception as e:
        print(f"Error in {stock}: {e}")
        continue
    ]
)

st.dataframe(result, use_container_width=True)
