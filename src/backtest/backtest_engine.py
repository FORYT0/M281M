"""
Backtest Engine - Main backtesting orchestration.
Runs complete backtests with all components integrated.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from dataclasses import dataclass, field
import uuid

from .data_loader import HistoricalDataLoader, DataSource
from .replayer import DataReplayer, ReplayEvent, EventType
from .execution_simulator import ExecutionSimulator, SlippageModel, Fill
from .performance_analyzer import PerformanceAnalyzer, PerformanceMetrics


@dataclass
class BacktestConfig:
    """Configuration for backtest."""
    
    # Data
    symbol: str
    start_date: datetime
    end_date: datetime
    timeframe: str = "1h"
    data_source: DataSource = DataSource.CSV
    
    # Initial conditions
    initial_balance: float = 10000.0
    
    # Execution
    slippage_model: SlippageModel = SlippageModel.VOLUME_BASED
    base_slippage_bps: float = 2.0
    commission_rate: float = 0.001
    latency_mean_ms: float = 50.0
    
    # Replay
    replay_speed: float = 0.0  # 0 = max speed
    
    # Analysis
    risk_free_rate: float = 0.02
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'symbol': self.symbol,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'timeframe': self.timeframe,
            'initial_balance': self.initial_balance,
            'slippage_model': self.slippage_model.value,
            'base_slippage_bps': self.base_slippage_bps,
            'commission_rate': self.commission_rate,
            'latency_mean_ms': self.latency_mean_ms,
            'risk_free_rate': self.risk_free_rate
        }


@dataclass
class BacktestResult:
    """Results from a backtest run."""
    
    config: BacktestConfig
    metrics: PerformanceMetrics
    equity_curve: pd.Series
    trades: List[Dict[str, Any]]
    signals: List[Dict[str, Any]] = field(default_factory=list)
    execution_stats: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'config': self.config.to_dict(),
            'metrics': self.metrics.to_dict(),
            'trades': self.trades,
            'signals': self.signals,
            'execution_stats': self.execution_stats
        }
    
    def summary(self) -> str:
        """Generate text summary."""
        m = self.metrics
        
        summary = f"""
{'='*60}
BACKTEST SUMMARY
{'='*60}

Period: {m.start_date.date()} to {m.end_date.date()} ({m.total_days} days)
Symbol: {self.config.symbol}

RETURNS
-------
Total Return:      {m.total_return:+.2%}
Annualized Return: {m.annualized_return:+.2%}
Initial Balance:   ${m.initial_balance:,.2f}
Final Balance:     ${m.final_balance:,.2f}

RISK METRICS
------------
Sharpe Ratio:      {m.sharpe_ratio:.2f}
Sortino Ratio:     {m.sortino_ratio:.2f}
Calmar Ratio:      {m.calmar_ratio:.2f}
Max Drawdown:      {m.max_drawdown:.2%}
Recovery Factor:   {m.recovery_factor:.2f}

TRADE STATISTICS
----------------
Total Trades:      {m.total_trades}
Win Rate:          {m.win_rate:.2%}
Profit Factor:     {m.profit_factor:.2f}
Avg Win:           ${m.avg_win:+,.2f}
Avg Loss:          ${m.avg_loss:+,.2f}
Largest Win:       ${m.largest_win:+,.2f}
Largest Loss:      ${m.largest_loss:+,.2f}

{'='*60}
"""
        return summary


class BacktestEngine:
    """
    Main backtesting engine.
    
    Orchestrates:
    - Data loading
    - Event replay
    - Strategy execution
    - Performance analysis
    """
    
    def __init__(self, data_dir: str = "data/historical"):
        """
        Initialize backtest engine.
        
        Args:
            data_dir: Directory containing historical data
        """
        self.data_loader = HistoricalDataLoader(data_dir)
    
    def run_backtest(
        self,
        strategy_func: Callable[[ReplayEvent], Optional[Dict[str, Any]]],
        config: BacktestConfig
    ) -> BacktestResult:
        """
        Run a complete backtest.
        
        Args:
            strategy_func: Function that takes ReplayEvent and returns signal dict
                          Signal dict should have: {'direction': 'long'/'short', 'size': float}
            config: Backtest configuration
        
        Returns:
            BacktestResult with all metrics and data
        """
        print(f"\n{'='*60}")
        print(f"Starting Backtest: {config.symbol}")
        print(f"{'='*60}")
        print(f"Period: {config.start_date.date()} to {config.end_date.date()}")
        print(f"Initial Balance: ${config.initial_balance:,.2f}")
        print(f"{'='*60}\n")
        
        # Load data
        print("Loading historical data...")
        data = self.data_loader.load_ohlcv(
            symbol=config.symbol,
            start_date=config.start_date,
            end_date=config.end_date,
            timeframe=config.timeframe,
            source=config.data_source
        )
        
        # Validate data
        validation = self.data_loader.validate_data(data, data_type='ohlcv')
        if not validation.is_valid:
            raise ValueError(f"Data validation failed: {validation.errors}")
        
        print(f"OK Loaded {len(data)} candles")
        print(f"  Date range: {validation.date_range[0]} to {validation.date_range[1]}")
        
        # Initialize components
        execution_sim = ExecutionSimulator(
            slippage_model=config.slippage_model,
            base_slippage_bps=config.base_slippage_bps,
            commission_rate=config.commission_rate,
            latency_mean_ms=config.latency_mean_ms
        )
        
        replayer = DataReplayer(
            speed=config.replay_speed,
            start_date=config.start_date,
            end_date=config.end_date
        )
        
        # State tracking
        balance = config.initial_balance
        position = 0.0  # Current position size
        equity_history = []
        trades = []
        signals = []
        entry_price = 0.0
        entry_time = None
        
        # Event handler
        def on_event(event: ReplayEvent):
            nonlocal balance, position, entry_price, entry_time
            
            # Get current price
            current_price = event.data['close']
            
            # Calculate unrealized PnL correctly
            if position > 0:
                # Long position: profit when price goes up
                unrealized_pnl = position * (current_price - entry_price)
            elif position < 0:
                # Short position: profit when price goes down
                unrealized_pnl = abs(position) * (entry_price - current_price)
            else:
                unrealized_pnl = 0
            
            current_equity = balance + unrealized_pnl
            
            equity_history.append({
                'timestamp': event.timestamp,
                'equity': current_equity,
                'balance': balance,
                'position': position,
                'price': current_price
            })
            
            # Call strategy
            signal = strategy_func(event)
            
            if signal:
                signals.append({
                    'timestamp': event.timestamp,
                    'signal': signal,
                    'price': current_price
                })
                
                # Execute signal
                direction = signal.get('direction')
                size = signal.get('size', 0)
                
                if direction and size > 0:
                    # Determine order side and size
                    if direction == 'long' and position <= 0:
                        # Open long or close short then open long
                        side = 'buy'
                        order_size = size if position == 0 else size + abs(position)
                    elif direction == 'short' and position >= 0:
                        # Open short or close long then open short
                        side = 'sell'
                        order_size = size if position == 0 else size + abs(position)
                    else:
                        # Already in desired position
                        return
                    
                    # Check if we have enough balance for long positions
                    if side == 'buy' and position == 0:
                        max_size = balance / current_price * 0.95  # 95% to leave room for fees
                        order_size = min(order_size, max_size)
                        if order_size <= 0:
                            return  # Not enough balance
                    
                    # Simulate execution
                    fill = execution_sim.simulate_execution(
                        order_id=str(uuid.uuid4()),
                        symbol=config.symbol,
                        side=side,
                        size=order_size,
                        price=current_price,
                        market_state={'volume': event.data.get('volume', 100)}
                    )
                    
                    # Update position and balance
                    if side == 'buy':
                        # Close short position if exists
                        if position < 0:
                            # PnL from closing short: we shorted at entry_price, buying back at fill.filled_price
                            pnl = (entry_price - fill.filled_price) * abs(position)
                            balance += pnl
                            
                            trades.append({
                                'entry_time': entry_time,
                                'exit_time': event.timestamp,
                                'side': 'short',
                                'size': abs(position),
                                'entry_price': entry_price,
                                'exit_price': fill.filled_price,
                                'pnl': pnl,
                                'commission': fill.commission
                            })
                            
                            # Deduct commission for closing
                            balance -= fill.commission
                            
                            # Calculate remaining size for new long
                            remaining_size = fill.filled_size - abs(position)
                            if remaining_size > 0:
                                # Open new long with remaining size
                                position = remaining_size
                                entry_price = fill.filled_price
                                entry_time = event.timestamp
                                # Deduct cost of long position
                                balance -= remaining_size * fill.filled_price
                            else:
                                position = 0
                        else:
                            # Open new long position
                            position = fill.filled_size
                            entry_price = fill.filled_price
                            entry_time = event.timestamp
                            # Deduct cost of buying + commission
                            balance -= fill.filled_size * fill.filled_price
                            balance -= fill.commission
                        
                    else:  # sell
                        # Close long position if exists
                        if position > 0:
                            # PnL from closing long: we bought at entry_price, selling at fill.filled_price
                            pnl = (fill.filled_price - entry_price) * position
                            
                            # Add back the original cost + PnL
                            balance += position * entry_price  # Original cost
                            balance += pnl  # Profit/loss
                            
                            trades.append({
                                'entry_time': entry_time,
                                'exit_time': event.timestamp,
                                'side': 'long',
                                'size': position,
                                'entry_price': entry_price,
                                'exit_price': fill.filled_price,
                                'pnl': pnl,
                                'commission': fill.commission
                            })
                            
                            # Deduct commission for closing
                            balance -= fill.commission
                            
                            # Calculate remaining size for new short
                            remaining_size = fill.filled_size - position
                            if remaining_size > 0:
                                # Open new short with remaining size
                                position = -remaining_size
                                entry_price = fill.filled_price
                                entry_time = event.timestamp
                                # Add proceeds from shorting
                                balance += remaining_size * fill.filled_price
                            else:
                                position = 0
                        else:
                            # Open new short position
                            position = -fill.filled_size
                            entry_price = fill.filled_price
                            entry_time = event.timestamp
                            # Add proceeds from shorting - commission
                            balance += fill.filled_size * fill.filled_price
                            balance -= fill.commission
        
        # Run replay
        print("\nRunning backtest...")
        replayer.replay(
            data=data,
            callback=on_event,
            symbol=config.symbol,
            event_type=EventType.OHLCV
        )
        
        # Close any open position at end
        if position != 0:
            final_price = data.iloc[-1]['close']
            
            if position > 0:
                # Close long: sell at final price
                pnl = (final_price - entry_price) * position
                # Return original cost + PnL
                balance += position * entry_price  # Original cost
                balance += pnl  # Profit/loss
            else:
                # Close short: buy back at final price
                pnl = (entry_price - final_price) * abs(position)
                balance += pnl
                # Short proceeds were already added when position opened
            
            trades.append({
                'entry_time': entry_time,
                'exit_time': data.iloc[-1]['timestamp'],
                'side': 'long' if position > 0 else 'short',
                'size': abs(position),
                'entry_price': entry_price,
                'exit_price': final_price,
                'pnl': pnl,
                'commission': 0
            })
            
            position = 0
            
            # Add final equity point after closing position
            equity_history.append({
                'timestamp': data.iloc[-1]['timestamp'],
                'equity': balance,  # No unrealized PnL since position is closed
                'balance': balance,
                'position': 0,
                'price': final_price
            })
        
        # Create equity curve
        equity_df = pd.DataFrame(equity_history)
        equity_curve = equity_df.set_index('timestamp')['equity']
        
        # Analyze performance
        print("\nAnalyzing performance...")
        analyzer = PerformanceAnalyzer(risk_free_rate=config.risk_free_rate)
        metrics = analyzer.analyze(
            equity_curve=equity_curve,
            trades=trades,
            initial_balance=config.initial_balance
        )
        
        # Get execution stats
        execution_stats = execution_sim.get_stats()
        
        # Create result
        result = BacktestResult(
            config=config,
            metrics=metrics,
            equity_curve=equity_curve,
            trades=trades,
            signals=signals,
            execution_stats=execution_stats
        )
        
        # Print summary
        print(result.summary())
        
        return result
    
    def run_multiple_backtests(
        self,
        strategy_func: Callable,
        configs: List[BacktestConfig]
    ) -> List[BacktestResult]:
        """
        Run multiple backtests with different configurations.
        
        Args:
            strategy_func: Strategy function
            configs: List of backtest configurations
        
        Returns:
            List of BacktestResults
        """
        results = []
        
        for i, config in enumerate(configs):
            print(f"\n{'='*60}")
            print(f"Backtest {i+1}/{len(configs)}")
            print(f"{'='*60}")
            
            result = self.run_backtest(strategy_func, config)
            results.append(result)
        
        return results
    
    def compare_results(self, results: List[BacktestResult]) -> pd.DataFrame:
        """
        Compare multiple backtest results.
        
        Args:
            results: List of backtest results
        
        Returns:
            DataFrame with comparison metrics
        """
        comparison = []
        
        for i, result in enumerate(results):
            m = result.metrics
            comparison.append({
                'backtest': f"Backtest {i+1}",
                'symbol': result.config.symbol,
                'total_return': m.total_return,
                'annualized_return': m.annualized_return,
                'sharpe_ratio': m.sharpe_ratio,
                'max_drawdown': m.max_drawdown,
                'win_rate': m.win_rate,
                'profit_factor': m.profit_factor,
                'total_trades': m.total_trades
            })
        
        return pd.DataFrame(comparison)
