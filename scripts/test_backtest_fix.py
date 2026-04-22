"""
Test script to validate backtest position tracking fixes.
Tests simple scenarios to ensure PnL calculations are correct.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.backtest.backtest_engine import BacktestEngine, BacktestConfig
from src.backtest.data_loader import DataSource


def create_simple_data(start_price=100, trend='up', periods=10):
    """Create simple synthetic data for testing."""
    dates = [datetime(2024, 1, 1) + timedelta(hours=i) for i in range(periods)]
    
    if trend == 'up':
        # Price goes up steadily
        prices = [start_price + i * 10 for i in range(periods)]
    elif trend == 'down':
        # Price goes down steadily
        prices = [start_price - i * 10 for i in range(periods)]
    elif trend == 'flat':
        # Price stays flat
        prices = [start_price] * periods
    else:
        # Oscillating
        prices = [start_price + (10 if i % 2 == 0 else -10) for i in range(periods)]
    
    data = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': [p * 1.01 for p in prices],
        'low': [p * 0.99 for p in prices],
        'close': prices,
        'volume': [1000000] * periods  # 1M volume to avoid excessive slippage
    })
    
    return data


def test_simple_long_profit():
    """Test 1: Simple long position with profit."""
    print("\n" + "="*60)
    print("TEST 1: Simple Long Position (Profit)")
    print("="*60)
    print("Scenario: Buy at 100, sell at 190")
    print("Expected: ~90% return (minus fees)")
    
    # Create uptrend data
    data = create_simple_data(start_price=100, trend='up', periods=10)
    
    # Save to CSV with correct naming convention
    os.makedirs('data/historical', exist_ok=True)
    data.to_csv('data/historical/synthetic_test_long_1h.csv', index=False)
    
    # Simple buy and hold strategy
    signal_sent = False
    def strategy(event):
        nonlocal signal_sent
        if not signal_sent:
            signal_sent = True
            return {'direction': 'long', 'size': 90.0}  # Buy 90 units
        return None
    
    # Run backtest
    engine = BacktestEngine()
    config = BacktestConfig(
        symbol='test_long',
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 2),
        initial_balance=10000.0,
        commission_rate=0.001
    )
    
    result = engine.run_backtest(strategy, config)
    
    # Validate
    print(f"\nValidation:")
    print(f"  Initial: ${result.metrics.initial_balance:,.2f}")
    print(f"  Final:   ${result.metrics.final_balance:,.2f}")
    print(f"  Return:  {result.metrics.total_return:+.2%}")
    print(f"  Trades:  {result.metrics.total_trades}")
    
    # Expected: bought 90 units at 100, sold at 190
    # PnL should be 90 * 90 = 8100 (minus fees)
    expected_return = 0.75  # ~75% after fees
    actual_return = result.metrics.total_return
    
    if actual_return > expected_return:
        print(f"  [PASS]: Return {actual_return:.2%} > {expected_return:.2%}")
        return True
    else:
        print(f"  [FAIL]: Return {actual_return:.2%} < {expected_return:.2%}")
        return False


def test_simple_short_profit():
    """Test 2: Simple short position with profit."""
    print("\n" + "="*60)
    print("TEST 2: Simple Short Position (Profit)")
    print("="*60)
    print("Scenario: Short at 100, cover at 10")
    print("Expected: ~90% return (minus fees)")
    
    # Create downtrend data
    data = create_simple_data(start_price=100, trend='down', periods=10)
    data.to_csv('data/historical/synthetic_test_short_1h.csv', index=False)
    
    # Simple short and hold strategy
    signal_sent = False
    def strategy(event):
        nonlocal signal_sent
        if not signal_sent:
            signal_sent = True
            return {'direction': 'short', 'size': 100.0}
        return None
    
    # Run backtest
    engine = BacktestEngine()
    config = BacktestConfig(
        symbol='test_short',
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 2),
        initial_balance=10000.0,
        commission_rate=0.001
    )
    
    result = engine.run_backtest(strategy, config)
    
    # Validate
    print(f"\nValidation:")
    print(f"  Initial: ${result.metrics.initial_balance:,.2f}")
    print(f"  Final:   ${result.metrics.final_balance:,.2f}")
    print(f"  Return:  {result.metrics.total_return:+.2%}")
    print(f"  Trades:  {result.metrics.total_trades}")
    
    # Expected: shorted 100 at 100, covered at 10
    # PnL should be 100 * 90 = 9000 (minus fees)
    expected_return = 0.85  # ~85% after fees
    actual_return = result.metrics.total_return
    
    if actual_return > expected_return:
        print(f"  [PASS]: Return {actual_return:.2%} > {expected_return:.2%}")
        return True
    else:
        print(f"  [FAIL]: Return {actual_return:.2%} < {expected_return:.2%}")
        return False


def test_long_loss():
    """Test 3: Long position with loss."""
    print("\n" + "="*60)
    print("TEST 3: Long Position (Loss)")
    print("="*60)
    print("Scenario: Buy at 100, sell at 10")
    print("Expected: ~-90% return")
    
    # Create downtrend data
    data = create_simple_data(start_price=100, trend='down', periods=10)
    data.to_csv('data/historical/synthetic_test_long_loss_1h.csv', index=False)
    
    # Buy and hold in downtrend
    signal_sent = False
    def strategy(event):
        nonlocal signal_sent
        if not signal_sent:
            signal_sent = True
            return {'direction': 'long', 'size': 90.0}
        return None
    
    # Run backtest
    engine = BacktestEngine()
    config = BacktestConfig(
        symbol='test_long_loss',
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 2),
        initial_balance=10000.0,
        commission_rate=0.001
    )
    
    result = engine.run_backtest(strategy, config)
    
    # Validate
    print(f"\nValidation:")
    print(f"  Initial: ${result.metrics.initial_balance:,.2f}")
    print(f"  Final:   ${result.metrics.final_balance:,.2f}")
    print(f"  Return:  {result.metrics.total_return:+.2%}")
    print(f"  Trades:  {result.metrics.total_trades}")
    
    # Should lose money
    if result.metrics.total_return < -0.75:  # Lost at least 75%
        print(f"  [PASS]: Lost money as expected")
        return True
    else:
        print(f"  [FAIL]: Should have lost ~80%")
        return False


def test_balance_conservation():
    """Test 4: Balance conservation (no trades)."""
    print("\n" + "="*60)
    print("TEST 4: Balance Conservation")
    print("="*60)
    print("Scenario: No trades executed")
    print("Expected: Balance unchanged")
    
    # Create any data
    data = create_simple_data(start_price=100, trend='up', periods=10)
    data.to_csv('data/historical/synthetic_test_notrade_1h.csv', index=False)
    
    # Never trade strategy
    def strategy(event):
        return None
    
    # Run backtest
    engine = BacktestEngine()
    config = BacktestConfig(
        symbol='test_notrade',
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 2),
        initial_balance=10000.0,
        commission_rate=0.001
    )
    
    result = engine.run_backtest(strategy, config)
    
    # Validate
    print(f"\nValidation:")
    print(f"  Initial: ${result.metrics.initial_balance:,.2f}")
    print(f"  Final:   ${result.metrics.final_balance:,.2f}")
    print(f"  Return:  {result.metrics.total_return:+.2%}")
    print(f"  Trades:  {result.metrics.total_trades}")
    
    # Balance should be exactly the same
    if abs(result.metrics.total_return) < 0.0001:
        print(f"  [PASS]: Balance unchanged")
        return True
    else:
        print(f"  [FAIL]: Balance should be unchanged")
        return False


if __name__ == '__main__':
    print("\n" + "="*60)
    print("BACKTEST POSITION TRACKING VALIDATION")
    print("="*60)
    print("Testing fixed position tracking logic...")
    
    results = []
    
    # Run all tests
    results.append(("Simple Long Profit", test_simple_long_profit()))
    results.append(("Simple Short Profit", test_simple_short_profit()))
    results.append(("Long Loss", test_long_loss()))
    results.append(("Balance Conservation", test_balance_conservation()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nAll tests passed! Position tracking is fixed.")
    else:
        print(f"\n{total - passed} test(s) failed. Review the output above.")
