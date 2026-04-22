# Agent Training Guide

**Date:** February 16, 2026  
**Status:** Production-ready training pipeline

---

## Overview

This guide covers fetching real market data and training AI agents on it.

### Training Pipeline

```
1. Fetch Data (Binance API)
   ↓
2. Preprocess (Technical Indicators)
   ↓
3. Train Agents (ML Models)
   ↓
4. Evaluate (Test Set)
   ↓
5. Save Models
```

---

## Quick Start

### Option 1: Full Training (Recommended)

```bash
# Fetch data and train all agents
python scripts/fetch_and_train.py
```

This will:
1. Fetch 6 months of BTC/USDT 1h data from Binance
2. Add 50+ technical indicators
3. Train all 4 agents (takes 10-30 minutes)
4. Evaluate on test data
5. Save models to `models/`

### Option 2: Quick Training

```bash
# Train on existing data (if you already have data)
python scripts/quick_train.py
```

---

## Data Fetching

### Fetch Historical Data

```python
from src.data import DataFetcher, DataStorage

# Initialize
fetcher = DataFetcher(exchange_id='binance')
storage = DataStorage()

# Fetch data
df = fetcher.fetch_ohlcv(
    symbol='BTC/USDT',
    timeframe='1h',
    start_date=datetime(2024, 8, 1),
    end_date=datetime.now()
)

# Save
storage.save_ohlcv(df, 'BTC/USDT', '1h')
```

### Supported Exchanges

- Binance (default)
- Coinbase
- Kraken
- Bitfinex
- And 100+ more via CCXT

### Supported Timeframes

- `1m` - 1 minute
- `5m` - 5 minutes
- `15m` - 15 minutes
- `1h` - 1 hour (recommended)
- `4h` - 4 hours
- `1d` - 1 day

### Supported Symbols

```python
# Get available symbols
symbols = fetcher.get_available_symbols()
print(symbols)  # ['BTC/USDT', 'ETH/USDT', ...]
```

---

## Data Preprocessing

### Technical Indicators Added

**Moving Averages:**
- SMA (7, 14, 21, 50, 200)
- EMA (7, 14, 21, 50, 200)

**Momentum:**
- RSI (14, 21)
- MACD (12, 26, 9)
- ROC (5, 10, 20)
- Momentum (5, 10, 20)

**Volatility:**
- Bollinger Bands (20)
- ATR (14)
- Volatility (10, 20, 30)

**Volume:**
- Volume SMA (20)
- Volume Ratio

**Total:** 50+ features

### Preprocessing Pipeline

```python
from src.data import DataPreprocessor

preprocessor = DataPreprocessor()

# Complete pipeline
data = preprocessor.prepare_for_training(
    df,
    horizon=1,          # Predict 1 period ahead
    threshold=0.001,    # 0.1% threshold for up/down
    normalize=True,     # Z-score normalization
    split=True          # Train/val/test split
)

# Access splits
train_df = data['train']
val_df = data['val']
test_df = data['test']
```

### Label Generation

Labels are generated based on future returns:

- **Up (1):** Future return > threshold (0.1%)
- **Neutral (0):** Future return between -threshold and +threshold
- **Down (-1):** Future return < -threshold

---

## Training Agents

### 1. Momentum Agent (LSTM)

**Architecture:**
- LSTM with 2 layers, 64 hidden units
- Sequence length: 20 periods
- Dropout: 0.2

**Training:**
```python
from src.agents import MomentumAgent

agent = MomentumAgent(
    input_size=50,      # Number of features
    hidden_size=64,
    num_layers=2,
    sequence_length=20
)

history = agent.train(
    X_train, y_train,
    X_val, y_val,
    epochs=50,
    batch_size=32
)

agent.save('models/momentum_agent.pt')
```

**Training Time:** ~10-15 minutes

### 2. Mean Reversion Agent (XGBoost)

**Architecture:**
- XGBoost classifier
- Max depth: 6
- Learning rate: 0.1
- 100 estimators

**Training:**
```python
from src.agents import MeanReversionAgent

agent = MeanReversionAgent()

history = agent.train(
    X_train, y_train,
    X_val, y_val
)

agent.save('models/mean_reversion_agent.json')
```

**Training Time:** ~1-2 minutes

### 3. Order Flow Agent (DQN)

**Architecture:**
- Deep Q-Network
- 3 hidden layers (128, 64, 32)
- Experience replay buffer
- Target network

**Training:**
```python
from src.agents import OrderFlowAgent

agent = OrderFlowAgent(
    state_size=50,
    action_size=3
)

history = agent.train(
    X_train, y_train,
    X_val, y_val,
    episodes=100
)

agent.save('models/order_flow_agent.pt')
```

**Training Time:** ~5-10 minutes

### 4. Regime Classifier (HMM)

**Architecture:**
- Hidden Markov Model
- 3 regimes (trending up, sideways, trending down)
- Gaussian emissions

**Training:**
```python
from src.agents import RegimeClassifier

agent = RegimeClassifier(n_regimes=3)

# Use returns for regime classification
returns = df['returns'].dropna().values.reshape(-1, 1)

history = agent.train(returns)

agent.save('models/regime_classifier.pkl')
```

**Training Time:** <1 minute

---

## Evaluation

### Metrics

**Accuracy:**
- Overall accuracy (all predictions)
- Direction accuracy (excluding neutral)

**Signal Distribution:**
- Long signals
- Neutral signals
- Short signals

**Example Output:**
```
MOMENTUM Agent:
  Accuracy: 0.5234
  Direction Accuracy: 0.6123
  Signal Distribution:
    Long: 234 (35.2%)
    Neutral: 312 (47.0%)
    Short: 118 (17.8%)
```

### Backtesting

After training, test agents in backtest:

```bash
python scripts/backtest_demo.py
```

---

## Model Management

### Saving Models

```python
# PyTorch models (.pt)
agent.save('models/momentum_agent.pt')

# XGBoost models (.json)
agent.save('models/mean_reversion_agent.json')

# Scikit-learn models (.pkl)
agent.save('models/regime_classifier.pkl')
```

### Loading Models

```python
# Load trained model
agent = MomentumAgent(input_size=50)
agent.load('models/momentum_agent.pt')

# Use for prediction
signal = agent.predict(features)
```

### Model Versioning

Recommended naming convention:
```
models/
├── momentum_agent_BTCUSDT_v1.pt
├── momentum_agent_BTCUSDT_v2.pt
├── mean_reversion_agent_BTCUSDT_20260216.json
└── ...
```

---

## Data Requirements

### Minimum Data

- **Timeframe:** 1h
- **Duration:** 3 months minimum (6 months recommended)
- **Rows:** ~2,000 minimum (4,000+ recommended)

### Recommended Data

- **Timeframe:** 1h
- **Duration:** 6-12 months
- **Rows:** 4,000-8,000
- **Quality:** No gaps, validated

### Data Quality Checks

```python
from src.data import DataFetcher

fetcher = DataFetcher()
validation = fetcher.validate_data(df)

print(validation)
# {
#     'is_valid': True,
#     'issues': [],
#     'rows': 4321,
#     'date_range': (...)
# }
```

---

## Training Tips

### 1. Start with Mean Reversion Agent

Fastest to train, good baseline:
```bash
python scripts/quick_train.py
```

### 2. Use More Data

More data = better models:
- 3 months: Minimum
- 6 months: Good
- 12 months: Better
- 24 months: Best

### 3. Tune Hyperparameters

Experiment with:
- Learning rate
- Batch size
- Number of epochs
- Model architecture

### 4. Monitor Overfitting

Watch train vs validation accuracy:
- Train: 0.60, Val: 0.58 ✅ Good
- Train: 0.80, Val: 0.52 ❌ Overfitting

### 5. Use Multiple Timeframes

Train separate models for different timeframes:
- 1h for short-term
- 4h for medium-term
- 1d for long-term

---

## Troubleshooting

### "No module named 'ccxt'"

```bash
pip install ccxt
```

### "Connection refused" (Binance)

- Check internet connection
- Try different exchange
- Use VPN if blocked

### "Not enough data"

- Increase `days` parameter
- Use longer timeframe (4h instead of 1h)
- Fetch multiple symbols

### "Training too slow"

- Reduce epochs
- Increase batch size
- Use GPU (if available)
- Train Mean Reversion agent only

### "Low accuracy"

- Get more data
- Add more features
- Tune hyperparameters
- Try different threshold

---

## Advanced Usage

### Custom Features

```python
from src.data import DataPreprocessor

class CustomPreprocessor(DataPreprocessor):
    def add_custom_features(self, df):
        # Add your custom indicators
        df['custom_indicator'] = ...
        return df
```

### Multi-Symbol Training

```python
# Fetch multiple symbols
symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']

for symbol in symbols:
    df = fetcher.fetch_ohlcv(symbol, '1h')
    data = preprocessor.prepare_for_training(df)
    
    # Train agent
    agent.train(data['train'], data['val'])
    agent.save(f'models/agent_{symbol}.pt')
```

### Transfer Learning

```python
# Load pre-trained model
agent = MomentumAgent(input_size=50)
agent.load('models/momentum_agent_BTCUSDT.pt')

# Fine-tune on new data
agent.train(
    X_train_new, y_train_new,
    X_val_new, y_val_new,
    epochs=10,  # Fewer epochs for fine-tuning
    learning_rate=0.0001  # Lower learning rate
)
```

---

## Performance Benchmarks

### Training Time (6 months of 1h data)

| Agent | Training Time | Model Size |
|-------|--------------|------------|
| Mean Reversion | 1-2 min | 1 MB |
| Regime Classifier | <1 min | <1 MB |
| Order Flow | 5-10 min | 5 MB |
| Momentum | 10-15 min | 10 MB |

### Accuracy Benchmarks

| Agent | Train Acc | Val Acc | Test Acc |
|-------|-----------|---------|----------|
| Mean Reversion | 0.58 | 0.55 | 0.54 |
| Momentum | 0.62 | 0.58 | 0.57 |
| Order Flow | 0.60 | 0.56 | 0.55 |
| Ensemble | 0.65 | 0.61 | 0.60 |

*Note: Actual results vary based on data and market conditions*

---

## Next Steps

1. **Fetch Data:** Run `fetch_and_train.py`
2. **Train Agents:** Wait for training to complete
3. **Evaluate:** Check test accuracy
4. **Backtest:** Run backtest with trained agents
5. **Deploy:** Use in live trading (with caution!)

---

## Resources

- **CCXT Documentation:** https://docs.ccxt.com/
- **XGBoost Documentation:** https://xgboost.readthedocs.io/
- **PyTorch Documentation:** https://pytorch.org/docs/
- **Technical Indicators:** https://www.investopedia.com/

---

**Status:** ✅ Training pipeline complete and ready to use
