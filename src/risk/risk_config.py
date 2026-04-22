"""
Risk Configuration - Centralized risk parameters.
"""

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class RiskConfig:
    """
    Centralized risk management configuration.
    
    All risk parameters in one place for easy tuning.
    """
    
    # Trade-Level Risk
    max_position_size: float = 1.0  # Maximum position size per trade
    min_risk_reward_ratio: float = 1.5  # Minimum risk/reward ratio
    max_slippage_bps: float = 10.0  # Maximum allowed slippage (basis points)
    stop_loss_atr_multiplier: float = 2.0  # Stop loss = ATR * multiplier
    take_profit_atr_multiplier: float = 3.0  # Take profit = ATR * multiplier
    
    # Portfolio-Level Risk
    max_portfolio_exposure: float = 0.95  # Max % of capital deployed
    max_position_concentration: float = 0.30  # Max % in single position
    max_correlation: float = 0.7  # Max correlation between positions
    var_confidence_level: float = 0.95  # VaR confidence level
    var_time_horizon: int = 1  # VaR time horizon (days)
    max_var_pct: float = 0.05  # Max VaR as % of portfolio
    
    # Regime-Aware Risk
    volatile_regime_size_reduction: float = 0.5  # Reduce size by 50% in volatile regime
    trending_regime_size_increase: float = 1.2  # Increase size by 20% in trending regime
    sideways_regime_size_factor: float = 0.8  # Reduce size by 20% in sideways regime
    
    # Adversarial Risk
    order_book_imbalance_threshold: float = 0.7  # Pause if imbalance > 70%
    sudden_volume_spike_threshold: float = 3.0  # Pause if volume > 3x average
    price_manipulation_threshold: float = 0.02  # Pause if price moves > 2% in 1 min
    spoofing_detection_enabled: bool = True
    
    # Meta-Risk (Circuit Breakers)
    max_daily_drawdown_pct: float = 0.05  # Max 5% daily drawdown
    max_consecutive_losses: int = 3  # Pause after 3 consecutive losses
    max_daily_trades: int = 50  # Max trades per day
    min_time_between_trades_sec: int = 60  # Min 60 seconds between trades
    cooldown_period_after_loss_sec: int = 300  # 5 min cooldown after loss
    
    # Position Sizing
    default_position_size_pct: float = 0.02  # Default 2% of capital per trade
    max_leverage: float = 1.0  # No leverage by default
    
    # Monitoring
    enable_risk_logging: bool = True
    enable_risk_alerts: bool = True
    risk_check_timeout_ms: int = 100  # Max time for risk check
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'trade_level': {
                'max_position_size': self.max_position_size,
                'min_risk_reward_ratio': self.min_risk_reward_ratio,
                'max_slippage_bps': self.max_slippage_bps,
                'stop_loss_atr_multiplier': self.stop_loss_atr_multiplier,
                'take_profit_atr_multiplier': self.take_profit_atr_multiplier
            },
            'portfolio_level': {
                'max_portfolio_exposure': self.max_portfolio_exposure,
                'max_position_concentration': self.max_position_concentration,
                'max_correlation': self.max_correlation,
                'var_confidence_level': self.var_confidence_level,
                'var_time_horizon': self.var_time_horizon,
                'max_var_pct': self.max_var_pct
            },
            'regime_aware': {
                'volatile_regime_size_reduction': self.volatile_regime_size_reduction,
                'trending_regime_size_increase': self.trending_regime_size_increase,
                'sideways_regime_size_factor': self.sideways_regime_size_factor
            },
            'adversarial': {
                'order_book_imbalance_threshold': self.order_book_imbalance_threshold,
                'sudden_volume_spike_threshold': self.sudden_volume_spike_threshold,
                'price_manipulation_threshold': self.price_manipulation_threshold,
                'spoofing_detection_enabled': self.spoofing_detection_enabled
            },
            'meta_risk': {
                'max_daily_drawdown_pct': self.max_daily_drawdown_pct,
                'max_consecutive_losses': self.max_consecutive_losses,
                'max_daily_trades': self.max_daily_trades,
                'min_time_between_trades_sec': self.min_time_between_trades_sec,
                'cooldown_period_after_loss_sec': self.cooldown_period_after_loss_sec
            },
            'position_sizing': {
                'default_position_size_pct': self.default_position_size_pct,
                'max_leverage': self.max_leverage
            }
        }
    
    @classmethod
    def conservative(cls) -> 'RiskConfig':
        """Create conservative risk configuration."""
        return cls(
            max_position_size=0.5,
            min_risk_reward_ratio=2.0,
            max_slippage_bps=5.0,
            max_portfolio_exposure=0.70,
            max_position_concentration=0.20,
            max_daily_drawdown_pct=0.03,
            max_consecutive_losses=2,
            default_position_size_pct=0.01
        )
    
    @classmethod
    def aggressive(cls) -> 'RiskConfig':
        """Create aggressive risk configuration."""
        return cls(
            max_position_size=2.0,
            min_risk_reward_ratio=1.2,
            max_slippage_bps=20.0,
            max_portfolio_exposure=1.0,
            max_position_concentration=0.50,
            max_daily_drawdown_pct=0.10,
            max_consecutive_losses=5,
            default_position_size_pct=0.05,
            max_leverage=2.0
        )
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'RiskConfig':
        """Create config from dictionary."""
        # Flatten nested dict
        flat_config = {}
        for category, params in config_dict.items():
            if isinstance(params, dict):
                flat_config.update(params)
        
        return cls(**flat_config)
