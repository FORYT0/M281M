"""
Trade-Level Risk Manager - Layer 1.
Handles stop loss, take profit, and slippage checks.
"""

import logging
from typing import Dict, Any, Optional

from .risk_config import RiskConfig

logger = logging.getLogger(__name__)


class TradeRiskManager:
    """
    Layer 1: Trade-level risk management.
    
    Checks:
    - Dynamic stop loss (ATR-based)
    - Take profit (minimum risk/reward ratio)
    - Maximum slippage
    """
    
    def __init__(self, config: RiskConfig):
        """Initialize trade risk manager."""
        self.config = config
    
    def check(
        self,
        order: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check trade-level risk.
        
        Args:
            order: Order details (symbol, side, size, price)
            market_data: Market data (price, atr, bid, ask, spread)
        
        Returns:
            Dict with approved, stop_loss, take_profit, warnings, reasons
        """
        result = {
            'approved': True,
            'stop_loss': None,
            'take_profit': None,
            'warnings': [],
            'reasons': []
        }
        
        side = order.get('side', 'long')
        price = market_data.get('price', order.get('price'))
        atr = market_data.get('atr', price * 0.02)  # Default 2% if no ATR
        
        # Calculate stop loss
        stop_distance = atr * self.config.stop_loss_atr_multiplier
        if side == 'long':
            stop_loss = price - stop_distance
        else:
            stop_loss = price + stop_distance
        
        result['stop_loss'] = stop_loss
        
        # Calculate take profit
        tp_distance = atr * self.config.take_profit_atr_multiplier
        if side == 'long':
            take_profit = price + tp_distance
        else:
            take_profit = price - tp_distance
        
        result['take_profit'] = take_profit
        
        # Check risk/reward ratio
        risk = abs(price - stop_loss)
        reward = abs(take_profit - price)
        rr_ratio = reward / risk if risk > 0 else 0
        
        if rr_ratio < self.config.min_risk_reward_ratio:
            result['approved'] = False
            result['reasons'].append(
                f"Risk/reward ratio {rr_ratio:.2f} below minimum {self.config.min_risk_reward_ratio}"
            )
        
        # Check slippage
        bid = market_data.get('bid', price)
        ask = market_data.get('ask', price)
        spread = ask - bid
        spread_bps = (spread / price) * 10000
        
        if spread_bps > self.config.max_slippage_bps:
            result['warnings'].append(
                f"High spread: {spread_bps:.1f} bps (max: {self.config.max_slippage_bps})"
            )
        
        # Check position size
        size = order.get('size', 0)
        if size > self.config.max_position_size:
            result['approved'] = False
            result['reasons'].append(
                f"Position size {size:.4f} exceeds maximum {self.config.max_position_size}"
            )
        
        return result
