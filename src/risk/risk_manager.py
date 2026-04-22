"""
Risk Manager - Main risk management orchestrator.
"""

import time
import logging
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, field

from .risk_config import RiskConfig
from .trade_risk import TradeRiskManager
from .portfolio_risk import PortfolioRiskManager
from .regime_risk import RegimeRiskManager
from .adversarial_risk import AdversarialRiskManager
from .meta_risk import MetaRiskManager

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskDecision:
    """
    Risk decision result.
    
    Attributes:
        approved: Whether the order is approved
        risk_level: Overall risk level
        adjusted_size: Adjusted position size (if modified)
        stop_loss: Recommended stop loss price
        take_profit: Recommended take profit price
        reasons: List of reasons for decision
        warnings: List of warnings
        metadata: Additional metadata
    """
    approved: bool
    risk_level: RiskLevel
    adjusted_size: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'approved': self.approved,
            'risk_level': self.risk_level.value,
            'adjusted_size': self.adjusted_size,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'reasons': self.reasons,
            'warnings': self.warnings,
            'metadata': self.metadata
        }


class RiskManager:
    """
    Multi-layer risk management system.
    
    Layers:
    1. Trade-Level: Stop loss, take profit, slippage
    2. Portfolio-Level: VaR, exposure, correlation
    3. Regime-Aware: Adjust based on market regime
    4. Adversarial: Detect manipulation
    5. Meta-Risk: Circuit breakers, drawdown limits
    """
    
    def __init__(
        self,
        config: Optional[RiskConfig] = None,
        initial_capital: float = 10000.0
    ):
        """
        Initialize risk manager.
        
        Args:
            config: Risk configuration
            initial_capital: Initial capital
        """
        self.config = config or RiskConfig()
        self.initial_capital = initial_capital
        
        # Initialize risk layers
        self.trade_risk = TradeRiskManager(self.config)
        self.portfolio_risk = PortfolioRiskManager(self.config, initial_capital)
        self.regime_risk = RegimeRiskManager(self.config)
        self.adversarial_risk = AdversarialRiskManager(self.config)
        self.meta_risk = MetaRiskManager(self.config)
        
        # Statistics
        self.total_checks = 0
        self.approved_orders = 0
        self.rejected_orders = 0
        self.modified_orders = 0
        
        logger.info("Risk Manager initialized")
    
    def check_order(
        self,
        order: Dict[str, Any],
        market_data: Dict[str, Any],
        portfolio_state: Dict[str, Any],
        regime: Optional[str] = None
    ) -> RiskDecision:
        """
        Perform comprehensive risk check on an order.
        
        Args:
            order: Order details (symbol, side, size, price, etc.)
            market_data: Current market data (price, volume, orderbook, etc.)
            portfolio_state: Current portfolio state (positions, balance, etc.)
            regime: Current market regime (optional)
        
        Returns:
            RiskDecision with approval status and adjustments
        """
        start_time = time.time()
        self.total_checks += 1
        
        symbol = order.get('symbol')
        side = order.get('side')
        size = order.get('size')
        price = market_data.get('price', order.get('price'))
        
        logger.info(f"Risk check: {symbol} {side} {size} @ {price}")
        
        # Initialize decision
        decision = RiskDecision(
            approved=True,
            risk_level=RiskLevel.LOW,
            adjusted_size=size
        )
        
        try:
            # Layer 5: Meta-Risk (Circuit Breakers) - Check first
            meta_check = self.meta_risk.check(order, portfolio_state)
            if not meta_check['approved']:
                decision.approved = False
                decision.risk_level = RiskLevel.CRITICAL
                decision.reasons.extend(meta_check['reasons'])
                self.rejected_orders += 1
                logger.warning(f"Order rejected by meta-risk: {meta_check['reasons']}")
                return decision
            
            if meta_check.get('warnings'):
                decision.warnings.extend(meta_check['warnings'])
            
            # Layer 4: Adversarial Risk
            adversarial_check = self.adversarial_risk.check(market_data)
            if not adversarial_check['approved']:
                decision.approved = False
                decision.risk_level = RiskLevel.HIGH
                decision.reasons.extend(adversarial_check['reasons'])
                self.rejected_orders += 1
                logger.warning(f"Order rejected by adversarial risk: {adversarial_check['reasons']}")
                return decision
            
            if adversarial_check.get('warnings'):
                decision.warnings.extend(adversarial_check['warnings'])
            
            # Layer 3: Regime-Aware Risk
            if regime:
                regime_check = self.regime_risk.check(order, regime)
                if regime_check.get('size_adjustment'):
                    decision.adjusted_size = size * regime_check['size_adjustment']
                    decision.warnings.append(
                        f"Size adjusted for {regime} regime: {size} -> {decision.adjusted_size:.4f}"
                    )
                    self.modified_orders += 1
            
            # Layer 2: Portfolio-Level Risk
            portfolio_check = self.portfolio_risk.check(order, portfolio_state, price)
            if not portfolio_check['approved']:
                decision.approved = False
                decision.risk_level = RiskLevel.HIGH
                decision.reasons.extend(portfolio_check['reasons'])
                self.rejected_orders += 1
                logger.warning(f"Order rejected by portfolio risk: {portfolio_check['reasons']}")
                return decision
            
            if portfolio_check.get('warnings'):
                decision.warnings.extend(portfolio_check['warnings'])
            
            if portfolio_check.get('size_adjustment'):
                decision.adjusted_size = min(
                    decision.adjusted_size or size,
                    portfolio_check['size_adjustment']
                )
                decision.warnings.append(
                    f"Size adjusted for portfolio limits: {decision.adjusted_size:.4f}"
                )
                self.modified_orders += 1
            
            # Layer 1: Trade-Level Risk
            trade_check = self.trade_risk.check(order, market_data)
            if not trade_check['approved']:
                decision.approved = False
                decision.risk_level = RiskLevel.MEDIUM
                decision.reasons.extend(trade_check['reasons'])
                self.rejected_orders += 1
                logger.warning(f"Order rejected by trade risk: {trade_check['reasons']}")
                return decision
            
            # Set stop loss and take profit
            decision.stop_loss = trade_check.get('stop_loss')
            decision.take_profit = trade_check.get('take_profit')
            
            if trade_check.get('warnings'):
                decision.warnings.extend(trade_check['warnings'])
            
            # Determine overall risk level
            if len(decision.warnings) == 0:
                decision.risk_level = RiskLevel.LOW
            elif len(decision.warnings) <= 2:
                decision.risk_level = RiskLevel.MEDIUM
            else:
                decision.risk_level = RiskLevel.HIGH
            
            # Final approval
            if decision.approved:
                self.approved_orders += 1
                logger.info(f"Order approved: {symbol} {side} {decision.adjusted_size}")
            
            # Add metadata
            decision.metadata = {
                'check_time_ms': (time.time() - start_time) * 1000,
                'layers_checked': 5,
                'original_size': size,
                'final_size': decision.adjusted_size
            }
            
        except Exception as e:
            logger.error(f"Error in risk check: {e}")
            decision.approved = False
            decision.risk_level = RiskLevel.CRITICAL
            decision.reasons.append(f"Risk check error: {str(e)}")
            self.rejected_orders += 1
        
        return decision
    
    def update_portfolio(self, portfolio_state: Dict[str, Any]):
        """
        Update portfolio state.
        
        Args:
            portfolio_state: Current portfolio state
        """
        self.portfolio_risk.update_state(portfolio_state)
        self.meta_risk.update_state(portfolio_state)
    
    def record_trade(self, trade: Dict[str, Any]):
        """
        Record a completed trade.
        
        Args:
            trade: Trade details
        """
        self.meta_risk.record_trade(trade)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get risk management statistics.
        
        Returns:
            Dictionary with statistics
        """
        approval_rate = self.approved_orders / self.total_checks if self.total_checks > 0 else 0
        modification_rate = self.modified_orders / self.total_checks if self.total_checks > 0 else 0
        
        return {
            'total_checks': self.total_checks,
            'approved_orders': self.approved_orders,
            'rejected_orders': self.rejected_orders,
            'modified_orders': self.modified_orders,
            'approval_rate': approval_rate,
            'modification_rate': modification_rate,
            'meta_risk': self.meta_risk.get_statistics(),
            'portfolio_risk': self.portfolio_risk.get_statistics()
        }
    
    def reset_daily_limits(self):
        """Reset daily limits (call at start of each trading day)."""
        self.meta_risk.reset_daily_limits()
        logger.info("Daily risk limits reset")
    
    def get_current_risk_level(self) -> RiskLevel:
        """
        Get current overall risk level.
        
        Returns:
            Current risk level
        """
        # Check meta-risk state
        if self.meta_risk.is_circuit_breaker_active():
            return RiskLevel.CRITICAL
        
        # Check portfolio risk
        portfolio_stats = self.portfolio_risk.get_statistics()
        if portfolio_stats.get('exposure', 0) > 0.9:
            return RiskLevel.HIGH
        elif portfolio_stats.get('exposure', 0) > 0.7:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
