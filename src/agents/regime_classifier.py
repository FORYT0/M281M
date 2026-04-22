"""
Regime Classifier Agent - Identifies market state.
Uses Hidden Markov Model to classify market into regimes:
- Trending (strong directional movement)
- Range-bound (sideways, mean-reverting)
- Volatile (high uncertainty, choppy)
"""

import numpy as np
import pickle
from typing import Dict, Any, List, Tuple
from datetime import datetime
from sklearn.preprocessing import StandardScaler
from hmmlearn import hmm

from .base_agent import BaseAgent, AgentSignal


class RegimeClassifier(BaseAgent):
    """
    Classifies market regime using Hidden Markov Model.
    
    Regimes:
    0 - Trending: Strong directional movement, high momentum
    1 - Range-bound: Sideways movement, mean-reverting
    2 - Volatile: High volatility, uncertain direction
    """
    
    REGIME_NAMES = {
        0: 'trending',
        1: 'range_bound',
        2: 'volatile'
    }
    
    def __init__(self, symbol: str, n_regimes: int = 3):
        """
        Initialize regime classifier.
        
        Args:
            symbol: Trading symbol
            n_regimes: Number of market regimes (default 3)
        """
        super().__init__(name='regime_classifier', symbol=symbol)
        
        self.n_regimes = n_regimes
        self.model = None
        self.scaler = StandardScaler()
        
        # Feature configuration
        self.feature_names = [
            'price_change',
            'volatility',
            'volume_change',
            'rsi',
            'order_flow_imbalance',
            'vpin'
        ]
    
    def _extract_features(self, features: Dict[str, Any]) -> np.ndarray:
        """
        Extract and normalize features for regime classification.
        
        Args:
            features: Raw feature dictionary
        
        Returns:
            Normalized feature vector
        """
        # Calculate derived features
        price = features.get('price', 0)
        
        # Price change (use EMA as baseline)
        ema_21 = features.get('ema_21', price)
        price_change = (price - ema_21) / ema_21 if ema_21 > 0 else 0
        
        # Volatility proxy (distance between EMAs)
        ema_9 = features.get('ema_9', price)
        volatility = abs(ema_9 - ema_21) / ema_21 if ema_21 > 0 else 0
        
        # Volume change (use bid/ask volume as proxy)
        bid_vol = features.get('bid_volume', 1)
        ask_vol = features.get('ask_volume', 1)
        volume_change = (bid_vol + ask_vol) / 2
        
        # Technical indicators
        rsi = features.get('rsi', 50) / 100  # Normalize to 0-1
        ofi = features.get('order_flow_imbalance', 0)
        vpin = features.get('vpin', 0)
        
        feature_vector = np.array([
            price_change,
            volatility,
            volume_change,
            rsi,
            ofi,
            vpin
        ])
        
        return feature_vector
    
    def predict(self, features: Dict[str, Any]) -> AgentSignal:
        """
        Predict current market regime.
        
        Args:
            features: Market features
        
        Returns:
            AgentSignal with regime classification
        """
        if not self.is_trained or self.model is None:
            # Return neutral if not trained
            return AgentSignal(
                agent_name=self.name,
                timestamp=datetime.now(),
                symbol=self.symbol,
                direction='neutral',
                confidence=0.0,
                reasoning={'error': 'Model not trained'}
            )
        
        # Extract and scale features
        feature_vector = self._extract_features(features)
        feature_scaled = self.scaler.transform(feature_vector.reshape(1, -1))
        
        # Predict regime
        regime = self.model.predict(feature_scaled)[0]
        regime_probs = self.model.predict_proba(feature_scaled)[0]
        
        regime_name = self.REGIME_NAMES.get(regime, 'unknown')
        confidence = float(regime_probs[regime])
        
        # Map regime to trading direction
        # Trending -> follow trend
        # Range-bound -> mean reversion
        # Volatile -> reduce exposure
        if regime == 0:  # Trending
            # Use price momentum to determine direction
            price_change = feature_vector[0]
            direction = 'long' if price_change > 0 else 'short'
        elif regime == 1:  # Range-bound
            # Mean reversion: fade extremes
            rsi = features.get('rsi', 50)
            if rsi > 70:
                direction = 'short'  # Overbought
            elif rsi < 30:
                direction = 'long'  # Oversold
            else:
                direction = 'neutral'
        else:  # Volatile
            direction = 'neutral'  # Stay out
        
        self._update_stats()
        
        return AgentSignal(
            agent_name=self.name,
            timestamp=datetime.now(),
            symbol=self.symbol,
            direction=direction,
            confidence=confidence,
            reasoning={
                'regime': regime_name,
                'regime_id': int(regime),
                'regime_probabilities': {
                    'trending': float(regime_probs[0]),
                    'range_bound': float(regime_probs[1]),
                    'volatile': float(regime_probs[2])
                }
            },
            features_used={
                name: float(val)
                for name, val in zip(self.feature_names, feature_vector)
            }
        )
    
    def train(
        self,
        training_data: List[Dict[str, Any]],
        n_iter: int = 100
    ) -> Dict[str, float]:
        """
        Train HMM on historical feature data.
        
        Args:
            training_data: List of feature dictionaries
            n_iter: Number of EM iterations
        
        Returns:
            Training metrics
        """
        if len(training_data) < 100:
            raise ValueError("Need at least 100 samples for training")
        
        # Extract features from all samples
        feature_matrix = np.array([
            self._extract_features(sample)
            for sample in training_data
        ])
        
        # Fit scaler
        self.scaler.fit(feature_matrix)
        feature_scaled = self.scaler.transform(feature_matrix)
        
        # Train Gaussian HMM
        self.model = hmm.GaussianHMM(
            n_components=self.n_regimes,
            covariance_type='full',
            n_iter=n_iter,
            random_state=42
        )
        
        self.model.fit(feature_scaled)
        self.is_trained = True
        
        # Calculate training metrics
        log_likelihood = self.model.score(feature_scaled)
        
        # Predict regimes for training data
        regimes = self.model.predict(feature_scaled)
        regime_counts = np.bincount(regimes, minlength=self.n_regimes)
        
        metrics = {
            'log_likelihood': float(log_likelihood),
            'n_samples': len(training_data),
            'regime_distribution': {
                self.REGIME_NAMES[i]: int(count)
                for i, count in enumerate(regime_counts)
            }
        }
        
        return metrics
    
    def save(self, path: str) -> None:
        """Save model to disk."""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'n_regimes': self.n_regimes,
            'feature_names': self.feature_names,
            'is_trained': self.is_trained
        }
        
        with open(path, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load(self, path: str) -> None:
        """Load model from disk."""
        with open(path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.n_regimes = model_data['n_regimes']
        self.feature_names = model_data['feature_names']
        self.is_trained = model_data['is_trained']
    
    def get_regime_transitions(
        self,
        feature_sequence: List[Dict[str, Any]]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get regime sequence and transition probabilities.
        
        Args:
            feature_sequence: Sequence of feature dictionaries
        
        Returns:
            Tuple of (regime_sequence, transition_matrix)
        """
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        # Extract and scale features
        feature_matrix = np.array([
            self._extract_features(sample)
            for sample in feature_sequence
        ])
        feature_scaled = self.scaler.transform(feature_matrix)
        
        # Predict regime sequence
        regimes = self.model.predict(feature_scaled)
        
        # Get transition matrix
        transition_matrix = self.model.transmat_
        
        return regimes, transition_matrix
