import pandas as pd
import numpy as np


class PatternEngine:

    def __init__(self):
        pass

    # ==========================================
    # Bullish Engulfing
    # ==========================================

    def bullish_engulfing(self, data):

        prev = data.shift(1)

        return (
            (prev["Close"] < prev["Open"]) &
            (data["Close"] > data["Open"]) &
            (data["Open"] < prev["Close"]) &
            (data["Close"] > prev["Open"])
        )

    # ==========================================
    # Bearish Engulfing
    # ==========================================

    def bearish_engulfing(self, data):

        prev = data.shift(1)

        return (
            (prev["Close"] > prev["Open"]) &
            (data["Close"] < data["Open"]) &
            (data["Open"] > prev["Close"]) &
            (data["Close"] < prev["Open"])
        )

    # ==========================================
    # Hammer
    # ==========================================

    def hammer(self, data):

        body = abs(data["Close"] - data["Open"])

        lower_shadow = np.minimum(
            data["
          
    # ==========================================
    # Morning Star
    # ==========================================

    def morning_star(self, data):

        prev2 = data.shift(2)
        prev1 = data.shift(1)

        return (
            (prev2["Close"] < prev2["Open"]) &
            (abs(prev1["Close"] - prev1["Open"]) <
             abs(prev2["Close"] - prev2["Open"]) * 0.3) &
            (data["Close"] > data["Open"]) &
            (data["Close"] >
             (prev2["Open"] + prev2["Close"]) / 2)
        )

    # ==========================================
    # Evening Star
    # ==========================================

    def evening_star(self, data):

        prev2 = data.shift(2)
        prev1 = data.shift(1)

        return (
            (prev2["Close"] > prev2["Open"]) &
            (abs(prev1["Close"] - prev1["Open"]) <
             abs(prev2["Close"] - prev2["Open"]) * 0.3) &
            (data["Close"] < data["Open"]) &
            (data["Close"] <
             (prev2["Open"] + prev2["Close"]) / 2)
        )

    # ==========================================
    # Inside Bar
    # ==========================================

    def inside_bar(self, data):

        prev = data.shift(1)

        return (
            (data["High"] < prev["High"]) &
            (data["Low"] > prev["Low"])
        )

    # ==========================================
    # Consolidation
    # ==========================================

    def consolidation(self, data, bars=10):

        high = data["High"].rolling(bars).max()

        low = data["Low"].rolling(bars).min()

        return ((high - low) / low) < 0.03

    # ==========================================
    # Breakout
    # ==========================================

    def breakout(self, data, bars=20):

        resistance = data["High"].rolling(bars).max().shift(1)

        support = data["Low"].rolling(bars).min().shift(1)

        breakout_up = data["Close"] > resistance

        breakout_down = data["Close"] < support

        return breakout_up, breakout_down

    # ==========================================
    # Fake Breakout Detection
    # ==========================================

    def fake_breakout(self, data, bars=20):

        resistance = data["High"].rolling(bars).max().shift(1)
        support = data["Low"].rolling(bars).min().shift(1)

        fake_up = (
            (data["High"] > resistance) &
            (data["Close"] < resistance)
        )

        fake_down = (
            (data["Low"] < support) &
            (data["Close"] > support)
        )

        return fake_up, fake_down

    # ==========================================
    # Support Detection
    # ==========================================

    def support(self, data, bars=20):

        return data["Low"].rolling(bars).min()

    # ==========================================
    # Resistance Detection
    # ==========================================

    def resistance(self, data, bars=20):

        return data["High"].rolling(bars).max()

    # ==========================================
    # Pattern Score
    # ==========================================

    def pattern_score(self, data):

        score = 0

        if self.bullish_engulfing(data).iloc[-1]:
            score += 25

        if self.hammer(data).iloc[-1]:
            score += 20

        if self.morning_star(data).iloc[-1]:
            score += 25

        if self.breakout(data)[0].iloc[-1]:
            score += 20

        if self.inside_bar(data).iloc[-1]:
            score += 10

        return score

    # ==========================================
    # Process Pattern Engine
    # ==========================================

    def process(self, data):

        data = data.copy()

        data["BULLISH_ENGULFING"] = self.bullish_engulfing(data)
        data["BEARISH_ENGULFING"] = self.bearish_engulfing(data)
        data["HAMMER"] = self.hammer(data)
        data["SHOOTING_STAR"] = self.shooting_star(data)
        data["DOJI"] = self.doji(data)
        data["MORNING_STAR"] = self.morning_star(data)
        data["EVENING_STAR"] = self.evening_star(data)
        data["INSIDE_BAR"] = self.inside_bar(data)
        data["CONSOLIDATION"] = self.consolidation(data)

        score = self.pattern_score(data)

        return data, score
        
# ======================================
# Detect All Patterns
# ======================================

def detect_patterns(self, data):

    return {
        "BullishEngulfing": self.bullish_engulfing(data).iloc[-1],
        "Hammer": self.hammer(data).iloc[-1],
        "MorningStar": self.morning_star(data).iloc[-1],
        "Breakout": self.breakout(data)[0].iloc[-1],
        "FakeBreakout": self.fake_breakout(data).iloc[-1],
        "PatternScore": self.pattern_score(data)
    }
