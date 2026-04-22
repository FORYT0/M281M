"""
Regime-Aware Risk Manager - Layer 3.
Adjusts risk based on market regime.
"""

import logging
from typing import Dict, Any, Optional

from .risk_config import RiskConfig

logger = logging.getLogger(__name__)


class RegimeRiskManager:
    """
    Layer 3: Regime-aware risk management.
    
    Adjusts position sizes based on market regime:
    - Volatile: Reduce size
    - Trending: Increase size
    - Sideways: Moderate size
    """
    
    def __init__(self, config: RiskConfig):
        """Initialize regime risk manager."""
        self.config = config
    
    def check(
        self,
        order: Dict[str, Any],
        regime: str
    ) -> Dict[str, Any]:
        """
        Check regime-based risk adjustments.
        
        Args:
            order: Order details
            regime: Current market regime ('volatile', 'trending', 'sideways', 'neutral')
        
        Returns:
            Dict with size_adjustment, warnings
        """
        result = {
            'size_adjustment': None,
            'warnings': []
        }
        
        regime_lower = regime.lower() if regime else 'neutral'
        
        # Adjust size based on regime
        if 'volatile' in regime_lower or 'high_volatility' in regime_lower:
            result['size_adjustment'] = self.config.volatile_regime_size_reduction
            result['warnings'].append(
                f"Size reduced for volatile regime: {self.config.volatile_regime_size_reduction:.1%}"
            )
        
        elif 'trending' in regime_lower or 'trend' in regime_lower:
            result['size_adjustment'] = self.config.trending_regime_size_increase
            result['warnings'].append(
                f"Size increased for trending regime: {self.config.trending_regime_size_increase:.1%}"
            )
        
        elif 'sideways' in regime_lower or 'ranging' in regime_lower:
            result['size_adjustment'] = self.config.sideways_regime_size_factor
            result['warnings'].append(
                f"Size adjusted for sideways regime: {self.config.sideways_regime_size_factor:.1%}"
            )
        
        return result
