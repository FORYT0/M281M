"""
Debug script to trace through a simple backtest step by step.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from datetime import datetime, timedelta

# Create simple data: price goes from 100 to 110
dates = [datetime(2024, 1, 1) + timedelta(hours=i) for i in range(2)]
prices = [100, 110]

data = pd.DataFrame({
    'timestamp': dates,
    'open': prices,
    'high': [p * 1.01 for p in prices],
    'low': [p * 0.99 for p in prices],
    'close': prices,
    'volume': [1000000] * 2  # 1M volume
})

os.makedirs('data/historical', exist_ok=True)
data.to_csv('data/historical/synthetic_debug_1h.csv', index=False)

# Manual simulation
print("="*60)
print("MANUAL BACKTEST SIMULATION")
print("="*60)
print("\nScenario: Buy 10 units at $100, sell at $110")
print("Expected PnL: 10 * ($110 - $100) = $100")
print("Expected final balance: $10,000 + $100 - fees = ~$10,098")

balance = 10000.0
position = 0
entry_price = 0

print(f"\nInitial state:")
print(f"  Balance: ${balance:,.2f}")
print(f"  Position: {position}")

# Event 1: Buy at 100
print(f"\nEvent 1: Price = $100")
print(f"  Action: Buy 10 units")

buy_size = 10.0
buy_price = 100.0
commission = buy_size * buy_price * 0.001

print(f"  Cost: {buy_size} * ${buy_price} = ${buy_size * buy_price:,.2f}")
print(f"  Commission: ${commission:,.2f}")

balance -= buy_size * buy_price
balance -= commission
position = buy_size
entry_price = buy_price

print(f"  New balance: ${balance:,.2f}")
print(f"  New position: {position}")
print(f"  Entry price: ${entry_price}")

# Event 2: Sell at 110
print(f"\nEvent 2: Price = $110")
print(f"  Action: Sell {position} units")

sell_price = 110.0
pnl = (sell_price - entry_price) * position
proceeds = position * sell_price
commission = proceeds * 0.001

print(f"  PnL: {position} * (${sell_price} - ${entry_price}) = ${pnl:,.2f}")
print(f"  Proceeds: {position} * ${sell_price} = ${proceeds:,.2f}")
print(f"  Commission: ${commission:,.2f}")

# Method 1: Add back cost + PnL
balance_method1 = balance + (position * entry_price) + pnl - commission
print(f"\n  Method 1 (cost + PnL): ${balance} + ${position * entry_price} + ${pnl} - ${commission} = ${balance_method1:,.2f}")

# Method 2: Add proceeds
balance_method2 = balance + proceeds - commission
print(f"  Method 2 (proceeds): ${balance} + ${proceeds} - ${commission} = ${balance_method2:,.2f}")

print(f"\n  Both methods should give same result: {abs(balance_method1 - balance_method2) < 0.01}")

# Now run actual backtest
print("\n" + "="*60)
print("ACTUAL BACKTEST")
print("="*60)

from src.backtest.backtest_engine import BacktestEngine, BacktestConfig

signal_sent = False
def strategy(event):
    global signal_sent
    if not signal_sent:
        signal_sent = True
        return {'direction': 'long', 'size': 10.0}
    return None

engine = BacktestEngine()
config = BacktestConfig(
    symbol='debug',
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 2),
    initial_balance=10000.0,
    commission_rate=0.001
)

result = engine.run_backtest(strategy, config)

print(f"\nComparison:")
print(f"  Expected: ${balance_method1:,.2f}")
print(f"  Actual:   ${result.metrics.final_balance:,.2f}")
print(f"  Difference: ${result.metrics.final_balance - balance_method1:,.2f}")

if abs(result.metrics.final_balance - balance_method1) < 1.0:
    print("\n[PASS] Backtest matches manual calculation!")
else:
    print("\n[FAIL] Backtest does not match manual calculation")
    print("\nTrades:")
    for trade in result.trades:
        print(f"  {trade}")
