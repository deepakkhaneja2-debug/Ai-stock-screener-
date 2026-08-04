import time
import logging
from typing import List, Dict

import pandas as pd
import yfinance as yf

from config import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DataEngine:
    """Handles data fetching and validation from Yahoo Finance."""

    def __init__(self):
        self.retry_count = 3
        self.retry_delay = 2
        self.auto_adjust = True
        self.min_data_rows = 100
        self.required_columns = ["Open", "High", "Low", "Close", "Volume"]

    def download_stock(
        self,
        symbol: str,
        interval: str = "1d",
        period: str = "6mo"
    ) -> pd.DataFrame:
        """Download a single stock's data with retries."""
        for attempt in range(self.retry_count):
            try:
                data = yf.download(
                    symbol,
                    interval=interval,
                    period=period,
                    progress=False,
                    auto_adjust=self.auto_adjust,
                    threads=False
                )
                if data is None or data.empty:
                    raise ValueError("No data received")

                # Flatten MultiIndex columns if present
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)

                # Validate required columns
                if not all(col in data.columns for col in self.required_columns):
                    raise ValueError("Missing required columns")

                data = self.clean_data(data)
                if data.empty:
                    raise ValueError("Data empty after cleaning")

                return data

            except Exception as e:
                logger.warning(f"{symbol} attempt {attempt+1}/{self.retry_count}: {e}")
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay)

        logger.error(f"Failed to download {symbol}")
        return pd.DataFrame()

    def download_multiple(
        self,
        symbols: List[str],
        interval: str = "1d",
        period: str = "6mo"
    ) -> Dict[str, pd.DataFrame]:
        """Download multiple stocks sequentially (no threading to avoid API issues)."""
        result = {}
        for symbol in symbols:
            data = self.download_stock(symbol, interval, period)
            if self.validate_data(data):
                result[symbol] = data
            else:
                logger.warning(f"{symbol} rejected after validation")
        return result

    def validate_data(self, data: pd.DataFrame) -> bool:
        """Check if data meets minimum requirements."""
        if data is None or data.empty:
            return False
        if len(data) < self.min_data_rows:
            return False
        if not all(col in data.columns for col in self.required_columns):
            return False
        return True

    def clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Clean and prepare data for analysis."""
        if data is None or data.empty:
            return pd.DataFrame()

        data = data.copy()

        # Remove duplicate timestamps
        data = data[~data.index.duplicated(keep="last")]

        # Convert to numeric and drop invalid rows
        numeric_cols = ["Open", "High", "Low", "Close", "Volume"]
        for col in numeric_cols:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors="coerce")

        data = data.dropna(subset=numeric_cols)

        # Remove non‑positive prices
        data = data[
            (data["Close"] > 0) &
            (data["High"] > 0) &
            (data["Low"] > 0)
        ]
        return data

    def load_symbols(self) -> List[str]:
        """Return list of symbols to scan based on config."""
        if WATCHLIST_ONLY:
            return ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]

        if SCANNER_MODE == "CASH":
            return [
                "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS",
                "ICICIBANK.NS", "SBIN.NS", "LT.NS", "AXISBANK.NS", "TATASTEEL.NS"
            ]
        elif SCANNER_MODE == "FNO":
            return [
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
        else:
            return [
                "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS",
                "ICICIBANK.NS", "SBIN.NS", "LT.NS", "AXISBANK.NS", "TATASTEEL.NS"
            ]

    def scan_ready_data(self) -> Dict[str, pd.DataFrame]:
        """Fetch and validate data for all symbols in the scan list."""
        symbols = self.load_symbols()
        logger.info(f"Scanning {len(symbols)} symbols")
        return self.download_multiple(
            symbols=symbols,
            interval=PRIMARY_TIMEFRAME,
            period="6mo"
        )