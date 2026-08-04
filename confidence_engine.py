import logging
import pandas as pd

from config import *  # <-- YEH IMPORT MISSING THA. Isse fix kar diya.

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ConfidenceEngine:
    """Calculates confidence score from multiple weighted components."""

    def __init__(self):
        self.weight_strategy = CONFIDENCE_WEIGHT_STRATEGY
        self.weight_trend = CONFIDENCE_WEIGHT_TREND
        self.weight_pattern = CONFIDENCE_WEIGHT_PATTERN
        self.weight_volume = CONFIDENCE_WEIGHT_VOLUME
        self.weight_atr = CONFIDENCE_WEIGHT_ATR

    def _compute_atr_quality(self, atr: float) -> float:
        """Return a quality score for ATR."""
        if atr <= 0:
            return 0.0
        return min(100, atr * 10)  # Simplified quality metric

    def calculate(
        self,
        strategy_score: float,
        trend_score: float,
        pattern_score: float,
        volume_spike: bool,
        atr: float = 0.0
    ) -> float:
        """Return a confidence score between 0 and 100."""
        # Clamp inputs
        strategy_score = max(0, min(100, strategy_score))
        trend_score = max(0, min(100, trend_score))
        pattern_score = max(0, min(100, pattern_score))

        volume_boost = 20.0 if volume_spike else 0.0
        atr_quality = self._compute_atr_quality(atr)

        weighted = (
            self.weight_strategy * strategy_score +
            self.weight_trend * trend_score +
            self.weight_pattern * pattern_score +
            self.weight_volume * volume_boost +
            self.weight_atr * atr_quality
        )

        confidence = max(0, min(100, round(weighted, 2)))
        logger.debug(f"Confidence: {confidence} (S={strategy_score}, T={trend_score}, "
                     f"P={pattern_score}, V={volume_boost}, A={atr_quality})")
        return confidence