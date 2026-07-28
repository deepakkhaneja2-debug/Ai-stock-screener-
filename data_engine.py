import time
import logging
from typing import List, Dict

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

    def download_stock(self, symbol, interval="1d", period="6mo"):

        for attempt in range(self.retry_count):

            try:

                data = yf.download(
                    symbol,
                    interval=interval,
                    period=period,
                    progress=False,
                    auto_adjust=False
                )

                if data.empty:
                    raise Exception("No Data")

                data.dropna(inplace=True)

                if isinstance(data.columns,   
                pd.MultiIndex):
                    data.columns =  
               data.columns.get_level_values(0)

                return data

            except Exception as e:

                logging.warning(
                    f"{symbol} Retry {attempt+1} : {e}"
                )

                time.sleep(self.retry_delay)

        return pd.DataFrame()

    def download_multiple(self,
                          symbols: List[str],
                          interval="1d",
                          period="6mo"):

        result = {}

        for symbol in symbols:

            result[symbol] = self.download_stock(
                symbol,
                interval,
                period
            )

        return result
                            
    def validate_data(self, data):

        if data.empty:
            return False

        if len(data) < 100:
            return False

        return True


    def get_multi_timeframe_data(self, symbol):

        return {
            "1d": self.download_stock(symbol, "1d", "6mo"),
            "4h": self.download_stock(symbol, "4h", "6mo")
        }


    def get_market_index(self):

        return {
            "NIFTY": self.download_stock("^NSEI"),
            "BANKNIFTY": self.download_stock("^NSEBANK")
        }


    def clean_data(self, data):

        data = data.copy()

        data.drop_duplicates(inplace=True)

        data.dropna(inplace=True)

        return data 
      
    def load_symbols(self):

        if SCANNER_MODE == "CASH":

            return [
                "RELIANCE.NS",
                "TCS.NS",
                "INFY.NS",
                "HDFCBANK.NS",
                "ICICIBANK.NS"
            ]

        elif SCANNER_MODE == "FNO":

            return [
                "RELIANCE.NS",
                "SBIN.NS",
                "LT.NS",
                "AXISBANK.NS",
                "TATASTEEL.NS"
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


    def scan_ready_data(self):

        symbols = self.load_symbols()

        return self.download_multiple(
            symbols=symbols,
            interval=PRIMARY_TIMEFRAME,
            period="6mo"
        )
