"""
Backtesting Framework for M281M Trading System.

Provides tools for testing trading strategies on historical data
with realistic execution simulation and comprehensive performance analysis.
"""

from .data_loader import HistoricalDataLoader, DataSource
from .replayer import DataReplayer, ReplayEvent
from .execution_simulator import ExecutionSimulator, Fill, SlippageModel
from .performance_analyzer import PerformanceAnalyzer, PerformanceMetrics
from .backtest_engine import BacktestEngine, BacktestResult, BacktestConfig
from .visualization import BacktestVisualizer

__all__ = [
    'HistoricalDataLoader',
    'DataSource',
    'DataReplayer',
    'ReplayEvent',
    'ExecutionSimulator',
    'Fill',
    'SlippageModel',
    'PerformanceAnalyzer',
    'PerformanceMetrics',
    'BacktestEngine',
    'BacktestResult',
    'BacktestConfig',
    'BacktestVisualizer'
]
