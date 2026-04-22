# M281M Testing Guide

## Phase 0 Testing

### Prerequisites

You have Python 3.14.0 installed and a virtual environment created at `venv/`.

### Step 1: Install Dependencies

Due to network speed, install dependencies in batches:

```cmd
.\venv\Scripts\python.exe -m pip install pandas numpy
.\venv\Scripts\python.exe -m pip install websockets aiohttp
.\venv\Scripts\python.exe -m pip install loguru
```

### Step 2: Verify Structure

```cmd
.\venv\Scripts\python.exe scripts\quick_test.py
```

Expected output: All checkmarks (✓) for directories and files.

### Step 3: Test Tick Simulator (Offline)

```cmd
.\venv\Scripts\python.exe scripts\test_simulator.py
```

This will:
- Generate 1 hour of synthetic BTC/USDT order book data
- Replay it at 10x speed
- Display progress every 100 ticks

Expected output:
```
Generating 60 minutes of synthetic data...
Generated 36000 ticks, saved to data/historical/synthetic_btcusdt_1h.csv

Starting replay at 10x speed...
Tick 100: Price=50123.45, Spread=12.34, Progress=0.3%
...
Replay completed! Processed 36000 ticks
```

### Step 4: Test WebSocket Client (Online - Requires Internet)

```cmd
.\venv\Scripts\python.exe scripts\test_websocket.py
```

This will:
- Connect to Binance testnet
- Subscribe to BTC/USDT order book updates (20 levels, 100ms)
- Display best bid/ask every second

Expected output:
```
Connecting to Binance testnet...
WebSocket connected successfully

[14:30:01] Bid: 50000.00 | Ask: 50001.00 | Spread: 1.00 (2.00 bps) | Updates: 10
[14:30:02] Bid: 50000.50 | Ask: 50001.50 | Spread: 1.00 (2.00 bps) | Updates: 20
...
```

Press Ctrl+C to stop.

## Troubleshooting

### ModuleNotFoundError

If you see "No module named 'X'", install it:
```cmd
.\venv\Scripts\python.exe -m pip install X
```

### WebSocket Connection Failed

- Check internet connection
- Binance testnet may be down (try mainnet by editing the script)
- Firewall may be blocking WebSocket connections

### Slow Installation

Windows + slow network can make pip installations take time. Be patient or:
- Use a faster network
- Install packages one at a time
- Consider using a package cache

## Next Phase

Once all tests pass, you're ready for Phase 1: Feature Engineering!
