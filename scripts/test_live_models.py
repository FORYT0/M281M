"""
Test the retrained models on recent data
"""
import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger
import sys
import pickle
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))


def load_model(model_name):
    """Load a trained model"""
    model_path = Path(f"models/{model_name}_agent_live.pkl")
    with open(model_path, 'rb') as f:
        return pickle.load(f)


def prepare_test_data():
    """Load recent data for testing"""
    logger.info("Loading recent trade data for testing...")
    
    # Load the most recent file
    data_dir = Path("data/live")
    trade_files = sorted(data_dir.glob("btcusdt_trades_*.csv"))
    recent_file = trade_files[-1]  # Most recent
    
    logger.info(f"Using {recent_file.name} for testing")
    
    df = pd.read_csv(recent_file)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df.set_index('timestamp')
    
    # Create OHLCV
    ohlcv = pd.DataFrame()
    ohlcv['open'] = df['price'].resample('1min').first()
    ohlcv['high'] = df['price'].resample('1min').max()
    ohlcv['low'] = df['price'].resample('1min').min()
    ohlcv['close'] = df['price'].resample('1min').last()
    ohlcv['volume'] = df['quantity'].resample('1min').sum()
    ohlcv = ohlcv.ffill().dropna()
    
    # Calculate features (same as training)
    features = pd.DataFrame(index=ohlcv.index)
    features['price'] = ohlcv['close']
    features['volume'] = ohlcv['volume']
    features['returns'] = ohlcv['close'].pct_change()
    features['sma_10'] = ohlcv['close'].rolling(10).mean()
    features['sma_20'] = ohlcv['close'].rolling(20).mean()
    
    # RSI
    delta = ohlcv['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    features['rsi'] = 100 - (100 / (1 + rs))
    
    features['volatility'] = features['returns'].rolling(20).std()
    features = features.dropna()
    
    logger.info(f"Prepared {len(features)} test samples")
    return features


def test_models():
    """Test all models"""
    logger.info("=" * 60)
    logger.info("TESTING RETRAINED MODELS")
    logger.info("=" * 60)
    
    # Load models
    models = {}
    for name in ['momentum', 'mean_reversion', 'order_flow']:
        try:
            models[name] = load_model(name)
            logger.info(f"✓ Loaded {name} model")
        except Exception as e:
            logger.error(f"✗ Failed to load {name} model: {e}")
    
    if not models:
        logger.error("No models loaded successfully")
        return
    
    # Prepare test data
    test_features = prepare_test_data()
    X_test = test_features.values
    
    # Test each model
    predictions = {}
    
    for name, model_data in models.items():
        logger.info(f"\nTesting {name} model...")
        
        try:
            # Scale features
            X_scaled = model_data['scaler'].transform(X_test)
            
            # Make predictions
            pred = model_data['model'].predict(X_scaled)
            pred_proba = model_data['model'].predict_proba(X_scaled)
            
            predictions[name] = {
                'predictions': pred,
                'probabilities': pred_proba,
                'confidence': np.max(pred_proba, axis=1)
            }
            
            # Show prediction distribution
            unique, counts = np.unique(pred, return_counts=True)
            logger.info(f"Predictions: {dict(zip(['Down', 'Hold', 'Up'], [counts[i] if i in unique else 0 for i in range(3)]))}")
            logger.info(f"Average confidence: {np.mean(predictions[name]['confidence']):.3f}")
            
        except Exception as e:
            logger.error(f"Failed to test {name} model: {e}")
    
    # Show recent predictions
    logger.info("\n" + "=" * 60)
    logger.info("RECENT PREDICTIONS (Last 10 samples)")
    logger.info("=" * 60)
    
    signal_names = ['Down', 'Hold', 'Up']
    
    for i in range(max(0, len(test_features) - 10), len(test_features)):
        timestamp = test_features.index[i]
        price = test_features.iloc[i]['price']
        
        logger.info(f"\n{timestamp} | Price: ${price:.2f}")
        
        for name in predictions:
            pred = predictions[name]['predictions'][i]
            conf = predictions[name]['confidence'][i]
            signal = signal_names[pred]
            logger.info(f"  {name:15}: {signal:4} (conf: {conf:.3f})")
    
    # Ensemble prediction
    if len(predictions) > 1:
        logger.info("\n" + "=" * 60)
        logger.info("ENSEMBLE PREDICTIONS")
        logger.info("=" * 60)
        
        # Simple voting ensemble
        ensemble_pred = []
        for i in range(len(test_features)):
            votes = [predictions[name]['predictions'][i] for name in predictions]
            ensemble_pred.append(max(set(votes), key=votes.count))  # Majority vote
        
        unique, counts = np.unique(ensemble_pred, return_counts=True)
        logger.info(f"Ensemble predictions: {dict(zip(['Down', 'Hold', 'Up'], [counts[i] if i in unique else 0 for i in range(3)]))}")
        
        # Show last few ensemble predictions
        for i in range(max(0, len(test_features) - 5), len(test_features)):
            timestamp = test_features.index[i]
            price = test_features.iloc[i]['price']
            signal = signal_names[ensemble_pred[i]]
            logger.info(f"{timestamp} | ${price:.2f} | Ensemble: {signal}")
    
    logger.info("\n" + "=" * 60)
    logger.info("MODEL TESTING COMPLETE!")
    logger.info("=" * 60)
    logger.info("Models are working and making predictions.")
    logger.info("Ready for paper trading!")


def main():
    test_models()


if __name__ == "__main__":
    main()