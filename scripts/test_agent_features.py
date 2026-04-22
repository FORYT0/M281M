"""
Agent Feature Integration Test - Tests feature adapter with synthetic data.
Validates feature extraction and agent inference without live connection.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import time
from datetime import datetime, timedelta

from src.pipeline.features import FeatureCalculator
from src.agents.feature_adapter import FeatureAdapter

# Try to import agents, but continue if not available
try:
    from src.agents.agent_ensemble import AgentEnsemble
    from src.agents.regime_classifier import RegimeClassifier
    AGENTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠ Warning: Agent modules not available: {e}")
    print("  Skipping agent inference tests")
    AGENTS_AVAILABLE = False


def generate_synthetic_trades(n_trades: int = 100, base_price: float = 50000.0):
    """
    Generate synthetic trade data for testing.
    
    Args:
        n_trades: Number of trades to generate
        base_price: Starting price
    
    Yields:
        Trade dictionaries
    """
    price = base_price
    timestamp = datetime.now()
    
    for i in range(n_trades):
        # Random walk
        price_change = np.random.randn() * 10
        price += price_change
        
        # Random quantity
        quantity = abs(np.random.randn() * 0.1 + 0.5)
        
        # Random side
        is_buyer_maker = np.random.random() > 0.5
        
        # Increment timestamp
        timestamp += timedelta(milliseconds=100)
        
        yield {
            'price': price,
            'quantity': quantity,
            'is_buyer_maker': is_buyer_maker,
            'timestamp': int(timestamp.timestamp() * 1000)
        }


def test_feature_extraction():
    """Test feature extraction from pipeline."""
    print("\n" + "="*70)
    print("TEST 1: Feature Extraction")
    print("="*70)
    
    feature_calc = FeatureCalculator()
    feature_adapter = FeatureAdapter(lookback_window=20)
    
    # Generate and process trades
    trades = list(generate_synthetic_trades(50))
    
    print(f"\nProcessing {len(trades)} synthetic trades...")
    
    for i, trade in enumerate(trades):
        # Update feature calculator
        feature_calc.update_trade(
            price=trade['price'],
            quantity=trade['quantity'],
            is_buyer_maker=trade['is_buyer_maker'],
            timestamp=trade['timestamp']
        )
        
        # Get pipeline features
        pipeline_features = feature_calc.get_features()
        pipeline_features['timestamp'] = datetime.fromtimestamp(trade['timestamp'] / 1000)
        
        # Extract agent features
        agent_features = feature_adapter.extract_features(
            pipeline_features,
            symbol='BTCUSDT'
        )
        
        if i % 10 == 0:
            print(f"\nTrade #{i+1}:")
            print(f"  Price: ${agent_features.price:,.2f}")
            print(f"  EMA(9): ${agent_features.ema_fast:,.2f}")
            print(f"  EMA(21): ${agent_features.ema_slow:,.2f}")
            print(f"  RSI: {agent_features.rsi:.2f}")
            print(f"  OFI: {agent_features.ofi:.4f}")
            print(f"  VPIN: {agent_features.vpin:.4f}")
            print(f"  Volatility: {agent_features.volatility:.4f}")
    
    print("\n✓ Feature extraction test passed")
    return True


def test_agent_inference():
    """Test agent inference with features."""
    if not AGENTS_AVAILABLE:
        print("\n" + "="*70)
        print("TEST 2: Agent Inference - SKIPPED")
        print("="*70)
        print("⚠ Agent modules not available")
        return True
    
    print("\n" + "="*70)
    print("TEST 2: Agent Inference")
    print("="*70)
    
    feature_calc = FeatureCalculator()
    feature_adapter = FeatureAdapter(lookback_window=20)
    regime_classifier = RegimeClassifier()
    ensemble = AgentEnsemble(regime_classifier=regime_classifier)
    
    # Generate and process trades
    trades = list(generate_synthetic_trades(100))
    
    print(f"\nProcessing {len(trades)} trades through agents...")
    
    latencies = []
    signals = []
    
    for i, trade in enumerate(trades):
        start_time = time.time()
        
        # Update features
        feature_calc.update_trade(
            price=trade['price'],
            quantity=trade['quantity'],
            is_buyer_maker=trade['is_buyer_maker'],
            timestamp=trade['timestamp']
        )
        
        pipeline_features = feature_calc.get_features()
        pipeline_features['timestamp'] = datetime.fromtimestamp(trade['timestamp'] / 1000)
        
        agent_features = feature_adapter.extract_features(
            pipeline_features,
            symbol='BTCUSDT'
        )
        
        # Get ensemble signal (every 5 trades)
        if i % 5 == 0 and i > 20:  # Need some history first
            signal = ensemble.predict(
                symbol='BTCUSDT',
                features=agent_features.to_dict()
            )
            
            latency_ms = (time.time() - start_time) * 1000
            latencies.append(latency_ms)
            signals.append(signal)
            
            if len(signals) % 5 == 0:
                print(f"\nSignal #{len(signals)}:")
                print(f"  Direction: {signal.direction}")
                print(f"  Confidence: {signal.confidence:.2%}")
                print(f"  Strength: {signal.strength:.2f}")
                print(f"  Latency: {latency_ms:.2f}ms")
    
    # Print statistics
    print(f"\n{'='*70}")
    print("Inference Statistics:")
    print(f"{'='*70}")
    print(f"Total Signals: {len(signals)}")
    print(f"Latency Mean: {np.mean(latencies):.2f}ms")
    print(f"Latency Std: {np.std(latencies):.2f}ms")
    print(f"Latency Min: {np.min(latencies):.2f}ms")
    print(f"Latency Max: {np.max(latencies):.2f}ms")
    print(f"Latency P95: {np.percentile(latencies, 95):.2f}ms")
    
    # Check latency target
    avg_latency = np.mean(latencies)
    if avg_latency < 50:
        print(f"\n✓ PASSED: Average latency {avg_latency:.2f}ms < 50ms target")
    else:
        print(f"\n✗ WARNING: Average latency {avg_latency:.2f}ms > 50ms target")
    
    # Signal distribution
    directions = [s.direction for s in signals]
    print(f"\nSignal Distribution:")
    print(f"  Long: {directions.count('long')}")
    print(f"  Short: {directions.count('short')}")
    print(f"  Neutral: {directions.count('neutral')}")
    
    print("\n✓ Agent inference test passed")
    return True


def test_sequence_features():
    """Test sequence feature generation for LSTM."""
    print("\n" + "="*70)
    print("TEST 3: Sequence Features")
    print("="*70)
    
    feature_calc = FeatureCalculator()
    feature_adapter = FeatureAdapter(lookback_window=20)
    
    # Generate trades
    trades = list(generate_synthetic_trades(30))
    
    print(f"\nProcessing {len(trades)} trades...")
    
    for trade in trades:
        feature_calc.update_trade(
            price=trade['price'],
            quantity=trade['quantity'],
            is_buyer_maker=trade['is_buyer_maker'],
            timestamp=trade['timestamp']
        )
        
        pipeline_features = feature_calc.get_features()
        pipeline_features['timestamp'] = datetime.fromtimestamp(trade['timestamp'] / 1000)
        
        feature_adapter.extract_features(pipeline_features, 'BTCUSDT')
    
    # Get sequence features
    sequence = feature_adapter.get_sequence_features(n_steps=10)
    
    print(f"\nSequence shape: {sequence.shape}")
    print(f"Expected: (10, 10)")
    
    assert sequence.shape == (10, 10), "Sequence shape mismatch"
    
    print(f"\nFirst time step features:")
    print(f"  {sequence[0]}")
    
    print(f"\nLast time step features:")
    print(f"  {sequence[-1]}")
    
    # Get tabular features
    tabular = feature_adapter.get_tabular_features()
    
    print(f"\nTabular features shape: {tabular.shape}")
    print(f"Expected: (10,)")
    
    assert tabular.shape == (10,), "Tabular shape mismatch"
    
    print(f"\nTabular features:")
    print(f"  {tabular}")
    
    print("\n✓ Sequence features test passed")
    return True


def test_normalization():
    """Test feature normalization."""
    print("\n" + "="*70)
    print("TEST 4: Feature Normalization")
    print("="*70)
    
    feature_calc = FeatureCalculator()
    feature_adapter = FeatureAdapter(lookback_window=20, normalize=True)
    
    # Generate trades with varying volatility
    trades = list(generate_synthetic_trades(50))
    
    print(f"\nProcessing {len(trades)} trades with normalization...")
    
    volatilities = []
    ofis = []
    
    for trade in trades:
        feature_calc.update_trade(
            price=trade['price'],
            quantity=trade['quantity'],
            is_buyer_maker=trade['is_buyer_maker'],
            timestamp=trade['timestamp']
        )
        
        pipeline_features = feature_calc.get_features()
        pipeline_features['timestamp'] = datetime.fromtimestamp(trade['timestamp'] / 1000)
        
        agent_features = feature_adapter.extract_features(pipeline_features, 'BTCUSDT')
        
        volatilities.append(agent_features.volatility)
        ofis.append(agent_features.ofi)
    
    print(f"\nNormalized Volatility:")
    print(f"  Mean: {np.mean(volatilities):.4f}")
    print(f"  Std: {np.std(volatilities):.4f}")
    
    print(f"\nNormalized OFI:")
    print(f"  Mean: {np.mean(ofis):.4f}")
    print(f"  Std: {np.std(ofis):.4f}")
    
    # Check normalization (should be close to 0 mean, 1 std)
    assert abs(np.mean(volatilities)) < 0.5, "Volatility mean not normalized"
    assert abs(np.mean(ofis)) < 0.5, "OFI mean not normalized"
    
    print("\n✓ Normalization test passed")
    return True


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("AGENT FEATURE INTEGRATION TESTS")
    print("="*70)
    print("\nTesting feature extraction and agent inference...")
    
    tests = [
        ("Feature Extraction", test_feature_extraction),
        ("Agent Inference", test_agent_inference),
        ("Sequence Features", test_sequence_features),
        ("Normalization", test_normalization)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} failed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    exit(main())
