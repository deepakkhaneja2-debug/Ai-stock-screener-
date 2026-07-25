import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="AI Stock Screener", layout="wide")

st.title("📈 AI Stock Screener V1")
st.write("Professional NSE Stock Scanner")

# ==========================
# NSE Stocks
# ==========================

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

# ==========================
# RSI Function
# ==========================

def calculate_rsi(close, period=14):
    delta = close.diff()

    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    return rsi

# Result list
rows = []
# ==========================
# Scan Stocks
# ==========================

for stock in stocks:
    try:
        df = yf.download(
            stock,
            period="6mo",
            progress=False,
            auto_adjust=True
        )

        if df.empty:
            continue

        close = df["Close"]

        # Handle MultiIndex
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]

        # EMA
        ema20 = close.ewm(span=20, adjust=False).mean()
        ema50 = close.ewm(span=50, adjust=False).mean()

        # RSI
        rsi = calculate_rsi(close)

        # MACD
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()

        macd = ema12 - ema26
        signal_line = macd.ewm(span=9, adjust=False).mean()

        price = float(close.iloc[-1])

        ema20_last = float(ema20.iloc[-1])
        ema50_last = float(ema50.iloc[-1])

        rsi_last = float(rsi.iloc[-1])
        macd_last = float(macd.iloc[-1])
        signal_last = float(signal_line.iloc[-1])

        # AI Score
        score = 0

        if price > ema20_last:
            score += 20

        if ema20_last > ema50_last:
            score += 20

        if 50 <= rsi_last <= 70:
            score += 20

        if macd_last > signal_last:
            score += 20

        if price > ema50_last:
            score += 20

        # Signal
        if score >= 80:
            signal = "STRONG BUY 🟢"
        elif score >= 60:
            signal = "BUY ✅"
        elif score >= 40:
            signal = "WATCH 👀"
        else:
            signal = "SELL ❌"

        rows.append([
            stock,
            round(price,2),
            round(ema20_last,2),
            round(ema50_last,2),
            round(rsi_last,2),
            round(macd_last,2),
            score,
            signal
        ])

    except Exception as e:
        print(stock, e)
        continue
# ==========================
# Create DataFrame
# ==========================

result = pd.DataFrame(
    rows,
    columns=[
        "Stock",
        "Price",
        "EMA20",
        "EMA50",
        "RSI",
        "MACD",
        "AI Score",
        "Signal"
    ]
)

# Sort by AI Score
result = result.sort_values(
    by="AI Score",
    ascending=False
)

# ==========================
# Search Box
# ==========================

search = st.text_input("🔍 Search Stock")

if search:
    result = result[
        result["Stock"].str.contains(search.upper())
    ]

# ==========================
# Show Table
# ==========================

st.dataframe(
    result,
    use_container_width=True
)

# ==========================
# Download Excel
# ==========================

csv = result.to_csv(index=False).encode("utf-8")

st.download_button(
    label="📥 Download CSV",
    data=csv,
    file_name="AI_Stock_Scanner.csv",
    mime="text/csv"
)

st.success("✅ Scanner Completed Successfully")
# AI Stock Screener V1 Backup
