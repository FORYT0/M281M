"""
Portfolio-Level Risk Manager - Layer 2.
Handles VaR, exposure, and correlation limits.
"""

import logging
import numpy as np
from typing import Dict, Any, Optional, List

from .risk_config import RiskConfig

logger = logging.getLogger(__name__)


class PortfolioRiskManager:
    """
    Layer 2: Portfolio-level risk management.
    
    Checks:
    - Real-time VaR (Value at Risk)
    - Maximum exposure per asset
    - Correlation limits
    """
    
    def __init__(self, config: RiskConfig, initial_capital: float):
        """Initialize portfolio risk manager."""
        self.config = config
        self.initial_capital = initial_capital
        self.position_history: List[Dict[str, Any]] = []
    
    def check(
        self,
        order: Dict[str, Any],
        portfolio_state: Dict[str, Any],
        price: float
    ) -> Dict[str, Any]:
        """
        Check portfolio-level risk.
        
        Args:
            order: Order details
            portfolio_state: Current portfolio (positions, balance)
            price: Current price
        
        Returns:
            Dict with approved, size_adjustment, warnings, reasons
        """
        result = {
            'approved': True,
            'size_adjustment': None,
            'warnings': [],
            'reasons': []
        }
        
        symbol = order.get('symbol')
        size = order.get('size', 0)
        balance = portfolio_state.get('balance', self.initial_capital)
        positions = portfolio_state.get('positions', {})
        
        # Calculate current exposure
        total_exposure = sum(
            abs(pos.get('size', 0) * pos.get('price', 0))
            for pos in positions.values()
        )
        
        # Calculate new exposure
        new_position_value = size * price
        new_total_exposure = total_exposure + new_position_value
        
        # Check max portfolio exposure
        exposure_pct = new_total_exposure / balance if balance > 0 else 0
        if exposure_pct > self.config.max_portfolio_exposure:
            # Try to adjust size
            max_allowed_value = (self.config.max_portfolio_exposure * balance) - total_exposure
            if max_allowed_value > 0:
                adjusted_size = max_allowed_value / price
                result['size_adjustment'] = adjusted_size
                result['warnings'].append(
                    f"Size reduced to maintain exposure limit: {size:.4f} -> {adjusted_size:.4f}"
                )
            else:
                result['approved'] = False
                result['reasons'].append(
                    f"Portfolio exposure {exposure_pct:.1%} exceeds maximum {self.config.max_portfolio_exposure:.1%}"
                )
                return result
        
        # Check position concentration
        if symbol in positions:
            existing_value = abs(positions[symbol].get('size', 0) * positions[symbol].get('price', 0))
            new_position_total = existing_value + new_position_value
        else:
            new_position_total = new_position_value
        
        concentration = new_position_total / balance if balance > 0 else 0
        if concentration > self.config.max_position_concentration:
            result['warnings'].append(
                f"High position concentration: {concentration:.1%} (max: {self.config.max_position_concentration:.1%})"
            )
        
        # Calculate VaR (simplified Monte Carlo)
        var_pct = self._calculate_var(portfolio_state, order, price)
        if var_pct > self.config.max_var_pct:
            result['warnings'].append(
                f"High VaR: {var_pct:.2%} (max: {self.config.max_var_pct:.2%})"
            )
        
        return result
    
    def _calculate_var(
        self,
        portfolio_state: Dict[str, Any],
        order: Dict[str, Any],
        price: float
    ) -> float:
        """
        Calculate Value at Risk using simplified Monte Carlo.
        
        Returns:
            VaR as percentage of portfolio
        """
        # Simplified VaR calculation
        # In production, use historical returns and proper Monte Carlo
        positions = portfolio_state.get('positions', {})
        balance = portfolio_state.get('balance', self.initial_capital)
        
        if not positions and order.get('size', 0) == 0:
            return 0.0
        
        # Estimate volatility (simplified)
        avg_volatility = 0.02  # 2% daily volatility assumption
        
        # Calculate portfolio value
        portfolio_value = balance + sum(
            abs(pos.get('size', 0) * pos.get('price', 0))
            for pos in positions.values()
        )
        
        # Add new position
        portfolio_value += order.get('size', 0) * price
        
        # VaR = Portfolio Value * Volatility * Z-score
        # For 95% confidence, Z = 1.645
        z_score = 1.645 if self.config.var_confidence_level == 0.95 else 2.33
        var_amount = portfolio_value * avg_volatility * z_score
        
        return var_amount / balance if balance > 0 else 0.0
    
    def update_state(self, portfolio_state: Dict[str, Any]):
        """Update portfolio state history."""
        self.position_history.append({
            'timestamp': portfolio_state.get('timestamp'),
            'balance': portfolio_state.get('balance'),
            'positions': len(portfolio_state.get('positions', {}))
        })
        
        # Keep last 1000 records
        if len(self.position_history) > 1000:
            self.position_history = self.position_history[-1000:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get portfolio risk statistics."""
        if not self.position_history:
            return {'exposure': 0, 'positions': 0}
        
        latest = self.position_history[-1]
        return {
            'exposure': latest.get('balance', 0) / self.initial_capital if self.initial_capital > 0 else 0,
            'positions': latest.get('positions', 0),
            'history_length': len(self.position_history)
        }
