"""
Order Flow Agent - Deep Q-Network for order book-based decisions.
Learns optimal actions from order book microstructure patterns.
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import pickle
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from collections import deque
import random

from .base_agent import BaseAgent, AgentSignal


class DQNetwork(nn.Module):
    """Deep Q-Network for order flow analysis."""
    
    def __init__(self, state_size: int, action_size: int = 3, hidden_size: int = 128):
        super().__init__()
        
        self.network = nn.Sequential(
            nn.Linear(state_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Linear(64, action_size)
        )
    
    def forward(self, x):
        return self.network(x)


class ReplayBuffer:
    """Experience replay buffer for DQN training."""
    
    def __init__(self, capacity: int = 10000):
        self.buffer = deque(maxlen=capacity)
    
    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))
    
    def sample(self, batch_size: int):
        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        return (
            np.array(states),
            np.array(actions),
            np.array(rewards),
            np.array(next_states),
            np.array(dones)
        )
    
    def __len__(self):
        return len(self.buffer)


class OrderFlowAgent(BaseAgent):
    """
    Order flow agent using Deep Q-Network.
    
    Actions:
    0 - Short: Sell signal
    1 - Neutral: No action
    2 - Long: Buy signal
    """
    
    def __init__(
        self,
        symbol: str,
        state_size: int = 30,
        hidden_size: int = 128,
        device: str = 'cpu'
    ):
        """
        Initialize order flow agent.
        
        Args:
            symbol: Trading symbol
            state_size: Size of state vector
            hidden_size: Hidden layer size
            device: 'cpu' or 'cuda'
        """
        super().__init__(name='order_flow_agent', symbol=symbol)
        
        self.state_size = state_size
        self.hidden_size = hidden_size
        self.device = device
        self.action_size = 3
        
        # DQN components
        self.policy_net = None
        self.target_net = None
        self.optimizer = None
        self.replay_buffer = ReplayBuffer(capacity=10000)
        
        # Training hyperparameters
        self.gamma = 0.99  # Discount factor
        self.epsilon = 1.0  # Exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001
        self.batch_size = 64
        self.target_update_freq = 10
        
        # Feature extraction
        self.feature_names = self._get_feature_names()
    
    def _get_feature_names(self) -> List[str]:
        """Define features extracted from order book."""
        features = [
            'order_flow_imbalance',
            'vpin',
            'cumulative_delta',
            'bid_volume',
            'ask_volume',
            'liquidity_imbalance',
        ]
        
        # Add order book depth features (top 5 levels)
        for i in range(5):
            features.extend([
                f'bid_price_{i}',
                f'bid_volume_{i}',
                f'ask_price_{i}',
                f'ask_volume_{i}'
            ])
        
        return features
    
    def _extract_state(self, features: Dict[str, Any]) -> np.ndarray:
        """
        Extract state vector from features.
        
        Args:
            features: Market features including order book
        
        Returns:
            State vector for DQN
        """
        state = []
        
        # Microstructure features
        state.append(features.get('order_flow_imbalance', 0.0))
        state.append(features.get('vpin', 0.0))
        state.append(features.get('cumulative_delta', 0.0))
        state.append(features.get('bid_volume', 0.0))
        state.append(features.get('ask_volume', 0.0))
        
        # Liquidity heatmap
        heatmap = features.get('liquidity_heatmap', {})
        state.append(heatmap.get('liquidity_imbalance', 0.0))
        
        # Order book depth (top 5 levels)
        bid_prices = heatmap.get('bid_prices', [])
        bid_volumes = heatmap.get('bid_volumes', [])
        ask_prices = heatmap.get('ask_prices', [])
        ask_volumes = heatmap.get('ask_volumes', [])
        
        for i in range(5):
            if i < len(bid_prices):
                state.append(bid_prices[i])
                state.append(bid_volumes[i])
            else:
                state.extend([0.0, 0.0])
            
            if i < len(ask_prices):
                state.append(ask_prices[i])
                state.append(ask_volumes[i])
            else:
                state.extend([0.0, 0.0])
        
        # Pad or truncate to state_size
        state_array = np.array(state, dtype=np.float32)
        if len(state_array) < self.state_size:
            state_array = np.pad(
                state_array,
                (0, self.state_size - len(state_array)),
                mode='constant'
            )
        else:
            state_array = state_array[:self.state_size]
        
        return state_array
    
    def predict(self, features: Dict[str, Any]) -> AgentSignal:
        """
        Predict action from order flow state.
        
        Args:
            features: Market features
        
        Returns:
            AgentSignal with action
        """
        if not self.is_trained or self.policy_net is None:
            return AgentSignal(
                agent_name=self.name,
                timestamp=datetime.now(),
                symbol=self.symbol,
                direction='neutral',
                confidence=0.0,
                reasoning={'error': 'Model not trained'}
            )
        
        # Extract state
        state = self._extract_state(features)
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        
        # Get Q-values
        self.policy_net.eval()
        with torch.no_grad():
            q_values = self.policy_net(state_tensor)
            action = torch.argmax(q_values, dim=1).item()
            confidence = torch.softmax(q_values, dim=1)[0, action].item()
        
        # Map action to direction
        direction_map = {0: 'short', 1: 'neutral', 2: 'long'}
        direction = direction_map[action]
        
        self._update_stats()
        
        return AgentSignal(
            agent_name=self.name,
            timestamp=datetime.now(),
            symbol=self.symbol,
            direction=direction,
            confidence=float(confidence),
            reasoning={
                'action': int(action),
                'q_values': {
                    'short': float(q_values[0, 0]),
                    'neutral': float(q_values[0, 1]),
                    'long': float(q_values[0, 2])
                },
                'order_flow_imbalance': features.get('order_flow_imbalance', 0.0),
                'vpin': features.get('vpin', 0.0)
            },
            features_used={
                'state_vector': state.tolist()
            }
        )
    
    def train(
        self,
        training_data: List[Tuple[Dict[str, Any], int, float, Dict[str, Any], bool]],
        epochs: int = 100
    ) -> Dict[str, float]:
        """
        Train DQN on experience tuples.
        
        Args:
            training_data: List of (state_features, action, reward, next_state_features, done)
            epochs: Number of training epochs
        
        Returns:
            Training metrics
        """
        if len(training_data) < 100:
            raise ValueError("Need at least 100 samples for training")
        
        # Initialize networks
        self.policy_net = DQNetwork(
            state_size=self.state_size,
            action_size=self.action_size,
            hidden_size=self.hidden_size
        ).to(self.device)
        
        self.target_net = DQNetwork(
            state_size=self.state_size,
            action_size=self.action_size,
            hidden_size=self.hidden_size
        ).to(self.device)
        
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()
        
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=self.learning_rate)
        
        # Populate replay buffer
        for state_features, action, reward, next_state_features, done in training_data:
            state = self._extract_state(state_features)
            next_state = self._extract_state(next_state_features)
            self.replay_buffer.push(state, action, reward, next_state, done)
        
        # Training loop
        losses = []
        
        for epoch in range(epochs):
            if len(self.replay_buffer) < self.batch_size:
                continue
            
            # Sample batch
            states, actions, rewards, next_states, dones = self.replay_buffer.sample(
                self.batch_size
            )
            
            # Convert to tensors
            states = torch.FloatTensor(states).to(self.device)
            actions = torch.LongTensor(actions).to(self.device)
            rewards = torch.FloatTensor(rewards).to(self.device)
            next_states = torch.FloatTensor(next_states).to(self.device)
            dones = torch.FloatTensor(dones).to(self.device)
            
            # Compute Q-values
            current_q = self.policy_net(states).gather(1, actions.unsqueeze(1))
            
            # Compute target Q-values
            with torch.no_grad():
                next_q = self.target_net(next_states).max(1)[0]
                target_q = rewards + (1 - dones) * self.gamma * next_q
            
            # Compute loss
            loss = nn.MSELoss()(current_q.squeeze(), target_q)
            
            # Optimize
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
            
            losses.append(loss.item())
            
            # Update target network
            if (epoch + 1) % self.target_update_freq == 0:
                self.target_net.load_state_dict(self.policy_net.state_dict())
            
            if (epoch + 1) % 20 == 0:
                print(f"Epoch {epoch+1}/{epochs}, Loss: {loss.item():.4f}")
        
        self.is_trained = True
        
        metrics = {
            'final_loss': losses[-1] if losses else 0.0,
            'avg_loss': np.mean(losses) if losses else 0.0,
            'n_samples': len(training_data),
            'epochs': epochs,
            'buffer_size': len(self.replay_buffer)
        }
        
        return metrics
    
    def save(self, path: str) -> None:
        """Save model to disk."""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
        
        model_data = {
            'policy_net_state': self.policy_net.state_dict(),
            'target_net_state': self.target_net.state_dict(),
            'optimizer_state': self.optimizer.state_dict(),
            'state_size': self.state_size,
            'hidden_size': self.hidden_size,
            'feature_names': self.feature_names,
            'is_trained': self.is_trained,
            'epsilon': self.epsilon
        }
        
        with open(path, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load(self, path: str) -> None:
        """Load model from disk."""
        with open(path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.state_size = model_data['state_size']
        self.hidden_size = model_data['hidden_size']
        self.feature_names = model_data['feature_names']
        self.is_trained = model_data['is_trained']
        self.epsilon = model_data['epsilon']
        
        # Recreate networks
        self.policy_net = DQNetwork(
            state_size=self.state_size,
            action_size=self.action_size,
            hidden_size=self.hidden_size
        ).to(self.device)
        
        self.target_net = DQNetwork(
            state_size=self.state_size,
            action_size=self.action_size,
            hidden_size=self.hidden_size
        ).to(self.device)
        
        self.policy_net.load_state_dict(model_data['policy_net_state'])
        self.target_net.load_state_dict(model_data['target_net_state'])
        
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=self.learning_rate)
        self.optimizer.load_state_dict(model_data['optimizer_state'])
        
        self.policy_net.eval()
        self.target_net.eval()
