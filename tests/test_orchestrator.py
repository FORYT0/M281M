"""
Unit tests for orchestrator components.
"""

import pytest
import numpy as np
from datetime import datetime, timedelta

from src.agents import AgentRegistry, AgentEnsemble, EnsembleSignal
from src.orchestrator import (
    SignalValidator,
    PositionSizer,
    SizingMethod,
    ExecutionManager,
    MetaLearner,
    TradingOrchestrator
)


@pytest.fixture
def sample_ensemble_signal():
    """Create a sample ensemble signal."""
    return EnsembleSignal(
        timestamp=datetime.now(),
        symbol='BTCUSDT',
        direction='long',
        confidence=0.75,
        agent_signals={},
        votes={'long': 3, 'short': 0, 'neutral': 1},
        num_agents=4,
        agreement_score=0.75
    )


class TestSignalValidator:
    """Test signal validator."""
    
    def test_initialization(self):
        """Test validator initialization."""
        validator = SignalValidator(
            min_confidence=0.6,
            min_agreement=0.5
        )
        
        assert validator.min_confidence == 0.6
        assert validator.min_agreement == 0.5
    
    def test_validate_good_signal(self, sample_ensemble_signal):
        """Test validation of a good signal."""
        validator = SignalValidator(min_confidence=0.6, min_agreement=0.5)
        
        result = validator.validate(sample_ensemble_signal)
        
        assert result.is_valid
        assert len(result.reasons) == 0
        assert result.quality_score > 0.5
    
    def test_validate_low_confidence(self, sample_ensemble_signal):
        """Test rejection of low confidence signal."""
        validator = SignalValidator(min_confidence=0.9, min_agreement=0.5)
        
        result = validator.validate(sample_ensemble_signal)
        
        assert not result.is_valid
        assert any('Confidence' in reason for reason in result.reasons)
    
    def test_validate_low_agreement(self, sample_ensemble_signal):
        """Test rejection of low agreement signal."""
        validator = SignalValidator(min_confidence=0.6, min_agreement=0.9)
        
        result = validator.validate(sample_ensemble_signal)
        
        assert not result.is_valid
        assert any('Agreement' in reason for reason in result.reasons)
    
    def test_validate_neutral_signal(self, sample_ensemble_signal):
        """Test rejection of neutral signal."""
        validator = SignalValidator()
        
        sample_ensemble_signal.direction = 'neutral'
        result = validator.validate(sample_ensemble_signal)
        
        assert not result.is_valid
        assert any('neutral' in reason for reason in result.reasons)
    
    def test_cooldown_period(self, sample_ensemble_signal):
        """Test cooldown period enforcement."""
        validator = SignalValidator(cooldown_seconds=60)
        
        # First signal should pass
        result1 = validator.validate(sample_ensemble_signal)
        assert result1.is_valid
        
        # Second signal immediately after should fail
        result2 = validator.validate(sample_ensemble_signal)
        assert not result2.is_valid
        assert any('Cooldown' in reason for reason in result2.reasons)
    
    def test_set_thresholds(self):
        """Test updating thresholds."""
        validator = SignalValidator(min_confidence=0.6)
        
        validator.set_thresholds(min_confidence=0.8)
        assert validator.min_confidence == 0.8
    
    def test_get_stats(self, sample_ensemble_signal):
        """Test statistics tracking."""
        validator = SignalValidator()
        
        validator.validate(sample_ensemble_signal)
        validator.validate(sample_ensemble_signal)
        
        stats = validator.get_stats()
        assert stats['total_signals'] == 2
        assert 'pass_rate' in stats


class TestPositionSizer:
    """Test position sizer."""
    
    def test_initialization(self):
        """Test sizer initialization."""
        sizer = PositionSizer(
            method=SizingMethod.KELLY,
            max_position_pct=0.1
        )
        
        assert sizer.method == SizingMethod.KELLY
        assert sizer.max_position_pct == 0.1
    
    def test_calculate_size_kelly(self, sample_ensemble_signal):
        """Test Kelly criterion sizing."""
        sizer = PositionSizer(method=SizingMethod.KELLY)
        
        position_size = sizer.calculate_size(
            signal=sample_ensemble_signal,
            account_balance=10000.0,
            current_price=50000.0,
            win_rate=0.6,
            win_loss_ratio=1.5
        )
        
        assert position_size.size > 0
        assert position_size.size_pct <= sizer.max_position_pct
        assert position_size.method == 'kelly'
    
    def test_calculate_size_fixed(self, sample_ensemble_signal):
        """Test fixed sizing."""
        sizer = PositionSizer(method=SizingMethod.FIXED, max_position_pct=0.1)
        
        position_size = sizer.calculate_size(
            signal=sample_ensemble_signal,
            account_balance=10000.0,
            current_price=50000.0
        )
        
        assert position_size.size > 0
        assert position_size.method == 'fixed'
    
    def test_confidence_scaling(self, sample_ensemble_signal):
        """Test confidence-based scaling."""
        sizer = PositionSizer(confidence_scaling=True)
        
        # High confidence
        sample_ensemble_signal.confidence = 0.9
        size_high = sizer.calculate_size(
            signal=sample_ensemble_signal,
            account_balance=10000.0,
            current_price=50000.0
        )
        
        # Low confidence
        sample_ensemble_signal.confidence = 0.5
        size_low = sizer.calculate_size(
            signal=sample_ensemble_signal,
            account_balance=10000.0,
            current_price=50000.0
        )
        
        assert size_high.size > size_low.size
    
    def test_position_limits(self, sample_ensemble_signal):
        """Test position size limits."""
        sizer = PositionSizer(
            max_position_pct=0.1,
            min_position_pct=0.01
        )
        
        position_size = sizer.calculate_size(
            signal=sample_ensemble_signal,
            account_balance=10000.0,
            current_price=50000.0
        )
        
        assert position_size.size_pct >= sizer.min_position_pct
        assert position_size.size_pct <= sizer.max_position_pct


class TestExecutionManager:
    """Test execution manager."""
    
    def test_initialization(self):
        """Test manager initialization."""
        manager = ExecutionManager(initial_balance=10000.0)
        
        assert manager.initial_balance == 10000.0
        assert manager.current_balance == 10000.0
        assert len(manager.positions) == 0
    
    def test_open_position(self):
        """Test opening a position."""
        manager = ExecutionManager(initial_balance=10000.0)
        
        trade = manager.execute_signal(
            symbol='BTCUSDT',
            direction='long',
            size=0.1,
            current_price=50000.0,
            signal_confidence=0.75
        )
        
        assert trade.symbol == 'BTCUSDT'
        assert trade.side == 'buy'
        assert len(manager.positions) == 1
        assert 'BTCUSDT' in manager.positions
    
    def test_close_position(self):
        """Test closing a position."""
        manager = ExecutionManager(initial_balance=10000.0)
        
        # Open position
        manager.execute_signal(
            symbol='BTCUSDT',
            direction='long',
            size=0.1,
            current_price=50000.0,
            signal_confidence=0.75
        )
        
        # Close position at profit
        trade = manager.execute_signal(
            symbol='BTCUSDT',
            direction='short',
            size=0.1,
            current_price=51000.0,
            signal_confidence=0.75
        )
        
        assert trade.pnl is not None
        assert trade.pnl > 0  # Profit
        assert len(manager.positions) == 0
    
    def test_pnl_calculation(self):
        """Test PnL calculation."""
        manager = ExecutionManager(initial_balance=10000.0)
        
        # Open long position
        manager.execute_signal(
            symbol='BTCUSDT',
            direction='long',
            size=0.1,
            current_price=50000.0,
            signal_confidence=0.75
        )
        
        # Update price
        manager.update_position_prices({'BTCUSDT': 51000.0})
        
        position = manager.get_position('BTCUSDT')
        assert position.unrealized_pnl > 0
    
    def test_performance_metrics(self):
        """Test performance metrics."""
        manager = ExecutionManager(initial_balance=10000.0)
        
        # Execute some trades
        manager.execute_signal('BTCUSDT', 'long', 0.1, 50000.0, 0.75)
        manager.execute_signal('BTCUSDT', 'short', 0.1, 51000.0, 0.75)
        
        metrics = manager.get_performance_metrics()
        
        assert 'total_trades' in metrics
        assert 'win_rate' in metrics
        assert 'total_pnl' in metrics


class TestMetaLearner:
    """Test meta-learner."""
    
    def test_initialization(self):
        """Test learner initialization."""
        learner = MetaLearner(learning_rate=0.01)
        
        assert learner.learning_rate == 0.01
        assert len(learner.agent_performance) == 0
    
    def test_initialize_agent(self):
        """Test agent initialization."""
        learner = MetaLearner()
        
        learner.initialize_agent('test_agent', initial_weight=1.5)
        
        assert 'test_agent' in learner.agent_performance
        assert learner.weights['test_agent'] == 1.5
    
    def test_update_performance(self):
        """Test performance update."""
        learner = MetaLearner()
        
        learner.update_performance(
            agent_name='test_agent',
            signal_direction='long',
            actual_outcome='long',
            confidence=0.8,
            pnl=100.0
        )
        
        perf = learner.agent_performance['test_agent']
        assert perf.total_signals == 1
        assert perf.correct_signals == 1
        assert perf.accuracy == 1.0
    
    def test_weight_updates(self):
        """Test weight updates."""
        learner = MetaLearner(update_frequency=5)
        
        # Simulate good performance
        for i in range(10):
            learner.update_performance(
                agent_name='good_agent',
                signal_direction='long',
                actual_outcome='long',
                confidence=0.8,
                pnl=100.0
            )
        
        # Simulate bad performance
        for i in range(10):
            learner.update_performance(
                agent_name='bad_agent',
                signal_direction='long',
                actual_outcome='short',
                confidence=0.6,
                pnl=-50.0
            )
        
        weights = learner.get_optimal_weights()
        
        # Good agent should have higher weight
        assert weights['good_agent'] > weights['bad_agent']
    
    def test_regime_aware_weights(self):
        """Test regime-specific weights."""
        learner = MetaLearner(regime_aware=True)
        
        # Update with regime
        for i in range(10):
            learner.update_performance(
                agent_name='test_agent',
                signal_direction='long',
                actual_outcome='long',
                confidence=0.8,
                regime='trending'
            )
        
        regime_weights = learner.get_regime_weights()
        assert 'trending' in regime_weights


class TestTradingOrchestrator:
    """Test trading orchestrator."""
    
    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator with mock ensemble."""
        registry = AgentRegistry()
        ensemble = AgentEnsemble(registry, strategy='weighted')
        
        return TradingOrchestrator(
            ensemble=ensemble,
            initial_balance=10000.0,
            min_confidence=0.6
        )
    
    def test_initialization(self, orchestrator):
        """Test orchestrator initialization."""
        assert orchestrator.executor.initial_balance == 10000.0
        assert orchestrator.validator.min_confidence == 0.6
    
    def test_process_signal(self, orchestrator, sample_ensemble_signal):
        """Test signal processing."""
        result = orchestrator.process_signal(
            symbol='BTCUSDT',
            ensemble_signal=sample_ensemble_signal,
            current_price=50000.0
        )
        
        assert 'validated' in result
        assert 'executed' in result
        assert result['symbol'] == 'BTCUSDT'
    
    def test_get_status(self, orchestrator):
        """Test status retrieval."""
        status = orchestrator.get_status()
        
        assert 'signals_processed' in status
        assert 'equity' in status
        assert 'open_positions' in status
    
    def test_get_performance_metrics(self, orchestrator):
        """Test performance metrics."""
        metrics = orchestrator.get_performance_metrics()
        
        assert 'orchestrator' in metrics
        assert 'execution' in metrics
        assert 'validation' in metrics


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
