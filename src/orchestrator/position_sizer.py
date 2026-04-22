"""
Position Sizer - Calculates optimal position sizes.
Implements Kelly Criterion and confidence-based scaling.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum

from src.agents.agent_ensemble import EnsembleSignal


class SizingMethod(Enum):
    """Position sizing methods."""
    FIXED = "fixed"
    KELLY = "kelly"
    CONFIDENCE = "confidence"
    VOLATILITY_ADJUSTED = "volatility_adjusted"


@dataclass
class PositionSize:
    """Calculated position size."""
    
    symbol: str
    direction: str  # 'long' or 'short'
    size: float  # Position size in base currency
    size_pct: float  # Position size as % of account
    method: str  # Sizing method used
    confidence: float  # Signal confidence
    reasoning: Dict[str, Any]  # Calculation details
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'symbol': self.symbol,
            'direction': self.direction,
            'size': self.size,
            'size_pct': self.size_pct,
            'method': self.method,
            'confidence': self.confidence,
            'reasoning': self.reasoning
        }


class PositionSizer:
    """
    Calculates position sizes based on signal quality and risk parameters.
    
    Methods:
    - Fixed: Constant position size
    - Kelly Criterion: Optimal growth sizing
    - Confidence: Scale by signal confidence
    - Volatility Adjusted: Scale by market volatility
    """
    
    def __init__(
        self,
        method: SizingMethod = SizingMethod.KELLY,
        max_position_pct: float = 0.1,
        min_position_pct: float = 0.01,
        kelly_fraction: float = 0.25,
        confidence_scaling: bool = True,
        volatility_adjustment: bool = True
    ):
        """
        Initialize position sizer.
        
        Args:
            method: Position sizing method
            max_position_pct: Maximum position size (% of account)
            min_position_pct: Minimum position size (% of account)
            kelly_fraction: Fraction of Kelly to use (0-1)
            confidence_scaling: Scale by signal confidence
            volatility_adjustment: Adjust for volatility
        """
        self.method = method
        self.max_position_pct = max_position_pct
        self.min_position_pct = min_position_pct
        self.kelly_fraction = kelly_fraction
        self.confidence_scaling = confidence_scaling
        self.volatility_adjustment = volatility_adjustment
        
        # Default parameters
        self.default_win_rate = 0.55
        self.default_win_loss_ratio = 1.5
        self.default_volatility = 0.02
    
    def calculate_size(
        self,
        signal: EnsembleSignal,
        account_balance: float,
        current_price: float,
        win_rate: Optional[float] = None,
        win_loss_ratio: Optional[float] = None,
        volatility: Optional[float] = None
    ) -> PositionSize:
        """
        Calculate position size for a signal.
        
        Args:
            signal: Ensemble signal
            account_balance: Current account balance
            current_price: Current asset price
            win_rate: Historical win rate (optional)
            win_loss_ratio: Average win/loss ratio (optional)
            volatility: Asset volatility (optional)
        
        Returns:
            PositionSize with calculated size
        """
        # Use defaults if not provided
        win_rate = win_rate or self.default_win_rate
        win_loss_ratio = win_loss_ratio or self.default_win_loss_ratio
        volatility = volatility or self.default_volatility
        
        # Calculate base size based on method
        if self.method == SizingMethod.FIXED:
            size_pct = self._fixed_size()
        elif self.method == SizingMethod.KELLY:
            size_pct = self._kelly_size(win_rate, win_loss_ratio)
        elif self.method == SizingMethod.CONFIDENCE:
            size_pct = self._confidence_size(signal.confidence)
        elif self.method == SizingMethod.VOLATILITY_ADJUSTED:
            size_pct = self._volatility_adjusted_size(volatility)
        else:
            size_pct = self.max_position_pct / 2
        
        # Apply confidence scaling
        if self.confidence_scaling:
            size_pct *= signal.confidence
        
        # Apply volatility adjustment
        if self.volatility_adjustment and volatility:
            vol_factor = self.default_volatility / max(volatility, 0.001)
            size_pct *= min(vol_factor, 2.0)  # Cap at 2x
        
        # Apply limits
        size_pct = np.clip(size_pct, self.min_position_pct, self.max_position_pct)
        
        # Calculate absolute size
        size = (account_balance * size_pct) / current_price
        
        # Reasoning
        reasoning = {
            'base_method': self.method.value,
            'win_rate': win_rate,
            'win_loss_ratio': win_loss_ratio,
            'volatility': volatility,
            'confidence_scaling': self.confidence_scaling,
            'volatility_adjustment': self.volatility_adjustment,
            'kelly_fraction': self.kelly_fraction if self.method == SizingMethod.KELLY else None
        }
        
        return PositionSize(
            symbol=signal.symbol,
            direction=signal.direction,
            size=size,
            size_pct=size_pct,
            method=self.method.value,
            confidence=signal.confidence,
            reasoning=reasoning
        )
    
    def _fixed_size(self) -> float:
        """Fixed position size."""
        return self.max_position_pct / 2
    
    def _kelly_size(self, win_rate: float, win_loss_ratio: float) -> float:
        """
        Kelly Criterion position size.
        
        Kelly % = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
        """
        kelly_pct = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
        kelly_pct = max(0, kelly_pct)  # No negative positions
        
        # Apply Kelly fraction for safety
        return kelly_pct * self.kelly_fraction
    
    def _confidence_size(self, confidence: float) -> float:
        """Size based on signal confidence."""
        return self.max_position_pct * confidence
    
    def _volatility_adjusted_size(self, volatility: float) -> float:
        """Size inversely proportional to volatility."""
        target_risk = 0.02  # 2% risk
        size_pct = target_risk / max(volatility, 0.001)
        return min(size_pct, self.max_position_pct)
    
    def calculate_max_size(
        self,
        symbol: str,
        account_balance: float,
        current_price: float
    ) -> float:
        """
        Calculate maximum position size for a symbol.
        
        Args:
            symbol: Trading symbol
            account_balance: Current account balance
            current_price: Current asset price
        
        Returns:
            Maximum position size in base currency
        """
        return (account_balance * self.max_position_pct) / current_price
    
    def adjust_for_existing_position(
        self,
        new_size: PositionSize,
        existing_size: float,
        account_balance: float,
        current_price: float
    ) -> PositionSize:
        """
        Adjust new position size considering existing position.
        
        Args:
            new_size: Calculated new position size
            existing_size: Current position size
            account_balance: Current account balance
            current_price: Current asset price
        
        Returns:
            Adjusted position size
        """
        max_size = self.calculate_max_size(new_size.symbol, account_balance, current_price)
        
        # If same direction, check if we can add
        if (new_size.direction == 'long' and existing_size > 0) or \
           (new_size.direction == 'short' and existing_size < 0):
            available_size = max_size - abs(existing_size)
            adjusted_size = min(new_size.size, available_size)
        else:
            # Opposite direction - can close and reverse
            adjusted_size = new_size.size
        
        # Update reasoning
        new_size.reasoning['existing_position'] = existing_size
        new_size.reasoning['adjusted'] = adjusted_size != new_size.size
        new_size.size = max(0, adjusted_size)
        new_size.size_pct = (adjusted_size * current_price) / account_balance
        
        return new_size
    
    def set_method(self, method: SizingMethod):
        """Change sizing method."""
        self.method = method
    
    def set_limits(self, max_pct: float, min_pct: float):
        """
        Update position size limits.
        
        Args:
            max_pct: Maximum position size (% of account)
            min_pct: Minimum position size (% of account)
        """
        self.max_position_pct = max_pct
        self.min_position_pct = min_pct
    
    def set_kelly_fraction(self, fraction: float):
        """
        Set Kelly fraction (safety factor).
        
        Args:
            fraction: Fraction of Kelly to use (0-1)
        """
        self.kelly_fraction = np.clip(fraction, 0.0, 1.0)
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return {
            'method': self.method.value,
            'max_position_pct': self.max_position_pct,
            'min_position_pct': self.min_position_pct,
            'kelly_fraction': self.kelly_fraction,
            'confidence_scaling': self.confidence_scaling,
            'volatility_adjustment': self.volatility_adjustment
        }
