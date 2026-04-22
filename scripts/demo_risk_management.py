"""
Risk Management Demo.
Shows risk management in action with realistic scenarios.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
from src.risk import RiskManager, RiskConfig


def demo_conservative_trading():
    """Demo conservative risk profile."""
    print("\n" + "=" * 60)
    print("Demo 1: Conservative Trading Profile")
    print("=" * 60)
    
    config = RiskConfig.conservative()
    risk_manager = RiskManager(config, initial_capital=10000)
    
    print(f"\nInitial Capital: $10,000")
    print(f"Max Position Size: {config.max_position_size}")
    print(f"Max Portfolio Exposure: {config.max_portfolio_exposure:.0%}")
    print(f"Max Daily Drawdown: {config.max_daily_drawdown_pct:.0%}")
    
    # Scenario: Try to open a large position
    print("\n--- Scenario: Attempting large position ---")
    order = {'symbol': 'BTCUSDT', 'side': 'long', 'size': 0.15, 'price': 50000}
    market_data = {'price': 50000, 'atr': 1000, 'bid': 49995, 'ask': 50005}
    portfolio_state = {'balance': 10000, 'positions': {}}
    
    decision = risk_manager.check_order(order, market_data, portfolio_state)
    
    print(f"Order: {order['side'].upper()} {order['size']} BTC @ ${order['price']}")
    print(f"Approved: {decision.approved}")
    print(f"Risk Level: {decision.risk_level.value}")
    if decision.reasons:
        print(f"Reasons: {', '.join(decision.reasons)}")
    if decision.warnings:
        print(f"Warnings: {', '.join(decision.warnings)}")


def demo_aggressive_trading():
    """Demo aggressive risk profile."""
    print("\n" + "=" * 60)
    print("Demo 2: Aggressive Trading Profile")
    print("=" * 60)
    
    config = RiskConfig.aggressive()
    risk_manager = RiskManager(config, initial_capital=10000)
    
    print(f"\nInitial Capital: $10,000")
    print(f"Max Position Size: {config.max_position_size}")
    print(f"Max Portfolio Exposure: {config.max_portfolio_exposure:.0%}")
    print(f"Max Daily Drawdown: {config.max_daily_drawdown_pct:.0%}")
    print(f"Max Leverage: {config.max_leverage}x")
    
    # Scenario: Multiple positions
    print("\n--- Scenario: Building multiple positions ---")
    
    orders = [
        {'symbol': 'BTCUSDT', 'side': 'long', 'size': 0.15, 'price': 50000},
        {'symbol': 'ETHUSDT', 'side': 'long', 'size': 2.0, 'price': 3000},
        {'symbol': 'SOLUSDT', 'side': 'long', 'size': 50, 'price': 100}
    ]
    
    portfolio_state = {'balance': 10000, 'positions': {}}
    
    for order in orders:
        market_data = {'price': order['price'], 'atr': order['price'] * 0.02}
        decision = risk_manager.check_order(order, market_data, portfolio_state)
        
        print(f"\nOrder: {order['side'].upper()} {order['size']} {order['symbol']} @ ${order['price']}")
        print(f"  Approved: {decision.approved}")
        print(f"  Risk Level: {decision.risk_level.value}")
        
        if decision.approved:
            size = decision.adjusted_size or order['size']
            portfolio_state['positions'][order['symbol']] = {
                'size': size,
                'price': order['price']
            }
            portfolio_state['balance'] -= size * order['price'] * 0.1
            print(f"  Position opened: {size:.4f} units")


def demo_regime_adaptation():
    """Demo regime-based risk adaptation."""
    print("\n" + "=" * 60)
    print("Demo 3: Regime-Based Risk Adaptation")
    print("=" * 60)
    
    config = RiskConfig()
    risk_manager = RiskManager(config, initial_capital=10000)
    
    order = {'symbol': 'BTCUSDT', 'side': 'long', 'size': 0.1, 'price': 50000}
    market_data = {'price': 50000, 'atr': 1000}
    portfolio_state = {'balance': 10000, 'positions': {}}
    
    regimes = ['trending', 'volatile', 'sideways', 'neutral']
    
    print("\nSame order in different market regimes:")
    print(f"Base order: {order['side'].upper()} {order['size']} BTC @ ${order['price']}")
    
    for regime in regimes:
        decision = risk_manager.check_order(order, market_data, portfolio_state, regime=regime)
        
        final_size = decision.adjusted_size or order['size']
        adjustment = ((final_size / order['size']) - 1) * 100
        
        print(f"\n{regime.upper()} regime:")
        print(f"  Final size: {final_size:.4f} ({adjustment:+.0f}%)")
        print(f"  Risk level: {decision.risk_level.value}")


def demo_circuit_breakers():
    """Demo circuit breaker activation."""
    print("\n" + "=" * 60)
    print("Demo 4: Circuit Breakers in Action")
    print("=" * 60)
    
    config = RiskConfig(max_consecutive_losses=3, max_daily_drawdown_pct=0.05)
    risk_manager = RiskManager(config, initial_capital=10000)
    
    order = {'symbol': 'BTCUSDT', 'side': 'long', 'size': 0.1, 'price': 50000}
    market_data = {'price': 50000, 'atr': 1000}
    portfolio_state = {'balance': 10000, 'positions': {}}
    
    print("\n--- Scenario: Consecutive losses trigger circuit breaker ---")
    
    # Simulate 3 consecutive losses
    for i in range(3):
        print(f"\nTrade {i+1}: Loss of $200")
        risk_manager.record_trade({'symbol': 'BTCUSDT', 'pnl': -200})
        portfolio_state['balance'] -= 200
    
    # Try to place another order
    print("\n--- Attempting new order after 3 losses ---")
    decision = risk_manager.check_order(order, market_data, portfolio_state)
    
    print(f"Approved: {decision.approved}")
    print(f"Risk Level: {decision.risk_level.value}")
    if decision.reasons:
        print(f"Reasons: {', '.join(decision.reasons)}")
    
    # Show statistics
    stats = risk_manager.get_statistics()
    print(f"\nMeta-risk stats:")
    print(f"  Consecutive losses: {stats['meta_risk']['consecutive_losses']}")
    print(f"  Circuit breaker: {'ACTIVE' if stats['meta_risk']['circuit_breaker_active'] else 'INACTIVE'}")


def demo_adversarial_detection():
    """Demo adversarial risk detection."""
    print("\n" + "=" * 60)
    print("Demo 5: Adversarial Risk Detection")
    print("=" * 60)
    
    config = RiskConfig()
    risk_manager = RiskManager(config, initial_capital=10000)
    
    order = {'symbol': 'BTCUSDT', 'side': 'long', 'size': 0.1, 'price': 50000}
    portfolio_state = {'balance': 10000, 'positions': {}}
    
    print("\n--- Scenario 1: Normal market conditions ---")
    market_data = {
        'price': 50000,
        'atr': 1000,
        'volume': 100,
        'orderbook': {
            'bids': [[49990, 10], [49980, 10], [49970, 10]],
            'asks': [[50010, 10], [50020, 10], [50030, 10]]
        }
    }
    
    decision = risk_manager.check_order(order, market_data, portfolio_state)
    print(f"Approved: {decision.approved}")
    print(f"Risk Level: {decision.risk_level.value}")
    
    print("\n--- Scenario 2: Suspected order book spoofing ---")
    market_data['orderbook'] = {
        'bids': [[49990, 100], [49980, 100], [49970, 100]],
        'asks': [[50010, 1], [50020, 1], [50030, 1]]
    }
    
    decision = risk_manager.check_order(order, market_data, portfolio_state)
    print(f"Approved: {decision.approved}")
    print(f"Risk Level: {decision.risk_level.value}")
    if decision.reasons:
        print(f"Detection: {decision.reasons[0]}")


def demo_full_workflow():
    """Demo complete risk management workflow."""
    print("\n" + "=" * 60)
    print("Demo 6: Complete Risk Management Workflow")
    print("=" * 60)
    
    config = RiskConfig()
    risk_manager = RiskManager(config, initial_capital=10000)
    
    print("\nSimulating a trading session with multiple orders...")
    
    scenarios = [
        {
            'name': 'Good trade in trending market',
            'order': {'symbol': 'BTCUSDT', 'side': 'long', 'size': 0.1, 'price': 50000},
            'market': {'price': 50000, 'atr': 1000, 'volume': 100},
            'regime': 'trending'
        },
        {
            'name': 'Risky trade in volatile market',
            'order': {'symbol': 'ETHUSDT', 'side': 'long', 'size': 1.0, 'price': 3000},
            'market': {'price': 3000, 'atr': 200, 'volume': 500},
            'regime': 'volatile'
        },
        {
            'name': 'Trade with poor R:R ratio',
            'order': {'symbol': 'SOLUSDT', 'side': 'short', 'size': 10, 'price': 100},
            'market': {'price': 100, 'atr': 1, 'volume': 50},
            'regime': 'sideways'
        }
    ]
    
    portfolio_state = {'balance': 10000, 'positions': {}}
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n--- Trade {i}: {scenario['name']} ---")
        
        decision = risk_manager.check_order(
            scenario['order'],
            scenario['market'],
            portfolio_state,
            regime=scenario['regime']
        )
        
        print(f"Order: {scenario['order']['side'].upper()} {scenario['order']['size']} {scenario['order']['symbol']}")
        print(f"Regime: {scenario['regime']}")
        print(f"Approved: {decision.approved}")
        print(f"Risk Level: {decision.risk_level.value}")
        
        if decision.adjusted_size:
            print(f"Size adjusted: {scenario['order']['size']} -> {decision.adjusted_size:.4f}")
        
        if decision.stop_loss:
            print(f"Stop Loss: ${decision.stop_loss:.2f}")
        
        if decision.take_profit:
            print(f"Take Profit: ${decision.take_profit:.2f}")
        
        if decision.warnings:
            print(f"Warnings: {len(decision.warnings)}")
            for warning in decision.warnings:
                print(f"  - {warning}")
        
        if decision.reasons:
            print(f"Rejection reasons:")
            for reason in decision.reasons:
                print(f"  - {reason}")
    
    # Final statistics
    print("\n" + "=" * 60)
    print("Session Statistics")
    print("=" * 60)
    
    stats = risk_manager.get_statistics()
    print(f"Total checks: {stats['total_checks']}")
    print(f"Approved: {stats['approved_orders']}")
    print(f"Rejected: {stats['rejected_orders']}")
    print(f"Modified: {stats['modified_orders']}")
    print(f"Approval rate: {stats['approval_rate']:.1%}")


def main():
    """Run all demos."""
    print("=" * 60)
    print("Risk Management System Demo")
    print("=" * 60)
    
    try:
        demo_conservative_trading()
        time.sleep(1)
        
        demo_aggressive_trading()
        time.sleep(1)
        
        demo_regime_adaptation()
        time.sleep(1)
        
        demo_circuit_breakers()
        time.sleep(1)
        
        demo_adversarial_detection()
        time.sleep(1)
        
        demo_full_workflow()
        
        print("\n" + "=" * 60)
        print("Demo completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
