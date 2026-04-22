"""
Orchestrator Demo - Complete trading system demonstration.
Shows the full pipeline: Features → Agents → Ensemble → Orchestrator → Execution
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from datetime import datetime
from pathlib import Path

from src.pipeline.multi_stream_client import MultiStreamAggregator
from src.agents import (
    AgentRegistry,
    RegimeClassifier,
    MomentumAgent,
    MeanReversionAgent,
    OrderFlowAgent,
    AgentEnsemble
)
from src.orchestrator import (
    TradingOrchestrator,
    SizingMethod
)


class CompleteTradingSystem:
    """
    Complete trading system integrating all components.
    """
    
    def __init__(
        self,
        symbols: list[str],
        initial_balance: float = 10000.0,
        model_dir: str = 'models'
    ):
        """
        Initialize complete trading system.
        
        Args:
            symbols: Trading symbols to monitor
            initial_balance: Starting account balance
            model_dir: Directory containing trained models
        """
        self.symbols = symbols
        self.initial_balance = initial_balance
        self.model_dir = Path(model_dir)
        
        # Create agent registry and ensemble
        self.registry = AgentRegistry()
        
        for symbol in symbols:
            self.registry.register(RegimeClassifier(symbol))
            self.registry.register(MomentumAgent(symbol, sequence_length=20))
            self.registry.register(MeanReversionAgent(symbol))
            self.registry.register(OrderFlowAgent(symbol, state_size=30))
        
        self.ensemble = AgentEnsemble(
            self.registry,
            strategy='regime_aware'
        )
        
        # Create orchestrator
        self.orchestrator = TradingOrchestrator(
            ensemble=self.ensemble,
            initial_balance=initial_balance,
            min_confidence=0.65,
            min_agreement=0.6,
            max_position_pct=0.1,
            sizing_method=SizingMethod.KELLY,
            enable_meta_learning=True
        )
        
        # Statistics
        self.feature_count = 0
        self.signal_count = 0
        self.start_time = None
    
    def load_models(self) -> bool:
        """Load trained models."""
        if not self.model_dir.exists():
            print(f"⚠ Model directory {self.model_dir} not found")
            print("  Running with untrained models")
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
        
        return loaded_count > 0
    
    async def on_features(self, symbol: str, features: dict):
        """
        Callback for new features - runs complete pipeline.
        
        Args:
            symbol: Trading symbol
            features: Computed features
        """
        try:
            self.feature_count += 1
            
            # Get ensemble signal
            ensemble_signal = self.ensemble.predict(symbol, features)
            
            # Process through orchestrator
            current_price = features.get('price', 0)
            result = self.orchestrator.process_signal(
                symbol=symbol,
                ensemble_signal=ensemble_signal,
                current_price=current_price,
                features=features
            )
            
            self.signal_count += 1
            
            # Display result
            self._display_result(symbol, features, ensemble_signal, result)
            
        except Exception as e:
            print(f"✗ Error processing features for {symbol}: {e}")
    
    def _display_result(self, symbol: str, features: dict, signal, result: dict):
        """Display processing result."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Extract key info
        price = features.get('price', 0)
        rsi = features.get('rsi', 50)
        ofi = features.get('order_flow_imbalance', 0)
        
        # Signal info
        direction_emoji = {'long': '🟢', 'short': '🔴', 'neutral': '⚪'}
        emoji = direction_emoji.get(signal.direction, '⚪')
        
        print(f"\n{'='*70}")
        print(f"[{timestamp}] {symbol} - ${price:,.2f}")
        print(f"{'='*70}")
        
        # Market features
        print(f"📊 Features: RSI={rsi:.1f} | OFI={ofi:+.3f}")
        
        # Ensemble signal
        print(f"\n{emoji} Ensemble Signal: {signal.direction.upper()}")
        print(f"   Confidence: {signal.confidence:.1%} | Agreement: {signal.agreement_score:.1%}")
        print(f"   Votes: {signal.votes}")
        
        # Validation
        if result['validated']:
            print(f"\n✓ Signal VALIDATED")
            print(f"   Quality Score: {result['validation_result']['quality_score']:.1%}")
        else:
            print(f"\n✗ Signal REJECTED")
            reasons = result['validation_result']['reasons']
            for reason in reasons:
                print(f"   - {reason}")
        
        # Position sizing
        if result['position_size']:
            pos_size = result['position_size']
            print(f"\n💰 Position Size:")
            print(f"   Size: {pos_size['size']:.4f} {symbol[:3]}")
            print(f"   % of Account: {pos_size['size_pct']:.2%}")
            print(f"   Method: {pos_size['method']}")
        
        # Execution
        if result['executed']:
            trade = result['trade']
            print(f"\n✅ TRADE EXECUTED")
            print(f"   {trade['side'].upper()} {trade['size']:.4f} @ ${trade['price']:,.2f}")
        else:
            print(f"\n⏸️  No trade executed")
        
        # Portfolio status
        status = self.orchestrator.get_status()
        print(f"\n📈 Portfolio:")
        print(f"   Equity: ${status['equity']:,.2f}")
        print(f"   PnL: ${status['total_pnl']:+,.2f}")
        print(f"   Open Positions: {status['open_positions']}")
    
    async def start(self):
        """Start the complete trading system."""
        self.start_time = datetime.now()
        
        print("=" * 70)
        print("M281M Complete Trading System")
        print("=" * 70)
        print(f"Symbols: {', '.join(self.symbols)}")
        print(f"Initial Balance: ${self.initial_balance:,.2f}")
        print(f"Strategy: Regime-Aware Ensemble")
        print(f"Position Sizing: Kelly Criterion")
        print(f"Meta-Learning: Enabled")
        print("=" * 70)
        
        # Load models
        print("\nLoading models...")
        self.load_models()
        
        # Connect to market data
        print(f"\nConnecting to Binance...")
        aggregator = MultiStreamAggregator(
            symbols=self.symbols,
            feature_callback=self.on_features,
            testnet=False
        )
        
        print(f"✓ Connected to Binance mainnet")
        print(f"\nMonitoring {', '.join(self.symbols)}...")
        print("Press Ctrl+C to stop and see final report\n")
        
        # Start streaming
        try:
            await aggregator.start()
        except KeyboardInterrupt:
            print("\n\nStopping...")
            await aggregator.stop()
            self._print_final_report()
    
    def _print_final_report(self):
        """Print final performance report."""
        if not self.start_time:
            return
        
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        print("\n" + "=" * 70)
        print("FINAL PERFORMANCE REPORT")
        print("=" * 70)
        
        # Session info
        print(f"\n📅 Session Info:")
        print(f"   Duration: {uptime:.1f}s")
        print(f"   Features Processed: {self.feature_count}")
        print(f"   Signals Generated: {self.signal_count}")
        
        # Get comprehensive metrics
        metrics = self.orchestrator.get_performance_metrics()
        
        # Orchestrator stats
        orch_stats = metrics['orchestrator']
        print(f"\n🎯 Signal Processing:")
        print(f"   Processed: {orch_stats['signals_processed']}")
        print(f"   Executed: {orch_stats['signals_executed']}")
        print(f"   Execution Rate: {orch_stats['execution_rate']:.1%}")
        
        # Execution stats
        exec_stats = metrics['execution']
        print(f"\n💼 Trading Performance:")
        print(f"   Initial Balance: ${exec_stats['initial_balance']:,.2f}")
        print(f"   Final Equity: ${exec_stats['equity']:,.2f}")
        print(f"   Total Return: {exec_stats['total_return']:+.2%}")
        print(f"   Total PnL: ${exec_stats['total_pnl']:+,.2f}")
        print(f"   Realized PnL: ${exec_stats['realized_pnl']:+,.2f}")
        print(f"   Unrealized PnL: ${exec_stats['unrealized_pnl']:+,.2f}")
        
        print(f"\n📊 Trade Statistics:")
        print(f"   Total Trades: {exec_stats['total_trades']}")
        print(f"   Winning Trades: {exec_stats['winning_trades']}")
        print(f"   Losing Trades: {exec_stats['losing_trades']}")
        print(f"   Win Rate: {exec_stats['win_rate']:.1%}")
        print(f"   Avg Win: ${exec_stats['avg_win']:+,.2f}")
        print(f"   Avg Loss: ${exec_stats['avg_loss']:+,.2f}")
        print(f"   Profit Factor: {exec_stats['profit_factor']:.2f}")
        
        # Validation stats
        val_stats = metrics['validation']
        print(f"\n✅ Validation Statistics:")
        print(f"   Pass Rate: {val_stats['pass_rate']:.1%}")
        print(f"   Rejection Reasons: {val_stats['rejection_reasons']}")
        
        # Meta-learning stats
        if 'meta_learning' in metrics:
            ml_stats = metrics['meta_learning']
            print(f"\n🧠 Meta-Learning:")
            print(f"   Weight Updates: {ml_stats['weight_updates']}")
            print(f"   Current Weights: {ml_stats['current_weights']}")
        
        # Open positions
        positions = self.orchestrator.get_positions()
        if positions:
            print(f"\n📍 Open Positions:")
            for symbol, pos in positions.items():
                print(f"   {symbol}: {pos.size:+.4f} @ ${pos.entry_price:,.2f}")
                print(f"      Unrealized PnL: ${pos.unrealized_pnl:+,.2f} ({pos.unrealized_pnl_pct:+.2%})")
        
        print("\n" + "=" * 70)
        print("✓ Session complete")
        print("=" * 70)


async def main():
    """Main entry point."""
    # Configuration
    SYMBOLS = ['BTCUSDT']
    INITIAL_BALANCE = 10000.0
    MODEL_DIR = 'models'
    
    # Create and start system
    system = CompleteTradingSystem(
        symbols=SYMBOLS,
        initial_balance=INITIAL_BALANCE,
        model_dir=MODEL_DIR
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
