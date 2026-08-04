import logging
import pandas as pd
from typing import Dict, List, Union

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class StrategyEngine:
    """
    Combines multiple trading strategies to generate BUY/SELL/WATCH signals.
    Each strategy contributes up to 20 points (positive = bullish, negative = bearish).
    The total score is normalized to 0-100 and used to determine the signal.
    """

    def __init__(self):
        self.max_score_per_strategy = 20
        self.buy_threshold = 60
        self.sell_threshold = 60

    def _safe_get_last(self, data: pd.DataFrame, column: str, default: float = 0.0) -> float:
        if data.empty or column not in data.columns:
            return default
        try:
            val = data[column].iloc[-1]
            if pd.isna(val):
                return default
            return float(val)
        except (IndexError, ValueError, TypeError):
            return default

    def _safe_get_bool(self, data: pd.DataFrame, column: str) -> bool:
        if data.empty or column not in data.columns:
            return False
        try:
            val = data[column].iloc[-1]
            return bool(val) if not pd.isna(val) else False
        except (IndexError, ValueError, TypeError):
            return False

    # ---------- Individual Strategies ----------

    def _ema_trend_strategy(self, data: pd.DataFrame) -> int:
        if data.empty:
            return 0
        ema20 = self._safe_get_last(data, "EMA20")
        ema50 = self._safe_get_last(data, "EMA50")
        close = self._safe_get_last(data, "Close")
        if ema20 == 0 or ema50 == 0:
            return 0
        if ema20 > ema50 and close > ema20:
            return 20
        elif ema20 < ema50 and close < ema20:
            return -20
        return 0

    def _macd_strategy(self, data: pd.DataFrame) -> int:
        if data.empty:
            return 0
        macd = self._safe_get_last(data, "MACD")
        signal = self._safe_get_last(data, "MACD_SIGNAL")
        if macd > signal:
            return 20
        elif macd < signal:
            return -20
        return 0

    def _rsi_strategy(self, data: pd.DataFrame) -> int:
        if data.empty:
            return 0
        rsi = self._safe_get_last(data, "RSI")
        if rsi == 0:
            return 0
        if 55 <= rsi <= 70:
            return 20
        elif 30 <= rsi <= 45:
            return -20
        return 0

    def _volume_spike_strategy(self, data: pd.DataFrame) -> int:
        if data.empty:
            return 0
        spike = self._safe_get_bool(data, "VOL_SPIKE")
        if not spike:
            return 0
        close = self._safe_get_last(data, "Close")
        vwap = self._safe_get_last(data, "VWAP")
        if close > vwap:
            return 20
        elif close < vwap:
            return -20
        return 0

    def _pattern_strategy(self, data: pd.DataFrame) -> int:
        if data.empty:
            return 0
        bullish = ["BULLISH_ENGULFING", "HAMMER", "MORNING_STAR", "INSIDE_BAR"]
        bearish = ["BEARISH_ENGULFING", "SHOOTING_STAR", "EVENING_STAR"]
        for pat in bullish:
            if self._safe_get_bool(data, pat):
                return 20
        for pat in bearish:
            if self._safe_get_bool(data, pat):
                return -20
        return 0

    def _breakout_strategy(self, data: pd.DataFrame) -> int:
        if data.empty:
            return 0
        up = self._safe_get_bool(data, "BREAKOUT_UP")
        down = self._safe_get_bool(data, "BREAKOUT_DOWN")
        if up:
            return 20
        elif down:
            return -20
        return 0

    def _trend_score_strategy(self, data: pd.DataFrame) -> int:
        if data.empty:
            return 0
        trend = self._safe_get_last(data, "TrendScore")
        if trend >= 60:
            return 20
        elif trend <= 40:
            return -20
        return 0

    # ---------- Evaluation ----------

    def evaluate(self, data: pd.DataFrame) -> Dict[str, Union[str, int, List[str]]]:
        """
        Returns:
            {
                "signal": "BUY" / "SELL" / "WATCH",
                "strategy_score": int (0-100),
                "triggered_strategies": List[str]
            }
        """
        if data.empty:
            logger.warning("Empty DataFrame passed to StrategyEngine.evaluate")
            return {"signal": "WATCH", "strategy_score": 0, "triggered_strategies": []}

        required = ["Close", "EMA20", "EMA50", "MACD", "MACD_SIGNAL",
                    "RSI", "VOL_SPIKE", "VWAP", "TrendScore"]
        missing = [c for c in required if c not in data.columns]
        if missing:
            logger.warning(f"Missing columns: {missing}")
            return {"signal": "WATCH", "strategy_score": 0, "triggered_strategies": []}

        try:
            strategies = {
                "EMA_Trend": self._ema_trend_strategy(data),
                "MACD_Momentum": self._macd_strategy(data),
                "RSI": self._rsi_strategy(data),
                "Volume_Spike": self._volume_spike_strategy(data),
                "Candlestick_Pattern": self._pattern_strategy(data),
                "Breakout": self._breakout_strategy(data),
                "Trend_Score": self._trend_score_strategy(data),
            }

            total = sum(strategies.values())
            max_total = len(strategies) * self.max_score_per_strategy
            norm_score = ((total + max_total) / (2 * max_total)) * 100
            norm_score = max(0, min(100, round(norm_score)))

            if norm_score >= self.buy_threshold:
                signal = "BUY"
            elif norm_score <= (100 - self.sell_threshold):
                signal = "SELL"
            else:
                signal = "WATCH"

            if signal == "BUY":
                triggered = [n for n, s in strategies.items() if s > 0]
            elif signal == "SELL":
                triggered = [n for n, s in strategies.items() if s < 0]
            else:
                triggered = [n for n, s in strategies.items() if s != 0]

            logger.info(f"Signal: {signal}, Score: {norm_score}, Triggered: {triggered}")
            return {
                "signal": signal,
                "strategy_score": norm_score,
                "triggered_strategies": triggered
            }

        except Exception as e:
            logger.error(f"Error in evaluate: {e}", exc_info=True)
            return {"signal": "WATCH", "strategy_score": 0, "triggered_strategies": []}