# Risk Management Quick Start

## Installation

No additional dependencies required. Risk management is built into the system.

## Basic Usage

```python
from src.risk import RiskManager, RiskConfig

# Initialize with default config
risk_manager = RiskManager(
    config=RiskConfig(),
    initial_capital=10000
)

# Check an order
decision = risk_manager.check_order(
    order={'symbol': 'BTCUSDT', 'side': 'long', 'size': 0.1},
    market_data={'price': 50000, 'atr': 1000},
    portfolio_state={'balance': 10000, 'positions': {}},
    regime='trending'
)

# Execute if approved
if decision.approved:
    execute_trade(decision.adjusted_size)
```

## Risk Profiles

### Conservative
```python
config = RiskConfig.conservative()
# 1% position size, 70% exposure, 3% drawdown limit
```

### Aggressive
```python
config = RiskConfig.aggressive()
# 5% position size, 100% exposure, 10% drawdown limit
```

### Custom
```python
config = RiskConfig(
    max_position_size=0.5,
    max_portfolio_exposure=0.80,
    max_daily_drawdown_pct=0.05,
    min_risk_reward_ratio=2.0
)
```

## Decision Object

```python
decision.approved          # bool: Order approved?
decision.risk_level        # LOW, MEDIUM, HIGH, CRITICAL
decision.adjusted_size     # float: Adjusted position size
decision.stop_loss         # float: Recommended stop loss
decision.take_profit       # float: Recommended take profit
decision.reasons           # List[str]: Rejection reasons
decision.warnings          # List[str]: Warnings
```

## Recording Trades

```python
# After trade execution
risk_manager.record_trade({
    'symbol': 'BTCUSDT',
    'pnl': 150.0
})

# Update portfolio
risk_manager.update_portfolio({
    'balance': 10150,
    'positions': {...}
})
```

## Statistics

```python
stats = risk_manager.get_statistics()

print(f"Approval rate: {stats['approval_rate']:.1%}")
print(f"Rejected: {stats['rejected_orders']}")
print(f"Circuit breaker: {stats['meta_risk']['circuit_breaker_active']}")
```

## Daily Reset

```python
# Reset at start of trading day
risk_manager.reset_daily_limits()
```

## Configuration Parameters

### Trade-Level
- `max_position_size`: 1.0
- `min_risk_reward_ratio`: 1.5
- `max_slippage_bps`: 10.0
- `stop_loss_atr_multiplier`: 2.0
- `take_profit_atr_multiplier`: 3.0

### Portfolio-Level
- `max_portfolio_exposure`: 0.95
- `max_position_concentration`: 0.30
- `max_var_pct`: 0.05

### Meta-Risk
- `max_daily_drawdown_pct`: 0.05
- `max_consecutive_losses`: 3
- `max_daily_trades`: 50

## Testing

```bash
# Run test suite
python scripts/test_risk_management.py

# Run demos
python scripts/demo_risk_management.py

# Integration demo
python scripts/demo_orchestrator_with_risk.py
```

## Common Patterns

### Pre-Trade Check
```python
decision = risk_manager.check_order(order, market_data, portfolio_state)
if not decision.approved:
    logger.warning(f"Risk check failed: {decision.reasons}")
    return

execute_trade(decision.adjusted_size)
```

### Post-Trade Recording
```python
trade_result = execute_trade(...)
risk_manager.record_trade({
    'symbol': trade_result.symbol,
    'pnl': trade_result.pnl
})
```

### Circuit Breaker Check
```python
if risk_manager.meta_risk.is_circuit_breaker_active():
    logger.warning("Circuit breaker active - pausing trading")
    return
```

### Current Risk Level
```python
risk_level = risk_manager.get_current_risk_level()
if risk_level == RiskLevel.CRITICAL:
    # Reduce position sizes or pause trading
    pass
```

## Error Handling

```python
try:
    decision = risk_manager.check_order(...)
except Exception as e:
    logger.error(f"Risk check error: {e}")
    # Reject order on error
    decision.approved = False
```

## Performance Tips

1. Reuse RiskManager instance (don't create per order)
2. Update portfolio state in batches
3. Reset daily limits at market open
4. Monitor statistics for optimization

## Troubleshooting

### Order Always Rejected
- Check risk profile (conservative vs aggressive)
- Verify portfolio state is up to date
- Check if circuit breaker is active
- Review rejection reasons in decision.reasons

### Size Always Adjusted
- Check regime-based adjustments
- Verify portfolio exposure limits
- Review position concentration limits

### Circuit Breaker Stuck
- Check consecutive losses count
- Verify daily drawdown calculation
- Manually reset if needed: `risk_manager.reset_daily_limits()`

## Documentation

- Full docs: `docs/PHASE_5_COMPLETE.md`
- Summary: `PHASE_5_COMPLETE.md`
- This guide: `docs/RISK_MANAGEMENT_QUICK_START.md`
