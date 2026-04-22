"""
Training script for AI agents.
Generates synthetic training data and trains all agents.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

from src.agents import (
    AgentRegistry,
    RegimeClassifier,
    MomentumAgent,
    MeanReversionAgent,
    OrderFlowAgent
)


def generate_synthetic_market_data(n_samples: int = 1000):
    """
    Generate synthetic market data for training.
    
    Returns:
        List of feature dictionaries
    """
    print(f"Generating {n_samples} synthetic market samples...")
    
    data = []
    base_price = 50000.0
    cumulative_delta = 0.0
    
    for i in range(n_samples):
        # Simulate price movement
        price_change = np.random.randn() * 50
        price = base_price + price_change
        base_price = price * 0.99 + base_price * 0.01  # Slow drift
        
        # Generate features
        ema_9 = price * (1 + np.random.randn() * 0.001)
        ema_21 = price * (1 + np.random.randn() * 0.002)
        rsi = 50 + np.random.randn() * 20
        rsi = max(0, min(100, rsi))  # Clip to 0-100
        
        ofi = np.random.randn() * 0.3
        vpin = abs(np.random.randn() * 0.2)
        
        bid_volume = abs(np.random.randn() * 5 + 10)
        ask_volume = abs(np.random.randn() * 5 + 10)
        
        cumulative_delta += np.random.randn() * 100
        
        # Generate order book
        bid_prices = [price - i for i in range(1, 6)]
        bid_volumes = [abs(np.random.randn() * 2 + 5) for _ in range(5)]
        ask_prices = [price + i for i in range(1, 6)]
        ask_volumes = [abs(np.random.randn() * 2 + 5) for _ in range(5)]
        
        features = {
            'timestamp': datetime.now() + timedelta(seconds=i),
            'price': price,
            'ema_9': ema_9,
            'ema_21': ema_21,
            'rsi': rsi,
            'order_flow_imbalance': ofi,
            'cumulative_delta': cumulative_delta,
            'vpin': vpin,
            'vwap': price * (1 + np.random.randn() * 0.0005),
            'bid_volume': bid_volume,
            'ask_volume': ask_volume,
            'liquidity_heatmap': {
                'bid_prices': bid_prices,
                'bid_volumes': bid_volumes,
                'ask_prices': ask_prices,
                'ask_volumes': ask_volumes,
                'liquidity_imbalance': (sum(bid_volumes) - sum(ask_volumes)) / 
                                      (sum(bid_volumes) + sum(ask_volumes))
            }
        }
        
        data.append(features)
    
    print(f"✓ Generated {len(data)} samples")
    return data


def train_regime_classifier(agent, data):
    """Train regime classifier on market data."""
    print("\n=== Training Regime Classifier ===")
    
    # Use all data for regime classification
    metrics = agent.train(data, n_iter=100)
    
    print(f"✓ Training complete")
    print(f"  Log likelihood: {metrics['log_likelihood']:.2f}")
    print(f"  Regime distribution: {metrics['regime_distribution']}")
    
    return metrics


def train_momentum_agent(agent, data):
    """Train momentum agent on sequences."""
    print("\n=== Training Momentum Agent ===")
    
    sequence_length = agent.sequence_length
    training_data = []
    
    # Create sequences with labels
    for i in range(len(data) - sequence_length - 10):
        sequence = data[i:i+sequence_length]
        
        # Label based on future price movement
        current_price = data[i+sequence_length-1]['price']
        future_price = data[i+sequence_length+10]['price']
        price_change = (future_price - current_price) / current_price
        
        if price_change > 0.002:  # >0.2% up
            label = 2  # Up
        elif price_change < -0.002:  # <-0.2% down
            label = 0  # Down
        else:
            label = 1  # Neutral
        
        training_data.append((sequence, label))
    
    print(f"  Created {len(training_data)} sequences")
    
    # Train
    metrics = agent.train(training_data, epochs=50, batch_size=32)
    
    print(f"✓ Training complete")
    print(f"  Training accuracy: {metrics['training_accuracy']:.2%}")
    print(f"  Final loss: {metrics['final_loss']:.4f}")
    
    return metrics


def train_mean_reversion_agent(agent, data):
    """Train mean reversion agent."""
    print("\n=== Training Mean Reversion Agent ===")
    
    training_data = []
    
    # Create labeled samples
    for i in range(len(data) - 20):
        features = data[i]
        
        # Label based on price vs VWAP and RSI
        price = features['price']
        vwap = features['vwap']
        rsi = features['rsi']
        
        # Check if reversion occurred in next 20 samples
        future_prices = [data[i+j]['price'] for j in range(1, 21)]
        avg_future_price = np.mean(future_prices)
        
        price_to_vwap = (price - vwap) / vwap
        
        if price_to_vwap < -0.01 and avg_future_price > price:
            label = 1  # Reversion up
        elif price_to_vwap > 0.01 and avg_future_price < price:
            label = 2  # Reversion down
        else:
            label = 0  # No reversion
        
        training_data.append((features, label))
    
    print(f"  Created {len(training_data)} samples")
    
    # Train
    metrics = agent.train(training_data, n_estimators=100)
    
    print(f"✓ Training complete")
    print(f"  Training accuracy: {metrics['training_accuracy']:.2%}")
    print(f"  Class distribution: {metrics['class_distribution']}")
    
    # Show feature importance
    importance = agent.get_feature_importance()
    if importance:
        print(f"  Top features:")
        sorted_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)
        for feat, score in sorted_features[:5]:
            print(f"    {feat}: {score:.2f}")
    
    return metrics


def train_order_flow_agent(agent, data):
    """Train order flow agent with DQN."""
    print("\n=== Training Order Flow Agent ===")
    
    training_data = []
    
    # Create experience tuples (state, action, reward, next_state, done)
    for i in range(len(data) - 10):
        state = data[i]
        next_state = data[i+1]
        
        # Simulate action and reward
        current_price = state['price']
        next_price = next_state['price']
        price_change = (next_price - current_price) / current_price
        
        # Determine optimal action based on future price
        if price_change > 0.001:
            action = 2  # Long
            reward = price_change * 100
        elif price_change < -0.001:
            action = 0  # Short
            reward = -price_change * 100
        else:
            action = 1  # Neutral
            reward = 0
        
        done = (i % 100 == 0)  # Episode boundaries
        
        training_data.append((state, action, reward, next_state, done))
    
    print(f"  Created {len(training_data)} experience tuples")
    
    # Train
    metrics = agent.train(training_data, epochs=100)
    
    print(f"✓ Training complete")
    print(f"  Final loss: {metrics['final_loss']:.4f}")
    print(f"  Average loss: {metrics['avg_loss']:.4f}")
    print(f"  Buffer size: {metrics['buffer_size']}")
    
    return metrics


def save_agents(registry, output_dir='models'):
    """Save all trained agents."""
    print(f"\n=== Saving Models ===")
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    agents = registry.get_all('BTCUSDT')
    
    for key, agent in agents.items():
        if agent.is_trained:
            filename = f"{agent.name}_BTCUSDT.pkl"
            filepath = output_path / filename
            agent.save(str(filepath))
            print(f"✓ Saved {agent.name} to {filepath}")
    
    print(f"\n✓ All models saved to {output_dir}/")


def main():
    """Main training pipeline."""
    print("=" * 60)
    print("M281M AI Trading System - Agent Training")
    print("=" * 60)
    
    # Generate synthetic data
    data = generate_synthetic_market_data(n_samples=2000)
    
    # Create registry and agents
    registry = AgentRegistry()
    
    regime_agent = RegimeClassifier('BTCUSDT')
    momentum_agent = MomentumAgent('BTCUSDT', sequence_length=20)
    mean_reversion_agent = MeanReversionAgent('BTCUSDT')
    order_flow_agent = OrderFlowAgent('BTCUSDT', state_size=30)
    
    registry.register(regime_agent)
    registry.register(momentum_agent)
    registry.register(mean_reversion_agent)
    registry.register(order_flow_agent)
    
    # Train each agent
    try:
        train_regime_classifier(regime_agent, data)
        train_momentum_agent(momentum_agent, data)
        train_mean_reversion_agent(mean_reversion_agent, data)
        train_order_flow_agent(order_flow_agent, data)
        
        # Save models
        save_agents(registry)
        
        # Print summary
        print("\n" + "=" * 60)
        print("Training Summary")
        print("=" * 60)
        stats = registry.get_stats()
        print(f"Total agents: {stats['total_agents']}")
        print(f"Trained agents: {stats['trained_agents']}")
        print("\n✓ All agents trained successfully!")
        
    except Exception as e:
        print(f"\n✗ Error during training: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
