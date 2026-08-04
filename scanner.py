#!/usr/bin/env python3
"""
Standalone scanner script for AI Stock Scanner V1.4.
Scans all 39 NSE stocks and exports results to Excel.
"""

import yfinance as yf
import pandas as pd
from data_engine import DataEngine


def rsi(s: pd.Series, p: int = 14) -> pd.Series:
    """Calculate RSI for a price series."""
    d = s.diff()
    u = d.clip(lower=0)
    l = -d.clip(upper=0)
    rs = u.rolling(p).mean() / l.rolling(p).mean()
    return 100 - 100 / (1 + rs)


def main() -> None:
    """Main scanner function."""
    print("AI Stock Scanner V1.4")
    print("Loading symbols...")
    
    # Use the single source of truth for symbols
    engine = DataEngine()
    stocks = engine.load_symbols()
    print(f"Scanning {len(stocks)} stocks...")
    
    rows = []
    for st in stocks:
        try:
            print(f"  Processing {st}...")
            df = yf.download(st, period="6mo", progress=False, auto_adjust=True)
            if df.empty:
                print(f"    No data for {st}")
                continue
            
            c = df["Close"].squeeze()
            e20 = c.ewm(span=20).mean().iloc[-1]
            e50 = c.ewm(span=50).mean().iloc[-1]
            rv = rsi(c).iloc[-1]
            
            # Signal logic
            if c.iloc[-1] > e20 > e50:
                sig = "BUY"
            elif c.iloc[-1] < e20 < e50:
                sig = "SELL"
            else:
                sig = "WATCH"
            
            rows.append([st, round(c.iloc[-1], 2), round(e20, 2), round(e50, 2), round(rv, 2), sig])
            print(f"    {st}: {sig} @ ₹{round(c.iloc[-1], 2)}")
            
        except Exception as e:
            print(f"    Error processing {st}: {e}")
    
    # Create DataFrame and export
    out = pd.DataFrame(rows, columns=["Stock", "Price", "EMA20", "EMA50", "RSI", "Signal"])
    print(f"\nScan complete. Found {len(out)} stocks with data.")
    print(out.to_string())
    
    out.to_excel("NSE_Scanner.xlsx", index=False)
    print("Results saved to NSE_Scanner.xlsx")


if __name__ == "__main__":
    main()