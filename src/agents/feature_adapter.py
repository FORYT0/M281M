"""
Feature Adapter - Adapts pipeline features to agent input format.
Handles feature extraction, normalization, and formatting for agents.
"""

import numpy as np
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class AgentFeatures:
    """Standardized features for agent consumption."""
    
    # Price features
    price: float
    returns: np.ndarray  # Recent returns
    volatility: float
    
    # Technical indicators
    ema_fast: float
    ema_slow: float
    rsi: float
    
    # Order flow features
    ofi: float  # Order Flow Imbalance
    cumulative_delta: float
    vpin: float
    
    # Volume features
    volume: float
    vwap: float
    
    # Liquidity features
    bid_ask_spread: float
    depth_imbalance: float
    
    # Metadata
    timestamp: Any
    symbol: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'price': self.price,
            'returns': self.returns.tolist() if isinstance(self.returns, np.ndarray) else self.returns,
            'volatility': self.volatility,
            'ema_fast': self.ema_fast,
            'ema_slow': self.ema_slow,
            'rsi': self.rsi,
            'ofi': self.ofi,
            'cumulative_delta': self.cumulative_delta,
            'vpin': self.vpin,
            'volume': self.volume,
            'vwap': self.vwap,
            'bid_ask_spread': self.bid_ask_spread,
            'depth_imbalance': self.depth_imbalance,
            'timestamp': str(self.timestamp),
            'symbol': self.symbol
        }


class FeatureAdapter:
    """
    Adapts pipeline features to agent input format.
    
    Handles:
    - Feature extraction from pipeline output
    - Normalization and scaling
    - Sequence creation for LSTM agents
    - Missing value handling
    """
    
    def __init__(
        self,
        lookback_window: int = 20,
        normalize: bool = True
    ):
        """
        Initialize feature adapter.
        
        Args:
            lookback_window: Number of historical observations to keep
            normalize: Whether to normalize features
        """
        self.lookback_window = lookback_window
        self.normalize = normalize
        
        # Feature history for sequence creation
        self.price_history: List[float] = []
        self.feature_history: List[Dict[str, float]] = []
        
        # Normalization statistics (running mean/std)
        self.feature_stats: Dict[str, Dict[str, float]] = {}
    
    def extract_features(
        self,
        pipeline_features: Dict[str, Any],
        symbol: str
    ) -> AgentFeatures:
        """
        Extract and format features from pipeline output.
        
        Args:
            pipeline_features: Features from FeatureCalculator
            symbol: Trading symbol
        
        Returns:
            AgentFeatures object
        """
        # Extract price
        price = pipeline_features.get('price', 0.0)
        self.price_history.append(price)
        
        # Keep only recent history
        if len(self.price_history) > self.lookback_window:
            self.price_history.pop(0)
        
        # Calculate returns
        if len(self.price_history) >= 2:
            returns = np.diff(self.price_history) / self.price_history[:-1]
            returns = np.array(returns[-self.lookback_window:])
        else:
            returns = np.array([0.0])
        
        # Calculate volatility
        volatility = np.std(returns) if len(returns) > 1 else 0.0
        
        # Extract technical indicators
        ema_fast = pipeline_features.get('ema_9', price)
        ema_slow = pipeline_features.get('ema_21', price)
        rsi = pipeline_features.get('rsi_14', 50.0)
        
        # Extract order flow features
        ofi = pipeline_features.get('ofi', 0.0)
        cumulative_delta = pipeline_features.get('cumulative_delta', 0.0)
        vpin = pipeline_features.get('vpin', 0.5)
        
        # Extract volume features
        volume = pipeline_features.get('volume', 0.0)
        vwap = pipeline_features.get('vwap', price)
        
        # Extract liquidity features
        bid_ask_spread = pipeline_features.get('bid_ask_spread', 0.0)
        depth_imbalance = pipeline_features.get('depth_imbalance', 0.0)
        
        # Create AgentFeatures object
        features = AgentFeatures(
            price=price,
            returns=returns,
            volatility=volatility,
            ema_fast=ema_fast,
            ema_slow=ema_slow,
            rsi=rsi,
            ofi=ofi,
            cumulative_delta=cumulative_delta,
            vpin=vpin,
            volume=volume,
            vwap=vwap,
            bid_ask_spread=bid_ask_spread,
            depth_imbalance=depth_imbalance,
            timestamp=pipeline_features.get('timestamp'),
            symbol=symbol
        )
        
        # Store in history
        self.feature_history.append(features.to_dict())
        if len(self.feature_history) > self.lookback_window:
            self.feature_history.pop(0)
        
        # Normalize if enabled
        if self.normalize:
            features = self._normalize_features(features)
        
        return features
    
    def _normalize_features(self, features: AgentFeatures) -> AgentFeatures:
        """
        Normalize features using running statistics.
        
        Args:
            features: Raw features
        
        Returns:
            Normalized features
        """
        # Update running statistics
        self._update_stats('volatility', features.volatility)
        self._update_stats('ofi', features.ofi)
        self._update_stats('vpin', features.vpin)
        self._update_stats('volume', features.volume)
        
        # Normalize features (z-score)
        features.volatility = self._z_score('volatility', features.volatility)
        features.ofi = self._z_score('ofi', features.ofi)
        features.vpin = self._z_score('vpin', features.vpin)
        features.volume = self._z_score('volume', features.volume)
        
        return features
    
    def _update_stats(self, feature_name: str, value: float):
        """Update running mean and std for a feature."""
        if feature_name not in self.feature_stats:
            self.feature_stats[feature_name] = {
                'mean': value,
                'std': 0.0,
                'count': 1
            }
        else:
            stats = self.feature_stats[feature_name]
            count = stats['count'] + 1
            delta = value - stats['mean']
            stats['mean'] += delta / count
            stats['std'] = np.sqrt((stats['std']**2 * (count - 1) + delta**2) / count)
            stats['count'] = count
    
    def _z_score(self, feature_name: str, value: float) -> float:
        """Calculate z-score for a feature."""
        if feature_name not in self.feature_stats:
            return 0.0
        
        stats = self.feature_stats[feature_name]
        if stats['std'] == 0:
            return 0.0
        
        return (value - stats['mean']) / stats['std']
    
    def get_sequence_features(self, n_steps: int = 10) -> np.ndarray:
        """
        Get sequence of features for LSTM agents.
        
        Args:
            n_steps: Number of time steps
        
        Returns:
            Array of shape (n_steps, n_features)
        """
        if len(self.feature_history) < n_steps:
            # Pad with zeros if not enough history
            n_pad = n_steps - len(self.feature_history)
            padded = [self.feature_history[0]] * n_pad + self.feature_history
        else:
            padded = self.feature_history[-n_steps:]
        
        # Convert to array
        sequences = []
        for features in padded:
            seq = [
                features['price'],
                features['volatility'],
                features['ema_fast'],
                features['ema_slow'],
                features['rsi'],
                features['ofi'],
                features['cumulative_delta'],
                features['vpin'],
                features['volume'],
                features['vwap']
            ]
            sequences.append(seq)
        
        return np.array(sequences)
    
    def get_tabular_features(self) -> np.ndarray:
        """
        Get current features as flat array for XGBoost/classical ML.
        
        Returns:
            Feature array
        """
        if not self.feature_history:
            return np.zeros(10)
        
        latest = self.feature_history[-1]
        
        return np.array([
            latest['price'],
            latest['volatility'],
            latest['ema_fast'],
            latest['ema_slow'],
            latest['rsi'],
            latest['ofi'],
            latest['cumulative_delta'],
            latest['vpin'],
            latest['volume'],
            latest['vwap']
        ])
    
    def reset(self):
        """Reset adapter state."""
        self.price_history.clear()
        self.feature_history.clear()
        self.feature_stats.clear()
