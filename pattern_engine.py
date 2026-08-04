import pandas as pd
import numpy as np
import logging

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class PatternEngine:

    def __init__(self):
        pass

    # ==========================================
    # Bullish Engulfing
    # ==========================================

    def bullish_engulfing(self, data):
        # Check for minimum data
        if data.empty or len(data) < 2:
            return pd.Series(dtype=bool)

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
        if data.empty or len(data) < 2:
            return pd.Series(dtype=bool)

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
        if data.empty:
            return pd.Series(dtype=bool)

        body = abs(data["Close"] - data["Open"])
        lower_shadow = np.minimum(
            data["Open"],
            data["Close"]
        ) - data["Low"]
        upper_shadow = data["High"] - np.maximum(
            data["Open"],
            data["Close"]
        )

        return (
            (lower_shadow > body * 2) &
            (upper_shadow < body)
        )

    # ==========================================
    # Shooting Star
    # ==========================================

    def shooting_star(self, data):
        if data.empty:
            return pd.Series(dtype=bool)

        body = abs(data["Close"] - data["Open"])
        upper_shadow = data["High"] - np.maximum(
            data["Open"],
            data["Close"]
        )
        lower_shadow = np.minimum(
            data["Open"],
            data["Close"]
        ) - data["Low"]

        return (
            (upper_shadow > body * 2) &
            (lower_shadow < body)
        )

    # ==========================================
    # Doji
    # ==========================================

    def doji(self, data):
        if data.empty:
            return pd.Series(dtype=bool)

        body = abs(data["Close"] - data["Open"])
        candle = data["High"] - data["Low"]

        return body <= candle * 0.1

    # ==========================================
    # Morning Star
    # ==========================================

    def morning_star(self, data):
        if data.empty or len(data) < 3:
            return pd.Series(dtype=bool)

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
        if data.empty or len(data) < 3:
            return pd.Series(dtype=bool)

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
        if data.empty or len(data) < 2:
            return pd.Series(dtype=bool)

        prev = data.shift(1)
        return (
            (data["High"] < prev["High"]) &
            (data["Low"] > prev["Low"])
        )

    # ==========================================
    # Consolidation
    # ==========================================

    def consolidation(self, data, bars=10):
        if data.empty or len(data) < bars:
            # Return False for all rows if insufficient data
            return pd.Series(dtype=bool)

        high = data["High"].rolling(bars, min_periods=bars).max()
        low = data["Low"].rolling(bars, min_periods=bars).min()

        # Avoid division by zero; if low is zero or NaN, treat as False
        result = ((high - low) / low) < 0.03
        result = result.fillna(False)
        return result

    # ==========================================
    # Breakout
    # ==========================================

    def breakout(self, data, bars=20):
        if data.empty or len(data) < bars + 1:
            # Return False series for both directions
            false_series = pd.Series([False] * len(data), index=data.index) if not data.empty else pd.Series(dtype=bool)
            return false_series, false_series

        resistance = data["High"].rolling(bars, min_periods=bars).max().shift(1)
        support = data["Low"].rolling(bars, min_periods=bars).min().shift(1)

        breakout_up = data["Close"] > resistance
        breakout_down = data["Close"] < support

        # Fill NaN with False
        breakout_up = breakout_up.fillna(False)
        breakout_down = breakout_down.fillna(False)
        return breakout_up, breakout_down

    # ==========================================
    # Fake Breakout
    # ==========================================

    def fake_breakout(self, data, bars=20):
        if data.empty or len(data) < bars + 1:
            false_series = pd.Series([False] * len(data), index=data.index) if not data.empty else pd.Series(dtype=bool)
            return false_series, false_series

        resistance = data["High"].rolling(bars, min_periods=bars).max().shift(1)
        support = data["Low"].rolling(bars, min_periods=bars).min().shift(1)

        fake_up = (
            (data["High"] > resistance) &
            (data["Close"] < resistance)
        )
        fake_down = (
            (data["Low"] < support) &
            (data["Close"] > support)
        )

        fake_up = fake_up.fillna(False)
        fake_down = fake_down.fillna(False)
        return fake_up, fake_down

    # ==========================================
    # Support
    # ==========================================

    def support(self, data, bars=20):
        if data.empty:
            return pd.Series(dtype=float)
        return data["Low"].rolling(bars, min_periods=bars).min()

    # ==========================================
    # Resistance
    # ==========================================

    def resistance(self, data, bars=20):
        if data.empty:
            return pd.Series(dtype=float)
        return data["High"].rolling(bars, min_periods=bars).max()

    # ==========================================
    # Pattern Score
    # ==========================================

    def pattern_score(self, data):
        if data.empty:
            return 0

        score = 0

        try:
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
        except Exception as e:
            logger.warning(f"Error calculating pattern score: {e}")

        return score

    # ==========================================
    # Process
    # ==========================================

    def process(self, data):
        if data.empty:
            logger.warning("Empty data passed to pattern_engine.process")
            return data, 0

        # Ensure required columns exist
        required = ["Open", "High", "Low", "Close"]
        if not all(col in data.columns for col in required):
            logger.error("Missing required OHLC columns")
            return data, 0

        data = data.copy()

        try:
            data["BULLISH_ENGULFING"] = self.bullish_engulfing(data)
            data["BEARISH_ENGULFING"] = self.bearish_engulfing(data)
            data["HAMMER"] = self.hammer(data)
            data["SHOOTING_STAR"] = self.shooting_star(data)
            data["DOJI"] = self.doji(data)
            data["MORNING_STAR"] = self.morning_star(data)
            data["EVENING_STAR"] = self.evening_star(data)
            data["INSIDE_BAR"] = self.inside_bar(data)
            data["CONSOLIDATION"] = self.consolidation(data)
        except Exception as e:
            logger.error(f"Error adding pattern columns: {e}")
            # Continue with remaining logic, but patterns may be missing

        score = self.pattern_score(data)

        return data, score

    # ==========================================
    # Detect All Patterns
    # ==========================================

    def detect_patterns(self, data):
        if data.empty:
            return {
                "BullishEngulfing": False,
                "BearishEngulfing": False,
                "Hammer": False,
                "ShootingStar": False,
                "Doji": False,
                "MorningStar": False,
                "EveningStar": False,
                "InsideBar": False,
                "Breakout": False,
                "FakeBreakoutUp": False,
                "FakeBreakoutDown": False,
                "PatternScore": 0
            }

        try:
            fake_up, fake_down = self.fake_breakout(data)
            breakout_up, _ = self.breakout(data)

            return {
                "BullishEngulfing": self.bullish_engulfing(data).iloc[-1] if not data.empty else False,
                "BearishEngulfing": self.bearish_engulfing(data).iloc[-1] if not data.empty else False,
                "Hammer": self.hammer(data).iloc[-1] if not data.empty else False,
                "ShootingStar": self.shooting_star(data).iloc[-1] if not data.empty else False,
                "Doji": self.doji(data).iloc[-1] if not data.empty else False,
                "MorningStar": self.morning_star(data).iloc[-1] if not data.empty else False,
                "EveningStar": self.evening_star(data).iloc[-1] if not data.empty else False,
                "InsideBar": self.inside_bar(data).iloc[-1] if not data.empty else False,
                "Breakout": breakout_up.iloc[-1] if not data.empty else False,
                "FakeBreakoutUp": fake_up.iloc[-1] if not data.empty else False,
                "FakeBreakoutDown": fake_down.iloc[-1] if not data.empty else False,
                "PatternScore": self.pattern_score(data)
            }
        except Exception as e:
            logger.error(f"Error in detect_patterns: {e}")
            return {
                "BullishEngulfing": False,
                "BearishEngulfing": False,
                "Hammer": False,
                "ShootingStar": False,
                "Doji": False,
                "MorningStar": False,
                "EveningStar": False,
                "InsideBar": False,
                "Breakout": False,
                "FakeBreakoutUp": False,
                "FakeBreakoutDown": False,
                "PatternScore": 0
            }