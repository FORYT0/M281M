"""
Signal Validator - Filters and validates trading signals.
Ensures only high-quality signals proceed to execution.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict

from src.agents.agent_ensemble import EnsembleSignal


@dataclass
class ValidationResult:
    """Result of signal validation."""
    
    is_valid: bool
    signal: EnsembleSignal
    reasons: List[str]
    quality_score: float  # 0.0 to 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'is_valid': self.is_valid,
            'reasons': self.reasons,
            'quality_score': self.quality_score,
            'signal': self.signal.to_dict()
        }


class SignalValidator:
    """
    Validates trading signals before execution.
    
    Validation criteria:
    - Minimum confidence threshold
    - Minimum agreement score
    - Regime-based filtering
    - Cooldown periods
    - Direction consistency
    """
    
    def __init__(
        self,
        min_confidence: float = 0.6,
        min_agreement: float = 0.5,
        cooldown_seconds: int = 60,
        regime_filters: Optional[Dict[str, Dict[str, float]]] = None
    ):
        """
        Initialize signal validator.
        
        Args:
            min_confidence: Minimum confidence threshold (0-1)
            min_agreement: Minimum agreement score (0-1)
            cooldown_seconds: Minimum time between signals for same symbol
            regime_filters: Regime-specific thresholds
        """
        self.min_confidence = min_confidence
        self.min_agreement = min_agreement
        self.cooldown_seconds = cooldown_seconds
        self.regime_filters = regime_filters or {}
        
        # Track last signal time per symbol
        self.last_signal_time: Dict[str, datetime] = {}
        
        # Statistics
        self.total_signals = 0
        self.valid_signals = 0
        self.rejection_reasons = defaultdict(int)
    
    def validate(self, signal: EnsembleSignal) -> ValidationResult:
        """
        Validate a trading signal.
        
        Args:
            signal: Ensemble signal to validate
        
        Returns:
            ValidationResult with validation outcome
        """
        self.total_signals += 1
        
        reasons = []
        quality_score = 0.0
        
        # Check if neutral (always reject)
        if signal.direction == 'neutral':
            reasons.append("Signal is neutral")
            self.rejection_reasons['neutral'] += 1
            return ValidationResult(
                is_valid=False,
                signal=signal,
                reasons=reasons,
                quality_score=0.0
            )
        
        # Check confidence threshold
        if signal.confidence < self.min_confidence:
            reasons.append(
                f"Confidence {signal.confidence:.2%} below threshold {self.min_confidence:.2%}"
            )
            self.rejection_reasons['low_confidence'] += 1
        else:
            quality_score += 0.3
        
        # Check agreement score
        if signal.agreement_score < self.min_agreement:
            reasons.append(
                f"Agreement {signal.agreement_score:.2%} below threshold {self.min_agreement:.2%}"
            )
            self.rejection_reasons['low_agreement'] += 1
        else:
            quality_score += 0.3
        
        # Check cooldown period
        if signal.symbol in self.last_signal_time:
            time_since_last = (signal.timestamp - self.last_signal_time[signal.symbol]).total_seconds()
            if time_since_last < self.cooldown_seconds:
                reasons.append(
                    f"Cooldown active: {time_since_last:.0f}s < {self.cooldown_seconds}s"
                )
                self.rejection_reasons['cooldown'] += 1
            else:
                quality_score += 0.2
        else:
            quality_score += 0.2
        
        # Check regime-specific filters
        regime = self._get_regime_from_signal(signal)
        if regime and regime in self.regime_filters:
            regime_config = self.regime_filters[regime]
            regime_min_conf = regime_config.get('min_confidence', self.min_confidence)
            
            if signal.confidence < regime_min_conf:
                reasons.append(
                    f"Confidence {signal.confidence:.2%} below {regime} regime threshold {regime_min_conf:.2%}"
                )
                self.rejection_reasons[f'regime_{regime}'] += 1
            else:
                quality_score += 0.2
        else:
            quality_score += 0.2
        
        # Determine if valid
        is_valid = len(reasons) == 0
        
        if is_valid:
            self.valid_signals += 1
            self.last_signal_time[signal.symbol] = signal.timestamp
            quality_score = min(1.0, quality_score + signal.confidence * 0.3)
        
        return ValidationResult(
            is_valid=is_valid,
            signal=signal,
            reasons=reasons,
            quality_score=quality_score
        )
    
    def _get_regime_from_signal(self, signal: EnsembleSignal) -> Optional[str]:
        """Extract regime from signal if available."""
        regime_signal = signal.agent_signals.get('regime_classifier')
        if regime_signal and regime_signal.reasoning:
            return regime_signal.reasoning.get('regime')
        return None
    
    def set_thresholds(
        self,
        min_confidence: Optional[float] = None,
        min_agreement: Optional[float] = None,
        cooldown_seconds: Optional[int] = None
    ):
        """
        Update validation thresholds.
        
        Args:
            min_confidence: New minimum confidence
            min_agreement: New minimum agreement
            cooldown_seconds: New cooldown period
        """
        if min_confidence is not None:
            self.min_confidence = min_confidence
        if min_agreement is not None:
            self.min_agreement = min_agreement
        if cooldown_seconds is not None:
            self.cooldown_seconds = cooldown_seconds
    
    def set_regime_filter(self, regime: str, min_confidence: float):
        """
        Set regime-specific confidence threshold.
        
        Args:
            regime: Regime name (e.g., 'volatile', 'trending')
            min_confidence: Minimum confidence for this regime
        """
        if regime not in self.regime_filters:
            self.regime_filters[regime] = {}
        self.regime_filters[regime]['min_confidence'] = min_confidence
    
    def reset_cooldown(self, symbol: str):
        """Reset cooldown for a symbol."""
        if symbol in self.last_signal_time:
            del self.last_signal_time[symbol]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get validation statistics."""
        pass_rate = self.valid_signals / self.total_signals if self.total_signals > 0 else 0.0
        
        return {
            'total_signals': self.total_signals,
            'valid_signals': self.valid_signals,
            'rejected_signals': self.total_signals - self.valid_signals,
            'pass_rate': pass_rate,
            'rejection_reasons': dict(self.rejection_reasons),
            'thresholds': {
                'min_confidence': self.min_confidence,
                'min_agreement': self.min_agreement,
                'cooldown_seconds': self.cooldown_seconds
            },
            'regime_filters': self.regime_filters
        }
    
    def reset_stats(self):
        """Reset validation statistics."""
        self.total_signals = 0
        self.valid_signals = 0
        self.rejection_reasons.clear()
