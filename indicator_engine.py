import pandas as pd
import numpy as np

from config import *


class IndicatorEngine:

    def __init__(self):
        pass

    # ===============================
    # EMA
    # ===============================

    def ema(self, data, period):

        return data["Close"].ewm(
            span=period,
            adjust=False
        ).mean()

    # ===============================
    # RSI
    # ===============================

    def rsi(self, data, period=14):

        delta = data["Close"].diff()

        gain = delta.clip(lower=0)

        loss = -delta.clip(upper=0)

        avg_gain = gain.rolling(period).mean()

        avg_loss = loss.rolling(period).mean()

        # Prevent division by zero
        avg_loss_safe = avg_loss.replace(0, np.nan)

        rs = avg_gain / avg_loss_safe

        rsi = 100 - (100 / (1 + rs))

        # Fill NaN values with 50 (neutral) if needed
        rsi = rsi.fillna(50)

        return rsi

    # ===============================
    # ATR
    # ===============================

    def atr(self, data, period=14):

        high_low = data["High"] - data["Low"]

        high_close = np.abs(
            data["High"] - data["Close"].shift()
        )

        low_close = np.abs(
            data["Low"] - data["Close"].shift()
        )

        ranges = pd.concat(
            [high_low, high_close, low_close],
            axis=1
        )

        true_range = ranges.max(axis=1)

        atr = true_range.rolling(period).mean()

        return atr

    # ===============================
    # Add Basic Indicators
    # ===============================

    def add_basic_indicators(self, data):

        data = data.copy()

        data["EMA20"] = self.ema(data, EMA_FAST)

        data["EMA50"] = self.ema(data, EMA_SLOW)

        data["RSI"] = self.rsi(data)

        data["ATR"] = self.atr(data)

        return data

    # ===============================
    # MACD
    # ===============================

    def macd(self, data):

        # Use config constants
        ema12 = data["Close"].ewm(span=MACD_FAST, adjust=False).mean()

        ema26 = data["Close"].ewm(span=MACD_SLOW, adjust=False).mean()

        macd = ema12 - ema26

        signal = macd.ewm(span=MACD_SIGNAL, adjust=False).mean()

        histogram = macd - signal

        return macd, signal, histogram

    # ===============================
    # VWAP
    # ===============================

    def vwap(self, data):

        tp = (
            data["High"] +
            data["Low"] +
            data["Close"]
        ) / 3

        vol_cum = data["Volume"].cumsum()

        # Prevent division by zero
        vol_cum_safe = vol_cum.replace(0, 1)

        return ((tp * data["Volume"]).cumsum() / vol_cum_safe)

    # ===============================
    # Volume Average
    # ===============================

    def volume_ma(self, data, period=20):

        return data["Volume"].rolling(period).mean()

    # ===============================
    # Volume Spike
    # ===============================

    def volume_spike(self, data, vol_ma=None):

        if vol_ma is None:
            vol_ma = self.volume_ma(data)

        return data["Volume"] > (vol_ma * 1.5)

    # ===============================
    # Add Advanced Indicators
    # ===============================

    def add_advanced_indicators(self, data):

        macd, signal, hist = self.macd(data)

        data["MACD"] = macd

        data["MACD_SIGNAL"] = signal

        data["MACD_HIST"] = hist

        data["VWAP"] = self.vwap(data)

        data["VOL_MA"] = self.volume_ma(data)

        # Use precomputed VOL_MA for volume spike
        data["VOL_SPIKE"] = self.volume_spike(data, vol_ma=data["VOL_MA"])

        return data

    # ===============================
    # Trend Score
    # ===============================

    def trend_score(self, data):

        if data.empty:
            return 0

        score = 0

        if data["EMA20"].iloc[-1] > data["EMA50"].iloc[-1]:
            score += 30

        if data["Close"].iloc[-1] > data["VWAP"].iloc[-1]:
            score += 20

        if data["MACD"].iloc[-1] > data["MACD_SIGNAL"].iloc[-1]:
            score += 20

        if data["VOL_SPIKE"].iloc[-1]:
            score += 15

        if data["RSI"].iloc[-1] > 55:
            score += 15

        return score

    # ===============================
    # Momentum Score
    # ===============================

    def momentum_score(self, data):

        if data.empty:
            return 0

        score = 0

        rsi = data["RSI"].iloc[-1]

        if 55 <= rsi <= 70:
            score += 40

        if data["MACD_HIST"].iloc[-1] > 0:
            score += 30

        # Improved ATR comparison with min_periods to avoid NaN
        atr_ma = data["ATR"].rolling(20, min_periods=1).mean()
        if data["ATR"].iloc[-1] > atr_ma.iloc[-1]:
            score += 30

        return score

    # ===============================
    # Final Indicator Score
    # ===============================

    def final_score(self, data):

        if data.empty:
            return {
                "trend_score": 0,
                "momentum_score": 0,
                "total_score": 0
            }

        trend = self.trend_score(data)

        momentum = self.momentum_score(data)

        total = trend + momentum

        return {
            "trend_score": trend,
            "momentum_score": momentum,
            "total_score": total
        }

    # ===============================
    # Process Complete Data
    # ===============================

    def process(self, data):

        data = self.add_basic_indicators(data)

        data = self.add_advanced_indicators(data)

        data["TrendScore"] = self.trend_score(data)

        # Ensure no NaN values remain after indicator calculations
        data = data = data.bfill().ffill()

        score = self.final_score(data)

        return data, score