"""
Fetch real data and train agents.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

from src.data import DataFetcher, DataStorage, DataPreprocessor
from src.agents import MomentumAgent, MeanReversionAgent, OrderFlowAgent
from src.agents.regime_classifier import RegimeClassifier

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch_data(
    symbol: str = 'BTC/USDT',
    timeframe: str = '1h',
    days: int = 180
):
    """
    Fetch historical data from Binance.
    
    Args:
        symbol: Trading pair
        timeframe: Timeframe
        days: Number of days of history
    
    Returns:
        DataFrame with OHLCV data
    """
    print("\n" + "="*60)
    print("STEP 1: Fetching Historical Data")
    print("="*60)
    
    # Initialize fetcher
    fetcher = DataFetcher(exchange_id='binance')
    storage = DataStorage()
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    print(f"\nFetching {symbol} {timeframe} data...")
    print(f"  Period: {start_date.date()} to {end_date.date()}")
    print(f"  Exchange: Binance")
    
    # Fetch data
    df = fetcher.fetch_ohlcv(
        symbol=symbol,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date
    )
    
    # Validate
    validation = fetcher.validate_data(df)
    
    print(f"\nData fetched:")
    print(f"  Rows: {len(df)}")
    print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"  Valid: {validation['is_valid']}")
    
    if not validation['is_valid']:
        print(f"  Issues: {validation['issues']}")
    
    # Save data
    filepath = storage.save_ohlcv(df, symbol, timeframe, format='csv')
    print(f"\nData saved to: {filepath}")
    
    return df


def preprocess_data(df: pd.DataFrame):
    """
    Preprocess data for training.
    
    Args:
        df: Raw OHLCV DataFrame
    
    Returns:
        Dictionary with train/val/test data
    """
    print("\n" + "="*60)
    print("STEP 2: Preprocessing Data")
    print("="*60)
    
    preprocessor = DataPreprocessor()
    
    print("\nAdding technical indicators...")
    print("  - Moving averages (SMA, EMA)")
    print("  - RSI, MACD, Bollinger Bands")
    print("  - ATR, Volume indicators")
    print("  - Momentum, Volatility")
    
    # Preprocess
    data = preprocessor.prepare_for_training(
        df,
        horizon=1,
        threshold=0.001,
        normalize=True,
        split=True
    )
    
    print(f"\nPreprocessing complete:")
    print(f"  Features: {data['n_features']}")
    print(f"  Train samples: {len(data['train'])}")
    print(f"  Validation samples: {len(data['val'])}")
    print(f"  Test samples: {len(data['test'])}")
    
    # Show label distribution
    train_labels = data['train']['label'].value_counts()
    print(f"\nLabel distribution (train):")
    print(f"  Down (-1): {train_labels.get(-1, 0)} ({train_labels.get(-1, 0)/len(data['train'])*100:.1f}%)")
    print(f"  Neutral (0): {train_labels.get(0, 0)} ({train_labels.get(0, 0)/len(data['train'])*100:.1f}%)")
    print(f"  Up (1): {train_labels.get(1, 0)} ({train_labels.get(1, 0)/len(data['train'])*100:.1f}%)")
    
    return data


def train_agents(data: dict, symbol: str = 'BTCUSDT'):
    """
    Train all agents on the data.
    
    Args:
        data: Preprocessed data dictionary
        symbol: Trading symbol
    
    Returns:
        Dictionary of trained agents
    """
    print("\n" + "="*60)
    print("STEP 3: Training Agents")
    print("="*60)
    
    agents = {}
    
    # Prepare feature columns
    exclude_cols = ['timestamp', 'label', 'target_return', 'future_return']
    feature_cols = [col for col in data['train'].columns if col not in exclude_cols]
    
    # Extract features and labels
    X_train = data['train'][feature_cols].values
    y_train = data['train']['label'].values
    
    X_val = data['val'][feature_cols].values
    y_val = data['val']['label'].values
    
    print(f"\nTraining data shape: {X_train.shape}")
    print(f"Validation data shape: {X_val.shape}")
    
    # 1. Train Momentum Agent
    print("\n" + "-"*60)
    print("Training Momentum Agent (LSTM)")
    print("-"*60)
    
    try:
        momentum_agent = MomentumAgent(
            input_size=X_train.shape[1],
            hidden_size=64,
            num_layers=2,
            sequence_length=20
        )
        
        # Prepare sequences for LSTM
        X_train_seq, y_train_seq = momentum_agent._prepare_sequences(X_train, y_train)
        X_val_seq, y_val_seq = momentum_agent._prepare_sequences(X_val, y_val)
        
        print(f"  Sequence shape: {X_train_seq.shape}")
        print(f"  Training for 50 epochs...")
        
        history = momentum_agent.train(
            X_train_seq,
            y_train_seq,
            X_val_seq,
            y_val_seq,
            epochs=50,
            batch_size=32
        )
        
        print(f"  Final train loss: {history['train_loss'][-1]:.4f}")
        print(f"  Final val loss: {history['val_loss'][-1]:.4f}")
        print(f"  Final val accuracy: {history['val_accuracy'][-1]:.4f}")
        
        # Save model
        os.makedirs('models', exist_ok=True)
        momentum_agent.save(f'models/momentum_agent_{symbol}.pt')
        print(f"  Model saved to models/momentum_agent_{symbol}.pt")
        
        agents['momentum'] = momentum_agent
        
    except Exception as e:
        print(f"  Error training momentum agent: {e}")
        import traceback
        traceback.print_exc()
    
    # 2. Train Mean Reversion Agent
    print("\n" + "-"*60)
    print("Training Mean Reversion Agent (XGBoost)")
    print("-"*60)
    
    try:
        mean_reversion_agent = MeanReversionAgent()
        
        print(f"  Training XGBoost classifier...")
        
        history = mean_reversion_agent.train(
            X_train,
            y_train,
            X_val,
            y_val
        )
        
        print(f"  Train accuracy: {history['train_accuracy']:.4f}")
        print(f"  Val accuracy: {history['val_accuracy']:.4f}")
        
        # Save model
        mean_reversion_agent.save(f'models/mean_reversion_agent_{symbol}.json')
        print(f"  Model saved to models/mean_reversion_agent_{symbol}.json")
        
        agents['mean_reversion'] = mean_reversion_agent
        
    except Exception as e:
        print(f"  Error training mean reversion agent: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. Train Order Flow Agent
    print("\n" + "-"*60)
    print("Training Order Flow Agent (DQN)")
    print("-"*60)
    
    try:
        order_flow_agent = OrderFlowAgent(
            state_size=X_train.shape[1],
            action_size=3
        )
        
        print(f"  Training DQN for 100 episodes...")
        print(f"  (Using supervised learning mode)")
        
        # Train using supervised learning (simplified)
        history = order_flow_agent.train(
            X_train,
            y_train,
            X_val,
            y_val,
            episodes=100
        )
        
        print(f"  Final reward: {history.get('avg_reward', 0):.4f}")
        
        # Save model
        order_flow_agent.save(f'models/order_flow_agent_{symbol}.pt')
        print(f"  Model saved to models/order_flow_agent_{symbol}.pt")
        
        agents['order_flow'] = order_flow_agent
        
    except Exception as e:
        print(f"  Error training order flow agent: {e}")
        import traceback
        traceback.print_exc()
    
    # 4. Train Regime Classifier
    print("\n" + "-"*60)
    print("Training Regime Classifier (HMM)")
    print("-"*60)
    
    try:
        regime_classifier = RegimeClassifier(n_regimes=3)
        
        print(f"  Training Hidden Markov Model...")
        
        # Use returns for regime classification
        returns = data['train']['returns'].dropna().values.reshape(-1, 1)
        
        history = regime_classifier.train(returns)
        
        print(f"  Converged: {history.get('converged', False)}")
        print(f"  Iterations: {history.get('n_iter', 0)}")
        
        # Save model
        regime_classifier.save(f'models/regime_classifier_{symbol}.pkl')
        print(f"  Model saved to models/regime_classifier_{symbol}.pkl")
        
        agents['regime'] = regime_classifier
        
    except Exception as e:
        print(f"  Error training regime classifier: {e}")
        import traceback
        traceback.print_exc()
    
    return agents


def evaluate_agents(agents: dict, data: dict):
    """
    Evaluate trained agents on test data.
    
    Args:
        agents: Dictionary of trained agents
        data: Preprocessed data dictionary
    """
    print("\n" + "="*60)
    print("STEP 4: Evaluating Agents")
    print("="*60)
    
    # Prepare test data
    exclude_cols = ['timestamp', 'label', 'target_return', 'future_return']
    feature_cols = [col for col in data['test'].columns if col not in exclude_cols]
    
    X_test = data['test'][feature_cols].values
    y_test = data['test']['label'].values
    
    print(f"\nTest data shape: {X_test.shape}")
    print(f"Test samples: {len(X_test)}")
    
    results = {}
    
    # Evaluate each agent
    for name, agent in agents.items():
        print(f"\n{name.upper()} Agent:")
        
        try:
            if name == 'momentum':
                # Prepare sequences
                X_test_seq, y_test_seq = agent._prepare_sequences(X_test, y_test)
                
                # Get predictions
                predictions = []
                for i in range(len(X_test_seq)):
                    features_dict = {f'feature_{j}': X_test_seq[i, -1, j] for j in range(X_test_seq.shape[2])}
                    signal = agent.predict(features_dict)
                    predictions.append(1 if signal.direction == 'long' else -1 if signal.direction == 'short' else 0)
                
                predictions = np.array(predictions)
                y_test_eval = y_test_seq
                
            elif name == 'mean_reversion':
                predictions = []
                for i in range(len(X_test)):
                    features_dict = {f'feature_{j}': X_test[i, j] for j in range(X_test.shape[1])}
                    signal = agent.predict(features_dict)
                    predictions.append(1 if signal.direction == 'long' else -1 if signal.direction == 'short' else 0)
                
                predictions = np.array(predictions)
                y_test_eval = y_test
                
            elif name == 'order_flow':
                predictions = []
                for i in range(len(X_test)):
                    features_dict = {f'feature_{j}': X_test[i, j] for j in range(X_test.shape[1])}
                    signal = agent.predict(features_dict)
                    predictions.append(1 if signal.direction == 'long' else -1 if signal.direction == 'short' else 0)
                
                predictions = np.array(predictions)
                y_test_eval = y_test
            
            else:
                continue
            
            # Calculate metrics
            accuracy = (predictions == y_test_eval).mean()
            
            # Direction accuracy (ignoring neutral)
            mask = (predictions != 0) & (y_test_eval != 0)
            if mask.sum() > 0:
                direction_accuracy = (predictions[mask] == y_test_eval[mask]).mean()
            else:
                direction_accuracy = 0
            
            # Signal distribution
            signal_dist = pd.Series(predictions).value_counts()
            
            print(f"  Accuracy: {accuracy:.4f}")
            print(f"  Direction Accuracy: {direction_accuracy:.4f}")
            print(f"  Signal Distribution:")
            print(f"    Long: {signal_dist.get(1, 0)} ({signal_dist.get(1, 0)/len(predictions)*100:.1f}%)")
            print(f"    Neutral: {signal_dist.get(0, 0)} ({signal_dist.get(0, 0)/len(predictions)*100:.1f}%)")
            print(f"    Short: {signal_dist.get(-1, 0)} ({signal_dist.get(-1, 0)/len(predictions)*100:.1f}%)")
            
            results[name] = {
                'accuracy': accuracy,
                'direction_accuracy': direction_accuracy,
                'signal_distribution': signal_dist.to_dict()
            }
            
        except Exception as e:
            print(f"  Error evaluating {name}: {e}")
    
    return results


if __name__ == '__main__':
    print("\n" + "="*60)
    print("FETCH REAL DATA AND TRAIN AGENTS")
    print("="*60)
    print("\nThis script will:")
    print("  1. Fetch 6 months of BTC/USDT 1h data from Binance")
    print("  2. Preprocess and add technical indicators")
    print("  3. Train all 4 agents (Momentum, Mean Reversion, Order Flow, Regime)")
    print("  4. Evaluate agents on test data")
    print("  5. Save trained models to models/")
    
    input("\nPress Enter to start...")
    
    try:
        # Fetch data
        df = fetch_data(
            symbol='BTC/USDT',
            timeframe='1h',
            days=180
        )
        
        # Preprocess
        data = preprocess_data(df)
        
        # Train agents
        agents = train_agents(data, symbol='BTCUSDT')
        
        # Evaluate
        results = evaluate_agents(agents, data)
        
        # Summary
        print("\n" + "="*60)
        print("TRAINING COMPLETE")
        print("="*60)
        
        print(f"\nTrained {len(agents)} agents:")
        for name in agents.keys():
            print(f"  - {name}")
        
        print(f"\nModels saved to models/")
        print(f"\nTest Results:")
        for name, metrics in results.items():
            print(f"  {name}: {metrics['accuracy']:.2%} accuracy")
        
        print("\nAgents are now ready to use!")
        print("Load them with:")
        print("  agent.load('models/momentum_agent_BTCUSDT.pt')")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
