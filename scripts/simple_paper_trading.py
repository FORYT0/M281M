"""
Simple paper trading system using retrained models
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

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.pipeline.websocket_client import BinanceWebSocketClient


class SimplePaperTrader:
    """Simple paper trading system"""
    
    def __init__(self, initial_capital=10000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.position = 0  # BTC position
        self.position_entry_price = 0
        self.trades = []
        self.equity_curve = []
        
        # Load models
        self.models = self.load_models()
        
        # Feature buffer for calculations
        self.price_buffer = []
        self.volume_buffer = []
        self.max_buffer_size = 100
        
        logger.info(f"Paper trader initialized with ${initial_capital:,.2f}")
    
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
            return 1, 0.0  # Hold with 0 confidence
        
        # Convert features to array
        feature_array = np.array([[
            features['price'],
            features['volume'],
            features['returns'],
            features['sma_10'],
            features['sma_20'],
            features['rsi'],
            features['volatility']
        ]])
        
        predictions = []
        confidences = []
        
        for name, model_data in self.models.items():
            try:
                # Scale features
                X_scaled = model_data['scaler'].transform(feature_array)
                
                # Predict
                pred = model_data['model'].predict(X_scaled)[0]
                proba = model_data['model'].predict_proba(X_scaled)[0]
                conf = np.max(proba)
                
                predictions.append(pred)
                confidences.append(conf)
                
            except Exception as e:
                logger.error(f"Prediction error for {name}: {e}")
        
        if not predictions:
            return 1, 0.0  # Hold
        
        # Majority vote
        signal = max(set(predictions), key=predictions.count)
        avg_confidence = np.mean(confidences)
        
        return signal, avg_confidence
    
    def execute_trade(self, signal, price, confidence, timestamp):
        """Execute paper trade based on signal"""
        signal_names = ['SELL', 'HOLD', 'BUY']
        
        # Require high confidence for trades
        min_confidence = 0.85
        
        if confidence < min_confidence:
            logger.info(f"Low confidence ({confidence:.3f}), holding position")
            return
        
        # BUY signal and no position
        if signal == 2 and self.position == 0:
            # Buy with 90% of capital
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
                'confidence': confidence
            }
            self.trades.append(trade)
            
            logger.info(f"🟢 BUY: {btc_amount:.6f} BTC @ ${price:.2f} (conf: {confidence:.3f})")
        
        # SELL signal and have position
        elif signal == 0 and self.position > 0:
            sell_value = self.position * price
            pnl = sell_value - (self.position * self.position_entry_price)
            pnl_pct = (pnl / (self.position * self.position_entry_price)) * 100
            
            self.capital += sell_value
            
            trade = {
                'timestamp': timestamp,
                'action': 'SELL',
                'price': price,
                'amount': self.position,
                'value': sell_value,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'confidence': confidence
            }
            self.trades.append(trade)
            
            logger.info(f"🔴 SELL: {self.position:.6f} BTC @ ${price:.2f} | PnL: ${pnl:.2f} ({pnl_pct:+.2f}%) (conf: {confidence:.3f})")
            
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
            price = float(data['c'])  # Close price
            volume = float(data['v'])  # Volume
            timestamp = datetime.fromtimestamp(data['E'] / 1000)
            
            # Update buffers
            self.price_buffer.append(price)
            self.volume_buffer.append(volume)
            
            if len(self.price_buffer) > self.max_buffer_size:
                self.price_buffer.pop(0)
                self.volume_buffer.pop(0)
            
            # Calculate features
            features = self.calculate_features(price, volume)
            
            if features:
                # Get signal
                signal, confidence = self.get_ensemble_signal(features)
                signal_names = ['SELL', 'HOLD', 'BUY']
                
                # Execute trade
                self.execute_trade(signal, price, confidence, timestamp)
                
                # Update equity
                self.update_equity(price, timestamp)
                
                # Log status every minute
                if len(self.equity_curve) % 60 == 0:
                    self.print_status(price, signal_names[signal], confidence)
        
        except Exception as e:
            logger.error(f"Error processing ticker: {e}")
    
    def print_status(self, price, signal, confidence):
        """Print current status"""
        if self.equity_curve:
            latest = self.equity_curve[-1]
            logger.info("=" * 60)
            logger.info(f"Price: ${price:.2f} | Signal: {signal} (conf: {confidence:.3f})")
            logger.info(f"Capital: ${self.capital:.2f} | Position: {self.position:.6f} BTC")
            logger.info(f"Total Value: ${latest['total_value']:.2f} | Returns: {latest['returns']:+.2f}%")
            logger.info(f"Trades: {len(self.trades)}")
            logger.info("=" * 60)
    
    def save_results(self):
        """Save trading results"""
        results_dir = Path("paper_trading_results")
        results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save trades
        if self.trades:
            trades_df = pd.DataFrame(self.trades)
            trades_df.to_csv(results_dir / f"trades_{timestamp}.csv", index=False)
            logger.info(f"Saved {len(self.trades)} trades")
        
        # Save equity curve
        if self.equity_curve:
            equity_df = pd.DataFrame(self.equity_curve)
            equity_df.to_csv(results_dir / f"equity_{timestamp}.csv", index=False)
            logger.info(f"Saved equity curve ({len(self.equity_curve)} points)")
        
        # Save summary
        summary = {
            'initial_capital': self.initial_capital,
            'final_capital': self.capital,
            'position': self.position,
            'total_trades': len(self.trades),
            'final_value': self.equity_curve[-1]['total_value'] if self.equity_curve else self.initial_capital,
            'total_return_pct': self.equity_curve[-1]['returns'] if self.equity_curve else 0
        }
        
        with open(results_dir / f"summary_{timestamp}.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Results saved to {results_dir}/")
        return summary


def main():
    logger.info("=" * 60)
    logger.info("SIMPLE PAPER TRADING SYSTEM")
    logger.info("=" * 60)
    logger.info("Starting paper trading with live market data...")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)
    
    # Initialize paper trader
    trader = SimplePaperTrader(initial_capital=10000)
    
    # Initialize WebSocket client with correct parameters
    streams = ['btcusdt@ticker']
    client = BinanceWebSocketClient(
        streams=streams,
        callback=trader.on_ticker_update,
        testnet=False  # Use mainnet for real data
    )
    
    try:
        # Run async event loop
        logger.info("Connecting to Binance WebSocket...")
        asyncio.run(client.start())
    
    except KeyboardInterrupt:
        logger.info("\nStopping paper trading...")
        
        # Save results
        logger.info("\nSaving results...")
        summary = trader.save_results()
        
        logger.info("\n" + "=" * 60)
        logger.info("PAPER TRADING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Initial Capital: ${summary['initial_capital']:,.2f}")
        logger.info(f"Final Value: ${summary['final_value']:,.2f}")
        logger.info(f"Total Return: {summary['total_return_pct']:+.2f}%")
        logger.info(f"Total Trades: {summary['total_trades']}")
        logger.info("=" * 60)
        
        logger.info("\nPaper trading stopped successfully!")


if __name__ == "__main__":
    main()
