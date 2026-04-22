"""
Mean Reversion Agent - Predicts short-term reversals using XGBoost.
Identifies overbought/oversold conditions and mean reversion opportunities.
"""

import numpy as np
import pickle
from typing import Dict, Any, List
from datetime import datetime
import xgboost as xgb
from sklearn.preprocessing import StandardScaler

from .base_agent import BaseAgent, AgentSignal


class MeanReversionAgent(BaseAgent):
    """
    Predicts mean reversion opportunities using XGBoost.
    
    Classes:
    0 - No reversion expected
    1 - Reversion up (currently oversold)
    2 - Reversion down (currently overbought)
    """
    
    def __init__(self, symbol: str):
        """
        Initialize mean reversion agent.
        
        Args:
            symbol: Trading symbol
        """
        super().__init__(name='mean_reversion_agent', symbol=symbol)
        
        # Feature configuration
        self.feature_names = [
            'price_to_vwap',
            'price_to_ema9',
            'price_to_ema21',
            'rsi',
            'rsi_divergence',
            'order_flow_imbalance',
            'vpin',
            'liquidity_imbalance',
            'ema_spread'
        ]
        
        self.model = None
        self.scaler = StandardScaler()
    
    def _extract_features(self, features: Dict[str, Any]) -> np.ndarray:
        """
        Extract mean reversion features.
        
        Args:
            features: Raw feature dictionary
        
        Returns:
            Feature vector for mean reversion
        """
        price = features.get('price', 0)
        vwap = features.get('vwap', price)
        ema_9 = features.get('ema_9', price)
        ema_21 = features.get('ema_21', price)
        rsi = features.get('rsi', 50)
        
        # Distance from VWAP (key mean reversion indicator)
        price_to_vwap = (price - vwap) / vwap if vwap > 0 else 0
        
        # Distance from EMAs
        price_to_ema9 = (price - ema_9) / ema_9 if ema_9 > 0 else 0
        price_to_ema21 = (price - ema_21) / ema_21 if ema_21 > 0 else 0
        
        # RSI and divergence from neutral
        rsi_normalized = rsi / 100
        rsi_divergence = abs(rsi - 50) / 50  # How far from neutral
        
        # Order flow and liquidity
        ofi = features.get('order_flow_imbalance', 0)
        vpin = features.get('vpin', 0)
        
        # Liquidity imbalance from heatmap
        heatmap = features.get('liquidity_heatmap', {})
        liquidity_imbalance = heatmap.get('liquidity_imbalance', 0)
        
        # EMA spread (volatility proxy)
        ema_spread = abs(ema_9 - ema_21) / ema_21 if ema_21 > 0 else 0
        
        feature_vector = np.array([
            price_to_vwap,
            price_to_ema9,
            price_to_ema21,
            rsi_normalized,
            rsi_divergence,
            ofi,
            vpin,
            liquidity_imbalance,
            ema_spread
        ])
        
        return feature_vector
    
    def predict(self, features: Dict[str, Any]) -> AgentSignal:
        """
        Predict mean reversion opportunity.
        
        Args:
            features: Market features
        
        Returns:
            AgentSignal with reversion prediction
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
        
        # Extract and scale features
        feature_vector = self._extract_features(features)
        feature_scaled = self.scaler.transform(feature_vector.reshape(1, -1))
        
        # Predict
        dmatrix = xgb.DMatrix(feature_scaled)
        probs = self.model.predict(dmatrix)[0]
        pred_class = int(np.argmax(probs))
        confidence = float(probs[pred_class])
        
        # Map class to direction
        # 0: No reversion -> neutral
        # 1: Reversion up (oversold) -> long
        # 2: Reversion down (overbought) -> short
        direction_map = {0: 'neutral', 1: 'long', 2: 'short'}
        direction = direction_map[pred_class]
        
        # Additional context
        rsi = features.get('rsi', 50)
        price_to_vwap = feature_vector[0]
        
        reasoning = {
            'predicted_class': pred_class,
            'class_probabilities': {
                'no_reversion': float(probs[0]),
                'reversion_up': float(probs[1]),
                'reversion_down': float(probs[2])
            },
            'rsi': float(rsi),
            'price_to_vwap_pct': float(price_to_vwap * 100),
            'signal_type': 'mean_reversion'
        }
        
        # Add warnings for extreme conditions
        if rsi > 80:
            reasoning['warning'] = 'Extremely overbought'
        elif rsi < 20:
            reasoning['warning'] = 'Extremely oversold'
        
        if abs(price_to_vwap) > 0.02:  # >2% from VWAP
            reasoning['vwap_deviation'] = 'Significant'
        
        self._update_stats()
        
        return AgentSignal(
            agent_name=self.name,
            timestamp=datetime.now(),
            symbol=self.symbol,
            direction=direction,
            confidence=confidence,
            reasoning=reasoning,
            features_used={
                name: float(val)
                for name, val in zip(self.feature_names, feature_vector)
            }
        )
    
    def train(
        self,
        training_data: List[Tuple[Dict[str, Any], int]],
        n_estimators: int = 100,
        max_depth: int = 6,
        learning_rate: float = 0.1
    ) -> Dict[str, float]:
        """
        Train XGBoost classifier.
        
        Args:
            training_data: List of (features, label) tuples
                          label: 0=no reversion, 1=reversion up, 2=reversion down
            n_estimators: Number of boosting rounds
            max_depth: Maximum tree depth
            learning_rate: Learning rate
        
        Returns:
            Training metrics
        """
        if len(training_data) < 100:
            raise ValueError("Need at least 100 samples for training")
        
        # Extract features and labels
        X_list = []
        y_list = []
        
        for sample, label in training_data:
            feature_vector = self._extract_features(sample)
            X_list.append(feature_vector)
            y_list.append(label)
        
        X = np.array(X_list)
        y = np.array(y_list)
        
        # Fit scaler
        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)
        
        # Prepare DMatrix
        dtrain = xgb.DMatrix(X_scaled, label=y)
        
        # XGBoost parameters
        params = {
            'objective': 'multi:softprob',
            'num_class': 3,
            'max_depth': max_depth,
            'learning_rate': learning_rate,
            'eval_metric': 'mlogloss',
            'seed': 42
        }
        
        # Train model
        self.model = xgb.train(
            params,
            dtrain,
            num_boost_round=n_estimators,
            verbose_eval=False
        )
        
        self.is_trained = True
        
        # Calculate training accuracy
        train_preds = self.model.predict(dtrain)
        train_pred_classes = np.argmax(train_preds, axis=1)
        accuracy = np.mean(train_pred_classes == y)
        
        # Class distribution
        class_counts = np.bincount(y, minlength=3)
        
        metrics = {
            'training_accuracy': float(accuracy),
            'n_samples': len(training_data),
            'class_distribution': {
                'no_reversion': int(class_counts[0]),
                'reversion_up': int(class_counts[1]),
                'reversion_down': int(class_counts[2])
            },
            'n_estimators': n_estimators
        }
        
        return metrics
    
    def save(self, path: str) -> None:
        """Save model to disk."""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
        
        # Save XGBoost model separately
        model_path = path.replace('.pkl', '_xgb.json')
        self.model.save_model(model_path)
        
        # Save other components
        model_data = {
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'is_trained': self.is_trained,
            'model_path': model_path
        }
        
        with open(path, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load(self, path: str) -> None:
        """Load model from disk."""
        with open(path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.scaler = model_data['scaler']
        self.feature_names = model_data['feature_names']
        self.is_trained = model_data['is_trained']
        
        # Load XGBoost model
        model_path = model_data['model_path']
        self.model = xgb.Booster()
        self.model.load_model(model_path)
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance scores.
        
        Returns:
            Dictionary mapping feature names to importance scores
        """
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        importance = self.model.get_score(importance_type='gain')
        
        # Map feature indices to names
        importance_named = {}
        for key, value in importance.items():
            # key format: 'f0', 'f1', etc.
            idx = int(key[1:])
            if idx < len(self.feature_names):
                importance_named[self.feature_names[idx]] = value
        
        return importance_named
