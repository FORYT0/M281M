"""
Orchestrator Layer for M281M Trading System.

Coordinates agents, validates signals, manages positions,
and implements meta-learning for adaptive trading.
"""

from .signal_validator import SignalValidator, ValidationResult
from .position_sizer import PositionSizer, PositionSize
from .execution_manager import ExecutionManager, Position, Trade
from .meta_learner import MetaLearner, AgentPerformance
from .orchestrator import TradingOrchestrator

__all__ = [
    'SignalValidator',
    'ValidationResult',
    'PositionSizer',
    'PositionSize',
    'ExecutionManager',
    'Position',
    'Trade',
    'MetaLearner',
    'AgentPerformance',
    'TradingOrchestrator'
]
