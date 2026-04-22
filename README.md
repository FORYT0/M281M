# M281M - AI Trading System

A production-ready, real-time AI trading system that scalps financial markets using advanced market microstructure and multi-agent machine learning.

## Features

- Real-time Level 2 order book processing
- Multi-agent ML architecture (Momentum, Order Flow, Mean Reversion)
- Regime-aware meta-learning orchestrator
- Multi-layer risk management system
- Walk-forward backtesting
- Low-latency deployment ready

## Setup

1. Run the setup script:
   ```bash
   bash setup.sh
   ```

2. Activate the virtual environment:
   ```bash
   source venv/bin/activate  # Unix/Mac
   venv\Scripts\activate     # Windows
   ```

3. Configure your API keys in `config/config.yaml`

## Quick Start

Test the WebSocket connection:
```bash
python scripts/test_websocket.py
```

Test the tick replay simulator:
```bash
python scripts/test_simulator.py
```

## Project Structure

```
m281m/
├── data/              # Market data storage
├── src/               # Source code
│   ├── pipeline/      # Data ingestion & features
│   ├── agents/        # ML agents
│   ├── risk/          # Risk management
│   ├── backtest/      # Backtesting engine
│   └── deployment/    # Production deployment
├── tests/             # Unit tests
├── docs/              # Documentation
├── scripts/           # Utility scripts
├── logs/              # Application logs
├── models/            # Trained models
└── config/            # Configuration files
```

## Development Phases

- [x] Phase 0: Environment & Foundations ✅
- [x] Phase 1: Data Pipeline & Features ✅ (0.074ms latency!)
- [ ] Phase 2: Multi-Agent AI Core ⏳ NEXT
- [ ] Phase 3: Orchestrator & Meta-Learning
- [ ] Phase 4: Backtesting
- [ ] Phase 5: Risk Management
- [ ] Phase 6: Deployment
- [ ] Phase 7: Continuous Learning
- [ ] Phase 8: Scaling & Optimization

## Documentation

See `docs/` for detailed architecture and API documentation.

## License

Proprietary - All Rights Reserved
