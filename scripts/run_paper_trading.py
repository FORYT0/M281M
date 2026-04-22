"""
Paper Trading Runner - Stage 3 of Phase 6.
Runs the complete trading system in paper trading mode.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import time
from datetime import datetime
from typing import Dict, Any
import numpy as np

from src.pipeline.websocket_client import BinanceWebSocketClient
from src.pipeline.features import FeatureCalculator
from src.agents import (
    MomentumAgent, MeanReversionAgent, 
    OrderFlowAgent, RegimeClassifier, AgentEnsemble
)
from src.orchestrator import TradingOrchestrator
from src.risk import RiskManager, RiskConfig
from src.deployment.paper_trader import PaperTradingEngine


class LiveTradingSystem:
    """
    Complete live trading system integrating all components.
    
    Pipeline:
    WebSocket → Features → Agents → Ensemble → Orchestrator → Risk → Paper Trading
    """
    
    def __init__(
        self,
        symbol: str = 'BTC/USDT',
        initial_balance: float = 10000.0,
        risk_profile: str = 'conservative'
    ):
        """
        Initialize live trading system.
        
        Args:
            symbol: Trading symbol
            initial_balance: Starting balance
            risk_profile: 'conservative' or 'aggressive'
        """
        self.symbol = symbol
        self.symbol_ws = symbol.replace('/', '').lower()  # btcusdt
        
        print(f"\nInitializing Live Trading System")
        print(f"Symbol: {symbol}")
        print(f"Initial Balance: ${initial_balance:,.2f}")
        print(f"Risk Profile: {risk_profile}")
        
        # Initialize components
        self.feature_calculator = FeatureCalculator()
        self.paper_trader = PaperTradingEngine(
            initial_balance=initial_balance,
            use_testnet=True
        )
        
        # Initialize risk manager
        if risk_profile == 'conservative':
            risk_config = RiskConfig.conservative()
        elif risk_profile == 'aggressive':
            risk_config = RiskConfig.aggressive()
        else:
            risk_config = RiskConfig()
        
        self.risk_manager = RiskManager(risk_config, initial_balance)
        
        # Load agents (will use pre-trained models if available)
        self._load_agents()
        
        # Initialize ensemble
        self.ensemble = AgentEnsemble(
            momentum_agent=self.momentum_agent,
            mean_reversion_agent=self.mean_reversion_agent,
            order_flow_agent=self.order_flow_agent,
            regime_classifier=self.regime_classifier
        )
        
        # Initialize orchestrator
        self.orchestrator = TradingOrchestrator(
            ensemble=self.ensemble,
            initial_balance=initial_balance,
            min_confidence=0.6,
            min_agreement=0.5
        )
        
        # State
        self.current_price = None
        self.features = None
        self.last_signal_time = 0
        self.signal_cooldown = 60  # 60 seconds between signals
        
        # Statistics
        self.start_time = time.time()
        self.messages_processed = 0
        self.signals_generated = 0
        self.trades_executed = 0
        
        print("System initialized successfully\n")
    
    def _load_agents(self):
        """Load pre-trained agents or create new ones."""
        try:
            # Try to load trained models
            self.momentum_agent = MomentumAgent(input_size=50)
            self.momentum_agent.load('models/momentum_agent.pt')
            print("Loaded Momentum Agent")
        except:
            self.momentum_agent = MomentumAgent(input_size=50)
            print("Created new Momentum Agent (untrained)")
        
        try:
            self.mean_reversion_agent = MeanReversionAgent()
            self.mean_reversion_agent.load('models/mean_reversion_agent.json')
            print("Loaded Mean Reversion Agent")
        except:
            self.mean_reversion_agent = MeanReversionAgent()
            print("Created new Mean Reversion Agent (untrained)")
        
        try:
            self.order_flow_agent = OrderFlowAgent(state_size=50)
            self.order_flow_agent.load('models/order_flow_agent.pt')
            print("Loaded Order Flow Agent")
        except:
            self.order_flow_agent = OrderFlowAgent(state_size=50)
            print("Created new Order Flow Agent (untrained)")
        
        try:
            self.regime_classifier = RegimeClassifier()
            self.regime_classifier.load('models/regime_classifier.pkl')
            print("Loaded Regime Classifier")
        except:
            self.regime_classifier = RegimeClassifier()
            print("Created new Regime Classifier (untrained)")
    
    async def handle_message(self, data: dict):
        """Process incoming WebSocket message."""
        try:
            stream = data.get('stream', '')
            event_data = data.get('data', {})
            
            if 'ticker' in stream:
                await self._handle_ticker(event_data)
            elif 'depth' in stream:
                await self._handle_orderbook(event_data)
            
            self.messages_processed += 1
            
        except Exception as e:
            print(f"Error handling message: {e}")
    
    async def _handle_ticker(self, data: dict):
        """Handle ticker update."""
        try:
            self.current_price = float(data.get('c', 0))
            
            # Update paper trader positions
            if self.current_price:
                self.paper_trader.update_positions({
                    self.symbol: self.current_price
                })
            
        except Exception as e:
            print(f"Error handling ticker: {e}")
    
    async def _handle_orderbook(self, data: dict):
        """Handle order book update and generate signals."""
        try:
            # Extract order book data
            bids = data.get('bids', [])
            asks = data.get('asks', [])
            
            if not bids or not asks:
                return
            
            # Calculate features
            features = self._calculate_features(data)
            if features is None:
                return
            
            self.features = features
            
            # Check cooldown
            current_time = time.time()
            if current_time - self.last_signal_time < self.signal_cooldown:
                return
            
            # Generate trading signal
            await self._generate_signal()
            
            self.last_signal_time = current_time
            
        except Exception as e:
            print(f"Error handling orderbook: {e}")
    
    def _calculate_features(self, orderbook_data: dict) -> Dict[str, Any]:
        """Calculate features from order book."""
        try:
            bids = orderbook_data.get('bids', [])
            asks = orderbook_data.get('asks', [])
            
            if not bids or not asks:
                return None
            
            # Extract basic features
            best_bid = float(bids[0][0])
            best_ask = float(asks[0][0])
            mid_price = (best_bid + best_ask) / 2
            spread = best_ask - best_bid
            
            # Calculate imbalance
            bid_volume = sum(float(bid[1]) for bid in bids[:5])
            ask_volume = sum(float(ask[1]) for ask in asks[:5])
            total_volume = bid_volume + ask_volume
            imbalance = (bid_volume - ask_volume) / total_volume if total_volume > 0 else 0
            
            # Create feature dict
            features = {
                'price': mid_price,
                'spread': spread,
                'spread_bps': (spread / mid_price) * 10000,
                'imbalance': imbalance,
                'bid_volume': bid_volume,
                'ask_volume': ask_volume
            }
            
            return features
            
        except Exception as e:
            print(f"Error calculating features: {e}")
            return None
    
    async def _generate_signal(self):
        """Generate and execute trading signal."""
        try:
            if not self.features or not self.current_price:
                return
            
            # Create feature array (simplified - in production use full feature set)
            feature_array = np.array([
                self.features['price'],
                self.features['spread_bps'],
                self.features['imbalance'],
                self.features['bid_volume'],
                self.features['ask_volume']
            ])
            
            # Pad to expected size (50 features)
            feature_array = np.pad(feature_array, (0, 45), mode='constant')
            
            # Get ensemble signal
            ensemble_signal = self.ensemble.get_ensemble_signal(
                features=feature_array,
                current_price=self.current_price
            )
            
            self.signals_generated += 1
            
            # Skip if no clear signal
            if ensemble_signal.direction == 'neutral':
                return
            
            # Prepare order
            order = {
                'symbol': self.symbol,
                'side': ensemble_signal.direction,
                'size': 0.01,  # Small size for paper trading
                'price': self.current_price
            }
            
            # Prepare market data for risk check
            market_data = {
                'price': self.current_price,
                'atr': self.current_price * 0.02,  # Estimate 2% ATR
                'bid': self.current_price - self.features['spread'] / 2,
                'ask': self.current_price + self.features['spread'] / 2,
                'volume': self.features['bid_volume'] + self.features['ask_volume']
            }
            
            # Get portfolio state
            portfolio_state = {
                'balance': self.paper_trader.balance,
                'positions': {
                    sym: {
                        'size': pos.size,
                        'price': pos.entry_price
                    }
                    for sym, pos in self.paper_trader.positions.items()
                }
            }
            
            # Risk check
            decision = self.risk_manager.check_order(
                order,
                market_data,
                portfolio_state,
                regime=ensemble_signal.agent_signals.get('regime_classifier', {}).get('reasoning', {}).get('regime', 'neutral')
            )
            
            if not decision.approved:
                print(f"\n[REJECTED] {ensemble_signal.direction.upper()} signal")
                print(f"  Reasons: {', '.join(decision.reasons)}")
                return
            
            # Execute trade
            await self._execute_trade(ensemble_signal, decision)
            
        except Exception as e:
            print(f"Error generating signal: {e}")
            import traceback
            traceback.print_exc()
    
    async def _execute_trade(self, signal, decision):
        """Execute trade through paper trader."""
        try:
            # Check if we have an existing position
            existing_position = self.paper_trader.get_position(self.symbol)
            
            if existing_position:
                # Close existing position if signal changed
                if existing_position.side != signal.direction:
                    trade = self.paper_trader.close_position(
                        self.symbol,
                        self.current_price
                    )
                    
                    if trade:
                        self.trades_executed += 1
                        self.risk_manager.record_trade({
                            'symbol': self.symbol,
                            'pnl': trade.pnl
                        })
                        self._print_trade_summary(trade)
            else:
                # Open new position
                trade = self.paper_trader.open_position(
                    symbol=self.symbol,
                    side=signal.direction,
                    size=decision.adjusted_size or 0.01,
                    price=self.current_price,
                    stop_loss=decision.stop_loss,
                    take_profit=decision.take_profit,
                    metadata={
                        'confidence': signal.confidence,
                        'agreement': signal.agreement_score
                    }
                )
                
                if trade:
                    self.trades_executed += 1
                    print(f"\n[EXECUTED] {signal.direction.upper()} signal")
                    print(f"  Size: {trade.size:.6f}")
                    print(f"  Price: ${trade.price:.2f}")
                    print(f"  Confidence: {signal.confidence:.1%}")
                    print(f"  Stop Loss: ${decision.stop_loss:.2f}")
                    print(f"  Take Profit: ${decision.take_profit:.2f}")
            
        except Exception as e:
            print(f"Error executing trade: {e}")
    
    def _print_trade_summary(self, trade):
        """Print trade summary."""
        print(f"\n[CLOSED] Position closed")
        print(f"  PnL: ${trade.pnl:+.2f}")
        print(f"  Hold time: {trade.metadata.get('hold_time', 0) / 60:.1f} minutes")
    
    def print_status(self):
        """Print system status."""
        uptime = time.time() - self.start_time
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        
        print("\n" + "="*60)
        print(f"Live Trading System Status - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        print(f"Uptime: {hours:02d}:{minutes:02d}")
        print(f"Messages: {self.messages_processed:,}")
        print(f"Signals: {self.signals_generated}")
        print(f"Trades: {self.trades_executed}")
        print(f"Current Price: ${self.current_price:.2f}" if self.current_price else "Current Price: N/A")
        
        # Paper trading stats
        self.paper_trader.print_status()
        
        # Risk stats
        risk_stats = self.risk_manager.get_statistics()
        print("Risk Management:")
        print(f"  Approval rate: {risk_stats['approval_rate']:.1%}")
        print(f"  Rejected: {risk_stats['rejected_orders']}")
        print(f"  Circuit breaker: {'ACTIVE' if risk_stats['meta_risk']['circuit_breaker_active'] else 'INACTIVE'}")
        print("="*60 + "\n")
    
    async def start(self):
        """Start live trading system."""
        print("\nStarting live trading system...")
        print("Press Ctrl+C to stop\n")
        
        # Define streams
        streams = [
            f'{self.symbol_ws}@ticker',
            f'{self.symbol_ws}@depth20@100ms'
        ]
        
        # Create WebSocket client
        client = BinanceWebSocketClient(
            streams=streams,
            callback=self.handle_message,
            testnet=False,  # Use mainnet for data
            max_reconnect_attempts=999999
        )
        
        # Start status printer
        async def print_status_loop():
            while True:
                await asyncio.sleep(300)  # Every 5 minutes
                self.print_status()
        
        # Run both tasks
        try:
            await asyncio.gather(
                client.start(),
                print_status_loop()
            )
        except KeyboardInterrupt:
            print("\n\nStopping system...")
            self.print_status()
            print("System stopped.")


async def main():
    """Main entry point."""
    print("="*60)
    print("Paper Trading System - Phase 6 Stage 3")
    print("="*60)
    print("\nThis runs the complete trading system in paper trading mode.")
    print("No real money is at risk.")
    print("\nPress Ctrl+C to stop")
    print("="*60)
    
    # Create system
    system = LiveTradingSystem(
        symbol='BTC/USDT',
        initial_balance=10000.0,
        risk_profile='conservative'
    )
    
    # Start trading
    await system.start()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSystem stopped by user")
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
