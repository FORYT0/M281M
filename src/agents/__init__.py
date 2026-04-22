"""
Multi-Agent AI Core for M281M Trading System.

Agents:
- RegimeClassifier: HMM-based market regime detection
- MomentumAgent: LSTM-based momentum prediction
- MeanReversionAgent: XGBoost-based mean reversion detection
- OrderFlowAgent: DQN-based order flow analysis

Integration:
- AgentRegistry: Centralized agent management
- AgentEnsemble: Multi-agent signal aggregation
"""

from .base_agent import BaseAgent, AgentSignal, AgentRegistry

# Try to import agents, but handle missing dependencies gracefully
try:
    from .regime_classifier import RegimeClassifier
except ImportError:
    RegimeClassifier = None

try:
    from .momentum_agent import MomentumAgent
except ImportError:
    MomentumAgent = None

try:
    from .mean_reversion_agent import MeanReversionAgent
except ImportError:
    MeanReversionAgent = None

try:
    from .order_flow_agent import OrderFlowAgent
except ImportError:
    OrderFlowAgent = None

try:
    from .agent_ensemble import AgentEnsemble, EnsembleSignal
except ImportError:
    AgentEnsemble = None
    EnsembleSignal = None

__all__ = [
    'BaseAgent',
    'AgentSignal',
    'AgentRegistry',
    'RegimeClassifier',
    'MomentumAgent',
    'MeanReversionAgent',
    'OrderFlowAgent',
    'AgentEnsemble',
    'EnsembleSignal'
]
