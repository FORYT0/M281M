"""
Backtest Demo - Demonstrates the complete backtesting framework.
Tests a simple moving average crossover strategy.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, timedelta
import numpy as np

from src.backtest import (
    BacktestEngine,
    BacktestConfig,
    DataSource,
    SlippageModel,
    BacktestVisualizer
)


def moving_average_strategy(window_fast=9, window_slow=21):
    """
    Simple moving average crossover strategy.
    
    Args:
        window_fast: Fast MA period
        window_slow: Slow MA period
    
    Returns:
        Strategy function
    """
    # State
    prices = []
    position = None
    
    def strategy(event):
        nonlocal position
        
        # Extract price
        price = event.data['close']
        prices.append(price)
        
        # Need enough data
        if len(prices) < window_slow:
            return None
        
        # Calculate MAs
        ma_fast = np.mean(prices[-window_fast:])
        ma_slow = np.mean(prices[-window_slow:])
        
        # Generate signals
        if ma_fast > ma_slow and position != 'long':
            # Bullish crossover
            position = 'long'
            return {
                'direction': 'long',
                'size': 0.1,  # 0.1 BTC
                'reason': f'MA crossover: {ma_fast:.2f} > {ma_slow:.2f}'
            }
        
        elif ma_fast < ma_slow and position != 'short':
            # Bearish crossover
            position = 'short'
            return {
                'direction': 'short',
                'size': 0.1,
                'reason': f'MA crossover: {ma_fast:.2f} < {ma_slow:.2f}'
            }
        
        return None
    
    return strategy


def rsi_strategy(period=14, oversold=30, overbought=70):
    """
    RSI mean reversion strategy.
    
    Args:
        period: RSI period
        oversold: Oversold threshold
        overbought: Overbought threshold
    
    Returns:
        Strategy function
    """
    prices = []
    position = None
    
    def calculate_rsi(prices, period):
        """Calculate RSI."""
        if len(prices) < period + 1:
            return 50
        
        deltas = np.diff(prices[-period-1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def strategy(event):
        nonlocal position
        
        price = event.data['close']
        prices.append(price)
        
        if len(prices) < period + 1:
            return None
        
        rsi = calculate_rsi(prices, period)
        
        # Generate signals
        if rsi < oversold and position != 'long':
            # Oversold - buy
            position = 'long'
            return {
                'direction': 'long',
                'size': 0.1,
                'reason': f'RSI oversold: {rsi:.1f}'
            }
        
        elif rsi > overbought and position != 'short':
            # Overbought - sell
            position = 'short'
            return {
                'direction': 'short',
                'size': 0.1,
                'reason': f'RSI overbought: {rsi:.1f}'
            }
        
        return None
    
    return strategy


def run_simple_backtest():
    """Run a simple backtest with MA crossover strategy."""
    print("=" * 70)
    print("SIMPLE BACKTEST DEMO")
    print("=" * 70)
    
    # Create engine
    engine = BacktestEngine(data_dir="data/historical")
    
    # Configure backtest
    config = BacktestConfig(
        symbol="BTCUSDT",
        start_date=datetime.now() - timedelta(days=180),
        end_date=datetime.now(),
        timeframe="1h",
        data_source=DataSource.SYNTHETIC,  # Use synthetic data
        initial_balance=10000.0,
        slippage_model=SlippageModel.VOLUME_BASED,
        base_slippage_bps=2.0,
        commission_rate=0.001,
        latency_mean_ms=50.0
    )
    
    # Create strategy
    strategy = moving_average_strategy(window_fast=9, window_slow=21)
    
    # Run backtest
    result = engine.run_backtest(strategy, config)
    
    # Visualize
    print("\nGenerating visualizations...")
    visualizer = BacktestVisualizer()
    visualizer.save_all_charts(result, output_dir="backtest_results/ma_crossover")
    
    return result


def run_strategy_comparison():
    """Compare multiple strategies."""
    print("\n" + "=" * 70)
    print("STRATEGY COMPARISON")
    print("=" * 70)
    
    engine = BacktestEngine(data_dir="data/historical")
    
    # Base config
    base_config = BacktestConfig(
        symbol="BTCUSDT",
        start_date=datetime.now() - timedelta(days=180),
        end_date=datetime.now(),
        timeframe="1h",
        data_source=DataSource.SYNTHETIC,
        initial_balance=10000.0
    )
    
    # Test different strategies
    strategies = [
        ("MA(9,21)", moving_average_strategy(9, 21)),
        ("MA(5,15)", moving_average_strategy(5, 15)),
        ("RSI(14)", rsi_strategy(14, 30, 70)),
        ("RSI(7)", rsi_strategy(7, 25, 75))
    ]
    
    results = []
    
    for name, strategy in strategies:
        print(f"\nTesting {name}...")
        result = engine.run_backtest(strategy, base_config)
        results.append((name, result))
    
    # Compare results
    print("\n" + "=" * 70)
    print("COMPARISON SUMMARY")
    print("=" * 70)
    
    comparison_data = []
    for name, result in results:
        m = result.metrics
        comparison_data.append({
            'Strategy': name,
            'Return': f"{m.total_return:+.2%}",
            'Sharpe': f"{m.sharpe_ratio:.2f}",
            'Max DD': f"{m.max_drawdown:.2%}",
            'Win Rate': f"{m.win_rate:.2%}",
            'Trades': m.total_trades
        })
    
    # Print comparison table
    import pandas as pd
    df = pd.DataFrame(comparison_data)
    print("\n" + df.to_string(index=False))
    
    return results


def run_parameter_optimization():
    """Optimize strategy parameters."""
    print("\n" + "=" * 70)
    print("PARAMETER OPTIMIZATION")
    print("=" * 70)
    
    engine = BacktestEngine(data_dir="data/historical")
    
    config = BacktestConfig(
        symbol="BTCUSDT",
        start_date=datetime.now() - timedelta(days=180),
        end_date=datetime.now(),
        timeframe="1h",
        data_source=DataSource.SYNTHETIC,
        initial_balance=10000.0
    )
    
    # Test different MA periods
    best_sharpe = -999
    best_params = None
    best_result = None
    
    print("\nTesting MA crossover parameters...")
    
    for fast in [5, 7, 9, 12]:
        for slow in [15, 21, 30, 50]:
            if fast >= slow:
                continue
            
            strategy = moving_average_strategy(fast, slow)
            result = engine.run_backtest(strategy, config)
            
            sharpe = result.metrics.sharpe_ratio
            print(f"  MA({fast},{slow}): Sharpe={sharpe:.2f}, Return={result.metrics.total_return:+.2%}")
            
            if sharpe > best_sharpe:
                best_sharpe = sharpe
                best_params = (fast, slow)
                best_result = result
    
    print(f"\n✓ Best parameters: MA({best_params[0]},{best_params[1]})")
    print(f"  Sharpe Ratio: {best_sharpe:.2f}")
    print(f"  Total Return: {best_result.metrics.total_return:+.2%}")
    
    # Visualize best result
    visualizer = BacktestVisualizer()
    visualizer.save_all_charts(best_result, output_dir="backtest_results/optimized")
    
    return best_result


def main():
    """Main demo function."""
    print("\n" + "=" * 70)
    print("M281M BACKTESTING FRAMEWORK DEMO")
    print("=" * 70)
    print("\nThis demo will:")
    print("1. Run a simple MA crossover backtest")
    print("2. Compare multiple strategies")
    print("3. Optimize strategy parameters")
    print("\n" + "=" * 70)
    
    try:
        # 1. Simple backtest
        result1 = run_simple_backtest()
        
        # 2. Strategy comparison
        results2 = run_strategy_comparison()
        
        # 3. Parameter optimization
        result3 = run_parameter_optimization()
        
        print("\n" + "=" * 70)
        print("DEMO COMPLETE!")
        print("=" * 70)
        print("\nResults saved to:")
        print("  - backtest_results/ma_crossover/")
        print("  - backtest_results/optimized/")
        print("\nCheck the HTML reports for detailed analysis!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
