import math
import pandas as pd
import numpy as np

from config import *


class RiskEngine:
    """
    Improved risk management with dynamic stop loss and target placement.
    Uses ATR for adaptive positioning.
    """

    def __init__(self):
        self.risk_percent = 1.0
        self.reward_ratio = 3.0  # Increased for better RR
        self.max_open_trades = 5
        self.max_daily_loss = 3.0
        self.entry_atr_buffer = ENTRY_ATR_BUFFER
        self.stop_atr_multiplier = STOP_ATR_MULTIPLIER
        self.target1_r = TARGET1_R
        self.target2_r = TARGET2_R
        self.target3_r = TARGET3_R

    def _safe_get(self, data: pd.DataFrame, column: str, default: float = 0.0) -> float:
        if data.empty or column not in data.columns:
            return default
        try:
            val = data[column].iloc[-1]
            return float(val) if pd.notna(val) else default
        except Exception:
            return default

    def _get_atr_quality(self, data: pd.DataFrame) -> float:
        """Calculate ATR quality - how recent and reliable."""
        if data.empty or "ATR" not in data.columns:
            return 1.0
        try:
            atr_series = data["ATR"].dropna()
            if len(atr_series) < 20:
                return 1.0
            recent_atr = atr_series.iloc[-5:].mean()
            avg_atr = atr_series.iloc[-20:].mean()
            if avg_atr == 0:
                return 1.0
            quality = min(2.0, recent_atr / avg_atr)
            return quality
        except Exception:
            return 1.0

    def _calculate_trailing_stop(self, high_price: float, low_price: float, 
                                  entry: float, atr: float) -> float:
        """Calculate trailing stop based on price action."""
        if atr <= 0:
            return 0
        profit = high_price - entry
        if profit > 0:
            # Trail after 1R profit
            if profit >= atr:
                return max(entry, high_price - atr * TRAILING_STOP_ATR)
        return entry - atr * self.stop_atr_multiplier

    def trade_plan(self, data: pd.DataFrame, capital: float, 
                   signal: str = "BUY") -> dict:
        """
        Generate improved trade plan with dynamic positioning.
        """
        if data.empty:
            return {}

        required = ["Close", "ATR", "High", "Low"]
        if not all(col in data.columns for col in required):
            return {}

        current_price = self._safe_get(data, "Close")
        atr = self._safe_get(data, "ATR")
        
        if atr <= 0 or current_price <= 0:
            return {}

        # Adjust ATR quality
        atr_quality = self._get_atr_quality(data)
        adjusted_atr = atr * atr_quality

        # Entry based on signal direction
        if signal == "BUY":
            entry = round(current_price + adjusted_atr * self.entry_atr_buffer, 2)
        elif signal == "SELL":
            entry = round(current_price - adjusted_atr * self.entry_atr_buffer, 2)
        else:
            return {}

        # Dynamic stop loss based on ATR and volatility
        if signal == "BUY":
            stoploss = round(entry - adjusted_atr * self.stop_atr_multiplier, 2)
        else:
            stoploss = round(entry + adjusted_atr * self.stop_atr_multiplier, 2)

        risk = abs(entry - stoploss)
        if risk <= 0:
            return {}

        # Targets based on risk-reward
        if signal == "BUY":
            target1 = round(entry + risk * self.target1_r, 2)
            target2 = round(entry + risk * self.target2_r, 2)
            target3 = round(entry + risk * self.target3_r, 2)
        else:
            target1 = round(entry - risk * self.target1_r, 2)
            target2 = round(entry - risk * self.target2_r, 2)
            target3 = round(entry - risk * self.target3_r, 2)

        # Position sizing with volatility adjustment
        qty = self._quantity(capital, entry, stoploss, adjusted_atr)
        
        # Calculate RR
        reward = abs(target2 - entry) if signal == "BUY" else abs(entry - target2)
        rr = round(reward / risk, 2) if risk > 0 else 0

        return {
            "CurrentPrice": round(current_price, 2),
            "Entry": entry,
            "StopLoss": stoploss,
            "Target1": target1,
            "Target2": target2,
            "Target3": target3,
            "RR": rr,
            "Quantity": qty,
            "RiskScore": self._risk_score(entry, stoploss),
            "RewardScore": self._reward_score(entry, target2),
            "Signal": signal,
            "ATR_Quality": round(atr_quality, 2)
        }

    def _quantity(self, capital: float, entry: float, sl: float, atr: float) -> int:
        """Calculate position size with volatility adjustment."""
        if capital <= 0 or atr <= 0:
            return 0
        risk_amount = capital * self.risk_percent / 100
        risk_per_share = abs(entry - sl)
        if risk_per_share <= 0:
            return 0
        
        # Adjust for volatility - reduce size in high volatility
        vol_adjustment = min(1.0, 1.0 / (atr / 10))
        qty = math.floor((risk_amount / risk_per_share) * vol_adjustment)
        return max(qty, 1)

    def _risk_score(self, entry: float, sl: float) -> int:
        risk = abs(entry - sl)
        if risk <= 1:
            return 100
        if risk <= 2:
            return 80
        if risk <= 3:
            return 60
        return 40

    def _reward_score(self, entry: float, target: float) -> int:
        reward = abs(target - entry)
        if reward >= 6:
            return 100
        if reward >= 4:
            return 80
        if reward >= 2:
            return 60
        return 40

    def calculate_trailing_stop(self, data: pd.DataFrame, entry: float,
                               stoploss: float, current_high: float) -> float:
        """Dynamic trailing stop based on price action."""
        if data.empty or "ATR" not in data.columns:
            return stoploss
        
        atr = self._safe_get(data, "ATR")
        if atr <= 0:
            return stoploss
        
        # Trail only after reaching 1.5R profit
        profit = current_high - entry
        if profit >= (entry - stoploss) * 1.5:
            new_stop = max(stoploss, current_high - atr * TRAILING_STOP_ATR)
            return new_stop
        return stoploss

    def should_break_even(self, data: pd.DataFrame, entry: float, 
                         target1: float, current_price: float) -> bool:
        """Determine if break-even should be triggered."""
        if not BREAK_EVEN_AT_TARGET1:
            return False
        # Break-even when price reaches target1
        return current_price >= target1