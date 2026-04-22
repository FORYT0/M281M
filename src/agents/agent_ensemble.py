"""
Agent Ensemble - Combines signals from multiple agents.
Implements voting and weighted aggregation strategies.
"""

import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from .base_agent import BaseAgent, AgentSignal, AgentRegistry


@dataclass
class EnsembleSignal:
    """Combined signal from multiple agents."""
    
    timestamp: datetime
    symbol: str
    
    # Aggregated decision
    direction: str  # 'long', 'short', 'neutral'
    confidence: float  # 0.0 to 1.0
    
    # Individual agent signals
    agent_signals: Dict[str, AgentSignal]
    
    # Voting breakdown
    votes: Dict[str, int]  # {'long': 2, 'short': 1, 'neutral': 1}
    
    # Metadata
    num_agents: int
    agreement_score: float  # How much agents agree (0-1)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'direction': self.direction,
            'confidence': self.confidence,
            'votes': self.votes,
            'num_agents': self.num_agents,
            'agreement_score': self.agreement_score,
            'agent_signals': {
                name: signal.to_dict()
                for name, signal in self.agent_signals.items()
            }
        }


class AgentEnsemble:
    """
    Combines multiple trading agents into an ensemble.
    
    Strategies:
    - Majority voting: Most common direction wins
    - Weighted voting: Weight by confidence
    - Regime-aware: Use regime classifier to weight agents
    """
    
    def __init__(
        self,
        registry: AgentRegistry,
        strategy: str = 'weighted',
        min_confidence: float = 0.5
    ):
        """
        Initialize agent ensemble.
        
        Args:
            registry: Agent registry containing all agents
            strategy: Aggregation strategy ('majority', 'weighted', 'regime_aware')
            min_confidence: Minimum confidence threshold for signals
        """
        self.registry = registry
        self.strategy = strategy
        self.min_confidence = min_confidence
        
        # Agent weights (can be learned or manually set)
        self.agent_weights = {
            'regime_classifier': 1.5,  # Higher weight for regime
            'momentum_agent': 1.0,
            'mean_reversion_agent': 1.0,
            'order_flow_agent': 1.2  # Higher weight for order flow
        }
    
    def predict(
        self,
        symbol: str,
        features: Dict[str, Any]
    ) -> EnsembleSignal:
        """
        Get ensemble prediction from all agents.
        
        Args:
            symbol: Trading symbol
            features: Market features
        
        Returns:
            EnsembleSignal with aggregated decision
        """
        # Get signals from all agents
        agent_signals = self.registry.predict_all(symbol, features)
        
        if not agent_signals:
            return self._create_neutral_signal(symbol)
        
        # Apply strategy
        if self.strategy == 'majority':
            return self._majority_voting(symbol, agent_signals)
        elif self.strategy == 'weighted':
            return self._weighted_voting(symbol, agent_signals)
        elif self.strategy == 'regime_aware':
            return self._regime_aware_voting(symbol, agent_signals, features)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")
    
    def _majority_voting(
        self,
        symbol: str,
        agent_signals: Dict[str, AgentSignal]
    ) -> EnsembleSignal:
        """Simple majority voting."""
        votes = {'long': 0, 'short': 0, 'neutral': 0}
        
        for signal in agent_signals.values():
            if signal.confidence >= self.min_confidence:
                votes[signal.direction] += 1
        
        # Determine winner
        direction = max(votes, key=votes.get)
        
        # Calculate agreement score
        total_votes = sum(votes.values())
        agreement_score = votes[direction] / total_votes if total_votes > 0 else 0.0
        
        # Average confidence of agents voting for winner
        winner_confidences = [
            s.confidence for s in agent_signals.values()
            if s.direction == direction and s.confidence >= self.min_confidence
        ]
        confidence = np.mean(winner_confidences) if winner_confidences else 0.0
        
        return EnsembleSignal(
            timestamp=datetime.now(),
            symbol=symbol,
            direction=direction,
            confidence=float(confidence),
            agent_signals=agent_signals,
            votes=votes,
            num_agents=len(agent_signals),
            agreement_score=float(agreement_score)
        )
    
    def _weighted_voting(
        self,
        symbol: str,
        agent_signals: Dict[str, AgentSignal]
    ) -> EnsembleSignal:
        """Weighted voting by agent confidence and preset weights."""
        weighted_votes = {'long': 0.0, 'short': 0.0, 'neutral': 0.0}
        vote_counts = {'long': 0, 'short': 0, 'neutral': 0}
        
        for agent_name, signal in agent_signals.items():
            if signal.confidence >= self.min_confidence:
                # Get agent weight
                weight = self.agent_weights.get(agent_name, 1.0)
                
                # Weight by confidence
                weighted_vote = signal.confidence * weight
                weighted_votes[signal.direction] += weighted_vote
                vote_counts[signal.direction] += 1
        
        # Determine winner
        direction = max(weighted_votes, key=weighted_votes.get)
        
        # Calculate confidence (normalized weighted score)
        total_weight = sum(weighted_votes.values())
        confidence = weighted_votes[direction] / total_weight if total_weight > 0 else 0.0
        
        # Calculate agreement score
        total_votes = sum(vote_counts.values())
        agreement_score = vote_counts[direction] / total_votes if total_votes > 0 else 0.0
        
        return EnsembleSignal(
            timestamp=datetime.now(),
            symbol=symbol,
            direction=direction,
            confidence=float(confidence),
            agent_signals=agent_signals,
            votes=vote_counts,
            num_agents=len(agent_signals),
            agreement_score=float(agreement_score)
        )
    
    def _regime_aware_voting(
        self,
        symbol: str,
        agent_signals: Dict[str, AgentSignal],
        features: Dict[str, Any]
    ) -> EnsembleSignal:
        """
        Regime-aware voting: adjust agent weights based on market regime.
        
        - Trending regime: Higher weight to momentum agent
        - Range-bound regime: Higher weight to mean reversion agent
        - Volatile regime: Higher weight to order flow agent, reduce overall confidence
        """
        # Get regime from regime classifier
        regime_signal = agent_signals.get('regime_classifier')
        
        if not regime_signal or not regime_signal.reasoning:
            # Fall back to weighted voting
            return self._weighted_voting(symbol, agent_signals)
        
        regime = regime_signal.reasoning.get('regime', 'unknown')
        
        # Adjust weights based on regime
        regime_weights = self.agent_weights.copy()
        
        if regime == 'trending':
            regime_weights['momentum_agent'] = 2.0
            regime_weights['mean_reversion_agent'] = 0.5
        elif regime == 'range_bound':
            regime_weights['mean_reversion_agent'] = 2.0
            regime_weights['momentum_agent'] = 0.5
        elif regime == 'volatile':
            regime_weights['order_flow_agent'] = 2.0
            regime_weights['momentum_agent'] = 0.7
            regime_weights['mean_reversion_agent'] = 0.7
        
        # Weighted voting with regime-adjusted weights
        weighted_votes = {'long': 0.0, 'short': 0.0, 'neutral': 0.0}
        vote_counts = {'long': 0, 'short': 0, 'neutral': 0}
        
        for agent_name, signal in agent_signals.items():
            if signal.confidence >= self.min_confidence:
                weight = regime_weights.get(agent_name, 1.0)
                weighted_vote = signal.confidence * weight
                weighted_votes[signal.direction] += weighted_vote
                vote_counts[signal.direction] += 1
        
        # Determine winner
        direction = max(weighted_votes, key=weighted_votes.get)
        
        # Calculate confidence
        total_weight = sum(weighted_votes.values())
        confidence = weighted_votes[direction] / total_weight if total_weight > 0 else 0.0
        
        # Reduce confidence in volatile regime
        if regime == 'volatile':
            confidence *= 0.7
        
        # Calculate agreement score
        total_votes = sum(vote_counts.values())
        agreement_score = vote_counts[direction] / total_votes if total_votes > 0 else 0.0
        
        return EnsembleSignal(
            timestamp=datetime.now(),
            symbol=symbol,
            direction=direction,
            confidence=float(confidence),
            agent_signals=agent_signals,
            votes=vote_counts,
            num_agents=len(agent_signals),
            agreement_score=float(agreement_score)
        )
    
    def _create_neutral_signal(self, symbol: str) -> EnsembleSignal:
        """Create neutral signal when no agents available."""
        return EnsembleSignal(
            timestamp=datetime.now(),
            symbol=symbol,
            direction='neutral',
            confidence=0.0,
            agent_signals={},
            votes={'long': 0, 'short': 0, 'neutral': 0},
            num_agents=0,
            agreement_score=0.0
        )
    
    def set_agent_weight(self, agent_name: str, weight: float):
        """
        Set weight for specific agent.
        
        Args:
            agent_name: Name of agent
            weight: Weight value (higher = more influence)
        """
        self.agent_weights[agent_name] = weight
    
    def get_agent_weights(self) -> Dict[str, float]:
        """Get current agent weights."""
        return self.agent_weights.copy()
    
    def set_strategy(self, strategy: str):
        """
        Change aggregation strategy.
        
        Args:
            strategy: 'majority', 'weighted', or 'regime_aware'
        """
        if strategy not in ['majority', 'weighted', 'regime_aware']:
            raise ValueError(f"Unknown strategy: {strategy}")
        self.strategy = strategy
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for all agents."""
        return self.registry.get_stats()
