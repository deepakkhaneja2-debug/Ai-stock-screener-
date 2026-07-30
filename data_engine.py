import time
import logging
from typing import List

import pandas as pd
import yfinance as yf

from config import *


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


class DataEngine:

    def __init__(self):

        self.retry_count = 3
        self.retry_delay = 2

    # =========================================
    # DOWNLOAD STOCK DATA
    # =========================================

    def download_stock(
        self,
        symbol,
        interval=None,
        period="6mo"
    ):

        if interval is None:
            interval = PRIMARY_TIMEFRAME

        for attempt in range(1, self.retry_count + 1):

            try:

                data = yf.download(
                    symbol,
                    interval=interval,
                    period=period,
                    progress=False,
                    auto_adjust=False,
                    threads=False
                )

                if data is None or data.empty:
                    raise ValueError("No market data received")

                # Flatten yfinance MultiIndex
                if isinstance(
                    data.columns,
                    pd.MultiIndex
                ):

                    data.columns = (
                        data.columns
                        .get_level_values(0)
                    )

                required_columns = [
                    "Open",
                    "High",
                    "Low",
                    "Close",
                    "Volume"
                ]

                missing = [
                    col
                    for col in required_columns
                    if col not in data.columns
                ]

                if missing:

                    raise ValueError(
                        f"Missing columns: {missing}"
                    )

                data = self.clean_data(data)

                if data.empty:
                    raise ValueError(
                        "Data empty after cleaning"
                    )

                return data

            except Exception as e:

                logging.warning(
                    f"{symbol} | "
                    f"{interval} | "
                    f"Attempt {attempt}/"
                    f"{self.retry_count} | {e}"
                )

                if attempt < self.retry_count:
                    time.sleep(self.retry_delay)

        logging.error(
            f"Failed to download {symbol} "
            f"({interval})"
        )

        return pd.DataFrame()

    # =========================================
    # DOWNLOAD MULTIPLE STOCKS
    # =========================================

    def download_multiple(
        self,
        symbols: List[str],
        interval=None,
        period="6mo"
    ):

        if interval is None:
            interval = PRIMARY_TIMEFRAME

        result = {}

        for symbol in symbols:

            data = self.download_stock(
                symbol=symbol,
                interval=interval,
                period=period
            )

            if self.validate_data(data):

                result[symbol] = data

            else:

                logging.warning(
                    f"{symbol} rejected "
                    f"after validation"
                )

        return result

    # =========================================
    # VALIDATE DATA
    # =========================================

    def validate_data(self, data):

        if data is None or data.empty:
            return False

        if len(data) < 100:
            return False

        required = [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume"
        ]

        for column in required:

            if column not in data.columns:
                return False

        return True

    # =========================================
    # CLEAN DATA
    # =========================================

    def clean_data(self, data):

        if data is None or data.empty:
            return pd.DataFrame()

        data = data.copy()

        # Remove duplicate timestamps
        data = data[
            ~data.index.duplicated(
                keep="last"
            )
        ]

        # Numeric conversion
        numeric_columns = [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume"
        ]

        for column in numeric_columns:

            if column in data.columns:

                data[column] = pd.to_numeric(
                    data[column],
                    errors="coerce"
                )

        # Remove invalid rows
        data.dropna(
            subset=numeric_columns,
            inplace=True
        )

        # Remove zero/negative prices
        data = data[
            (data["Close"] > 0) &
            (data["High"] > 0) &
            (data["Low"] > 0)
        ]

        return data

    # =========================================
    # MULTI TIMEFRAME DATA
    # =========================================

    def get_multi_timeframe_data(
        self,
        symbol
    ):

        primary = self.download_stock(
            symbol=symbol,
            interval=PRIMARY_TIMEFRAME,
            period="6mo"
        )

        confirmation = self.download_stock(
            symbol=symbol,
            interval=CONFIRMATION_TIMEFRAME,
            period="60d"
        )

        return {

            "primary": primary,

            "confirmation": confirmation
        }

    # =========================================
    # MARKET INDEX DATA
    # =========================================

    def get_market_index(self):

        market_data = {}

        if USE_NIFTY_FILTER:

            nifty = self.download_stock(
                symbol="^NSEI",
                interval=PRIMARY_TIMEFRAME,
                period="6mo"
            )

            if self.validate_data(nifty):
                market_data["NIFTY"] = nifty

        if USE_BANKNIFTY_FILTER:

            banknifty = self.download_stock(
                symbol="^NSEBANK",
                interval=PRIMARY_TIMEFRAME,
                period="6mo"
            )

            if self.validate_data(banknifty):
                market_data["BANKNIFTY"] = banknifty

        return market_data

    # =========================================
    # LOAD SYMBOLS
    # =========================================

    def load_symbols(self):

        if WATCHLIST_ONLY:

            return [
                "RELIANCE.NS",
                "TCS.NS",
                "INFY.NS",
                "HDFCBANK.NS",
                "ICICIBANK.NS"
            ]

        if SCANNER_MODE == "CASH":

            return [
                "RELIANCE.NS",
                "TCS.NS",
                "INFY.NS",
                "HDFCBANK.NS",
                "ICICIBANK.NS",
                "SBIN.NS",
                "LT.NS",
                "AXISBANK.NS",
                "TATASTEEL.NS"
            ]

        elif SCANNER_MODE == "FNO":

            return [
                "RELIANCE.NS",
                "SBIN.NS",
                "LT.NS",
                "AXISBANK.NS",
                "TATASTEEL.NS",
                "ICICIBANK.NS",
                "HDFCBANK.NS"
            ]

        else:

            return [
                "RELIANCE.NS",
                "TCS.NS",
                "INFY.NS",
                "HDFCBANK.NS",
                "ICICIBANK.NS",
                "SBIN.NS",
                "LT.NS",
                "AXISBANK.NS",
                "TATASTEEL.NS"
            ]

    # =========================================
    # SCANNER READY DATA
    # =========================================

    def scan_ready_data(self):

        symbols = self.load_symbols()

        logging.info(
            f"Scanning {len(symbols)} symbols"
        )

        return self.download_multiple(
            symbols=symbols,
            interval=PRIMARY_TIMEFRAME,
            period="6mo"
        )