"""
Quick training script - Train agents on existing data.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data import DataStorage, DataPreprocessor
from src.agents import MomentumAgent, MeanReversionAgent
import numpy as np

def main():
    print("="*60)
    print("QUICK AGENT TRAINING")
    print("="*60)
    
    # Load existing data
    storage = DataStorage()
    
    print("\nAvailable data:")
    available = storage.list_available_data()
    for symbol, timeframe, format in available:
        print(f"  - {symbol} {timeframe} ({format})")
    
    if not available:
        print("\nNo data found! Run fetch_and_train.py first.")
        return
    
    # Use first available
    symbol, timeframe, format = available[0]
    print(f"\nUsing: {symbol} {timeframe}")
    
    # Load data
    df = storage.load_ohlcv(symbol, timeframe, format)
    print(f"Loaded {len(df)} rows")
    
    # Preprocess
    print("\nPreprocessing...")
    preprocessor = DataPreprocessor()
    data = preprocessor.prepare_for_training(df)
    
    print(f"Train: {len(data['train'])} samples")
    print(f"Val: {len(data['val'])} samples")
    print(f"Test: {len(data['test'])} samples")
    
    # Prepare features
    exclude_cols = ['timestamp', 'label', 'target_return', 'future_return']
    feature_cols = [col for col in data['train'].columns if col not in exclude_cols]
    
    X_train = data['train'][feature_cols].values
    y_train = data['train']['label'].values
    X_val = data['val'][feature_cols].values
    y_val = data['val']['label'].values
    
    # Train Mean Reversion Agent (fastest)
    print("\nTraining Mean Reversion Agent...")
    agent = MeanReversionAgent()
    
    history = agent.train(X_train, y_train, X_val, y_val)
    
    print(f"Train accuracy: {history['train_accuracy']:.4f}")
    print(f"Val accuracy: {history['val_accuracy']:.4f}")
    
    # Save
    os.makedirs('models', exist_ok=True)
    agent.save(f'models/mean_reversion_agent_{symbol}.json')
    print(f"\nModel saved to models/mean_reversion_agent_{symbol}.json")
    
    print("\nDone! Agent is ready to use.")

if __name__ == '__main__':
    main()
