"""
Trading Orchestrator - Main coordination layer.
Integrates all components: validation, sizing, execution, and meta-learning.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger

from src.agents.agent_ensemble import AgentEnsemble, EnsembleSignal
from .signal_validator import SignalValidator, ValidationResult
from .position_sizer import PositionSizer, PositionSize, SizingMethod
from .execution_manager import ExecutionManager, Trade, Position
from .meta_learner import MetaLearner


class TradingOrchestrator:
    """
    Main orchestration layer for the trading system.
    
    Workflow:
    1. Receive ensemble signal
    2. Validate signal quality
    3. Calculate position size
    4. Execute trade
    5. Update meta-learner
    6. Track performance
    """
    
    def __init__(
        self,
        ensemble: AgentEnsemble,
        initial_balance: float = 10000.0,
        min_confidence: float = 0.6,
        min_agreement: float = 0.5,
        max_position_pct: float = 0.1,
        sizing_method: SizingMethod = SizingMethod.KELLY,
        enable_meta_learning: bool = True
    ):
        """
        Initialize trading orchestrator.
        
        Args:
            ensemble: Agent ensemble
            initial_balance: Starting account balance
            min_confidence: Minimum signal confidence
            min_agreement: Minimum agent agreement
            max_position_pct: Maximum position size (% of account)
            sizing_method: Position sizing method
            enable_meta_learning: Enable meta-learning
        """
        self.ensemble = ensemble
        self.enable_meta_learning = enable_meta_learning
        
        # Initialize components
        self.validator = SignalValidator(
            min_confidence=min_confidence,
            min_agreement=min_agreement
        )
        
        self.sizer = PositionSizer(
            method=sizing_method,
            max_position_pct=max_position_pct
        )
        
        self.executor = ExecutionManager(
            initial_balance=initial_balance
        )
        
        self.meta_learner = MetaLearner() if enable_meta_learning else None
        
        # Current prices (for position updates)
        self.current_prices: Dict[str, float] = {}
        
        # Statistics
        self.signals_processed = 0
        self.signals_executed = 0
        self.start_time = datetime.now()
    
    def process_signal(
        self,
        symbol: str,
        ensemble_signal: EnsembleSignal,
        current_price: float,
        features: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process an ensemble signal through the full pipeline.
        
        Args:
            symbol: Trading symbol
            ensemble_signal: Signal from agent ensemble
            current_price: Current market price
            features: Market features (optional, for meta-learning)
        
        Returns:
            Dictionary with processing results
        """
        self.signals_processed += 1
        self.current_prices[symbol] = current_price
        
        result = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'signal': ensemble_signal.to_dict(),
            'validated': False,
            'executed': False,
            'trade': None,
            'position_size': None,
            'validation_result': None
        }
        
        # Step 1: Validate signal
        validation = self.validator.validate(ensemble_signal)
        result['validation_result'] = validation.to_dict()
        result['validated'] = validation.is_valid
        
        if not validation.is_valid:
            logger.debug(
                f"Signal rejected for {symbol}: {', '.join(validation.reasons)}"
            )
            return result
        
        # Step 2: Calculate position size
        position_size = self.sizer.calculate_size(
            signal=ensemble_signal,
            account_balance=self.executor.calculate_equity(),
            current_price=current_price
        )
        
        result['position_size'] = position_size.to_dict()
        
        # Check if we have an existing position
        existing_position = self.executor.get_position(symbol)
        if existing_position:
            position_size = self.sizer.adjust_for_existing_position(
                new_size=position_size,
                existing_size=existing_position.size,
                account_balance=self.executor.calculate_equity(),
                current_price=current_price
            )
        
        # Step 3: Execute trade
        if position_size.size > 0:
            trade = self.executor.execute_signal(
                symbol=symbol,
                direction=ensemble_signal.direction,
                size=position_size.size,
                current_price=current_price,
                signal_confidence=ensemble_signal.confidence,
                metadata={
                    'validation_score': validation.quality_score,
                    'agent_votes': ensemble_signal.votes,
                    'agreement_score': ensemble_signal.agreement_score
                }
            )
            
            result['executed'] = True
            result['trade'] = trade.to_dict()
            self.signals_executed += 1
            
            logger.info(
                f"Executed {trade.side} {trade.size:.4f} {symbol} @ ${trade.price:.2f} "
                f"(confidence: {ensemble_signal.confidence:.1%})"
            )
        
        # Step 4: Update meta-learner (if enabled)
        if self.enable_meta_learning and self.meta_learner:
            self._update_meta_learner(ensemble_signal, features)
        
        return result
    
    def _update_meta_learner(
        self,
        signal: EnsembleSignal,
        features: Optional[Dict[str, Any]]
    ):
        """Update meta-learner with signal information."""
        # Extract regime if available
        regime = None
        regime_signal = signal.agent_signals.get('regime_classifier')
        if regime_signal and regime_signal.reasoning:
            regime = regime_signal.reasoning.get('regime')
        
        # Update each agent's performance
        # Note: Actual outcome will be updated later when we know the result
        for agent_name, agent_signal in signal.agent_signals.items():
            self.meta_learner.initialize_agent(agent_name)
    
    def update_agent_performance(
        self,
        symbol: str,
        actual_outcome: str,
        pnl: Optional[float] = None
    ):
        """
        Update agent performance after knowing the outcome.
        
        Args:
            symbol: Trading symbol
            actual_outcome: Actual market outcome ('long', 'short', 'neutral')
            pnl: Realized PnL (optional)
        """
        if not self.enable_meta_learning or not self.meta_learner:
            return
        
        # Get the last trade for this symbol
        trades = self.executor.get_trade_history(symbol=symbol, limit=1)
        if not trades:
            return
        
        last_trade = trades[-1]
        
        # Extract agent signals from metadata
        # In a real implementation, we'd store this separately
        # For now, we'll update based on the ensemble decision
        
        # Update meta-learner
        # This is simplified - in production, track each agent's individual performance
        pass
    
    def update_prices(self, prices: Dict[str, float]):
        """
        Update current prices for all positions.
        
        Args:
            prices: Dictionary of symbol -> current_price
        """
        self.current_prices.update(prices)
        self.executor.update_position_prices(prices)
    
    def close_position(self, symbol: str) -> Optional[Trade]:
        """
        Manually close a position.
        
        Args:
            symbol: Trading symbol
        
        Returns:
            Trade object if position existed
        """
        if symbol not in self.current_prices:
            logger.warning(f"No current price for {symbol}")
            return None
        
        return self.executor.close_position(symbol, self.current_prices[symbol])
    
    def close_all_positions(self) -> list:
        """Close all open positions."""
        return self.executor.close_all_positions(self.current_prices)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current orchestrator status."""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            'uptime_seconds': uptime,
            'signals_processed': self.signals_processed,
            'signals_executed': self.signals_executed,
            'execution_rate': self.signals_executed / self.signals_processed if self.signals_processed > 0 else 0.0,
            'current_prices': self.current_prices.copy(),
            'open_positions': len(self.executor.positions),
            'equity': self.executor.calculate_equity(),
            'total_pnl': self.executor.calculate_total_pnl()
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        metrics = {
            'orchestrator': self.get_status(),
            'execution': self.executor.get_performance_metrics(),
            'validation': self.validator.get_stats(),
            'position_sizing': self.sizer.get_config()
        }
        
        if self.enable_meta_learning and self.meta_learner:
            metrics['meta_learning'] = self.meta_learner.get_stats()
        
        return metrics
    
    def get_positions(self) -> Dict[str, Position]:
        """Get all current positions."""
        return self.executor.get_all_positions()
    
    def get_trade_history(
        self,
        symbol: Optional[str] = None,
        limit: Optional[int] = None
    ) -> list:
        """Get trade history."""
        return self.executor.get_trade_history(symbol, limit)
    
    def update_configuration(self, config: Dict[str, Any]):
        """
        Update orchestrator configuration.
        
        Args:
            config: Configuration dictionary
        """
        # Update validator
        if 'validation' in config:
            val_config = config['validation']
            self.validator.set_thresholds(
                min_confidence=val_config.get('min_confidence'),
                min_agreement=val_config.get('min_agreement'),
                cooldown_seconds=val_config.get('cooldown_seconds')
            )
        
        # Update position sizer
        if 'position_sizing' in config:
            size_config = config['position_sizing']
            if 'max_position_pct' in size_config:
                self.sizer.set_limits(
                    max_pct=size_config['max_position_pct'],
                    min_pct=size_config.get('min_position_pct', self.sizer.min_position_pct)
                )
            if 'kelly_fraction' in size_config:
                self.sizer.set_kelly_fraction(size_config['kelly_fraction'])
        
        # Update meta-learner
        if 'meta_learning' in config and self.meta_learner:
            ml_config = config['meta_learning']
            if 'learning_rate' in ml_config:
                self.meta_learner.set_learning_rate(ml_config['learning_rate'])
            if 'update_frequency' in ml_config:
                self.meta_learner.set_update_frequency(ml_config['update_frequency'])
        
        logger.info("Configuration updated")
    
    def reset(self):
        """Reset orchestrator to initial state."""
        self.executor.reset()
        self.validator.reset_stats()
        if self.meta_learner:
            self.meta_learner.reset_all()
        
        self.current_prices.clear()
        self.signals_processed = 0
        self.signals_executed = 0
        self.start_time = datetime.now()
        
        logger.info("Orchestrator reset")
