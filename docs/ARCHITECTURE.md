# M281M Architecture

## System Overview

M281M is a multi-agent AI trading system designed for high-frequency scalping with advanced risk management.

## Core Components

### 1. Data Pipeline
- **WebSocket Client**: Real-time market data ingestion from Binance
- **Feature Calculator**: Computes microstructure features (order flow, VPIN, etc.)
- **Time-Series DB**: InfluxDB for historical storage and retrieval

### 2. AI Agents
- **Regime Classifier**: Identifies market state (Trending/Range/Volatile)
- **Momentum Agent**: Temporal Fusion Transformer for impulse prediction
- **Order Flow Agent**: DQN for order book-based decisions
- **Mean Reversion Agent**: XGBoost for reversal signals
- **Orchestrator**: Meta-learner that combines specialist signals

### 3. Risk Management
- Layer 1: Trade-level (stop-loss, take-profit)
- Layer 2: Portfolio-level (VaR, exposure limits)
- Layer 3: Regime-aware (dynamic sizing)
- Layer 4: Adversarial (spoofing detection)
- Layer 5: Meta-risk (daily drawdown limits)

### 4. Backtesting
- Tick-replay simulator
- Walk-forward validation
- Adversarial scenario testing

### 5. Deployment
- Dockerized microservices
- Signal-only and auto-trade modes
- Real-time monitoring with Prometheus/Grafana

## Data Flow

```
Exchange → WebSocket → Feature Calculator → Agents → Orchestrator → Risk Manager → Execution
                              ↓
                         InfluxDB (storage)
```

## Technology Stack

- Python 3.9+ (core system)
- PyTorch (neural agents)
- WebSockets (real-time data)
- InfluxDB (time-series storage)
- Docker (deployment)
