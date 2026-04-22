"""
Base agent interface for all trading agents.
Provides common structure and contract for agent implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import numpy as np


@dataclass
class AgentSignal:
    """
    Standardized signal output from agents.
    """
    agent_name: str
    timestamp: datetime
    symbol: str
    
    # Signal direction and strength
    direction: str  # 'long', 'short', 'neutral'
    confidence: float  # 0.0 to 1.0
    
    # Optional position sizing suggestion
    suggested_size: Optional[float] = None
    
    # Reasoning and metadata
    reasoning: Optional[Dict[str, Any]] = None
    features_used: Optional[Dict[str, float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert signal to dictionary."""
        return {
            'agent_name': self.agent_name,
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'direction': self.direction,
            'confidence': self.confidence,
            'suggested_size': self.suggested_size,
            'reasoning': self.reasoning,
            'features_used': self.features_used
        }


class BaseAgent(ABC):
    """
    Abstract base class for all trading agents.
    
    All agents must implement:
    - predict(): Generate trading signal from features
    - train(): Train the agent on historical data
    - save(): Persist model to disk
    - load(): Load model from disk
    """
    
    def __init__(self, name: str, symbol: str):
        """
        Initialize base agent.
        
        Args:
            name: Agent identifier
            symbol: Trading symbol this agent operates on
        """
        self.name = name
        self.symbol = symbol
        self.is_trained = False
        self.model = None
        
        # Performance tracking
        self.prediction_count = 0
        self.last_prediction_time = None
        
    @abstractmethod
    def predict(self, features: Dict[str, Any]) -> AgentSignal:
        """
        Generate trading signal from market features.
        
        Args:
            features: Dictionary of computed features
        
        Returns:
            AgentSignal with direction and confidence
        """
        pass
    
    @abstractmethod
    def train(self, training_data: Any) -> Dict[str, float]:
        """
        Train the agent on historical data.
        
        Args:
            training_data: Training dataset (format depends on agent type)
        
        Returns:
            Dictionary of training metrics
        """
        pass
    
    @abstractmethod
    def save(self, path: str) -> None:
        """
        Save model to disk.
        
        Args:
            path: File path to save model
        """
        pass
    
    @abstractmethod
    def load(self, path: str) -> None:
        """
        Load model from disk.
        
        Args:
            path: File path to load model from
        """
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics."""
        return {
            'name': self.name,
            'symbol': self.symbol,
            'is_trained': self.is_trained,
            'prediction_count': self.prediction_count,
            'last_prediction_time': self.last_prediction_time
        }
    
    def _update_stats(self):
        """Update internal statistics."""
        self.prediction_count += 1
        self.last_prediction_time = datetime.now()


class AgentRegistry:
    """
    Registry for managing multiple agents.
    Provides centralized access to all trading agents.
    """
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
    
    def register(self, agent: BaseAgent) -> None:
        """
        Register an agent.
        
        Args:
            agent: Agent instance to register
        """
        key = f"{agent.name}_{agent.symbol}"
        self.agents[key] = agent
    
    def get(self, name: str, symbol: str) -> Optional[BaseAgent]:
        """
        Get agent by name and symbol.
        
        Args:
            name: Agent name
            symbol: Trading symbol
        
        Returns:
            Agent instance or None
        """
        key = f"{name}_{symbol}"
        return self.agents.get(key)
    
    def get_all(self, symbol: Optional[str] = None) -> Dict[str, BaseAgent]:
        """
        Get all agents, optionally filtered by symbol.
        
        Args:
            symbol: Optional symbol filter
        
        Returns:
            Dictionary of agents
        """
        if symbol:
            return {
                k: v for k, v in self.agents.items()
                if v.symbol == symbol
            }
        return self.agents.copy()
    
    def predict_all(
        self,
        symbol: str,
        features: Dict[str, Any]
    ) -> Dict[str, AgentSignal]:
        """
        Get predictions from all agents for a symbol.
        
        Args:
            symbol: Trading symbol
            features: Market features
        
        Returns:
            Dictionary mapping agent names to signals
        """
        agents = self.get_all(symbol)
        signals = {}
        
        for key, agent in agents.items():
            if agent.is_trained:
                try:
                    signal = agent.predict(features)
                    signals[agent.name] = signal
                except Exception as e:
                    # Log error but continue with other agents
                    print(f"Error in {agent.name}: {e}")
        
        return signals
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for all agents."""
        return {
            'total_agents': len(self.agents),
            'trained_agents': sum(1 for a in self.agents.values() if a.is_trained),
            'agents': {k: v.get_stats() for k, v in self.agents.items()}
        }
