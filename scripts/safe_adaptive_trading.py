"""
SAFE Adaptive Paper Trading System
With Hard Risk Kill Switch, Fixed Risk Per Trade, and Controlled Learning
"""
import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger
import sys
import pickle
from datetime import datetime, timedelta
import time
import json
import asyncio
from collections import deque

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.pipeline.websocket_client import BinanceWebSocketClient


class RiskKillSwitch:
    """Hard risk kill switch - stops trading on dangerous conditions"""
    
    def __init__(self, initial_capital):
        self.initial_capital = initial_capital
        self.max_drawdown_pct = 10.0  # 10% max drawdown
        self.max_consecutive_losses = 5
        self.max_daily_loss_pct = 3.0  # 3% max daily loss
        self.min_avg_confidence = 0.60  # 60% minimum confidence
        
        self.consecutive_losses = 0
        self.daily_start_capital = initial_capital
        self.daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0)
        self.confidence_buffer = deque(maxlen=20)
        
        self.is_killed = False
        self.kill_reason = None
        
        logger.info("🛡️ Risk Kill Switch Armed")
        logger.info(f"  Max Drawdown: {self.max_drawdown_pct}%")
        logger.info(f"  Max Consecutive Losses: {self.max_consecutive_losses}")
        logger.info(f"  Max Daily Loss: {self.max_daily_loss_pct}%")
        logger.info(f"  Min Avg Confidence: {self.min_avg_confidence}")
    
    def check(self, current_capital, position_value, last_trade_pnl, confidence):
        """Check all kill switch conditions"""
        if self.is_killed:
            return True
        
        total_value = current_capital + position_value
        
        # Reset daily tracking
        now = datetime.now()
        if now.date() > self.daily_reset_time.date():
            self.daily_start_capital = total_value
            self.daily_reset_time = now.replace(hour=0, minute=0, second=0)
            logger.info(f"📅 Daily reset - Starting capital: ${self.daily_start_capital:,.2f}")
        
        # Track confidence
        self.confidence_buffer.append(confidence)
        
        # 1. Check drawdown
        drawdown_pct = ((self.initial_capital - total_value) / self.initial_capital) * 100
        if drawdown_pct > self.max_drawdown_pct:
            self.kill(f"DRAWDOWN EXCEEDED: {drawdown_pct:.2f}% > {self.max_drawdown_pct}%")
            return True
        
        # 2. Check consecutive losses
        if last_trade_pnl is not None:
            if last_trade_pnl < 0:
                self.consecutive_losses += 1
                if self.consecutive_losses >= self.max_consecutive_losses:
                    self.kill(f"CONSECUTIVE LOSSES: {self.consecutive_losses} trades")
                    return True
            else:
                self.consecutive_losses = 0
        
        # 3. Check daily loss
        daily_loss_pct = ((self.daily_start_capital - total_value) / self.daily_start_capital) * 100
        if daily_loss_pct > self.max_daily_loss_pct:
            self.kill(f"DAILY LOSS EXCEEDED: {daily_loss_pct:.2f}% > {self.max_daily_loss_pct}%")
            return True
        
        # 4. Check average confidence
        if len(self.confidence_buffer) >= 10:
            avg_confidence = np.mean(self.confidence_buffer)
            if avg_confidence < self.min_avg_confidence:
                self.kill(f"LOW CONFIDENCE: {avg_confidence:.3f} < {self.min_avg_confidence}")
                return True
        
        return False
    
    def kill(self, reason):
        """Trigger kill switch"""
        self.is_killed = True
        self.kill_reason = reason
        logger.error("=" * 60)
        logger.error("🚨 KILL SWITCH TRIGGERED 🚨")
        logger.error(f"Reason: {reason}")
        logger.error("Trading stopped. Manual restart required.")
        logger.error("=" * 60)
    
    def get_status(self):
        """Get current risk status"""
        return {
            'is_killed': self.is_killed,
            'kill_reason': self.kill_reason,
            'consecutive_losses': self.consecutive_losses,
            'avg_confidence': np.mean(self.confidence_buffer) if self.confidence_buffer else 0.0
        }


class SafeAdaptivePaperTrader:
    """Safe paper trading with risk management and controlled learning"""
    
    def __init__(self, initial_capital=10000, risk_per_trade_pct=1.0, learning_mode='observe'):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.position = 0
        self.position_entry_price = 0
        self.trades = []
        self.equity_curve = []
        self.start_time = datetime.now()  # Track start time
        
        # Risk management
        self.risk_per_trade_pct = risk_per_trade_pct
        self.stop_loss_pct = 0.5  # 0.5% stop loss
        self.kill_switch = RiskKillSwitch(initial_capital)
        
        # Learning control
        self.learning_mode = learning_mode  # 'observe', 'test', 'active'
        self.experience_buffer = deque(maxlen=1000)
        self.shadow_models = {}  # Test models before replacing main ones
        self.learning_start_date = datetime.now() + timedelta(days=14)  # 2 weeks delay
        
        # Load models
        self.models = self.load_models()
        
        # Feature buffer
        self.price_buffer = []
        self.volume_buffer = []
        self.max_buffer_size = 100
        
        # Performance tracking
        self.model_performance = {name: {'correct': 0, 'total': 0} for name in self.models.keys()}
        
        logger.info(f"💰 Safe Adaptive Trader initialized with ${initial_capital:,.2f}")
        logger.info(f"⚖️ Risk per trade: {risk_per_trade_pct}% (${initial_capital * risk_per_trade_pct / 100:.2f})")
        logger.info(f"🛑 Stop loss: {self.stop_loss_pct}%")
        logger.info(f"🧠 Learning mode: {learning_mode.upper()}")
        if learning_mode == 'observe':
            logger.info(f"📅 Active learning starts: {self.learning_start_date.strftime('%Y-%m-%d')}")
    
    def load_models(self):
        """Load trained models"""
        models = {}
        for name in ['momentum', 'mean_reversion', 'order_flow']:
            try:
                model_path = Path(f"models/{name}_agent_live.pkl")
                with open(model_path, 'rb') as f:
                    models[name] = pickle.load(f)
                logger.info(f"✓ Loaded {name} model")
            except Exception as e:
                logger.error(f"✗ Failed to load {name} model: {e}")
        return models
    
    def calculate_position_size(self, price):
        """Calculate position size based on fixed risk per trade"""
        # Risk amount in dollars
        risk_amount = self.capital * (self.risk_per_trade_pct / 100)
        
        # Stop loss distance in dollars
        stop_distance = price * (self.stop_loss_pct / 100)
        
        # Position size = Risk / Stop Distance
        position_size_btc = risk_amount / stop_distance
        
        # Max position value = 90% of capital
        max_position_value = self.capital * 0.9
        max_position_size = max_position_value / price
        
        # Use smaller of the two
        position_size = min(position_size_btc, max_position_size)
        
        logger.debug(f"Position sizing: Risk=${risk_amount:.2f}, Stop=${stop_distance:.2f}, Size={position_size:.6f} BTC")
        
        return position_size
    
    def calculate_features(self, price, volume):
        """Calculate features from price/volume history"""
        if len(self.price_buffer) < 30:
            return None
        
        prices = np.array(self.price_buffer)
        volumes = np.array(self.volume_buffer)
        
        features = {
            'price': price,
            'volume': volume,
            'returns': (prices[-1] - prices[-2]) / prices[-2] if len(prices) > 1 else 0,
            'sma_10': np.mean(prices[-10:]) if len(prices) >= 10 else price,
            'sma_20': np.mean(prices[-20:]) if len(prices) >= 20 else price,
            'rsi': self.calculate_rsi(prices),
            'volatility': np.std(prices[-20:]) / np.mean(prices[-20:]) if len(prices) >= 20 else 0
        }
        
        return features
    
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = np.diff(prices[-period-1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def get_ensemble_signal(self, features):
        """Get ensemble prediction from all models"""
        if not features or not self.models:
            return 1, 0.0, {}
        
        feature_array = np.array([[
            features['price'],
            features['volume'],
            features['returns'],
            features['sma_10'],
            features['sma_20'],
            features['rsi'],
            features['volatility']
        ]])
        
        predictions = {}
        confidences = {}
        
        for name, model_data in self.models.items():
            try:
                X_scaled = model_data['scaler'].transform(feature_array)
                pred = model_data['model'].predict(X_scaled)[0]
                proba = model_data['model'].predict_proba(X_scaled)[0]
                conf = np.max(proba)
                
                predictions[name] = pred
                confidences[name] = conf
                
            except Exception as e:
                logger.error(f"Prediction error for {name}: {e}")
        
        if not predictions:
            return 1, 0.0, {}
        
        # Weighted voting based on recent performance
        weighted_votes = []
        for name, pred in predictions.items():
            perf = self.model_performance[name]
            accuracy = perf['correct'] / perf['total'] if perf['total'] > 0 else 0.5
            weight = max(0.1, accuracy)
            weighted_votes.extend([pred] * int(weight * 10))
        
        signal = max(set(weighted_votes), key=weighted_votes.count)
        avg_confidence = np.mean(list(confidences.values()))
        
        return signal, avg_confidence, predictions
    
    def store_experience(self, features, signal, actual_outcome, price):
        """Store experience for learning (observe mode)"""
        experience = {
            'features': features,
            'signal': signal,
            'actual_outcome': actual_outcome,
            'price': price,
            'timestamp': datetime.now()
        }
        self.experience_buffer.append(experience)
        
        logger.info(f"📝 Experience stored ({len(self.experience_buffer)}/1000)")
        
        # Check if we should start active learning
        if self.learning_mode == 'observe' and datetime.now() >= self.learning_start_date:
            if len(self.experience_buffer) >= 100:
                logger.info("=" * 60)
                logger.info("🎓 2 weeks complete! Ready for active learning.")
                logger.info(f"Collected {len(self.experience_buffer)} experiences")
                logger.info("Restart with learning_mode='active' to enable model updates")
                logger.info("=" * 60)
    
    def update_model_performance(self, predictions, actual_outcome):
        """Update model performance tracking"""
        for name, pred in predictions.items():
            self.model_performance[name]['total'] += 1
            if pred == actual_outcome:
                self.model_performance[name]['correct'] += 1
    
    def check_stop_loss(self, current_price):
        """Check if stop loss is hit"""
        if self.position > 0:
            loss_pct = ((self.position_entry_price - current_price) / self.position_entry_price) * 100
            if loss_pct >= self.stop_loss_pct:
                logger.warning(f"🛑 Stop loss triggered: {loss_pct:.2f}% loss")
                return True
        return False
    
    def execute_trade(self, signal, price, confidence, predictions, timestamp):
        """Execute paper trade with risk management"""
        # Check kill switch first
        position_value = self.position * price
        last_pnl = self.trades[-1]['pnl'] if self.trades and 'pnl' in self.trades[-1] else None
        
        if self.kill_switch.check(self.capital, position_value, last_pnl, confidence):
            # Close position if open
            if self.position > 0:
                logger.warning("⚠️ Closing position due to kill switch")
                self.force_close_position(price, timestamp, "KILL_SWITCH")
            return
        
        # Check stop loss
        if self.check_stop_loss(price):
            self.force_close_position(price, timestamp, "STOP_LOSS")
            return
        
        signal_names = ['SELL', 'HOLD', 'BUY']
        min_confidence = 0.85
        
        if confidence < min_confidence:
            return
        
        # BUY signal
        if signal == 2 and self.position == 0:
            # Calculate position size based on risk
            btc_amount = self.calculate_position_size(price)
            buy_value = btc_amount * price
            
            if buy_value > self.capital:
                logger.warning(f"Insufficient capital: ${buy_value:.2f} > ${self.capital:.2f}")
                return
            
            self.position = btc_amount
            self.position_entry_price = price
            self.capital -= buy_value
            
            trade = {
                'timestamp': timestamp,
                'action': 'BUY',
                'price': price,
                'amount': btc_amount,
                'value': buy_value,
                'confidence': confidence,
                'predictions': predictions,
                'stop_loss': price * (1 - self.stop_loss_pct / 100)
            }
            self.trades.append(trade)
            
            logger.info(f"🟢 BUY: {btc_amount:.6f} BTC @ ${price:.2f} (conf: {confidence:.3f})")
            logger.info(f"   Stop Loss: ${trade['stop_loss']:.2f}")
        
        # SELL signal
        elif signal == 0 and self.position > 0:
            self.close_position(price, timestamp, predictions, confidence, "SIGNAL")
    
    def close_position(self, price, timestamp, predictions, confidence, reason):
        """Close position and learn from result"""
        sell_value = self.position * price
        pnl = sell_value - (self.position * self.position_entry_price)
        pnl_pct = (pnl / (self.position * self.position_entry_price)) * 100
        
        self.capital += sell_value
        
        # Determine actual outcome
        if pnl > 0:
            actual_outcome = 2  # UP
        elif pnl < 0:
            actual_outcome = 0  # DOWN
        else:
            actual_outcome = 1  # HOLD
        
        # Update model performance
        self.update_model_performance(predictions, actual_outcome)
        
        # Store experience
        features = self.calculate_features(price, self.volume_buffer[-1] if self.volume_buffer else 0)
        if features:
            self.store_experience(features, 0, actual_outcome, price)
        
        trade = {
            'timestamp': timestamp,
            'action': 'SELL',
            'reason': reason,
            'price': price,
            'amount': self.position,
            'value': sell_value,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'confidence': confidence,
            'predictions': predictions
        }
        self.trades.append(trade)
        
        logger.info(f"🔴 SELL ({reason}): {self.position:.6f} BTC @ ${price:.2f} | PnL: ${pnl:.2f} ({pnl_pct:+.2f}%)")
        logger.info(f"📚 Learning: Outcome = {['DOWN', 'HOLD', 'UP'][actual_outcome]}")
        
        self.position = 0
        self.position_entry_price = 0
    
    def force_close_position(self, price, timestamp, reason):
        """Force close position (stop loss or kill switch)"""
        if self.position == 0:
            return
        
        sell_value = self.position * price
        pnl = sell_value - (self.position * self.position_entry_price)
        pnl_pct = (pnl / (self.position * self.position_entry_price)) * 100
        
        self.capital += sell_value
        
        trade = {
            'timestamp': timestamp,
            'action': 'FORCE_CLOSE',
            'reason': reason,
            'price': price,
            'amount': self.position,
            'value': sell_value,
            'pnl': pnl,
            'pnl_pct': pnl_pct
        }
        self.trades.append(trade)
        
        logger.warning(f"⚠️ FORCE CLOSE ({reason}): {self.position:.6f} BTC @ ${price:.2f} | PnL: ${pnl:.2f} ({pnl_pct:+.2f}%)")
        
        self.position = 0
        self.position_entry_price = 0
    
    def update_equity(self, price, timestamp):
        """Update equity curve"""
        total_value = self.capital + (self.position * price)
        
        self.equity_curve.append({
            'timestamp': timestamp,
            'capital': self.capital,
            'position_value': self.position * price,
            'total_value': total_value,
            'returns': ((total_value - self.initial_capital) / self.initial_capital) * 100
        })
    
    def on_ticker_update(self, data):
        """Handle ticker updates"""
        try:
            # Check if killed
            if self.kill_switch.is_killed:
                logger.error("System killed. Stopping...")
                raise KeyboardInterrupt("Kill switch triggered")
            
            price = float(data['c'])
            volume = float(data['v'])
            timestamp = datetime.fromtimestamp(data['E'] / 1000)
            
            self.price_buffer.append(price)
            self.volume_buffer.append(volume)
            
            if len(self.price_buffer) > self.max_buffer_size:
                self.price_buffer.pop(0)
                self.volume_buffer.pop(0)
            
            features = self.calculate_features(price, volume)
            
            if features:
                signal, confidence, predictions = self.get_ensemble_signal(features)
                signal_names = ['SELL', 'HOLD', 'BUY']
                
                self.execute_trade(signal, price, confidence, predictions, timestamp)
                self.update_equity(price, timestamp)
                
                if len(self.equity_curve) % 60 == 0:
                    self.print_status(price, signal_names[signal], confidence)
        
        except Exception as e:
            logger.error(f"Error processing ticker: {e}")
    
    def print_status(self, price, signal, confidence):
        """Print current status and write to status file for dashboard"""
        if self.equity_curve:
            latest = self.equity_curve[-1]
            risk_status = self.kill_switch.get_status()
            
            logger.info("=" * 60)
            logger.info(f"Price: ${price:.2f} | Signal: {signal} (conf: {confidence:.3f})")
            logger.info(f"Capital: ${self.capital:.2f} | Position: {self.position:.6f} BTC")
            logger.info(f"Total Value: ${latest['total_value']:.2f} | Returns: {latest['returns']:+.2f}%")
            logger.info(f"Trades: {len(self.trades)} | Experiences: {len(self.experience_buffer)}")
            logger.info(f"Consecutive Losses: {risk_status['consecutive_losses']} | Avg Conf: {risk_status['avg_confidence']:.3f}")
            
            # Model performance
            logger.info("Model Performance:")
            for name, perf in self.model_performance.items():
                if perf['total'] > 0:
                    accuracy = perf['correct'] / perf['total'] * 100
                    logger.info(f"  {name}: {accuracy:.1f}% ({perf['correct']}/{perf['total']})")
            
            logger.info("=" * 60)
            
            # Write status for dashboard
            self.write_status_file(price, signal, confidence)
    
    def write_status_file(self, price, signal, confidence):
        """Write current status to file for dashboard"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'status': 'KILLED' if self.kill_switch.is_killed else 'ACTIVE',
            'uptime': str(datetime.now() - self.start_time) if hasattr(self, 'start_time') else 'N/A',
            'price': price,
            'signal': signal,
            'confidence': confidence,
            'capital': self.capital,
            'position': self.position,
            'position_value': self.position * price,
            'total_value': self.capital + (self.position * price),
            'total_trades': len(self.trades),
            'experiences': len(self.experience_buffer),
            'kill_switch': self.kill_switch.get_status(),
            'model_performance': self.model_performance
        }
        
        try:
            with open('paper_trading_status.json', 'w') as f:
                json.dump(status, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write status file: {e}")
    
    def save_results(self):
        """Save trading results"""
        results_dir = Path("paper_trading_results")
        results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if self.trades:
            trades_df = pd.DataFrame(self.trades)
            trades_df.to_csv(results_dir / f"trades_{timestamp}.csv", index=False)
            logger.info(f"Saved {len(self.trades)} trades")
        
        if self.equity_curve:
            equity_df = pd.DataFrame(self.equity_curve)
            equity_df.to_csv(results_dir / f"equity_{timestamp}.csv", index=False)
        
        # Save experiences
        if self.experience_buffer:
            exp_data = []
            for exp in self.experience_buffer:
                exp_flat = {
                    'timestamp': exp['timestamp'],
                    'signal': exp['signal'],
                    'actual_outcome': exp['actual_outcome'],
                    'price': exp['price'],
                    **exp['features']
                }
                exp_data.append(exp_flat)
            exp_df = pd.DataFrame(exp_data)
            exp_df.to_csv(results_dir / f"experiences_{timestamp}.csv", index=False)
            logger.info(f"Saved {len(self.experience_buffer)} experiences")
        
        summary = {
            'initial_capital': self.initial_capital,
            'final_capital': self.capital,
            'position': self.position,
            'total_trades': len(self.trades),
            'final_value': self.equity_curve[-1]['total_value'] if self.equity_curve else self.initial_capital,
            'total_return_pct': self.equity_curve[-1]['returns'] if self.equity_curve else 0,
            'kill_switch_status': self.kill_switch.get_status(),
            'learning_mode': self.learning_mode,
            'experiences_collected': len(self.experience_buffer),
            'model_performance': self.model_performance
        }
        
        with open(results_dir / f"summary_{timestamp}.json", 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        logger.info(f"Results saved to {results_dir}/")
        return summary


def main():
    logger.info("=" * 60)
    logger.info("🛡️ SAFE ADAPTIVE PAPER TRADING SYSTEM")
    logger.info("=" * 60)
    logger.info("Features:")
    logger.info("  ✅ Hard Risk Kill Switch")
    logger.info("  ✅ Fixed Risk Per Trade (1%)")
    logger.info("  ✅ Stop Loss Protection (0.5%)")
    logger.info("  ✅ Controlled Learning (Observe mode for 2 weeks)")
    logger.info("=" * 60)
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)
    
    trader = SafeAdaptivePaperTrader(
        initial_capital=10000,
        risk_per_trade_pct=1.0,
        learning_mode='observe'  # Safe mode for first 2 weeks
    )
    
    streams = ['btcusdt@ticker']
    client = BinanceWebSocketClient(
        streams=streams,
        callback=trader.on_ticker_update,
        testnet=False
    )
    
    try:
        logger.info("Connecting to Binance WebSocket...")
        asyncio.run(client.start())
    
    except KeyboardInterrupt:
        logger.info("\nStopping safe adaptive paper trading...")
        
        logger.info("\nSaving results...")
        summary = trader.save_results()
        
        logger.info("\n" + "=" * 60)
        logger.info("SAFE ADAPTIVE PAPER TRADING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Initial Capital: ${summary['initial_capital']:,.2f}")
        logger.info(f"Final Value: ${summary['final_value']:,.2f}")
        logger.info(f"Total Return: {summary['total_return_pct']:+.2f}%")
        logger.info(f"Total Trades: {summary['total_trades']}")
        logger.info(f"Experiences Collected: {summary['experiences_collected']}")
        logger.info(f"Kill Switch: {'TRIGGERED' if summary['kill_switch_status']['is_killed'] else 'OK'}")
        if summary['kill_switch_status']['is_killed']:
            logger.info(f"Kill Reason: {summary['kill_switch_status']['kill_reason']}")
        logger.info("=" * 60)
        
        logger.info("\nSafe adaptive paper trading stopped successfully!")


if __name__ == "__main__":
    main()
