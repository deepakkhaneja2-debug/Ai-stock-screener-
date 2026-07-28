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

        rs = avg_gain / avg_loss

        rsi = 100 - (100 / (1 + rs))

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

        ema12 = data["Close"].ewm(span=12, adjust=False).mean()

        ema26 = data["Close"].ewm(span=26, adjust=False).mean()

        macd = ema12 - ema26

        signal = macd.ewm(span=9, adjust=False).mean()

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

        return (
            (tp * data["Volume"]).cumsum()
            / data["Volume"].cumsum()
        )


    # ===============================
    # Volume Average
    # ===============================

    def volume_ma(self, data, period=20):

        return data["Volume"].rolling(period).mean()


    # ===============================
    # Volume Spike
    # ===============================

    def volume_spike(self, data):

        avg = self.volume_ma(data)

        return data["Volume"] > (avg * 1.5)


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

        data["VOL_SPIKE"] = self.volume_spike(data)

        return data
      
    # ===============================
    # Trend Score
    # ===============================

    def trend_score(self, data):

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

        score = 0

        rsi = data["RSI"].iloc[-1]

        if 55 <= rsi <= 70:
            score += 40

        if data["MACD_HIST"].iloc[-1] > 0:
            score += 30

        if data["ATR"].iloc[-1] > data["ATR"].rolling(20).mean().iloc[-1]:
            score += 30

        return score


    # ===============================
    # Final Indicator Score
    # ===============================

    def final_score(self, data):

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

        score = self.final_score(data)

        return data, score
