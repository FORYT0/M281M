"""
Meta-Learner - Learns optimal agent weights from performance.
Implements online learning to adapt agent weights dynamically.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from collections import deque, defaultdict
from datetime import datetime


@dataclass
class AgentPerformance:
    """Tracks performance metrics for an agent."""
    
    agent_name: str
    total_signals: int = 0
    correct_signals: int = 0
    accuracy: float = 0.0
    avg_confidence: float = 0.0
    avg_pnl: float = 0.0
    sharpe_ratio: float = 0.0
    recent_pnls: deque = field(default_factory=lambda: deque(maxlen=100))
    
    def update(self, was_correct: bool, confidence: float, pnl: Optional[float] = None):
        """Update performance metrics."""
        self.total_signals += 1
        if was_correct:
            self.correct_signals += 1
        
        self.accuracy = self.correct_signals / self.total_signals
        
        # Update average confidence (EMA)
        alpha = 0.1
        self.avg_confidence = alpha * confidence + (1 - alpha) * self.avg_confidence
        
        # Update PnL tracking
        if pnl is not None:
            self.recent_pnls.append(pnl)
            self.avg_pnl = np.mean(self.recent_pnls)
            
            if len(self.recent_pnls) > 1:
                self.sharpe_ratio = np.mean(self.recent_pnls) / (np.std(self.recent_pnls) + 1e-6)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'agent_name': self.agent_name,
            'total_signals': self.total_signals,
            'correct_signals': self.correct_signals,
            'accuracy': self.accuracy,
            'avg_confidence': self.avg_confidence,
            'avg_pnl': self.avg_pnl,
            'sharpe_ratio': self.sharpe_ratio
        }


class MetaLearner:
    """
    Learns optimal agent weights through online learning.
    
    Methods:
    - EMA-based: Exponential moving average of performance
    - Gradient-based: Online gradient descent
    - Contextual: Regime-aware weight optimization
    """
    
    def __init__(
        self,
        learning_rate: float = 0.01,
        performance_window: int = 100,
        update_frequency: int = 10,
        regime_aware: bool = True,
        min_weight: float = 0.1,
        max_weight: float = 3.0
    ):
        """
        Initialize meta-learner.
        
        Args:
            learning_rate: Learning rate for weight updates
            performance_window: Window size for performance tracking
            update_frequency: Update weights every N signals
            regime_aware: Use regime-specific weights
            min_weight: Minimum agent weight
            max_weight: Maximum agent weight
        """
        self.learning_rate = learning_rate
        self.performance_window = performance_window
        self.update_frequency = update_frequency
        self.regime_aware = regime_aware
        self.min_weight = min_weight
        self.max_weight = max_weight
        
        # Agent performance tracking
        self.agent_performance: Dict[str, AgentPerformance] = {}
        
        # Current weights (agent_name -> weight)
        self.weights: Dict[str, float] = {}
        
        # Regime-specific weights (regime -> agent_name -> weight)
        self.regime_weights: Dict[str, Dict[str, float]] = defaultdict(dict)
        
        # Update counter
        self.signal_count = 0
        self.last_update = 0
        
        # Performance history
        self.weight_history: List[Dict[str, float]] = []
    
    def initialize_agent(self, agent_name: str, initial_weight: float = 1.0):
        """
        Initialize tracking for a new agent.
        
        Args:
            agent_name: Name of the agent
            initial_weight: Initial weight
        """
        if agent_name not in self.agent_performance:
            self.agent_performance[agent_name] = AgentPerformance(agent_name=agent_name)
            self.weights[agent_name] = initial_weight
    
    def update_performance(
        self,
        agent_name: str,
        signal_direction: str,
        actual_outcome: str,
        confidence: float,
        pnl: Optional[float] = None,
        regime: Optional[str] = None
    ):
        """
        Update agent performance based on outcome.
        
        Args:
            agent_name: Name of the agent
            signal_direction: Agent's signal direction
            actual_outcome: Actual market outcome
            confidence: Signal confidence
            pnl: Realized PnL (optional)
            regime: Current market regime (optional)
        """
        # Initialize if needed
        self.initialize_agent(agent_name)
        
        # Determine if signal was correct
        was_correct = signal_direction == actual_outcome
        
        # Update performance
        self.agent_performance[agent_name].update(was_correct, confidence, pnl)
        
        # Update regime-specific performance
        if regime and self.regime_aware:
            if agent_name not in self.regime_weights[regime]:
                self.regime_weights[regime][agent_name] = 1.0
        
        # Increment counter
        self.signal_count += 1
        
        # Check if we should update weights
        if self.signal_count - self.last_update >= self.update_frequency:
            self._update_weights(regime)
            self.last_update = self.signal_count
    
    def _update_weights(self, current_regime: Optional[str] = None):
        """Update agent weights based on performance."""
        if not self.agent_performance:
            return
        
        # Calculate performance scores
        scores = {}
        for agent_name, perf in self.agent_performance.items():
            if perf.total_signals < 10:
                # Not enough data yet
                scores[agent_name] = 1.0
                continue
            
            # Combine accuracy and Sharpe ratio
            accuracy_score = perf.accuracy
            sharpe_score = max(0, perf.sharpe_ratio) / 2  # Normalize
            confidence_score = perf.avg_confidence
            
            # Weighted combination
            score = (
                0.4 * accuracy_score +
                0.3 * sharpe_score +
                0.3 * confidence_score
            )
            
            scores[agent_name] = max(0.1, score)
        
        # Update weights using EMA
        for agent_name, score in scores.items():
            current_weight = self.weights.get(agent_name, 1.0)
            
            # Gradient update
            target_weight = score * 2.0  # Scale to reasonable range
            new_weight = current_weight + self.learning_rate * (target_weight - current_weight)
            
            # Apply limits
            new_weight = np.clip(new_weight, self.min_weight, self.max_weight)
            
            self.weights[agent_name] = new_weight
            
            # Update regime-specific weights
            if current_regime and self.regime_aware:
                regime_weight = self.regime_weights[current_regime].get(agent_name, 1.0)
                new_regime_weight = regime_weight + self.learning_rate * (target_weight - regime_weight)
                new_regime_weight = np.clip(new_regime_weight, self.min_weight, self.max_weight)
                self.regime_weights[current_regime][agent_name] = new_regime_weight
        
        # Save history
        self.weight_history.append(self.weights.copy())
    
    def get_optimal_weights(
        self,
        regime: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Get optimal weights for current context.
        
        Args:
            regime: Current market regime (optional)
        
        Returns:
            Dictionary of agent_name -> weight
        """
        if regime and self.regime_aware and regime in self.regime_weights:
            # Use regime-specific weights
            return self.regime_weights[regime].copy()
        else:
            # Use global weights
            return self.weights.copy()
    
    def get_agent_performance(
        self,
        agent_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get performance metrics for agents.
        
        Args:
            agent_name: Specific agent (optional)
        
        Returns:
            Performance metrics
        """
        if agent_name:
            if agent_name in self.agent_performance:
                return self.agent_performance[agent_name].to_dict()
            return {}
        else:
            return {
                name: perf.to_dict()
                for name, perf in self.agent_performance.items()
            }
    
    def get_weight_history(self) -> List[Dict[str, float]]:
        """Get history of weight updates."""
        return self.weight_history.copy()
    
    def get_regime_weights(self) -> Dict[str, Dict[str, float]]:
        """Get all regime-specific weights."""
        return {
            regime: weights.copy()
            for regime, weights in self.regime_weights.items()
        }
    
    def set_learning_rate(self, learning_rate: float):
        """Update learning rate."""
        self.learning_rate = learning_rate
    
    def set_update_frequency(self, frequency: int):
        """Update weight update frequency."""
        self.update_frequency = frequency
    
    def reset_agent_performance(self, agent_name: str):
        """Reset performance tracking for an agent."""
        if agent_name in self.agent_performance:
            self.agent_performance[agent_name] = AgentPerformance(agent_name=agent_name)
            self.weights[agent_name] = 1.0
    
    def reset_all(self):
        """Reset all performance tracking and weights."""
        self.agent_performance.clear()
        self.weights.clear()
        self.regime_weights.clear()
        self.signal_count = 0
        self.last_update = 0
        self.weight_history.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get meta-learner statistics."""
        return {
            'total_signals': self.signal_count,
            'num_agents': len(self.agent_performance),
            'num_regimes': len(self.regime_weights),
            'learning_rate': self.learning_rate,
            'update_frequency': self.update_frequency,
            'regime_aware': self.regime_aware,
            'weight_updates': len(self.weight_history),
            'current_weights': self.weights.copy(),
            'agent_performance': self.get_agent_performance()
        }
