"""
Meta-Risk Manager - Layer 5.
Circuit breakers and drawdown limits.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from collections import deque
from datetime import datetime, timedelta

from .risk_config import RiskConfig

logger = logging.getLogger(__name__)


class MetaRiskManager:
    """
    Layer 5: Meta-risk management (circuit breakers).
    
    Monitors:
    - Daily drawdown limit
    - Consecutive losses
    - Trade frequency
    - Cooldown periods
    """
    
    def __init__(self, config: RiskConfig):
        """Initialize meta-risk manager."""
        self.config = config
        
        # State tracking
        self.daily_start_balance = 0.0
        self.daily_peak_balance = 0.0
        self.consecutive_losses = 0
        self.daily_trade_count = 0
        self.last_trade_time = 0.0
        self.last_loss_time = 0.0
        self.circuit_breaker_active = False
        self.circuit_breaker_until = 0.0
        
        # Trade history
        self.trade_history: deque = deque(maxlen=1000)
        
        # Daily reset tracking
        self.last_reset_date = datetime.now().date()
    
    def check(
        self,
        order: Dict[str, Any],
        portfolio_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check meta-risk conditions.
        
        Args:
            order: Order details
            portfolio_state: Current portfolio state
        
        Returns:
            Dict with approved, warnings, reasons
        """
        result = {
            'approved': True,
            'warnings': [],
            'reasons': []
        }
        
        current_time = time.time()
        balance = portfolio_state.get('balance', 0)
        
        # Auto-reset daily limits if new day
        self._check_daily_reset()
        
        # Initialize daily tracking
        if self.daily_start_balance == 0:
            self.daily_start_balance = balance
            self.daily_peak_balance = balance
        
        # Update peak balance
        if balance > self.daily_peak_balance:
            self.daily_peak_balance = balance
        
        # Check if circuit breaker is active
        if self.circuit_breaker_active:
            if current_time < self.circuit_breaker_until:
                result['approved'] = False
                remaining = int(self.circuit_breaker_until - current_time)
                result['reasons'].append(
                    f"Circuit breaker active for {remaining}s"
                )
                return result
            else:
                self._deactivate_circuit_breaker()
        
        # Check daily drawdown
        drawdown = (self.daily_peak_balance - balance) / self.daily_peak_balance if self.daily_peak_balance > 0 else 0
        if drawdown > self.config.max_daily_drawdown_pct:
            result['approved'] = False
            result['reasons'].append(
                f"Daily drawdown {drawdown:.2%} exceeds limit {self.config.max_daily_drawdown_pct:.2%}"
            )
            self._activate_circuit_breaker(3600)  # 1 hour cooldown
            return result
        
        # Check consecutive losses
        if self.consecutive_losses >= self.config.max_consecutive_losses:
            result['approved'] = False
            result['reasons'].append(
                f"Max consecutive losses reached: {self.consecutive_losses}"
            )
            self._activate_circuit_breaker(1800)  # 30 min cooldown
            return result
        
        # Check daily trade limit
        if self.daily_trade_count >= self.config.max_daily_trades:
            result['approved'] = False
            result['reasons'].append(
                f"Daily trade limit reached: {self.daily_trade_count}/{self.config.max_daily_trades}"
            )
            return result
        
        # Check minimum time between trades
        if self.last_trade_time > 0:
            time_since_last = current_time - self.last_trade_time
            if time_since_last < self.config.min_time_between_trades_sec:
                result['approved'] = False
                result['reasons'].append(
                    f"Too soon since last trade: {time_since_last:.0f}s (min: {self.config.min_time_between_trades_sec}s)"
                )
                return result
        
        # Check cooldown after loss
        if self.last_loss_time > 0:
            time_since_loss = current_time - self.last_loss_time
            if time_since_loss < self.config.cooldown_period_after_loss_sec:
                result['approved'] = False
                result['reasons'].append(
                    f"Cooldown period after loss: {time_since_loss:.0f}s (required: {self.config.cooldown_period_after_loss_sec}s)"
                )
                return result
        
        # Warnings
        if drawdown > self.config.max_daily_drawdown_pct * 0.7:
            result['warnings'].append(
                f"Approaching daily drawdown limit: {drawdown:.2%}"
            )
        
        if self.daily_trade_count > self.config.max_daily_trades * 0.8:
            result['warnings'].append(
                f"Approaching daily trade limit: {self.daily_trade_count}/{self.config.max_daily_trades}"
            )
        
        return result
    
    def record_trade(self, trade: Dict[str, Any]):
        """
        Record a completed trade.
        
        Args:
            trade: Trade details with pnl
        """
        self.last_trade_time = time.time()
        self.daily_trade_count += 1
        
        pnl = trade.get('pnl', 0)
        self.trade_history.append({
            'timestamp': time.time(),
            'pnl': pnl,
            'symbol': trade.get('symbol')
        })
        
        # Track consecutive losses
        if pnl < 0:
            self.consecutive_losses += 1
            self.last_loss_time = time.time()
        else:
            self.consecutive_losses = 0
            self.last_loss_time = 0.0
    
    def update_state(self, portfolio_state: Dict[str, Any]):
        """Update portfolio state."""
        balance = portfolio_state.get('balance', 0)
        
        if self.daily_start_balance == 0:
            self.daily_start_balance = balance
            self.daily_peak_balance = balance
        
        if balance > self.daily_peak_balance:
            self.daily_peak_balance = balance
    
    def reset_daily_limits(self):
        """Reset daily limits (call at start of trading day)."""
        self.daily_trade_count = 0
        self.consecutive_losses = 0
        self.last_trade_time = 0.0
        self.last_loss_time = 0.0
        self.daily_start_balance = 0.0
        self.daily_peak_balance = 0.0
        self.last_reset_date = datetime.now().date()
        logger.info("Daily risk limits reset")
    
    def _check_daily_reset(self):
        """Check if we need to reset daily limits."""
        current_date = datetime.now().date()
        if current_date > self.last_reset_date:
            self.reset_daily_limits()
    
    def _activate_circuit_breaker(self, duration_seconds: int):
        """Activate circuit breaker."""
        self.circuit_breaker_active = True
        self.circuit_breaker_until = time.time() + duration_seconds
        logger.warning(f"Circuit breaker activated for {duration_seconds}s")
    
    def _deactivate_circuit_breaker(self):
        """Deactivate circuit breaker."""
        self.circuit_breaker_active = False
        self.circuit_breaker_until = 0.0
        logger.info("Circuit breaker deactivated")
    
    def is_circuit_breaker_active(self) -> bool:
        """Check if circuit breaker is active."""
        if self.circuit_breaker_active and time.time() >= self.circuit_breaker_until:
            self._deactivate_circuit_breaker()
        return self.circuit_breaker_active
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get meta-risk statistics."""
        current_time = time.time()
        
        # Calculate win rate from recent trades
        recent_trades = [t for t in self.trade_history if current_time - t['timestamp'] < 86400]
        wins = sum(1 for t in recent_trades if t['pnl'] > 0)
        win_rate = wins / len(recent_trades) if recent_trades else 0.0
        
        return {
            'daily_trade_count': self.daily_trade_count,
            'consecutive_losses': self.consecutive_losses,
            'circuit_breaker_active': self.circuit_breaker_active,
            'daily_drawdown': (self.daily_peak_balance - self.daily_start_balance) / self.daily_peak_balance if self.daily_peak_balance > 0 else 0,
            'win_rate_24h': win_rate,
            'total_trades': len(self.trade_history)
        }
