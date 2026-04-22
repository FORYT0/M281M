#!/bin/bash

echo "=========================================="
echo "M281M AI Trading System - Setup Script"
echo "=========================================="

# Check if Python 3.9+ is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Detected Python version: $PYTHON_VERSION"

# Create project directory structure
echo ""
echo "Creating project directory structure..."
mkdir -p data/live
mkdir -p data/historical
mkdir -p src/pipeline
mkdir -p src/agents
mkdir -p src/risk
mkdir -p src/backtest
mkdir -p src/deployment
mkdir -p tests
mkdir -p docs
mkdir -p scripts
mkdir -p logs
mkdir -p models
mkdir -p config

echo "✓ Directory structure created"

# Initialize Git repository
echo ""
echo "Initializing Git repository..."
if [ ! -d .git ]; then
    git init
    echo "✓ Git repository initialized"
else
    echo "✓ Git repository already exists"
fi

# Create .gitignore
echo ""
echo "Creating .gitignore..."
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Data
data/live/*.csv
data/historical/*.csv
data/historical/*.parquet
*.db
*.sqlite

# Logs
logs/*.log
*.log

# Models
models/*.pth
models/*.pkl
models/*.h5
*.ckpt

# Environment variables
.env
.env.local

# OS
.DS_Store
Thumbs.db

# Jupyter
.ipynb_checkpoints/
*.ipynb

# MLflow
mlruns/

# Temporary files
tmp/
temp/
*.tmp
EOF

echo "✓ .gitignore created"

# Create Python virtual environment
echo ""
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment and install dependencies
echo ""
echo "Installing dependencies..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # Unix-like
    source venv/bin/activate
fi

pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✓ Dependencies installed"

# Create initial configuration file
echo ""
echo "Creating initial configuration..."
cat > config/config.yaml << 'EOF'
# M281M Configuration

exchange:
  name: binance
  testnet: true
  api_key: ""
  api_secret: ""

trading:
  symbols:
    - BTCUSDT
  timeframes:
    - 1m
    - 5m
  
data:
  websocket_reconnect_delay: 5
  max_reconnect_attempts: 10
  
features:
  order_flow_window: 100
  vpin_window: 50
  ema_periods: [9, 21]
  rsi_period: 14

risk:
  max_position_size: 0.1
  max_daily_drawdown: 0.05
  stop_loss_atr_multiplier: 2.0
  take_profit_ratio: 1.5

database:
  influxdb_url: "http://localhost:8086"
  influxdb_token: ""
  influxdb_org: "m281m"
  influxdb_bucket: "market_data"

logging:
  level: INFO
  file: logs/m281m.log
EOF

echo "✓ Configuration file created at config/config.yaml"

# Create README
echo ""
echo "Creating README..."
cat > README.md << 'EOF'
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

## Project Structure

```
ai_trading_system/
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

## Quick Start

Test the WebSocket connection:
```bash
python scripts/test_websocket.py
```

## Development Phases

- [x] Phase 0: Environment & Foundations
- [ ] Phase 1: Data Pipeline & Features
- [ ] Phase 2: Multi-Agent AI Core
- [ ] Phase 3: Orchestrator & Meta-Learning
- [ ] Phase 4: Backtesting
- [ ] Phase 5: Risk Management
- [ ] Phase 6: Deployment
- [ ] Phase 7: Continuous Learning
- [ ] Phase 8: Scaling & Optimization

## License

Proprietary - All Rights Reserved
EOF

echo "✓ README.md created"

echo ""
echo "=========================================="
echo "Setup complete! 🚀"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate  (Unix/Mac)"
echo "   venv\\Scripts\\activate     (Windows)"
echo ""
echo "2. Update config/config.yaml with your API credentials"
echo ""
echo "3. Test the WebSocket client:"
echo "   python scripts/test_websocket.py"
echo ""
echo "Happy trading!"
