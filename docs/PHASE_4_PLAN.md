# Phase 4: Backtesting Framework

**Start Date:** February 15, 2026  
**Status:** In Progress

---

## Objectives

Build a comprehensive backtesting framework that:
1. Replays historical market data through the complete system
2. Simulates realistic trading conditions (slippage, latency, fees)
3. Calculates detailed performance metrics
4. Supports walk-forward optimization
5. Enables strategy comparison and analysis

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                  BACKTESTING FRAMEWORK                   │
└─────────────────────────────────────────────────────────┘

┌──────────────────┐
│ Historical Data  │  From InfluxDB or CSV
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Data Replayer    │  Simulates real-time feed
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Feature Engine   │  Computes features
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Trading System   │  Agents + Orchestrator
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Execution Sim    │  Realistic execution
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Performance      │  Metrics & Analysis
│ Analyzer         │
└──────────────────┘
```

---

## Components to Build

### 1. Historical Data Loader (`src/backtest/data_loader.py`)

**Purpose:** Load and prepare historical data

**Features:**
- Load from CSV/Parquet/InfluxDB
- Support multiple data types (OHLCV, trades, order book)
- Date range filtering
- Data validation
- Memory-efficient streaming

**Interface:**
```python
class HistoricalDataLoader:
    def load_ohlcv(symbol, start, end) -> DataFrame
    def load_trades(symbol, start, end) -> DataFrame
    def load_order_book(symbol, start, end) -> DataFrame
    def validate_data(data) -> bool
```

### 2. Data Replayer (`src/backtest/replayer.py`)

**Purpose:** Replay historical data as real-time stream

**Features:**
- Event-driven replay
- Configurable speed (1x, 10x, 100x, max)
- Timestamp synchronization
- Multiple data source merging
- Progress tracking

**Interface:**
```python
class DataReplayer:
    def replay(data, callback, speed=1.0)
    def replay_async(data, callback, speed=1.0)
    def get_progress() -> float
```

### 3. Execution Simulator (`src/backtest/execution_simulator.py`)

**Purpose:** Simulate realistic order execution

**Features:**
- Market impact modeling
- Slippage simulation
- Latency simulation
- Partial fills
- Order rejection scenarios

**Interface:**
```python
class ExecutionSimulator:
    def simulate_execution(order, market_state) -> Fill
    def calculate_slippage(order, liquidity) -> float
    def simulate_latency() -> float
```

### 4. Performance Analyzer (`src/backtest/performance_analyzer.py`)

**Purpose:** Calculate comprehensive performance metrics

**Metrics:**
- Returns (total, annualized, daily)
- Risk metrics (Sharpe, Sortino, max drawdown)
- Trade statistics (win rate, profit factor)
- Time-based analysis (monthly, yearly)
- Benchmark comparison

**Interface:**
```python
class PerformanceAnalyzer:
    def calculate_returns(trades) -> Dict
    def calculate_risk_metrics(equity_curve) -> Dict
    def calculate_trade_stats(trades) -> Dict
    def generate_report() -> Report
```

### 5. Backtest Engine (`src/backtest/backtest_engine.py`)

**Purpose:** Main backtesting orchestration

**Features:**
- Complete pipeline integration
- Multiple strategy testing
- Parameter optimization
- Walk-forward analysis
- Monte Carlo simulation

**Interface:**
```python
class BacktestEngine:
    def run_backtest(strategy, data, config) -> BacktestResult
    def optimize_parameters(strategy, data, param_grid) -> OptimizationResult
    def walk_forward_test(strategy, data, config) -> WalkForwardResult
```

### 6. Visualization (`src/backtest/visualization.py`)

**Purpose:** Generate charts and reports

**Charts:**
- Equity curve
- Drawdown chart
- Trade distribution
- Monthly returns heatmap
- Signal analysis

**Interface:**
```python
class BacktestVisualizer:
    def plot_equity_curve(results)
    def plot_drawdown(results)
    def plot_monthly_returns(results)
    def generate_html_report(results) -> str
```

---

## Implementation Plan

### Day 1: Data Infrastructure
- Historical data loader
- Data validation
- CSV/Parquet support

### Day 2: Data Replayer
- Event-driven replay
- Speed control
- Progress tracking

### Day 3: Execution Simulator
- Slippage modeling
- Latency simulation
- Market impact

### Day 4: Performance Analyzer
- Return calculations
- Risk metrics
- Trade statistics

### Day 5: Backtest Engine
- Pipeline integration
- Configuration management
- Result storage

### Day 6: Visualization
- Equity curves
- Performance charts
- HTML reports

### Day 7: Testing & Optimization
- Unit tests
- Integration tests
- Documentation

---

## Key Design Decisions

### 1. Event-Driven Architecture

**Decision:** Use event-driven replay instead of vectorized backtesting

**Rationale:**
- More realistic (matches live trading)
- Supports complex strategies
- Easier to debug
- Can test latency effects

### 2. Realistic Execution Simulation

**Decision:** Model slippage, latency, and market impact

**Rationale:**
- Prevents overfitting
- More accurate performance estimates
- Identifies execution risks
- Better live trading preparation

### 3. Comprehensive Metrics

**Decision:** Calculate 20+ performance metrics

**Rationale:**
- Multiple perspectives on performance
- Risk-adjusted returns
- Identify weaknesses
- Compare strategies objectively

### 4. Walk-Forward Testing

**Decision:** Support walk-forward optimization

**Rationale:**
- Prevents overfitting
- Tests adaptability
- More realistic than in-sample optimization
- Industry best practice

---

## Configuration

### Backtest Config
```yaml
backtest:
  start_date: "2024-01-01"
  end_date: "2024-12-31"
  initial_balance: 10000.0
  commission_rate: 0.001
  slippage_model: "volume_based"
  latency_ms: 50
```

### Execution Simulation
```yaml
execution:
  slippage:
    model: "volume_based"
    base_bps: 2.0
    impact_factor: 0.1
  latency:
    mean_ms: 50
    std_ms: 10
  partial_fills:
    enabled: true
    min_fill_pct: 0.5
```

### Performance Metrics
```yaml
metrics:
  risk_free_rate: 0.02
  benchmark: "BTC"
  periods_per_year: 365
  confidence_level: 0.95
```

---

## Success Metrics

### Accuracy
- Execution simulation within 5% of live results
- Slippage modeling validated against real data
- Latency simulation realistic

### Performance
- Backtest speed: >1000x real-time
- Memory usage: <2GB for 1 year of data
- Result generation: <1 second

### Completeness
- 20+ performance metrics
- 5+ visualization types
- Walk-forward testing
- Monte Carlo simulation

---

## Testing Strategy

### Unit Tests
- Data loader validation
- Replayer accuracy
- Execution simulator
- Metric calculations

### Integration Tests
- Full backtest pipeline
- Multiple strategies
- Different time periods
- Various configurations

### Validation Tests
- Compare with known results
- Benchmark against other frameworks
- Validate against live trading

---

## Performance Metrics to Calculate

### Returns
- Total return
- Annualized return
- Daily/monthly/yearly returns
- Cumulative returns
- Log returns

### Risk Metrics
- Sharpe ratio
- Sortino ratio
- Calmar ratio
- Maximum drawdown
- Average drawdown
- Drawdown duration
- Value at Risk (VaR)
- Conditional VaR (CVaR)
- Beta
- Alpha

### Trade Statistics
- Total trades
- Win rate
- Profit factor
- Average win/loss
- Largest win/loss
- Average trade duration
- Trades per day
- Consecutive wins/losses

### Time-Based Analysis
- Monthly returns
- Yearly returns
- Best/worst month
- Best/worst year
- Winning months %

---

## Visualization Types

### 1. Equity Curve
- Account balance over time
- Drawdown overlay
- Benchmark comparison

### 2. Drawdown Chart
- Underwater equity curve
- Drawdown periods highlighted
- Recovery times

### 3. Monthly Returns Heatmap
- Returns by month and year
- Color-coded performance
- Summary statistics

### 4. Trade Distribution
- Win/loss histogram
- Trade duration distribution
- PnL distribution

### 5. Signal Analysis
- Signal frequency
- Signal quality over time
- Agent contribution

---

## Integration Points

### With Phase 3 (Orchestrator)

```python
# Use orchestrator in backtest
orchestrator = TradingOrchestrator(...)

# Replay historical data
for event in replayer.replay(historical_data):
    features = calculator.update(event)
    signal = ensemble.predict(symbol, features)
    result = orchestrator.process_signal(symbol, signal, price)
```

### With Phase 1 (Features)

```python
# Compute features on historical data
calculator = FeatureCalculator()

for tick in historical_ticks:
    features = calculator.update(tick)
    # Use features in backtest
```

### With Phase 2 (Agents)

```python
# Test different agent configurations
for config in agent_configs:
    agent = create_agent(config)
    result = backtest_engine.run(agent, data)
    results.append(result)
```

---

## Next Steps

1. Create data loader for historical data
2. Implement event-driven replayer
3. Build execution simulator
4. Calculate performance metrics
5. Create backtest engine
6. Add visualization
7. Write comprehensive tests
8. Generate documentation

---

**Status:** Ready to begin implementation
