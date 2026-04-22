# Phase 3: Orchestrator & Meta-Learning

**Start Date:** February 15, 2026  
**Status:** In Progress

---

## Objectives

Build an intelligent orchestration layer that:
1. Coordinates all agents and manages their lifecycle
2. Implements meta-learning to optimize agent weights dynamically
3. Filters and validates signals before execution
4. Manages position sizing based on confidence and risk
5. Tracks performance and adapts in real-time

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR LAYER                    │
└─────────────────────────────────────────────────────────┘

┌──────────────────┐
│ Feature Stream   │  From Phase 1
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Agent Ensemble   │  From Phase 2
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR                          │
│  ┌────────────────────────────────────────────────┐     │
│  │ 1. Signal Validator                            │     │
│  │    - Confidence thresholds                     │     │
│  │    - Agreement requirements                    │     │
│  │    - Regime-based filtering                    │     │
│  └────────────────────────────────────────────────┘     │
│                          ↓                               │
│  ┌────────────────────────────────────────────────┐     │
│  │ 2. Meta-Learner                                │     │
│  │    - Performance tracking per agent            │     │
│  │    - Dynamic weight optimization               │     │
│  │    - Online learning                           │     │
│  └────────────────────────────────────────────────┘     │
│                          ↓                               │
│  ┌────────────────────────────────────────────────┐     │
│  │ 3. Position Sizer                              │     │
│  │    - Kelly criterion                           │     │
│  │    - Confidence-based sizing                   │     │
│  │    - Risk limits                               │     │
│  └────────────────────────────────────────────────┘     │
│                          ↓                               │
│  ┌────────────────────────────────────────────────┐     │
│  │ 4. Execution Manager                           │     │
│  │    - Order generation                          │     │
│  │    - Position tracking                         │     │
│  │    - PnL calculation                           │     │
│  └────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────┐
│ Trading Orders   │  To Phase 6 (Deployment)
└──────────────────┘
```

---

## Components to Build

### 1. Signal Validator (`src/orchestrator/signal_validator.py`)

**Purpose:** Filter and validate signals before execution

**Features:**
- Minimum confidence threshold
- Minimum agreement score
- Regime-based filtering
- Cooldown periods
- Signal quality scoring

**Interface:**
```python
class SignalValidator:
    def validate(signal: EnsembleSignal) -> ValidationResult
    def set_thresholds(min_confidence, min_agreement)
    def get_validation_stats() -> Dict
```

### 2. Meta-Learner (`src/orchestrator/meta_learner.py`)

**Purpose:** Learn optimal agent weights from performance

**Algorithms:**
- Online gradient descent
- Exponential moving average of performance
- Contextual bandits (regime-aware)
- Bayesian optimization

**Interface:**
```python
class MetaLearner:
    def update_performance(agent_name, signal, outcome)
    def get_optimal_weights(regime) -> Dict[str, float]
    def get_agent_performance() -> Dict
```

### 3. Position Sizer (`src/orchestrator/position_sizer.py`)

**Purpose:** Determine position size based on signal and risk

**Methods:**
- Kelly Criterion
- Fixed fractional
- Confidence-based scaling
- Volatility adjustment

**Interface:**
```python
class PositionSizer:
    def calculate_size(signal, account_balance, risk_params) -> float
    def adjust_for_volatility(size, volatility) -> float
    def get_max_position(symbol) -> float
```

### 4. Execution Manager (`src/orchestrator/execution_manager.py`)

**Purpose:** Manage order execution and position tracking

**Features:**
- Order generation
- Position tracking
- PnL calculation
- Trade history
- Performance metrics

**Interface:**
```python
class ExecutionManager:
    def execute_signal(signal, position_size)
    def get_current_position(symbol) -> Position
    def calculate_pnl() -> float
    def get_trade_history() -> List[Trade]
```

### 5. Orchestrator (`src/orchestrator/orchestrator.py`)

**Purpose:** Main coordination layer

**Responsibilities:**
- Receive signals from ensemble
- Validate signals
- Update meta-learner
- Calculate position size
- Execute trades
- Track performance

**Interface:**
```python
class TradingOrchestrator:
    def process_signal(symbol, ensemble_signal)
    def get_status() -> Dict
    def get_performance_metrics() -> Dict
    def update_configuration(config)
```

---

## Implementation Plan

### Day 1: Signal Validator
- Confidence thresholds
- Agreement requirements
- Regime filtering
- Unit tests

### Day 2: Position Sizer
- Kelly criterion
- Confidence scaling
- Risk limits
- Unit tests

### Day 3: Execution Manager
- Order generation
- Position tracking
- PnL calculation
- Unit tests

### Day 4: Meta-Learner (Basic)
- Performance tracking
- Simple weight updates
- EMA-based learning
- Unit tests

### Day 5: Orchestrator Integration
- Connect all components
- End-to-end flow
- Integration tests

### Day 6: Meta-Learner (Advanced)
- Contextual bandits
- Regime-aware learning
- Bayesian optimization

### Day 7: Testing & Documentation
- Full system tests
- Performance benchmarks
- Documentation
- Demo scripts

---

## Key Design Decisions

### 1. Signal Validation Strategy

**Decision:** Multi-stage validation with configurable thresholds

**Rationale:**
- Prevents low-quality signals from executing
- Reduces false positives
- Adaptable to different market conditions

### 2. Meta-Learning Approach

**Decision:** Start with simple EMA, add complexity incrementally

**Rationale:**
- Simple methods often work best
- Easy to debug and understand
- Can add sophistication later

### 3. Position Sizing Method

**Decision:** Kelly Criterion with confidence scaling

**Rationale:**
- Mathematically optimal for long-term growth
- Naturally incorporates signal confidence
- Well-studied in trading literature

### 4. Performance Tracking

**Decision:** Track per-agent and per-regime performance

**Rationale:**
- Enables regime-aware weight optimization
- Identifies which agents work in which conditions
- Supports adaptive behavior

---

## Configuration

### Signal Validation Config
```yaml
signal_validation:
  min_confidence: 0.6
  min_agreement: 0.5
  cooldown_seconds: 60
  regime_filters:
    volatile:
      min_confidence: 0.8
```

### Position Sizing Config
```yaml
position_sizing:
  method: kelly_criterion
  max_position_pct: 0.1
  confidence_scaling: true
  volatility_adjustment: true
```

### Meta-Learning Config
```yaml
meta_learning:
  learning_rate: 0.01
  performance_window: 100
  update_frequency: 10
  regime_aware: true
```

---

## Success Metrics

### Signal Quality
- Validation pass rate: >70%
- Average confidence: >0.65
- Agreement score: >0.60

### Meta-Learning
- Weight convergence: <100 iterations
- Performance improvement: >10% over baseline
- Adaptation speed: <50 signals

### Position Sizing
- Kelly fraction accuracy: ±5%
- Risk limit compliance: 100%
- Drawdown control: <20%

### Overall System
- End-to-end latency: <20ms
- Throughput: >50 signals/sec
- Uptime: >99%

---

## Testing Strategy

### Unit Tests
- Each component tested independently
- Mock dependencies
- Edge cases covered

### Integration Tests
- Full pipeline testing
- Real signal processing
- Performance validation

### Simulation Tests
- Historical data replay
- Strategy backtesting
- Risk scenario testing

---

## Next Steps

1. Create base classes and interfaces
2. Implement signal validator
3. Implement position sizer
4. Implement execution manager
5. Implement basic meta-learner
6. Build orchestrator
7. Integration testing
8. Advanced meta-learning
9. Documentation

---

**Status:** Ready to begin implementation
