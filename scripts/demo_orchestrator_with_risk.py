"""
Demo: Orchestrator with Risk Management Integration.
Shows how to integrate risk management with the trading orchestrator.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from src.risk import RiskManager, RiskConfig
from src.agents.agent_ensemble import EnsembleSignal, AgentSignal


def simulate_trading_session():
    """Simulate a trading session with risk management."""
    print("=" * 60)
    print("Orchestrator + Risk Management Integration Demo")
    print("=" * 60)
    
    # Initialize risk manager
    risk_config = RiskConfig(
        max_position_size=0.5,
        max_portfolio_exposure=0.80,
        max_daily_drawdown_pct=0.05,
        max_consecutive_losses=3
    )
    
    risk_manager = RiskManager(risk_config, initial_capital=10000)
    
    print(f"\nInitial Capital: $10,000")
    print(f"Risk Profile: Moderate")
    print(f"Max Exposure: {risk_config.max_portfolio_exposure:.0%}")
    print(f"Max Daily Drawdown: {risk_config.max_daily_drawdown_pct:.0%}")
    
    # Simulate portfolio state
    portfolio_state = {
        'balance': 10000,
        'positions': {},
        'timestamp': 0
    }
    
    # Simulate trading signals
    signals = [
        {
            'symbol': 'BTCUSDT',
            'direction': 'long',
            'confidence': 0.75,
            'size': 0.15,
            'price': 50000,
            'atr': 1000,
            'regime': 'trending',
            'expected_pnl': 300
        },
        {
            'symbol': 'ETHUSDT',
            'direction': 'long',
            'confidence': 0.65,
            'size': 1.5,
            'price': 3000,
            'atr': 100,
            'regime': 'volatile',
            'expected_pnl': -150
        },
        {
            'symbol': 'BTCUSDT',
            'direction': 'short',
            'confidence': 0.80,
            'size': 0.1,
            'price': 51000,
            'atr': 1200,
            'regime': 'trending',
            'expected_pnl': 200
        },
        {
            'symbol': 'SOLUSDT',
            'direction': 'long',
            'confidence': 0.70,
            'size': 50,
            'price': 100,
            'atr': 5,
            'regime': 'sideways',
            'expected_pnl': -100
        }
    ]
    
    print("\n" + "=" * 60)
    print("Processing Trading Signals")
    print("=" * 60)
    
    executed_trades = []
    
    for i, signal in enumerate(signals, 1):
        print(f"\n--- Signal {i}: {signal['symbol']} {signal['direction'].upper()} ---")
        print(f"Confidence: {signal['confidence']:.1%}")
        print(f"Regime: {signal['regime']}")
        print(f"Requested size: {signal['size']}")
        
        # Prepare order
        order = {
            'symbol': signal['symbol'],
            'side': signal['direction'],
            'size': signal['size'],
            'price': signal['price']
        }
        
        # Prepare market data
        market_data = {
            'price': signal['price'],
            'atr': signal['atr'],
            'bid': signal['price'] - 5,
            'ask': signal['price'] + 5,
            'volume': 100
        }
        
        # Risk check
        decision = risk_manager.check_order(
            order,
            market_data,
            portfolio_state,
            regime=signal['regime']
        )
        
        print(f"\nRisk Decision:")
        print(f"  Approved: {decision.approved}")
        print(f"  Risk Level: {decision.risk_level.value}")
        
        if decision.approved:
            final_size = decision.adjusted_size or signal['size']
            print(f"  Final size: {final_size:.4f}")
            
            if decision.stop_loss:
                print(f"  Stop Loss: ${decision.stop_loss:.2f}")
            if decision.take_profit:
                print(f"  Take Profit: ${decision.take_profit:.2f}")
            
            if decision.warnings:
                print(f"  Warnings: {len(decision.warnings)}")
                for warning in decision.warnings[:2]:
                    print(f"    - {warning}")
            
            # Simulate trade execution
            position_value = final_size * signal['price']
            portfolio_state['balance'] -= position_value * 0.1  # 10% margin
            
            # Add to positions
            if signal['symbol'] in portfolio_state['positions']:
                existing = portfolio_state['positions'][signal['symbol']]
                existing['size'] += final_size if signal['direction'] == 'long' else -final_size
            else:
                portfolio_state['positions'][signal['symbol']] = {
                    'size': final_size if signal['direction'] == 'long' else -final_size,
                    'price': signal['price'],
                    'stop_loss': decision.stop_loss,
                    'take_profit': decision.take_profit
                }
            
            # Record trade
            trade = {
                'symbol': signal['symbol'],
                'side': signal['direction'],
                'size': final_size,
                'price': signal['price'],
                'pnl': signal['expected_pnl']
            }
            
            executed_trades.append(trade)
            
            # Update portfolio balance with PnL
            portfolio_state['balance'] += signal['expected_pnl']
            
            # Record in risk manager
            risk_manager.record_trade(trade)
            risk_manager.update_portfolio(portfolio_state)
            
            print(f"  [EXECUTED] Position opened")
            
        else:
            print(f"  [REJECTED]")
            for reason in decision.reasons:
                print(f"    - {reason}")
    
    # Final statistics
    print("\n" + "=" * 60)
    print("Session Summary")
    print("=" * 60)
    
    print(f"\nPortfolio:")
    print(f"  Starting balance: $10,000")
    print(f"  Final balance: ${portfolio_state['balance']:.2f}")
    print(f"  Total PnL: ${portfolio_state['balance'] - 10000:.2f}")
    print(f"  Open positions: {len(portfolio_state['positions'])}")
    
    print(f"\nTrades:")
    print(f"  Signals received: {len(signals)}")
    print(f"  Trades executed: {len(executed_trades)}")
    print(f"  Execution rate: {len(executed_trades) / len(signals):.1%}")
    
    # Risk statistics
    stats = risk_manager.get_statistics()
    print(f"\nRisk Management:")
    print(f"  Total checks: {stats['total_checks']}")
    print(f"  Approved: {stats['approved_orders']}")
    print(f"  Rejected: {stats['rejected_orders']}")
    print(f"  Modified: {stats['modified_orders']}")
    print(f"  Approval rate: {stats['approval_rate']:.1%}")
    
    meta_stats = stats['meta_risk']
    print(f"\nMeta-Risk:")
    print(f"  Consecutive losses: {meta_stats['consecutive_losses']}")
    print(f"  Circuit breaker: {'ACTIVE' if meta_stats['circuit_breaker_active'] else 'INACTIVE'}")
    print(f"  Daily trades: {meta_stats['daily_trade_count']}")
    
    # Current risk level
    risk_level = risk_manager.get_current_risk_level()
    print(f"\nCurrent Risk Level: {risk_level.value.upper()}")
    
    print("\n" + "=" * 60)


def main():
    """Run demo."""
    try:
        simulate_trading_session()
        print("\nDemo completed successfully!")
        
    except Exception as e:
        print(f"\n[ERROR] Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
