"""
Retrain agents on collected live market data
"""
import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger
import sys
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.agents.momentum_agent import MomentumAgent
from src.agents.mean_reversion_agent import MeanReversionAgent
from src.agents.order_flow_agent import OrderFlowAgent
# Skip regime classifier for now (needs hmmlearn)
# from src.agents.regime_classifier import RegimeClassifier
from src.pipeline.features import FeatureCalculator


def load_and_merge_live_data():
    """Load and merge all live data files"""
    logger.info("Loading live data files...")
    
    data_dir = Path("data/live")
    
    # Load all trade files
    trade_files = sorted(data_dir.glob("btcusdt_trades_*.csv"))
    logger.info(f"Found {len(trade_files)} trade files")
    
    trades_list = []
    for file in trade_files:
        df = pd.read_csv(file)
        # Convert timestamp properly - it's already in milliseconds
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        trades_list.append(df)
    
    trades = pd.concat(trades_list, ignore_index=True)
    trades = trades.sort_values('timestamp').reset_index(drop=True)
    
    logger.info(f"Loaded {len(trades):,} trades")
    logger.info(f"Date range: {trades['timestamp'].min()} to {trades['timestamp'].max()}")
    
    return trades


def prepare_training_data(trades, window='1min'):
    """Convert trades to OHLCV bars and calculate features"""
    logger.info(f"Preparing {window} bars...")
    
    # Resample to OHLCV
    trades = trades.set_index('timestamp')
    
    ohlcv = pd.DataFrame()
    ohlcv['open'] = trades['price'].resample(window).first()
    ohlcv['high'] = trades['price'].resample(window).max()
    ohlcv['low'] = trades['price'].resample(window).min()
    ohlcv['close'] = trades['price'].resample(window).last()
    ohlcv['volume'] = trades['quantity'].resample(window).sum()
    
    # Forward fill missing values
    ohlcv = ohlcv.ffill().dropna()
    
    logger.info(f"Created {len(ohlcv):,} bars")
    
    # Calculate simple technical features
    logger.info("Calculating features...")
    
    features = pd.DataFrame(index=ohlcv.index)
    
    # Price features
    features['price'] = ohlcv['close']
    features['returns'] = ohlcv['close'].pct_change()
    features['log_returns'] = np.log(ohlcv['close'] / ohlcv['close'].shift(1))
    
    # Moving averages
    features['sma_5'] = ohlcv['close'].rolling(5).mean()
    features['sma_10'] = ohlcv['close'].rolling(10).mean()
    features['sma_20'] = ohlcv['close'].rolling(20).mean()
    features['ema_9'] = ohlcv['close'].ewm(span=9).mean()
    features['ema_21'] = ohlcv['close'].ewm(span=21).mean()
    
    # RSI
    delta = ohlcv['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    features['rsi'] = 100 - (100 / (1 + rs))
    
    # Volume features
    features['volume'] = ohlcv['volume']
    features['volume_sma'] = ohlcv['volume'].rolling(20).mean()
    features['volume_ratio'] = ohlcv['volume'] / features['volume_sma']
    
    # Price range features
    features['high_low_ratio'] = ohlcv['high'] / ohlcv['low']
    features['close_open_ratio'] = ohlcv['close'] / ohlcv['open']
    
    # Volatility
    features['volatility'] = features['returns'].rolling(20).std()
    
    # Bollinger Bands
    bb_sma = ohlcv['close'].rolling(20).mean()
    bb_std = ohlcv['close'].rolling(20).std()
    features['bb_upper'] = bb_sma + (bb_std * 2)
    features['bb_lower'] = bb_sma - (bb_std * 2)
    features['bb_position'] = (ohlcv['close'] - features['bb_lower']) / (features['bb_upper'] - features['bb_lower'])
    
    # MACD
    ema_12 = ohlcv['close'].ewm(span=12).mean()
    ema_26 = ohlcv['close'].ewm(span=26).mean()
    features['macd'] = ema_12 - ema_26
    features['macd_signal'] = features['macd'].ewm(span=9).mean()
    features['macd_histogram'] = features['macd'] - features['macd_signal']
    
    # Drop rows with NaN values
    features = features.dropna()
    
    logger.info(f"Calculated {len(features):,} feature vectors with {features.shape[1]} features")
    
    return ohlcv.loc[features.index], features


def create_labels(ohlcv, lookahead=10):
    """Create training labels based on future returns"""
    logger.info(f"Creating labels with {lookahead} bar lookahead...")
    
    returns = ohlcv['close'].pct_change(lookahead).shift(-lookahead)
    
    # Classification labels: -1 (short), 0 (hold), 1 (long)
    labels = pd.Series(0, index=returns.index)
    labels[returns > 0.002] = 1   # Long if >0.2% gain
    labels[returns < -0.002] = -1  # Short if >0.2% loss
    
    # Remove last lookahead bars (no future data)
    labels = labels[:-lookahead]
    
    logger.info(f"Label distribution:")
    logger.info(f"  Long: {(labels == 1).sum()} ({(labels == 1).sum() / len(labels) * 100:.1f}%)")
    logger.info(f"  Hold: {(labels == 0).sum()} ({(labels == 0).sum() / len(labels) * 100:.1f}%)")
    logger.info(f"  Short: {(labels == -1).sum()} ({(labels == -1).sum() / len(labels) * 100:.1f}%)")
    
    return labels


def train_momentum_agent(features, labels, ohlcv):
    """Train momentum agent"""
    logger.info("=" * 60)
    logger.info("Training Momentum Agent (LSTM)")
    logger.info("=" * 60)
    
    agent = MomentumAgent(symbol='BTCUSDT')
    
    # Prepare sequence data for LSTM
    X = features.values[:-10]  # Align with labels
    y = labels.values
    
    if len(X) == 0:
        logger.error("No training data available")
        return None
    
    # Split train/val
    split = int(len(X) * 0.8)
    X_train, X_val = X[:split], X[split:]
    y_train, y_val = y[:split], y[split:]
    
    logger.info(f"Training samples: {len(X_train):,}")
    logger.info(f"Validation samples: {len(X_val):,}")
    
    # Train
    agent.train(X_train, y_train, X_val, y_val, epochs=50, batch_size=64)
    
    # Save
    model_path = Path("models/momentum_agent_live.pkl")
    agent.save(model_path)
    logger.info(f"Saved to {model_path}")
    
    return agent


def train_mean_reversion_agent(features, labels):
    """Train mean reversion agent"""
    logger.info("=" * 60)
    logger.info("Training Mean Reversion Agent (XGBoost)")
    logger.info("=" * 60)
    
    agent = MeanReversionAgent(symbol='BTCUSDT')
    
    X = features.values[:-10]
    y = labels.values
    
    if len(X) == 0:
        logger.error("No training data available")
        return None
    
    # Split
    split = int(len(X) * 0.8)
    X_train, X_val = X[:split], X[split:]
    y_train, y_val = y[:split], y[split:]
    
    logger.info(f"Training samples: {len(X_train):,}")
    logger.info(f"Validation samples: {len(X_val):,}")
    
    # Train
    agent.train(X_train, y_train, X_val, y_val)
    
    # Save
    model_path = Path("models/mean_reversion_agent_live.pkl")
    agent.save(model_path)
    logger.info(f"Saved to {model_path}")
    
    return agent


def train_order_flow_agent(features, labels):
    """Train order flow agent"""
    logger.info("=" * 60)
    logger.info("Training Order Flow Agent (DQN)")
    logger.info("=" * 60)
    
    agent = OrderFlowAgent(symbol='BTCUSDT')
    
    X = features.values[:-10]
    y = labels.values
    
    if len(X) == 0:
        logger.error("No training data available")
        return None
    
    # Split
    split = int(len(X) * 0.8)
    X_train = X[:split]
    y_train = y[:split]
    
    logger.info(f"Training samples: {len(X_train):,}")
    
    # Train with RL approach
    agent.train(X_train, y_train, episodes=100)
    
    # Save
    model_path = Path("models/order_flow_agent_live.pkl")
    agent.save(model_path)
    logger.info(f"Saved to {model_path}")
    
    return agent


def train_regime_classifier(features):
    """Train regime classifier - SKIPPED (needs hmmlearn)"""
    logger.info("=" * 60)
    logger.info("Skipping Regime Classifier (needs C++ build tools)")
    logger.info("=" * 60)
    return None


def main():
    logger.info("=" * 60)
    logger.info("RETRAINING AGENTS ON LIVE DATA")
    logger.info("=" * 60)
    logger.info(f"Started at: {datetime.now()}")
    
    # Create models directory
    Path("models").mkdir(exist_ok=True)
    
    # Load data
    trades = load_and_merge_live_data()
    
    # Prepare training data
    ohlcv, features = prepare_training_data(trades, window='1min')
    
    # Create labels
    labels = create_labels(ohlcv, lookahead=10)
    
    # Align features with labels
    features = features.loc[labels.index]
    
    logger.info(f"Final dataset: {len(features):,} samples")
    
    # Train first 3 agents (skip regime classifier for now)
    try:
        momentum_agent = train_momentum_agent(features, labels, ohlcv)
        logger.info("✓ Momentum agent trained")
    except Exception as e:
        logger.error(f"Failed to train momentum agent: {e}")
    
    try:
        mr_agent = train_mean_reversion_agent(features, labels)
        logger.info("✓ Mean reversion agent trained")
    except Exception as e:
        logger.error(f"Failed to train mean reversion agent: {e}")
    
    try:
        of_agent = train_order_flow_agent(features, labels)
        logger.info("✓ Order flow agent trained")
    except Exception as e:
        logger.error(f"Failed to train order flow agent: {e}")
    
    # Skip regime classifier (needs hmmlearn C++ build tools)
    logger.info("⚠ Skipping regime classifier (requires C++ build tools)")
    
    logger.info("=" * 60)
    logger.info("TRAINING COMPLETE!")
    logger.info("=" * 60)
    logger.info(f"Finished at: {datetime.now()}")
    logger.info("\nModels saved to:")
    logger.info("  - models/momentum_agent_live.pkl")
    logger.info("  - models/mean_reversion_agent_live.pkl")
    logger.info("  - models/order_flow_agent_live.pkl")
    logger.info("  - (regime classifier skipped)")
    logger.info("\nNext steps:")
    logger.info("  1. Run backtest: python scripts/backtest_live_models.py")
    logger.info("  2. Start paper trading: python scripts/run_paper_trading.py")


if __name__ == "__main__":
    main()
