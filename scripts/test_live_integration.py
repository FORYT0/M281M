"""
Live Integration Test - Tests agents with real-time feature pipeline.
Validates end-to-end system with live Binance data.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import time
from datetime import datetime
from typing import Dict, Any

from src.pipeline.websocket_client import BinanceWebSocketClient
from src.pipeline.features import FeatureCalculator
from src.agents.feature_adapter import FeatureAdapter
from src.agents.agent_ensemble import AgentEnsemble
from src.agents.regime_classifier import RegimeClassifier


class LiveIntegrationTest:
    """
    Tests complete pipeline integration:
    WebSocket → Features → Agents → Ensemble → Signals
    """
    
    def __init__(self, symbol: str = "btcusdt"):
        """
        Initialize test.
        
        Args:
            symbol: Trading symbol
        """
        self.symbol = symbol
        
        # Components
        self.ws_client = None
        self.feature_calc = FeatureCalculator()
        self.feature_adapter = FeatureAdapter(lookback_window=20)
        self.regime_classifier = RegimeClassifier()
        self.ensemble = AgentEnsemble(regime_classifier=self.regime_classifier)
        
        # Metrics
        self.update_count = 0
        self.signal_count = 0
        self.start_time = None
        self.latencies = []
        
        # Latest data
        self.latest_features = None
        self.latest_signal = None
    
    async def on_trade(self, data: Dict[str, Any]):
        """
        Handle trade update.
        
        Args:
            data: Trade data from WebSocket
        """
        try:
            start_time = time.time()
            
            # Extract trade data
            price = float(data['p'])
            quantity = float(data['q'])
            is_buyer_maker = data['m']
            timestamp = data['T']
            
            # Update features
            self.feature_calc.update_trade(
                price=price,
                quantity=quantity,
                is_buyer_maker=is_buyer_maker,
                timestamp=timestamp
            )
            
            # Get computed features
            pipeline_features = self.feature_calc.get_features()
            pipeline_features['timestamp'] = datetime.fromtimestamp(timestamp / 1000)
            
            # Adapt features for agents
            agent_features = self.feature_adapter.extract_features(
                pipeline_features,
                self.symbol
            )
            
            self.latest_features = agent_features
            
            # Get agent predictions (every 10 updates to reduce noise)
            if self.update_count % 10 == 0:
                # Get ensemble signal
                signal = self.ensemble.predict(
                    symbol=self.symbol,
                    features=agent_features.to_dict()
                )
                
                self.latest_signal = signal
                self.signal_count += 1
                
                # Calculate latency
                latency_ms = (time.time() - start_time) * 1000
                self.latencies.append(latency_ms)
                
                # Print update
                if self.signal_count % 10 == 0:
                    avg_latency = sum(self.latencies[-100:]) / min(len(self.latencies), 100)
                    
                    print(f"\n{'='*70}")
                    print(f"Update #{self.update_count} | Signal #{self.signal_count}")
                    print(f"{'='*70}")
                    print(f"Time: {agent_features.timestamp}")
                    print(f"Price: ${price:,.2f}")
                    print(f"\nFeatures:")
                    print(f"  EMA(9): ${agent_features.ema_fast:,.2f}")
                    print(f"  EMA(21): ${agent_features.ema_slow:,.2f}")
                    print(f"  RSI: {agent_features.rsi:.2f}")
                    print(f"  OFI: {agent_features.ofi:.4f}")
                    print(f"  VPIN: {agent_features.vpin:.4f}")
                    print(f"  Volatility: {agent_features.volatility:.4f}")
                    
                    if signal:
                        print(f"\nEnsemble Signal:")
                        print(f"  Direction: {signal.direction}")
                        print(f"  Confidence: {signal.confidence:.2%}")
                        print(f"  Strength: {signal.strength:.2f}")
                        print(f"  Regime: {signal.metadata.get('regime', 'unknown')}")
                        print(f"  Agreement: {signal.metadata.get('agreement', 0):.2%}")
                    
                    print(f"\nPerformance:")
                    print(f"  Latency: {latency_ms:.2f}ms (avg: {avg_latency:.2f}ms)")
                    print(f"  Updates/sec: {self.update_count / (time.time() - self.start_time):.1f}")
                    print(f"{'='*70}")
            
            self.update_count += 1
            
        except Exception as e:
            print(f"✗ Error processing trade: {e}")
            import traceback
            traceback.print_exc()
    
    async def on_ticker(self, data: Dict[str, Any]):
        """
        Handle ticker update.
        
        Args:
            data: Ticker data from WebSocket
        """
        try:
            # Update VWAP
            vwap = float(data.get('w', 0))
            if vwap > 0:
                self.feature_calc.vwap = vwap
        except Exception as e:
            print(f"✗ Error processing ticker: {e}")
    
    async def on_depth(self, data: Dict[str, Any]):
        """
        Handle order book depth update.
        
        Args:
            data: Depth data from WebSocket
        """
        try:
            # Extract bids and asks
            bids = [(float(p), float(q)) for p, q in data.get('b', [])]
            asks = [(float(p), float(q)) for p, q in data.get('a', [])]
            
            if bids and asks:
                # Update order book features
                self.feature_calc.update_order_book(bids, asks)
        except Exception as e:
            print(f"✗ Error processing depth: {e}")
    
    async def run(self, duration_seconds: int = 60):
        """
        Run live integration test.
        
        Args:
            duration_seconds: How long to run test
        """
        print("\n" + "="*70)
        print("LIVE INTEGRATION TEST")
        print("="*70)
        print(f"Symbol: {self.symbol.upper()}")
        print(f"Duration: {duration_seconds} seconds")
        print(f"Target Latency: <50ms")
        print("="*70)
        
        self.start_time = time.time()
        
        # Create WebSocket client
        self.ws_client = BinanceWebSocketClient()
        
        # Subscribe to streams
        await self.ws_client.subscribe_trades(self.symbol, self.on_trade)
        await self.ws_client.subscribe_ticker(self.symbol, self.on_ticker)
        await self.ws_client.subscribe_depth(self.symbol, self.on_depth)
        
        print("\n✓ Connected to Binance WebSocket")
        print("✓ Subscribed to trades, ticker, and depth")
        print("\nReceiving live data...\n")
        
        # Run for specified duration
        try:
            await asyncio.sleep(duration_seconds)
        except KeyboardInterrupt:
            print("\n\n⚠ Test interrupted by user")
        
        # Disconnect
        await self.ws_client.disconnect()
        
        # Print summary
        self._print_summary()
    
    def _print_summary(self):
        """Print test summary."""
        elapsed = time.time() - self.start_time
        
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        
        print(f"\nDuration: {elapsed:.1f} seconds")
        print(f"Total Updates: {self.update_count}")
        print(f"Total Signals: {self.signal_count}")
        print(f"Updates/Second: {self.update_count / elapsed:.1f}")
        print(f"Signals/Second: {self.signal_count / elapsed:.1f}")
        
        if self.latencies:
            print(f"\nLatency Statistics:")
            print(f"  Mean: {sum(self.latencies) / len(self.latencies):.2f}ms")
            print(f"  Min: {min(self.latencies):.2f}ms")
            print(f"  Max: {max(self.latencies):.2f}ms")
            print(f"  P50: {sorted(self.latencies)[len(self.latencies)//2]:.2f}ms")
            print(f"  P95: {sorted(self.latencies)[int(len(self.latencies)*0.95)]:.2f}ms")
            print(f"  P99: {sorted(self.latencies)[int(len(self.latencies)*0.99)]:.2f}ms")
            
            # Check if we met target
            avg_latency = sum(self.latencies) / len(self.latencies)
            if avg_latency < 50:
                print(f"\n✓ PASSED: Average latency {avg_latency:.2f}ms < 50ms target")
            else:
                print(f"\n✗ FAILED: Average latency {avg_latency:.2f}ms > 50ms target")
        
        if self.latest_features:
            print(f"\nLatest Features:")
            print(f"  Price: ${self.latest_features.price:,.2f}")
            print(f"  RSI: {self.latest_features.rsi:.2f}")
            print(f"  OFI: {self.latest_features.ofi:.4f}")
            print(f"  VPIN: {self.latest_features.vpin:.4f}")
        
        if self.latest_signal:
            print(f"\nLatest Signal:")
            print(f"  Direction: {self.latest_signal.direction}")
            print(f"  Confidence: {self.latest_signal.confidence:.2%}")
            print(f"  Strength: {self.latest_signal.strength:.2f}")
        
        print("\n" + "="*70)
        print("TEST COMPLETE")
        print("="*70)


async def main():
    """Main test function."""
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description='Live integration test')
    parser.add_argument('--symbol', default='btcusdt', help='Trading symbol')
    parser.add_argument('--duration', type=int, default=60, help='Test duration in seconds')
    args = parser.parse_args()
    
    # Run test
    test = LiveIntegrationTest(symbol=args.symbol)
    await test.run(duration_seconds=args.duration)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
