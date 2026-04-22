"""
Momentum Agent - Predicts price impulses using LSTM.
Trained to identify strong directional moves in the next N seconds.
"""

import numpy as np
import torch
import torch.nn as nn
import pickle
from typing import Dict, Any, List, Tuple
from datetime import datetime
from sklearn.preprocessing import StandardScaler

from .base_agent import BaseAgent, AgentSignal


class LSTMModel(nn.Module):
    """LSTM network for momentum prediction."""
    
    def __init__(
        self,
        input_size: int,
        hidden_size: int = 64,
        num_layers: int = 2,
        dropout: float = 0.2
    ):
        super().__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True
        )
        
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 3)  # 3 classes: down, neutral, up
        )
    
    def forward(self, x):
        # x shape: (batch, sequence, features)
        lstm_out, _ = self.lstm(x)
        
        # Take last output
        last_output = lstm_out[:, -1, :]
        
        # Classification
        output = self.fc(last_output)
        return output


class MomentumAgent(BaseAgent):
    """
    Predicts short-term price momentum using LSTM.
    
    Classes:
    0 - Down: Price will decrease
    1 - Neutral: No significant movement
    2 - Up: Price will increase
    """
    
    def __init__(
        self,
        symbol: str,
        sequence_length: int = 20,
        hidden_size: int = 64,
        device: str = 'cpu'
    ):
        """
        Initialize momentum agent.
        
        Args:
            symbol: Trading symbol
            sequence_length: Number of time steps to look back
            hidden_size: LSTM hidden layer size
            device: 'cpu' or 'cuda'
        """
        super().__init__(name='momentum_agent', symbol=symbol)
        
        self.sequence_length = sequence_length
        self.hidden_size = hidden_size
        self.device = device
        
        # Feature configuration
        self.feature_names = [
            'price',
            'ema_9',
            'ema_21',
            'rsi',
            'order_flow_imbalance',
            'cumulative_delta',
            'vpin',
            'bid_volume',
            'ask_volume'
        ]
        
        self.model = None
        self.scaler = StandardScaler()
        self.feature_buffer = []  # Rolling buffer for sequence
    
    def _extract_features(self, features: Dict[str, Any]) -> np.ndarray:
        """Extract feature vector from features dict."""
        feature_vector = np.array([
            features.get(name, 0.0)
            for name in self.feature_names
        ])
        return feature_vector
    
    def predict(self, features: Dict[str, Any]) -> AgentSignal:
        """
        Predict momentum direction.
        
        Args:
            features: Market features
        
        Returns:
            AgentSignal with momentum prediction
        """
        if not self.is_trained or self.model is None:
            return AgentSignal(
                agent_name=self.name,
                timestamp=datetime.now(),
                symbol=self.symbol,
                direction='neutral',
                confidence=0.0,
                reasoning={'error': 'Model not trained'}
            )
        
        # Extract features
        feature_vector = self._extract_features(features)
        
        # Add to buffer
        self.feature_buffer.append(feature_vector)
        
        # Keep only sequence_length most recent
        if len(self.feature_buffer) > self.sequence_length:
            self.feature_buffer = self.feature_buffer[-self.sequence_length:]
        
        # Need full sequence
        if len(self.feature_buffer) < self.sequence_length:
            return AgentSignal(
                agent_name=self.name,
                timestamp=datetime.now(),
                symbol=self.symbol,
                direction='neutral',
                confidence=0.0,
                reasoning={'error': 'Warming up', 'buffer_size': len(self.feature_buffer)}
            )
        
        # Prepare input
        sequence = np.array(self.feature_buffer)
        sequence_scaled = self.scaler.transform(sequence)
        
        # Convert to tensor
        x = torch.FloatTensor(sequence_scaled).unsqueeze(0).to(self.device)
        
        # Predict
        self.model.eval()
        with torch.no_grad():
            logits = self.model(x)
            probs = torch.softmax(logits, dim=1)
            pred_class = torch.argmax(probs, dim=1).item()
            confidence = probs[0, pred_class].item()
        
        # Map class to direction
        direction_map = {0: 'short', 1: 'neutral', 2: 'long'}
        direction = direction_map[pred_class]
        
        self._update_stats()
        
        return AgentSignal(
            agent_name=self.name,
            timestamp=datetime.now(),
            symbol=self.symbol,
            direction=direction,
            confidence=float(confidence),
            reasoning={
                'predicted_class': int(pred_class),
                'class_probabilities': {
                    'down': float(probs[0, 0]),
                    'neutral': float(probs[0, 1]),
                    'up': float(probs[0, 2])
                }
            },
            features_used={
                name: float(val)
                for name, val in zip(self.feature_names, feature_vector)
            }
        )
    
    def train(
        self,
        training_data: List[Tuple[List[Dict[str, Any]], int]],
        epochs: int = 50,
        batch_size: int = 32,
        learning_rate: float = 0.001
    ) -> Dict[str, float]:
        """
        Train LSTM on historical sequences.
        
        Args:
            training_data: List of (feature_sequence, label) tuples
                          label: 0=down, 1=neutral, 2=up
            epochs: Number of training epochs
            batch_size: Batch size
            learning_rate: Learning rate
        
        Returns:
            Training metrics
        """
        if len(training_data) < 100:
            raise ValueError("Need at least 100 samples for training")
        
        # Extract all features for scaling
        all_features = []
        for sequence, _ in training_data:
            for sample in sequence:
                all_features.append(self._extract_features(sample))
        
        all_features = np.array(all_features)
        self.scaler.fit(all_features)
        
        # Prepare sequences
        X_list = []
        y_list = []
        
        for sequence, label in training_data:
            feature_matrix = np.array([
                self._extract_features(sample)
                for sample in sequence
            ])
            feature_scaled = self.scaler.transform(feature_matrix)
            X_list.append(feature_scaled)
            y_list.append(label)
        
        X = torch.FloatTensor(np.array(X_list)).to(self.device)
        y = torch.LongTensor(y_list).to(self.device)
        
        # Initialize model
        input_size = len(self.feature_names)
        self.model = LSTMModel(
            input_size=input_size,
            hidden_size=self.hidden_size
        ).to(self.device)
        
        # Training setup
        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
        
        # Training loop
        self.model.train()
        losses = []
        
        for epoch in range(epochs):
            # Shuffle data
            indices = torch.randperm(len(X))
            
            epoch_loss = 0
            n_batches = 0
            
            for i in range(0, len(X), batch_size):
                batch_indices = indices[i:i+batch_size]
                batch_X = X[batch_indices]
                batch_y = y[batch_indices]
                
                # Forward pass
                outputs = self.model(batch_X)
                loss = criterion(outputs, batch_y)
                
                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item()
                n_batches += 1
            
            avg_loss = epoch_loss / n_batches
            losses.append(avg_loss)
            
            if (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")
        
        self.is_trained = True
        
        # Calculate accuracy on training data
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(X)
            predictions = torch.argmax(outputs, dim=1)
            accuracy = (predictions == y).float().mean().item()
        
        metrics = {
            'final_loss': losses[-1],
            'training_accuracy': accuracy,
            'n_samples': len(training_data),
            'epochs': epochs
        }
        
        return metrics
    
    def save(self, path: str) -> None:
        """Save model to disk."""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
        
        model_data = {
            'model_state': self.model.state_dict(),
            'scaler': self.scaler,
            'sequence_length': self.sequence_length,
            'hidden_size': self.hidden_size,
            'feature_names': self.feature_names,
            'is_trained': self.is_trained
        }
        
        with open(path, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load(self, path: str) -> None:
        """Load model from disk."""
        with open(path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.sequence_length = model_data['sequence_length']
        self.hidden_size = model_data['hidden_size']
        self.feature_names = model_data['feature_names']
        self.scaler = model_data['scaler']
        self.is_trained = model_data['is_trained']
        
        # Recreate model
        input_size = len(self.feature_names)
        self.model = LSTMModel(
            input_size=input_size,
            hidden_size=self.hidden_size
        ).to(self.device)
        
        self.model.load_state_dict(model_data['model_state'])
        self.model.eval()
    
    def reset_buffer(self):
        """Reset feature buffer (e.g., when switching symbols)."""
        self.feature_buffer = []
