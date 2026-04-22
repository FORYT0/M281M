"""
Simple retraining script that works with existing agent interfaces
"""
import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger
import sys
from datetime import datetime
import pickle

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))


def load_and_prepare_data():
    """Load trade data and create simple features"""
    logger.info("Loading live data files...")
    
    data_dir = Path("data/live")
    trade_files = sorted(data_dir.glob("btcusdt_trades_*.csv"))
    logger.info(f"Found {len(trade_files)} trade files")
    
    trades_list = []
    for file in trade_files:
        df = pd.read_csv(file)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        trades_list.append(df)
    
    trades = pd.concat(trades_list, ignore_index=True)
    trades = trades.sort_values('timestamp').reset_index(drop=True)
    
    logger.info(f"Loaded {len(trades):,} trades")
    logger.info(f"Date range: {trades['timestamp'].min()} to {trades['timestamp'].max()}")
    
    # Create 1-minute OHLCV bars
    trades = trades.set_index('timestamp')
    
    ohlcv = pd.DataFrame()
    ohlcv['open'] = trades['price'].resample('1min').first()
    ohlcv['high'] = trades['price'].resample('1min').max()
    ohlcv['low'] = trades['price'].resample('1min').min()
    ohlcv['close'] = trades['price'].resample('1min').last()
    ohlcv['volume'] = trades['quantity'].resample('1min').sum()
    
    # Forward fill and drop NaN
    ohlcv = ohlcv.ffill().dropna()
    
    logger.info(f"Created {len(ohlcv):,} 1-minute bars")
    
    # Calculate simple features
    features = pd.DataFrame(index=ohlcv.index)
    features['price'] = ohlcv['close']
    features['volume'] = ohlcv['volume']
    features['returns'] = ohlcv['close'].pct_change()
    features['sma_10'] = ohlcv['close'].rolling(10).mean()
    features['sma_20'] = ohlcv['close'].rolling(20).mean()
    features['rsi'] = calculate_rsi(ohlcv['close'], 14)
    features['volatility'] = features['returns'].rolling(20).std()
    
    # Drop NaN rows
    features = features.dropna()
    
    logger.info(f"Calculated {len(features):,} feature vectors")
    
    return features


def calculate_rsi(prices, period=14):
    """Calculate RSI"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def create_labels(features, lookahead=10):
    """Create trading labels"""
    returns = features['price'].pct_change(lookahead).shift(-lookahead)
    
    labels = pd.Series(1, index=returns.index)  # Default: hold
    labels[returns > 0.002] = 2   # Up (buy)
    labels[returns < -0.002] = 0  # Down (sell)
    
    # Remove last lookahead bars
    labels = labels[:-lookahead]
    
    logger.info(f"Label distribution:")
    logger.info(f"  Down: {(labels == 0).sum()} ({(labels == 0).sum() / len(labels) * 100:.1f}%)")
    logger.info(f"  Hold: {(labels == 1).sum()} ({(labels == 1).sum() / len(labels) * 100:.1f}%)")
    logger.info(f"  Up: {(labels == 2).sum()} ({(labels == 2).sum() / len(labels) * 100:.1f}%)")
    
    return labels


def create_simple_models():
    """Create simple trained models using scikit-learn"""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report
    
    # Load data
    features = load_and_prepare_data()
    labels = create_labels(features)
    
    # Align features with labels
    features = features.loc[labels.index]
    
    # Prepare data
    X = features.values
    y = labels.values
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    logger.info(f"Training samples: {len(X_train):,}")
    logger.info(f"Test samples: {len(X_test):,}")
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Create models directory
    Path("models").mkdir(exist_ok=True)
    
    # Train models
    models = {}
    
    # Momentum model (Random Forest)
    logger.info("Training momentum model...")
    momentum_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    momentum_model.fit(X_train_scaled, y_train)
    
    # Evaluate
    train_score = momentum_model.score(X_train_scaled, y_train)
    test_score = momentum_model.score(X_test_scaled, y_test)
    logger.info(f"Momentum model - Train: {train_score:.3f}, Test: {test_score:.3f}")
    
    models['momentum'] = {
        'model': momentum_model,
        'scaler': scaler,
        'feature_names': features.columns.tolist(),
        'train_score': train_score,
        'test_score': test_score
    }
    
    # Mean reversion model (same for now)
    logger.info("Training mean reversion model...")
    mr_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        random_state=43,
        n_jobs=-1
    )
    mr_model.fit(X_train_scaled, y_train)
    
    train_score = mr_model.score(X_train_scaled, y_train)
    test_score = mr_model.score(X_test_scaled, y_test)
    logger.info(f"Mean reversion model - Train: {train_score:.3f}, Test: {test_score:.3f}")
    
    models['mean_reversion'] = {
        'model': mr_model,
        'scaler': scaler,
        'feature_names': features.columns.tolist(),
        'train_score': train_score,
        'test_score': test_score
    }
    
    # Order flow model
    logger.info("Training order flow model...")
    of_model = RandomForestClassifier(
        n_estimators=150,
        max_depth=12,
        random_state=44,
        n_jobs=-1
    )
    of_model.fit(X_train_scaled, y_train)
    
    train_score = of_model.score(X_train_scaled, y_train)
    test_score = of_model.score(X_test_scaled, y_test)
    logger.info(f"Order flow model - Train: {train_score:.3f}, Test: {test_score:.3f}")
    
    models['order_flow'] = {
        'model': of_model,
        'scaler': scaler,
        'feature_names': features.columns.tolist(),
        'train_score': train_score,
        'test_score': test_score
    }
    
    # Save models
    for name, model_data in models.items():
        model_path = Path(f"models/{name}_agent_live.pkl")
        with open(model_path, 'wb') as f:
            pickle.dump(model_data, f)
        logger.info(f"Saved {name} model to {model_path}")
    
    # Print classification report
    y_pred = momentum_model.predict(X_test_scaled)
    logger.info("Classification Report:")
    logger.info(f"\n{classification_report(y_test, y_pred, target_names=['Down', 'Hold', 'Up'])}")
    
    return models


def main():
    logger.info("=" * 60)
    logger.info("SIMPLE AGENT RETRAINING")
    logger.info("=" * 60)
    logger.info(f"Started at: {datetime.now()}")
    
    try:
        models = create_simple_models()
        
        logger.info("=" * 60)
        logger.info("TRAINING COMPLETE!")
        logger.info("=" * 60)
        logger.info(f"Finished at: {datetime.now()}")
        logger.info("\nModels saved:")
        for name in models.keys():
            logger.info(f"  - models/{name}_agent_live.pkl")
        
        logger.info("\nModel Performance:")
        for name, model_data in models.items():
            logger.info(f"  {name}: Train={model_data['train_score']:.3f}, Test={model_data['test_score']:.3f}")
        
        logger.info("\nNext steps:")
        logger.info("  1. Test models: python scripts/test_live_models.py")
        logger.info("  2. Start paper trading: python scripts/run_paper_trading.py")
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise


if __name__ == "__main__":
    main()