import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class ConfidenceEngine:
    """
    Computes a final confidence score (0-100) by combining:
        - Strategy Score (0-100)
        - Trend Score (0-100)
        - Pattern Score (0-100)
        - Volume Boost (0-20)
        - ATR Quality (0-100)
    with weighted contributions.
    """

    def __init__(self):
        # Weights (sum = 1.0)
        self.weight_strategy = 0.40
        self.weight_trend = 0.25
        self.weight_pattern = 0.20
        self.weight_volume = 0.10
        self.weight_atr = 0.05

    def calculate(
        self,
        strategy_score: float,
        trend_score: float,
        pattern_score: float,
        volume_spike: bool,
        atr: float = 0.0,
        atr_period: int = 20
    ) -> float:
        """
        Args:
            strategy_score: normalized strategy score (0-100)
            trend_score: TrendScore from indicator_engine (0-100)
            pattern_score: PatternScore from pattern_engine (0-100)
            volume_spike: True if volume spike detected
            atr: current ATR value
            atr_period: period for ATR moving average

        Returns:
            confidence (0-100, rounded to 2 decimals)
        """
        if strategy_score < 0 or strategy_score > 100:
            logger.warning(f"strategy_score out of range: {strategy_score}")
            strategy_score = max(0, min(100, strategy_score))
        if trend_score < 0 or trend_score > 100:
            logger.warning(f"trend_score out of range: {trend_score}")
            trend_score = max(0, min(100, trend_score))
        if pattern_score < 0 or pattern_score > 100:
            logger.warning(f"pattern_score out of range: {pattern_score}")
            pattern_score = max(0, min(100, pattern_score))

        # Volume boost: 20 if volume spike, else 0
        volume_boost = 20.0 if volume_spike else 0.0

        # ATR quality: ratio of current ATR to its 20-period average, mapped to 0-100
        atr_quality = self._compute_atr_quality(atr, atr_period)

        weighted = (
            self.weight_strategy * strategy_score +
            self.weight_trend * trend_score +
            self.weight_pattern * pattern_score +
            self.weight_volume * volume_boost +
            self.weight_atr * atr_quality
        )

        confidence = max(0, min(100, round(weighted, 2)))

        logger.debug(f"Confidence components: Strategy={strategy_score}, Trend={trend_score}, "
                     f"Pattern={pattern_score}, Volume={volume_boost}, ATR={atr_quality} -> {confidence}")

        return confidence

    def _compute_atr_quality(self, atr: float, period: int = 20) -> float:
        """
        Compute ATR quality based on the ratio of current ATR to its moving average.
        This method is intended to be called with the full data series, but here we
        assume the caller provides the current ATR value and we'll use a simple heuristic.
        """
        if atr <= 0:
            return 0.0
        # Since we don't have the full series, we return 50 (neutral) as a fallback.
        # In production, the caller should pass the ATR series or a precomputed ratio.
        return 50.0

    def calculate_with_series(self, data: pd.DataFrame) -> float:
        """
        Convenience method that extracts all needed values from a DataFrame.
        Expects columns: 'TrendScore', 'PatternScore' (or will compute pattern_score),
        'VOL_SPIKE', 'ATR'.
        """
        if data.empty:
            logger.warning("Empty DataFrame passed to calculate_with_series")
            return 0.0

        # Extract values safely
        trend = data["TrendScore"].iloc[-1] if "TrendScore" in data.columns else 0
        pattern = data["PatternScore"].iloc[-1] if "PatternScore" in data.columns else 0
        volume = data["VOL_SPIKE"].iloc[-1] if "VOL_SPIKE" in data.columns else False
        atr = data["ATR"].iloc[-1] if "ATR" in data.columns else 0

        # We need strategy_score; this method expects it to be passed separately,
        # so this is just a helper. In practice, strategy_score comes from StrategyEngine.
        # We'll raise a NotImplementedError to avoid misuse.
        raise NotImplementedError("Use calculate() method with explicit strategy_score.")