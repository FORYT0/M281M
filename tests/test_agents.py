"""
Unit tests for AI agents.
"""

import pytest
import numpy as np
from datetime import datetime

from src.agents import (
    AgentRegistry,
    RegimeClassifier,
    MomentumAgent,
    MeanReversionAgent,
    OrderFlowAgent,
    AgentEnsemble
)


@pytest.fixture
def sample_features():
    """Sample market features for testing."""
    return {
        'timestamp': datetime.now(),
        'price': 50000.0,
        'ema_9': 49900.0,
        'ema_21': 49800.0,
        'rsi': 65.0,
        'order_flow_imbalance': 0.3,
        'cumulative_delta': 1500.0,
        'vpin': 0.4,
        'vwap': 49950.0,
        'bid_volume': 10.5,
        'ask_volume': 8.2,
        'liquidity_heatmap': {
            'bid_prices': [49999, 49998, 49997, 49996, 49995],
            'bid_volumes': [5.0, 4.5, 4.0, 3.5, 3.0],
            'ask_prices': [50001, 50002, 50003, 50004, 50005],
            'ask_volumes': [4.0, 3.5, 3.0, 2.5, 2.0],
            'liquidity_imbalance': 0.2
        }
    }


@pytest.fixture
def agent_registry():
    """Create agent registry with all agents."""
    registry = AgentRegistry()
    
    # Register agents
    registry.register(RegimeClassifier('BTCUSDT'))
    registry.register(MomentumAgent('BTCUSDT'))
    registry.register(MeanReversionAgent('BTCUSDT'))
    registry.register(OrderFlowAgent('BTCUSDT'))
    
    return registry


class TestAgentRegistry:
    """Test agent registry functionality."""
    
    def test_register_agent(self, agent_registry):
        """Test agent registration."""
        assert len(agent_registry.agents) == 4
        
        # Check specific agent
        regime_agent = agent_registry.get('regime_classifier', 'BTCUSDT')
        assert regime_agent is not None
        assert regime_agent.name == 'regime_classifier'
    
    def test_get_all_agents(self, agent_registry):
        """Test getting all agents for a symbol."""
        agents = agent_registry.get_all('BTCUSDT')
        assert len(agents) == 4
    
    def test_get_stats(self, agent_registry):
        """Test getting registry statistics."""
        stats = agent_registry.get_stats()
        assert stats['total_agents'] == 4
        assert stats['trained_agents'] == 0  # None trained yet


class TestRegimeClassifier:
    """Test regime classifier agent."""
    
    def test_initialization(self):
        """Test agent initialization."""
        agent = RegimeClassifier('BTCUSDT')
        assert agent.name == 'regime_classifier'
        assert agent.symbol == 'BTCUSDT'
        assert not agent.is_trained
    
    def test_predict_untrained(self, sample_features):
        """Test prediction on untrained model."""
        agent = RegimeClassifier('BTCUSDT')
        signal = agent.predict(sample_features)
        
        assert signal.direction == 'neutral'
        assert signal.confidence == 0.0
        assert 'error' in signal.reasoning
    
    def test_train(self, sample_features):
        """Test training regime classifier."""
        agent = RegimeClassifier('BTCUSDT')
        
        # Generate synthetic training data
        training_data = []
        for i in range(200):
            features = sample_features.copy()
            features['price'] = 50000 + np.random.randn() * 100
            features['rsi'] = 50 + np.random.randn() * 20
            training_data.append(features)
        
        # Train
        metrics = agent.train(training_data, n_iter=50)
        
        assert agent.is_trained
        assert 'log_likelihood' in metrics
        assert metrics['n_samples'] == 200
    
    def test_predict_trained(self, sample_features):
        """Test prediction on trained model."""
        agent = RegimeClassifier('BTCUSDT')
        
        # Generate and train
        training_data = [sample_features.copy() for _ in range(200)]
        agent.train(training_data, n_iter=50)
        
        # Predict
        signal = agent.predict(sample_features)
        
        assert signal.direction in ['long', 'short', 'neutral']
        assert 0.0 <= signal.confidence <= 1.0
        assert 'regime' in signal.reasoning


class TestMomentumAgent:
    """Test momentum agent."""
    
    def test_initialization(self):
        """Test agent initialization."""
        agent = MomentumAgent('BTCUSDT')
        assert agent.name == 'momentum_agent'
        assert agent.sequence_length == 20
    
    def test_predict_untrained(self, sample_features):
        """Test prediction on untrained model."""
        agent = MomentumAgent('BTCUSDT')
        signal = agent.predict(sample_features)
        
        assert signal.direction == 'neutral'
        assert signal.confidence == 0.0
    
    def test_train(self, sample_features):
        """Test training momentum agent."""
        agent = MomentumAgent('BTCUSDT', sequence_length=10)
        
        # Generate synthetic sequences
        training_data = []
        for i in range(150):
            sequence = []
            for j in range(10):
                features = sample_features.copy()
                features['price'] = 50000 + i * 10 + j
                sequence.append(features)
            
            # Label: 0=down, 1=neutral, 2=up
            label = i % 3
            training_data.append((sequence, label))
        
        # Train
        metrics = agent.train(training_data, epochs=20, batch_size=16)
        
        assert agent.is_trained
        assert 'training_accuracy' in metrics
        assert metrics['n_samples'] == 150
    
    def test_buffer_warmup(self, sample_features):
        """Test feature buffer warmup."""
        agent = MomentumAgent('BTCUSDT', sequence_length=5)
        
        # Generate training data
        training_data = []
        for i in range(100):
            sequence = [sample_features.copy() for _ in range(5)]
            training_data.append((sequence, 1))
        
        agent.train(training_data, epochs=10)
        
        # Predict with insufficient buffer
        signal = agent.predict(sample_features)
        assert 'Warming up' in signal.reasoning.get('error', '')
        
        # Fill buffer
        for _ in range(5):
            signal = agent.predict(sample_features)
        
        # Should now predict
        assert signal.direction in ['long', 'short', 'neutral']


class TestMeanReversionAgent:
    """Test mean reversion agent."""
    
    def test_initialization(self):
        """Test agent initialization."""
        agent = MeanReversionAgent('BTCUSDT')
        assert agent.name == 'mean_reversion_agent'
    
    def test_predict_untrained(self, sample_features):
        """Test prediction on untrained model."""
        agent = MeanReversionAgent('BTCUSDT')
        signal = agent.predict(sample_features)
        
        assert signal.direction == 'neutral'
        assert signal.confidence == 0.0
    
    def test_train(self, sample_features):
        """Test training mean reversion agent."""
        agent = MeanReversionAgent('BTCUSDT')
        
        # Generate synthetic training data
        training_data = []
        for i in range(200):
            features = sample_features.copy()
            features['price'] = 50000 + np.random.randn() * 500
            features['vwap'] = 50000 + np.random.randn() * 100
            features['rsi'] = 50 + np.random.randn() * 30
            
            # Label based on RSI
            if features['rsi'] < 30:
                label = 1  # Reversion up
            elif features['rsi'] > 70:
                label = 2  # Reversion down
            else:
                label = 0  # No reversion
            
            training_data.append((features, label))
        
        # Train
        metrics = agent.train(training_data, n_estimators=50)
        
        assert agent.is_trained
        assert 'training_accuracy' in metrics
        assert metrics['n_samples'] == 200
    
    def test_feature_importance(self, sample_features):
        """Test feature importance extraction."""
        agent = MeanReversionAgent('BTCUSDT')
        
        # Generate and train
        training_data = []
        for i in range(200):
            features = sample_features.copy()
            features['rsi'] = 30 + i % 60
            label = 1 if features['rsi'] < 40 else (2 if features['rsi'] > 60 else 0)
            training_data.append((features, label))
        
        agent.train(training_data, n_estimators=50)
        
        # Get feature importance
        importance = agent.get_feature_importance()
        assert isinstance(importance, dict)


class TestOrderFlowAgent:
    """Test order flow agent."""
    
    def test_initialization(self):
        """Test agent initialization."""
        agent = OrderFlowAgent('BTCUSDT')
        assert agent.name == 'order_flow_agent'
        assert agent.action_size == 3
    
    def test_predict_untrained(self, sample_features):
        """Test prediction on untrained model."""
        agent = OrderFlowAgent('BTCUSDT')
        signal = agent.predict(sample_features)
        
        assert signal.direction == 'neutral'
        assert signal.confidence == 0.0
    
    def test_train(self, sample_features):
        """Test training order flow agent."""
        agent = OrderFlowAgent('BTCUSDT', state_size=30)
        
        # Generate synthetic experience tuples
        training_data = []
        for i in range(200):
            state = sample_features.copy()
            action = i % 3  # 0=short, 1=neutral, 2=long
            reward = np.random.randn()
            next_state = sample_features.copy()
            done = (i % 50 == 0)
            
            training_data.append((state, action, reward, next_state, done))
        
        # Train
        metrics = agent.train(training_data, epochs=30)
        
        assert agent.is_trained
        assert 'final_loss' in metrics
        assert metrics['n_samples'] == 200


class TestAgentEnsemble:
    """Test agent ensemble."""
    
    def test_initialization(self, agent_registry):
        """Test ensemble initialization."""
        ensemble = AgentEnsemble(agent_registry, strategy='weighted')
        assert ensemble.strategy == 'weighted'
    
    def test_predict_no_trained_agents(self, agent_registry, sample_features):
        """Test prediction with no trained agents."""
        ensemble = AgentEnsemble(agent_registry)
        signal = ensemble.predict('BTCUSDT', sample_features)
        
        # Should return neutral when no agents trained
        assert signal.direction == 'neutral'
        assert signal.num_agents == 0
    
    def test_majority_voting(self, agent_registry, sample_features):
        """Test majority voting strategy."""
        # Train a simple agent
        regime_agent = agent_registry.get('regime_classifier', 'BTCUSDT')
        training_data = [sample_features.copy() for _ in range(200)]
        regime_agent.train(training_data, n_iter=50)
        
        ensemble = AgentEnsemble(agent_registry, strategy='majority')
        signal = ensemble.predict('BTCUSDT', sample_features)
        
        assert signal.direction in ['long', 'short', 'neutral']
        assert 'votes' in signal.to_dict()
    
    def test_set_agent_weight(self, agent_registry):
        """Test setting agent weights."""
        ensemble = AgentEnsemble(agent_registry)
        
        ensemble.set_agent_weight('momentum_agent', 2.5)
        weights = ensemble.get_agent_weights()
        
        assert weights['momentum_agent'] == 2.5
    
    def test_change_strategy(self, agent_registry):
        """Test changing aggregation strategy."""
        ensemble = AgentEnsemble(agent_registry, strategy='majority')
        
        ensemble.set_strategy('weighted')
        assert ensemble.strategy == 'weighted'
        
        with pytest.raises(ValueError):
            ensemble.set_strategy('invalid_strategy')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
