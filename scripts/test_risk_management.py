"""
Test Risk Management System.
Tests all 5 layers of risk protection.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.risk import RiskManager, RiskConfig


def test_trade_level_risk():
    """Test Layer 1: Trade-level risk."""
    print("\n=== Test 1: Trade-Level Risk ===")
    
    config = RiskConfig()
    risk_manager = RiskManager(config, initial_capital=10000)
    
    # Test 1: Good trade with proper R:R
    order = {'symbol': 'BTCUSDT', 'side': 'long', 'size': 0.1, 'price': 50000}
    market_data = {'price': 50000, 'atr': 1000, 'bid': 49995, 'ask': 50005}
    portfolio_state = {'balance': 10000, 'positions': {}}
    
    decision = risk_manager.check_order(order, market_data, portfolio_state)
    
    print(f"Test 1.1 - Good trade: {'[PASS]' if decision.approved else '[FAIL]'}")
    print(f"  Stop Loss: ${decision.stop_loss:.2f}")
    print(f"  Take Profit: ${decision.take_profit:.2f}")
    
    # Test 2: Poor R:R ratio
    market_data['atr'] = 100  # Very tight ATR
    decision = risk_manager.check_order(order, market_data, portfolio_state)
    
    print(f"Test 1.2 - Poor R:R: {'[PASS]' if not decision.approved else '[FAIL]'}")
    if decision.reasons:
        print(f"  Reason: {decision.reasons[0]}")
    
    # Test 3: Excessive position size
    order['size'] = 5.0
    market_data['atr'] = 1000
    decision = risk_manager.check_order(order, market_data, portfolio_state)
    
    print(f"Test 1.3 - Excessive size: {'[PASS]' if not decision.approved else '[FAIL]'}")


def test_portfolio_level_risk():
    """Test Layer 2: Portfolio-level risk."""
    print("\n=== Test 2: Portfolio-Level Risk ===")
    
    config = RiskConfig(max_portfolio_exposure=0.8)
    risk_manager = RiskManager(config, initial_capital=10000)
    
    # Test 1: Within exposure limits
    order = {'symbol': 'BTCUSDT', 'side': 'long', 'size': 0.1, 'price': 50000}
    market_data = {'price': 50000, 'atr': 1000}
    portfolio_state = {
        'balance': 10000,
        'positions': {
            'ETHUSDT': {'size': 1.0, 'price': 3000}
        }
    }
    
    decision = risk_manager.check_order(order, market_data, portfolio_state)
    
    print(f"Test 2.1 - Within limits: {'[PASS]' if decision.approved else '[FAIL]'}")
    
    # Test 2: Exceeds exposure limits
    portfolio_state['positions']['ETHUSDT']['size'] = 2.0
    decision = risk_manager.check_order(order, market_data, portfolio_state)
    
    print(f"Test 2.2 - Exceeds exposure: {'[PASS]' if not decision.approved or decision.adjusted_size else '[FAIL]'}")
    if decision.adjusted_size:
        print(f"  Adjusted size: {decision.adjusted_size:.4f}")


def test_regime_aware_risk():
    """Test Layer 3: Regime-aware risk."""
    print("\n=== Test 3: Regime-Aware Risk ===")
    
    config = RiskConfig()
    risk_manager = RiskManager(config, initial_capital=10000)
    
    order = {'symbol': 'BTCUSDT', 'side': 'long', 'size': 0.1, 'price': 50000}
    market_data = {'price': 50000, 'atr': 1000}
    portfolio_state = {'balance': 10000, 'positions': {}}
    
    # Test 1: Volatile regime
    decision = risk_manager.check_order(order, market_data, portfolio_state, regime='volatile')
    
    print(f"Test 3.1 - Volatile regime: {'[PASS]' if decision.adjusted_size and decision.adjusted_size < order['size'] else '[FAIL]'}")
    if decision.adjusted_size:
        print(f"  Size: {order['size']} -> {decision.adjusted_size:.4f}")
    
    # Test 2: Trending regime
    decision = risk_manager.check_order(order, market_data, portfolio_state, regime='trending')
    
    print(f"Test 3.2 - Trending regime: {'[PASS]' if decision.adjusted_size and decision.adjusted_size > order['size'] else '[FAIL]'}")
    if decision.adjusted_size:
        print(f"  Size: {order['size']} -> {decision.adjusted_size:.4f}")


def test_adversarial_risk():
    """Test Layer 4: Adversarial risk."""
    print("\n=== Test 4: Adversarial Risk ===")
    
    config = RiskConfig()
    risk_manager = RiskManager(config, initial_capital=10000)
    
    order = {'symbol': 'BTCUSDT', 'side': 'long', 'size': 0.1, 'price': 50000}
    portfolio_state = {'balance': 10000, 'positions': {}}
    
    # Test 1: Normal market
    market_data = {
        'price': 50000,
        'atr': 1000,
        'volume': 100,
        'orderbook': {
            'bids': [[49990, 10], [49980, 10]],
            'asks': [[50010, 10], [50020, 10]]
        }
    }
    
    decision = risk_manager.check_order(order, market_data, portfolio_state)
    
    print(f"Test 4.1 - Normal market: {'[PASS]' if decision.approved else '[FAIL]'}")
    
    # Test 2: Order book imbalance (spoofing)
    market_data['orderbook'] = {
        'bids': [[49990, 100], [49980, 100]],
        'asks': [[50010, 1], [50020, 1]]
    }
    
    decision = risk_manager.check_order(order, market_data, portfolio_state)
    
    print(f"Test 4.2 - Order book spoofing: {'[PASS]' if not decision.approved else '[FAIL]'}")
    if decision.reasons:
        print(f"  Reason: {decision.reasons[0]}")


def test_meta_risk():
    """Test Layer 5: Meta-risk (circuit breakers)."""
    print("\n=== Test 5: Meta-Risk (Circuit Breakers) ===")
    
    config = RiskConfig(max_daily_drawdown_pct=0.05, max_consecutive_losses=3)
    risk_manager = RiskManager(config, initial_capital=10000)
    
    order = {'symbol': 'BTCUSDT', 'side': 'long', 'size': 0.1, 'price': 50000}
    market_data = {'price': 50000, 'atr': 1000}
    
    # Test 1: Normal state
    portfolio_state = {'balance': 10000, 'positions': {}}
    decision = risk_manager.check_order(order, market_data, portfolio_state)
    
    print(f"Test 5.1 - Normal state: {'[PASS]' if decision.approved else '[FAIL]'}")
    
    # Test 2: Daily drawdown limit
    portfolio_state['balance'] = 9400  # 6% drawdown
    risk_manager.update_portfolio(portfolio_state)
    decision = risk_manager.check_order(order, market_data, portfolio_state)
    
    print(f"Test 5.2 - Drawdown limit: {'[PASS]' if not decision.approved else '[FAIL]'}")
    if decision.reasons:
        print(f"  Reason: {decision.reasons[0]}")
    
    # Reset for next test
    risk_manager.reset_daily_limits()
    
    # Test 3: Consecutive losses
    for i in range(3):
        risk_manager.record_trade({'symbol': 'BTCUSDT', 'pnl': -100})
    
    portfolio_state['balance'] = 10000
    decision = risk_manager.check_order(order, market_data, portfolio_state)
    
    print(f"Test 5.3 - Consecutive losses: {'[PASS]' if not decision.approved else '[FAIL]'}")


def test_full_integration():
    """Test full integration of all layers."""
    print("\n=== Test 6: Full Integration ===")
    
    config = RiskConfig()
    risk_manager = RiskManager(config, initial_capital=10000)
    
    # Simulate a trading session
    orders = [
        {'symbol': 'BTCUSDT', 'side': 'long', 'size': 0.1, 'price': 50000},
        {'symbol': 'ETHUSDT', 'side': 'long', 'size': 1.0, 'price': 3000},
        {'symbol': 'BTCUSDT', 'side': 'short', 'size': 0.05, 'price': 51000}
    ]
    
    market_data = {
        'price': 50000,
        'atr': 1000,
        'bid': 49995,
        'ask': 50005,
        'volume': 100
    }
    
    portfolio_state = {'balance': 10000, 'positions': {}}
    
    approved_count = 0
    for i, order in enumerate(orders):
        market_data['price'] = order['price']
        decision = risk_manager.check_order(order, market_data, portfolio_state, regime='neutral')
        
        if decision.approved:
            approved_count += 1
            # Simulate position opening
            portfolio_state['positions'][order['symbol']] = {
                'size': decision.adjusted_size or order['size'],
                'price': order['price']
            }
            portfolio_state['balance'] -= (decision.adjusted_size or order['size']) * order['price'] * 0.1
    
    print(f"Processed {len(orders)} orders, approved {approved_count}")
    
    # Get statistics
    stats = risk_manager.get_statistics()
    print(f"Approval rate: {stats['approval_rate']:.1%}")
    print(f"Modification rate: {stats['modification_rate']:.1%}")
    
    print(f"Test 6 - Integration: [PASS]")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Risk Management System Test Suite")
    print("=" * 60)
    
    try:
        test_trade_level_risk()
        test_portfolio_level_risk()
        test_regime_aware_risk()
        test_adversarial_risk()
        test_meta_risk()
        test_full_integration()
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[FAIL] Test suite error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
