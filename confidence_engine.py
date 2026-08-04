import logging
import pandas as pd

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ConfidenceEngine:
    """Calculates confidence score from multiple weighted components."""

    def __init__(self):
        self.weight_strategy = 0.40
        self.weight_trend = 0.25
        self.weight_pattern = 0.20
        self.weight_volume = 0.10
        self.weight_atr = 0.05

    def _compute_atr_quality(self, atr: float) -> float:
        """Return a quality score for ATR (simplified)."""
        if atr <= 0:
            return 0.0
        # This is a simplified placeholder – in production you would compare
        # against a moving average. For now we return 50 (neutral).
        return 50.0

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