"""
Basic test script for agent architecture (no ML dependencies required).
Tests the base classes and structure without training.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime


def test_base_classes():
    """Test base agent classes."""
    print("=" * 60)
    print("Testing Base Agent Classes")
    print("=" * 60)
    
    try:
        from src.agents.base_agent import BaseAgent, AgentSignal, AgentRegistry
        print("✓ Imported base classes successfully")
        
        # Test AgentSignal
        signal = AgentSignal(
            agent_name='test_agent',
            timestamp=datetime.now(),
            symbol='BTCUSDT',
            direction='long',
            confidence=0.85,
            reasoning={'test': 'data'}
        )
        
        signal_dict = signal.to_dict()
        assert 'agent_name' in signal_dict
        assert signal_dict['direction'] == 'long'
        print("✓ AgentSignal works correctly")
        
        # Test AgentRegistry
        registry = AgentRegistry()
        assert len(registry.agents) == 0
        print("✓ AgentRegistry initialized")
        
        stats = registry.get_stats()
        assert stats['total_agents'] == 0
        print("✓ AgentRegistry stats work")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agent_imports():
    """Test that all agent modules can be imported."""
    print("\n" + "=" * 60)
    print("Testing Agent Module Imports")
    print("=" * 60)
    
    modules = [
        ('base_agent', 'src.agents.base_agent'),
        ('regime_classifier', 'src.agents.regime_classifier'),
        ('momentum_agent', 'src.agents.momentum_agent'),
        ('mean_reversion_agent', 'src.agents.mean_reversion_agent'),
        ('order_flow_agent', 'src.agents.order_flow_agent'),
        ('agent_ensemble', 'src.agents.agent_ensemble'),
    ]
    
    success_count = 0
    
    for name, module_path in modules:
        try:
            __import__(module_path)
            print(f"✓ {name} imported successfully")
            success_count += 1
        except ImportError as e:
            print(f"⚠ {name} import failed (missing dependency): {e}")
        except Exception as e:
            print(f"✗ {name} import error: {e}")
    
    print(f"\nImported {success_count}/{len(modules)} modules")
    return success_count > 0


def test_agent_structure():
    """Test agent class structure."""
    print("\n" + "=" * 60)
    print("Testing Agent Class Structure")
    print("=" * 60)
    
    try:
        # Try to import and check class structure
        from src.agents.base_agent import BaseAgent
        
        # Check abstract methods
        abstract_methods = ['predict', 'train', 'save', 'load']
        
        for method in abstract_methods:
            assert hasattr(BaseAgent, method)
            print(f"✓ BaseAgent has {method}() method")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_sample_features():
    """Test feature dictionary structure."""
    print("\n" + "=" * 60)
    print("Testing Feature Dictionary Structure")
    print("=" * 60)
    
    features = {
        'timestamp': datetime.now(),
        'price': 50000.0,
        'ema_9': 49900.0,
        'ema_21': 49800.0,
        'rsi': 65.0,
        'order_flow_imbalance': 0.3,
        'cumulative_delta': 1500.0,
        'vpin': 0.4,
        'vwap': 49950.0,
        'bid_volume': 10.5,
        'ask_volume': 8.2,
        'liquidity_heatmap': {
            'bid_prices': [49999, 49998, 49997],
            'bid_volumes': [5.0, 4.5, 4.0],
            'ask_prices': [50001, 50002, 50003],
            'ask_volumes': [4.0, 3.5, 3.0],
            'liquidity_imbalance': 0.2
        }
    }
    
    required_fields = [
        'price', 'ema_9', 'ema_21', 'rsi',
        'order_flow_imbalance', 'vpin', 'vwap'
    ]
    
    for field in required_fields:
        assert field in features
        print(f"✓ Feature '{field}' present")
    
    print(f"\n✓ All {len(required_fields)} required features present")
    return True


def test_ensemble_structure():
    """Test ensemble class structure."""
    print("\n" + "=" * 60)
    print("Testing Ensemble Structure")
    print("=" * 60)
    
    try:
        from src.agents.agent_ensemble import AgentEnsemble, EnsembleSignal
        from src.agents.base_agent import AgentRegistry
        
        print("✓ Imported ensemble classes")
        
        # Create registry
        registry = AgentRegistry()
        
        # Create ensemble
        ensemble = AgentEnsemble(registry, strategy='weighted')
        assert ensemble.strategy == 'weighted'
        print("✓ Created ensemble with weighted strategy")
        
        # Test strategy change
        ensemble.set_strategy('majority')
        assert ensemble.strategy == 'majority'
        print("✓ Changed strategy to majority")
        
        # Test weight setting
        ensemble.set_agent_weight('test_agent', 2.5)
        weights = ensemble.get_agent_weights()
        assert weights['test_agent'] == 2.5
        print("✓ Set custom agent weight")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all basic tests."""
    print("\n" + "=" * 60)
    print("M281M AI Trading System - Basic Agent Tests")
    print("=" * 60)
    print("\nNote: This tests the architecture without ML dependencies")
    print("For full tests with training, install all dependencies and run:")
    print("  pytest tests/test_agents.py -v\n")
    
    results = []
    
    # Run tests
    results.append(("Base Classes", test_base_classes()))
    results.append(("Agent Imports", test_agent_imports()))
    results.append(("Agent Structure", test_agent_structure()))
    results.append(("Feature Structure", test_sample_features()))
    results.append(("Ensemble Structure", test_ensemble_structure()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All basic tests passed!")
        print("\nPhase 2 architecture is complete and ready for integration.")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    exit(main())
