"""
Data Preprocessor - Prepare data for training.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class DataPreprocessor:
    """
    Preprocess market data for agent training.
    
    Features:
    - Feature engineering
    - Normalization
    - Train/validation/test split
    - Label generation
    """
    
    def __init__(self):
        """Initialize preprocessor."""
        self.feature_stats = {}
    
    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add technical indicators to OHLCV data.
        
        Args:
            df: DataFrame with OHLCV data
        
        Returns:
            DataFrame with added indicators
        """
        df = df.copy()
        
        # Returns
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # Moving averages
        for period in [7, 14, 21, 50, 200]:
            df[f'sma_{period}'] = df['close'].rolling(period).mean()
            df[f'ema_{period}'] = df['close'].ewm(span=period).mean()
        
        # RSI
        for period in [14, 21]:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
            rs = gain / loss
            df[f'rsi_{period}'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema_12 = df['close'].ewm(span=12).mean()
        ema_26 = df['close'].ewm(span=26).mean()
        df['macd'] = ema_12 - ema_26
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # Bollinger Bands
        for period in [20]:
            sma = df['close'].rolling(period).mean()
            std = df['close'].rolling(period).std()
            df[f'bb_upper_{period}'] = sma + (std * 2)
            df[f'bb_lower_{period}'] = sma - (std * 2)
            df[f'bb_width_{period}'] = (df[f'bb_upper_{period}'] - df[f'bb_lower_{period}']) / sma
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['atr_14'] = true_range.rolling(14).mean()
        
        # Volume indicators
        df['volume_sma_20'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma_20']
        
        # Price momentum
        for period in [5, 10, 20]:
            df[f'momentum_{period}'] = df['close'] - df['close'].shift(period)
            df[f'roc_{period}'] = (df['close'] - df['close'].shift(period)) / df['close'].shift(period) * 100
        
        # Volatility
        for period in [10, 20, 30]:
            df[f'volatility_{period}'] = df['returns'].rolling(period).std()
        
        logger.info(f"Added {len(df.columns) - 6} technical indicators")
        
        return df
    
    def generate_labels(
        self,
        df: pd.DataFrame,
        horizon: int = 1,
        threshold: float = 0.001
    ) -> pd.DataFrame:
        """
        Generate labels for supervised learning.
        
        Args:
            df: DataFrame with price data
            horizon: Periods ahead to predict
            threshold: Minimum return to classify as up/down
        
        Returns:
            DataFrame with labels
        """
        df = df.copy()
        
        # Future returns
        df['future_return'] = df['close'].shift(-horizon) / df['close'] - 1
        
        # Classification labels
        df['label'] = 0  # neutral
        df.loc[df['future_return'] > threshold, 'label'] = 1  # up
        df.loc[df['future_return'] < -threshold, 'label'] = -1  # down
        
        # Regression target
        df['target_return'] = df['future_return']
        
        logger.info(f"Generated labels with {horizon} period horizon")
        
        return df
    
    def normalize_features(
        self,
        df: pd.DataFrame,
        method: str = 'zscore',
        fit: bool = True
    ) -> pd.DataFrame:
        """
        Normalize features.
        
        Args:
            df: DataFrame with features
            method: Normalization method ('zscore', 'minmax', 'robust')
            fit: Whether to fit normalization parameters
        
        Returns:
            Normalized DataFrame
        """
        df = df.copy()
        
        # Select numeric columns (exclude timestamp and labels)
        exclude_cols = ['timestamp', 'label', 'target_return', 'future_return']
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        feature_cols = [col for col in numeric_cols if col not in exclude_cols]
        
        if method == 'zscore':
            if fit:
                self.feature_stats['mean'] = df[feature_cols].mean()
                self.feature_stats['std'] = df[feature_cols].std()
            
            df[feature_cols] = (df[feature_cols] - self.feature_stats['mean']) / self.feature_stats['std']
        
        elif method == 'minmax':
            if fit:
                self.feature_stats['min'] = df[feature_cols].min()
                self.feature_stats['max'] = df[feature_cols].max()
            
            df[feature_cols] = (df[feature_cols] - self.feature_stats['min']) / (
                self.feature_stats['max'] - self.feature_stats['min']
            )
        
        elif method == 'robust':
            if fit:
                self.feature_stats['median'] = df[feature_cols].median()
                self.feature_stats['q75'] = df[feature_cols].quantile(0.75)
                self.feature_stats['q25'] = df[feature_cols].quantile(0.25)
            
            iqr = self.feature_stats['q75'] - self.feature_stats['q25']
            df[feature_cols] = (df[feature_cols] - self.feature_stats['median']) / iqr
        
        # Replace inf and nan
        df[feature_cols] = df[feature_cols].replace([np.inf, -np.inf], np.nan)
        df[feature_cols] = df[feature_cols].fillna(0)
        
        logger.info(f"Normalized {len(feature_cols)} features using {method}")
        
        return df
    
    def split_data(
        self,
        df: pd.DataFrame,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Split data into train/validation/test sets.
        
        Args:
            df: DataFrame to split
            train_ratio: Training set ratio
            val_ratio: Validation set ratio
            test_ratio: Test set ratio
        
        Returns:
            Tuple of (train_df, val_df, test_df)
        """
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 0.001, "Ratios must sum to 1"
        
        n = len(df)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))
        
        train_df = df.iloc[:train_end].copy()
        val_df = df.iloc[train_end:val_end].copy()
        test_df = df.iloc[val_end:].copy()
        
        logger.info(f"Split data: train={len(train_df)}, val={len(val_df)}, test={len(test_df)}")
        
        return train_df, val_df, test_df
    
    def prepare_for_training(
        self,
        df: pd.DataFrame,
        horizon: int = 1,
        threshold: float = 0.001,
        normalize: bool = True,
        split: bool = True
    ) -> Dict[str, Any]:
        """
        Complete preprocessing pipeline.
        
        Args:
            df: Raw OHLCV DataFrame
            horizon: Prediction horizon
            threshold: Classification threshold
            normalize: Whether to normalize
            split: Whether to split into train/val/test
        
        Returns:
            Dictionary with processed data
        """
        logger.info("Starting preprocessing pipeline...")
        
        # Add technical indicators
        df = self.add_technical_indicators(df)
        
        # Generate labels
        df = self.generate_labels(df, horizon=horizon, threshold=threshold)
        
        # Drop rows with NaN (from indicators and future returns)
        df = df.dropna()
        
        logger.info(f"After preprocessing: {len(df)} rows")
        
        # Normalize
        if normalize:
            df = self.normalize_features(df, method='zscore', fit=True)
        
        # Split
        if split:
            train_df, val_df, test_df = self.split_data(df)
            
            # Normalize val and test using train stats
            if normalize:
                val_df = self.normalize_features(val_df, method='zscore', fit=False)
                test_df = self.normalize_features(test_df, method='zscore', fit=False)
            
            return {
                'train': train_df,
                'val': val_df,
                'test': test_df,
                'feature_stats': self.feature_stats,
                'n_features': len([col for col in df.columns if col not in ['timestamp', 'label', 'target_return', 'future_return']])
            }
        else:
            return {
                'data': df,
                'feature_stats': self.feature_stats,
                'n_features': len([col for col in df.columns if col not in ['timestamp', 'label', 'target_return', 'future_return']])
            }
