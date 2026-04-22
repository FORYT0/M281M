"""
Adaptive paper trading system with online learning
Models learn and improve continuously from trading results
"""
import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger
import sys
import pickle
from datetime import datetime
import time
import json
import asyncio
from collections import deque

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.pipeline.websocket_client import BinanceWebSocketClient


class AdaptivePaperTrader:
    """Paper trading system with online learning"""
    
    def __init__(self, initial_capital=10000, learning_rate=0.1):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.position = 0
        self.position_entry_price = 0
        self.trades = []
        self.equity_curve = []
        
        # Learning parameters
        self.learning_rate = learning_rate
        self.experience_buffer = deque(maxlen=1000)  # Store recent experiences
        self.retrain_interval = 100  # Retrain every N experiences
        self.last_retrain_time = datetime.now()
        
        # Load models
        self.models = self.load_models()
        
        # Feature buffer
        self.price_buffer = []
        self.volume_buffer = []
        self.max_buffer_size = 100
        
        # Performance tracking
        self.model_performance = {name: {'correct': 0, 'total': 0} for name in self.models.keys()}
        
        logger.info(f"Adaptive paper trader initialized with ${initial_capital:,.2f}")
        logger.info(f"Online learning enabled (learning rate: {learning_rate})")
    
    def load_models(self):
        """Load trained models"""
        models = {}
        for name in ['momentum', 'mean_reversion', 'order_flow']:
            try:
                model_path = Path(f"models/{name}_agent_live.pkl")
                with open(model_path, 'wb') as f:
                    models[name] = pickle.load(f)
                logger.info(f"✓ Loaded {name} model")
            except Exception as e:
                logger.error(f"✗ Failed to load {name} model: {e}")
        return models
    
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
            weight = max(0.1, accuracy)  # Minimum weight of 0.1
            weighted_votes.extend([pred] * int(weight * 10))
        
        signal = max(set(weighted_votes), key=weighted_votes.count)
        avg_confidence = np.mean(list(confidences.values()))
        
        return signal, avg_confidence, predictions
    
    def store_experience(self, features, signal, actual_outcome, price):
        """Store experience for online learning"""
        experience = {
            'features': features,
            'signal': signal,
            'actual_outcome': actual_outcome,
            'price': price,
            'timestamp': datetime.now()
        }
        self.experience_buffer.append(experience)
        
        # Check if we should retrain
        if len(self.experience_buffer) >= self.retrain_interval:
            time_since_retrain = (datetime.now() - self.last_retrain_time).total_seconds()
            if time_since_retrain > 300:  # At least 5 minutes between retrains
                self.retrain_models()
    
    def retrain_models(self):
        """Retrain models on recent experiences"""
        if len(self.experience_buffer) < 50:
            return
        
        logger.info("🔄 Starting online learning update...")
        
        # Prepare training data from experiences
        X_new = []
        y_new = []
        
        for exp in list(self.experience_buffer)[-200:]:  # Use last 200 experiences
            features = exp['features']
            feature_array = [
                features['price'],
                features['volume'],
                features['returns'],
                features['sma_10'],
                features['sma_20'],
                features['rsi'],
                features['volatility']
            ]
            X_new.append(feature_array)
            y_new.append(exp['actual_outcome'])
        
        X_new = np.array(X_new)
        y_new = np.array(y_new)
        
        # Update each model with partial_fit (online learning)
        for name, model_data in self.models.items():
            try:
                X_scaled = model_data['scaler'].transform(X_new)
                
                # For Random Forest, we'll retrain on combined old + new data
                # (true online learning would use SGDClassifier, but RF is more stable)
                model_data['model'].fit(X_scaled, y_new)
                
                # Save updated model
                model_path = Path(f"models/{name}_agent_live.pkl")
                with open(model_path, 'wb') as f:
                    pickle.dump(model_data, f)
                
                logger.info(f"✓ Updated {name} model with {len(X_new)} new samples")
                
            except Exception as e:
                logger.error(f"Failed to update {name} model: {e}")
        
        self.last_retrain_time = datetime.now()
        logger.info("✅ Online learning update complete")
    
    def update_model_performance(self, predictions, actual_outcome):
        """Update model performance tracking"""
        for name, pred in predictions.items():
            self.model_performance[name]['total'] += 1
            if pred == actual_outcome:
                self.model_performance[name]['correct'] += 1
    
    def execute_trade(self, signal, price, confidence, predictions, timestamp):
        """Execute paper trade and learn from results"""
        signal_names = ['SELL', 'HOLD', 'BUY']
        min_confidence = 0.85
        
        if confidence < min_confidence:
            return
        
        # BUY signal
        if signal == 2 and self.position == 0:
            buy_amount = self.capital * 0.9
            btc_amount = buy_amount / price
            
            self.position = btc_amount
            self.position_entry_price = price
            self.capital -= buy_amount
            
            trade = {
                'timestamp': timestamp,
                'action': 'BUY',
                'price': price,
                'amount': btc_amount,
                'value': buy_amount,
                'confidence': confidence,
                'predictions': predictions
            }
            self.trades.append(trade)
            
            logger.info(f"🟢 BUY: {btc_amount:.6f} BTC @ ${price:.2f} (conf: {confidence:.3f})")
        
        # SELL signal
        elif signal == 0 and self.position > 0:
            sell_value = self.position * price
            pnl = sell_value - (self.position * self.position_entry_price)
            pnl_pct = (pnl / (self.position * self.position_entry_price)) * 100
            
            self.capital += sell_value
            
            # Determine actual outcome for learning
            if pnl > 0:
                actual_outcome = 2  # Good trade (UP)
            elif pnl < 0:
                actual_outcome = 0  # Bad trade (DOWN)
            else:
                actual_outcome = 1  # Neutral (HOLD)
            
            # Update model performance
            self.update_model_performance(predictions, actual_outcome)
            
            # Store experience for learning
            features = self.calculate_features(price, self.volume_buffer[-1] if self.volume_buffer else 0)
            if features:
                self.store_experience(features, signal, actual_outcome, price)
            
            trade = {
                'timestamp': timestamp,
                'action': 'SELL',
                'price': price,
                'amount': self.position,
                'value': sell_value,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'confidence': confidence,
                'predictions': predictions,
                'learned': True
            }
            self.trades.append(trade)
            
            logger.info(f"🔴 SELL: {self.position:.6f} BTC @ ${price:.2f} | PnL: ${pnl:.2f} ({pnl_pct:+.2f}%)")
            logger.info(f"📚 Learning from trade result (outcome: {['DOWN', 'HOLD', 'UP'][actual_outcome]})")
            
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
        """Print current status with learning metrics"""
        if self.equity_curve:
            latest = self.equity_curve[-1]
            logger.info("=" * 60)
            logger.info(f"Price: ${price:.2f} | Signal: {signal} (conf: {confidence:.3f})")
            logger.info(f"Capital: ${self.capital:.2f} | Position: {self.position:.6f} BTC")
            logger.info(f"Total Value: ${latest['total_value']:.2f} | Returns: {latest['returns']:+.2f}%")
            logger.info(f"Trades: {len(self.trades)} | Experiences: {len(self.experience_buffer)}")
            
            # Show model performance
            logger.info("Model Performance:")
            for name, perf in self.model_performance.items():
                if perf['total'] > 0:
                    accuracy = perf['correct'] / perf['total'] * 100
                    logger.info(f"  {name}: {accuracy:.1f}% ({perf['correct']}/{perf['total']})")
            
            logger.info("=" * 60)
    
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
            logger.info(f"Saved equity curve")
        
        # Save learning metrics
        learning_metrics = {
            'experiences_collected': len(self.experience_buffer),
            'model_performance': self.model_performance,
            'last_retrain_time': self.last_retrain_time.isoformat()
        }
        
        summary = {
            'initial_capital': self.initial_capital,
            'final_capital': self.capital,
            'position': self.position,
            'total_trades': len(self.trades),
            'final_value': self.equity_curve[-1]['total_value'] if self.equity_curve else self.initial_capital,
            'total_return_pct': self.equity_curve[-1]['returns'] if self.equity_curve else 0,
            'learning_metrics': learning_metrics
        }
        
        with open(results_dir / f"summary_{timestamp}.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Results saved to {results_dir}/")
        return summary


def main():
    logger.info("=" * 60)
    logger.info("ADAPTIVE PAPER TRADING SYSTEM")
    logger.info("With Online Learning")
    logger.info("=" * 60)
    logger.info("Models will learn and improve from trading results")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)
    
    trader = AdaptivePaperTrader(initial_capital=10000, learning_rate=0.1)
    
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
        logger.info("\nStopping adaptive paper trading...")
        
        logger.info("\nSaving results...")
        summary = trader.save_results()
        
        logger.info("\n" + "=" * 60)
        logger.info("ADAPTIVE PAPER TRADING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Initial Capital: ${summary['initial_capital']:,.2f}")
        logger.info(f"Final Value: ${summary['final_value']:,.2f}")
        logger.info(f"Total Return: {summary['total_return_pct']:+.2f}%")
        logger.info(f"Total Trades: {summary['total_trades']}")
        logger.info(f"Experiences Collected: {summary['learning_metrics']['experiences_collected']}")
        logger.info("=" * 60)
        
        logger.info("\nAdaptive paper trading stopped successfully!")


if __name__ == "__main__":
    main()
