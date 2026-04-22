"""
Test script for agent ensemble.
Demonstrates multi-agent prediction and aggregation.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from datetime import datetime
from pathlib import Path

from src.agents import (
    AgentRegistry,
    RegimeClassifier,
    MomentumAgent,
    MeanReversionAgent,
    OrderFlowAgent,
    AgentEnsemble
)


def create_sample_features():
    """Create sample market features."""
    price = 50000.0
    
    return {
        'timestamp': datetime.now(),
        'price': price,
        'ema_9': price * 0.998,
        'ema_21': price * 0.995,
        'rsi': 65.0,
        'order_flow_imbalance': 0.3,
        'cumulative_delta': 1500.0,
        'vpin': 0.4,
        'vwap': price * 0.999,
        'bid_volume': 10.5,
        'ask_volume': 8.2,
        'liquidity_heatmap': {
            'bid_prices': [price - i for i in range(1, 6)],
            'bid_volumes': [5.0, 4.5, 4.0, 3.5, 3.0],
            'ask_prices': [price + i for i in range(1, 6)],
            'ask_volumes': [4.0, 3.5, 3.0, 2.5, 2.0],
            'liquidity_imbalance': 0.2
        }
    }


def load_trained_agents(registry, model_dir='models'):
    """Load trained agents from disk."""
    model_path = Path(model_dir)
    
    if not model_path.exists():
        print(f"⚠ Model directory {model_dir} not found")
        print("  Run 'python scripts/train_agents.py' first to train models")
        return False
    
    agents = registry.get_all('BTCUSDT')
    loaded_count = 0
    
    for key, agent in agents.items():
        filename = f"{agent.name}_BTCUSDT.pkl"
        filepath = model_path / filename
        
        if filepath.exists():
            try:
                agent.load(str(filepath))
                print(f"✓ Loaded {agent.name}")
                loaded_count += 1
            except Exception as e:
                print(f"✗ Failed to load {agent.name}: {e}")
        else:
            print(f"⚠ Model file not found: {filepath}")
    
    return loaded_count > 0


def test_individual_agents(registry, features):
    """Test each agent individually."""
    print("\n" + "=" * 60)
    print("Individual Agent Predictions")
    print("=" * 60)
    
    agents = registry.get_all('BTCUSDT')
    
    for key, agent in agents.items():
        if not agent.is_trained:
            print(f"\n{agent.name}: NOT TRAINED")
            continue
        
        signal = agent.predict(features)
        
        print(f"\n{agent.name}:")
        print(f"  Direction: {signal.direction}")
        print(f"  Confidence: {signal.confidence:.2%}")
        
        if signal.reasoning:
            print(f"  Reasoning:")
            for k, v in signal.reasoning.items():
                if isinstance(v, dict):
                    print(f"    {k}:")
                    for k2, v2 in v.items():
                        print(f"      {k2}: {v2}")
                else:
                    print(f"    {k}: {v}")


def test_ensemble_strategies(registry, features):
    """Test different ensemble strategies."""
    print("\n" + "=" * 60)
    print("Ensemble Predictions")
    print("=" * 60)
    
    strategies = ['majority', 'weighted', 'regime_aware']
    
    for strategy in strategies:
        print(f"\n--- {strategy.upper()} Strategy ---")
        
        ensemble = AgentEnsemble(registry, strategy=strategy)
        signal = ensemble.predict('BTCUSDT', features)
        
        print(f"Direction: {signal.direction}")
        print(f"Confidence: {signal.confidence:.2%}")
        print(f"Agreement Score: {signal.agreement_score:.2%}")
        print(f"Votes: {signal.votes}")
        print(f"Number of Agents: {signal.num_agents}")


def test_different_market_conditions(registry):
    """Test ensemble under different market conditions."""
    print("\n" + "=" * 60)
    print("Testing Different Market Conditions")
    print("=" * 60)
    
    ensemble = AgentEnsemble(registry, strategy='regime_aware')
    
    # Scenario 1: Strong uptrend
    print("\n--- Scenario 1: Strong Uptrend ---")
    features = create_sample_features()
    features['price'] = 51000
    features['ema_9'] = 50800
    features['ema_21'] = 50500
    features['rsi'] = 75
    features['order_flow_imbalance'] = 0.6
    
    signal = ensemble.predict('BTCUSDT', features)
    print(f"Direction: {signal.direction}, Confidence: {signal.confidence:.2%}")
    
    # Scenario 2: Oversold (mean reversion opportunity)
    print("\n--- Scenario 2: Oversold Condition ---")
    features = create_sample_features()
    features['price'] = 49000
    features['vwap'] = 50000
    features['rsi'] = 25
    features['order_flow_imbalance'] = -0.4
    
    signal = ensemble.predict('BTCUSDT', features)
    print(f"Direction: {signal.direction}, Confidence: {signal.confidence:.2%}")
    
    # Scenario 3: High volatility
    print("\n--- Scenario 3: High Volatility ---")
    features = create_sample_features()
    features['vpin'] = 0.8
    features['rsi'] = 50
    features['order_flow_imbalance'] = 0.1
    
    signal = ensemble.predict('BTCUSDT', features)
    print(f"Direction: {signal.direction}, Confidence: {signal.confidence:.2%}")


def test_agent_weights(registry, features):
    """Test custom agent weights."""
    print("\n" + "=" * 60)
    print("Testing Custom Agent Weights")
    print("=" * 60)
    
    ensemble = AgentEnsemble(registry, strategy='weighted')
    
    # Default weights
    print("\n--- Default Weights ---")
    print(f"Weights: {ensemble.get_agent_weights()}")
    signal = ensemble.predict('BTCUSDT', features)
    print(f"Direction: {signal.direction}, Confidence: {signal.confidence:.2%}")
    
    # Boost momentum agent
    print("\n--- Boosted Momentum Agent ---")
    ensemble.set_agent_weight('momentum_agent', 3.0)
    print(f"Weights: {ensemble.get_agent_weights()}")
    signal = ensemble.predict('BTCUSDT', features)
    print(f"Direction: {signal.direction}, Confidence: {signal.confidence:.2%}")


def main():
    """Main test pipeline."""
    print("=" * 60)
    print("M281M AI Trading System - Ensemble Testing")
    print("=" * 60)
    
    # Create registry and agents
    registry = AgentRegistry()
    
    registry.register(RegimeClassifier('BTCUSDT'))
    registry.register(MomentumAgent('BTCUSDT', sequence_length=20))
    registry.register(MeanReversionAgent('BTCUSDT'))
    registry.register(OrderFlowAgent('BTCUSDT', state_size=30))
    
    # Try to load trained models
    print("\nLoading trained models...")
    if not load_trained_agents(registry):
        print("\n⚠ No trained models found. Training with minimal data...")
        
        # Quick training for demo
        from scripts.train_agents import generate_synthetic_market_data
        data = generate_synthetic_market_data(n_samples=500)
        
        regime_agent = registry.get('regime_classifier', 'BTCUSDT')
        regime_agent.train(data, n_iter=50)
        print("✓ Trained regime classifier")
    
    # Create sample features
    features = create_sample_features()
    
    # Run tests
    try:
        test_individual_agents(registry, features)
        test_ensemble_strategies(registry, features)
        test_different_market_conditions(registry)
        test_agent_weights(registry, features)
        
        print("\n" + "=" * 60)
        print("✓ All tests completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
