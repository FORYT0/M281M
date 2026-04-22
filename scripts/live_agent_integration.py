"""
Live Agent Integration Demo - In-Memory
Connects Phase 1 (Features) with Phase 2 (Agents) in real-time.

This demonstrates the complete pipeline:
WebSocket → Features → Agents → Ensemble → Signals

Note: Uses synthetic-trained models. For production, retrain with real data.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from src.pipeline.multi_stream_client import MultiStreamAggregator
from src.agents import (
    AgentRegistry,
    RegimeClassifier,
    MomentumAgent,
    MeanReversionAgent,
    OrderFlowAgent,
    AgentEnsemble
)


class LiveAgentSystem:
    """
    Integrated system connecting live features to AI agents.
    """
    
    def __init__(
        self,
        symbols: list[str],
        model_dir: str = 'models',
        ensemble_strategy: str = 'regime_aware'
    ):
        """
        Initialize live agent system.
        
        Args:
            symbols: Trading symbols to monitor
            model_dir: Directory containing trained models
            ensemble_strategy: Ensemble aggregation strategy
        """
        self.symbols = symbols
        self.model_dir = Path(model_dir)
        self.ensemble_strategy = ensemble_strategy
        
        # Create agent registry
        self.registry = AgentRegistry()
        
        # Create agents for each symbol
        for symbol in symbols:
            self.registry.register(RegimeClassifier(symbol))
            self.registry.register(MomentumAgent(symbol, sequence_length=20))
            self.registry.register(MeanReversionAgent(symbol))
            self.registry.register(OrderFlowAgent(symbol, state_size=30))
        
        # Create ensemble
        self.ensemble = AgentEnsemble(
            self.registry,
            strategy=ensemble_strategy
        )
        
        # Statistics
        self.signal_count = 0
        self.start_time = None
        self.last_signals = {}
    
    def load_models(self) -> bool:
        """
        Load trained models from disk.
        
        Returns:
            True if at least one model loaded successfully
        """
        if not self.model_dir.exists():
            print(f"⚠ Model directory {self.model_dir} not found")
            print("  Models will run untrained (neutral signals only)")
            return False
        
        loaded_count = 0
        
        for symbol in self.symbols:
            agents = self.registry.get_all(symbol)
            
            for key, agent in agents.items():
                filename = f"{agent.name}_{symbol}.pkl"
                filepath = self.model_dir / filename
                
                if filepath.exists():
                    try:
                        agent.load(str(filepath))
                        print(f"✓ Loaded {agent.name} for {symbol}")
                        loaded_count += 1
                    except Exception as e:
                        print(f"✗ Failed to load {agent.name}: {e}")
                else:
                    print(f"⚠ Model not found: {filepath}")
        
        if loaded_count == 0:
            print("\n⚠ No models loaded. Agents will return neutral signals.")
            print("  To train models, run: python scripts/train_agents.py")
        
        return loaded_count > 0
    
    async def on_features(self, symbol: str, features: Dict[str, Any]):
        """
        Callback for new features - runs agents and generates signals.
        
        Args:
            symbol: Trading symbol
            features: Computed features
        """
        try:
            # Get ensemble prediction
            signal = self.ensemble.predict(symbol, features)
            
            # Update statistics
            self.signal_count += 1
            self.last_signals[symbol] = signal
            
            # Display signal
            self._display_signal(symbol, features, signal)
            
        except Exception as e:
            print(f"✗ Error processing features for {symbol}: {e}")
    
    def _display_signal(self, symbol: str, features: Dict[str, Any], signal):
        """Display signal in formatted output."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Extract key features
        price = features.get('price', 0)
        rsi = features.get('rsi', 50)
        ofi = features.get('order_flow_imbalance', 0)
        vpin = features.get('vpin', 0)
        
        # Format signal
        direction_emoji = {
            'long': '🟢',
            'short': '🔴',
            'neutral': '⚪'
        }
        
        emoji = direction_emoji.get(signal.direction, '⚪')
        
        # Confidence bar
        conf_bars = int(signal.confidence * 10)
        conf_bar = '█' * conf_bars + '░' * (10 - conf_bars)
        
        print(f"\n[{timestamp}] {symbol}")
        print(f"  Price: ${price:,.2f} | RSI: {rsi:.1f} | OFI: {ofi:+.3f} | VPIN: {vpin:.3f}")
        print(f"  {emoji} Signal: {signal.direction.upper():8} | Confidence: {conf_bar} {signal.confidence:.1%}")
        print(f"  Votes: {signal.votes} | Agreement: {signal.agreement_score:.1%}")
        
        # Show individual agent signals
        if signal.agent_signals:
            print(f"  Agents:")
            for agent_name, agent_signal in signal.agent_signals.items():
                print(f"    - {agent_name:20}: {agent_signal.direction:8} @ {agent_signal.confidence:.1%}")
    
    async def start(self):
        """Start the live agent system."""
        self.start_time = datetime.now()
        
        print("=" * 70)
        print("M281M Live Agent Integration")
        print("=" * 70)
        print(f"Symbols: {', '.join(self.symbols)}")
        print(f"Strategy: {self.ensemble_strategy}")
        print(f"Agents per symbol: 4 (Regime, Momentum, MeanReversion, OrderFlow)")
        print("=" * 70)
        
        # Load models
        print("\nLoading models...")
        self.load_models()
        
        # Create multi-stream aggregator
        print(f"\nConnecting to Binance...")
        aggregator = MultiStreamAggregator(
            symbols=self.symbols,
            feature_callback=self.on_features,
            testnet=False  # Use mainnet
        )
        
        print(f"✓ Connected to Binance mainnet")
        print(f"\nMonitoring {', '.join(self.symbols)}...")
        print("Press Ctrl+C to stop\n")
        
        # Start streaming
        try:
            await aggregator.start()
        except KeyboardInterrupt:
            print("\n\nStopping...")
            await aggregator.stop()
            self._print_summary()
    
    def _print_summary(self):
        """Print session summary."""
        if not self.start_time:
            return
        
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        print("\n" + "=" * 70)
        print("Session Summary")
        print("=" * 70)
        print(f"Uptime: {uptime:.1f}s")
        print(f"Signals generated: {self.signal_count}")
        print(f"Signals per second: {self.signal_count / uptime:.2f}")
        
        # Show last signals
        if self.last_signals:
            print(f"\nLast Signals:")
            for symbol, signal in self.last_signals.items():
                print(f"  {symbol}: {signal.direction.upper()} @ {signal.confidence:.1%}")
        
        # Agent statistics
        stats = self.registry.get_stats()
        print(f"\nAgent Statistics:")
        print(f"  Total agents: {stats['total_agents']}")
        print(f"  Trained agents: {stats['trained_agents']}")
        
        print("\n✓ Session complete")


async def main():
    """Main entry point."""
    # Configuration
    SYMBOLS = ['BTCUSDT']  # Can add more: ['BTCUSDT', 'ETHUSDT']
    MODEL_DIR = 'models'
    STRATEGY = 'regime_aware'  # 'majority', 'weighted', or 'regime_aware'
    
    # Create and start system
    system = LiveAgentSystem(
        symbols=SYMBOLS,
        model_dir=MODEL_DIR,
        ensemble_strategy=STRATEGY
    )
    
    await system.start()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nShutdown requested")
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
