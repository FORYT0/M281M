"""
Live Data Recorder - Stage 1 of Phase 6.
Records real market data from Binance for agent retraining.

Run this 24/7 for 1-2 weeks to collect real market data.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
import pandas as pd
from collections import deque

from src.pipeline.websocket_client import BinanceWebSocketClient


class LiveDataRecorder:
    """
    Records live market data from Binance WebSocket.
    
    Captures:
    - Order book snapshots (depth20@100ms)
    - Trade stream
    - Ticker updates
    """
    
    def __init__(
        self,
        symbol: str = 'btcusdt',
        output_dir: str = 'data/live',
        buffer_size: int = 1000
    ):
        """
        Initialize data recorder.
        
        Args:
            symbol: Trading symbol (lowercase)
            output_dir: Directory to save data
            buffer_size: Number of records to buffer before writing
        """
        self.symbol = symbol
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Data buffers
        self.orderbook_buffer = deque(maxlen=buffer_size)
        self.trade_buffer = deque(maxlen=buffer_size)
        self.ticker_buffer = deque(maxlen=buffer_size)
        
        # Statistics
        self.start_time = time.time()
        self.orderbook_count = 0
        self.trade_count = 0
        self.ticker_count = 0
        self.last_save_time = time.time()
        self.save_interval = 60  # Save every 60 seconds
        
        # File paths
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.orderbook_file = self.output_dir / f'{symbol}_orderbook_{self.session_id}.csv'
        self.trade_file = self.output_dir / f'{symbol}_trades_{self.session_id}.csv'
        self.ticker_file = self.output_dir / f'{symbol}_ticker_{self.session_id}.csv'
        
        print(f"Data Recorder initialized")
        print(f"Symbol: {symbol.upper()}")
        print(f"Output: {self.output_dir}")
        print(f"Session: {self.session_id}")
    
    async def handle_message(self, data: dict):
        """Process incoming WebSocket message."""
        try:
            # Debug: Print first message to see format
            if self.orderbook_count == 0 and self.trade_count == 0 and self.ticker_count == 0:
                print(f"\n[DEBUG] First message received:")
                print(f"[DEBUG] Keys: {list(data.keys())}")
                if 'stream' in data:
                    print(f"[DEBUG] Stream: {data.get('stream')}")
                if 'e' in data:
                    print(f"[DEBUG] Event type: {data.get('e')}")
                if 'data' in data and isinstance(data['data'], dict):
                    print(f"[DEBUG] Data keys: {list(data['data'].keys())}")
                print()
            
            # Handle combined stream format (has 'stream' and 'data' fields)
            if 'stream' in data and 'data' in data:
                stream = data.get('stream', '')
                event_data = data.get('data', {})
            else:
                # Handle single stream format (data is at root level)
                stream = ''
                event_data = data
                # Determine stream type from event type
                if 'e' in event_data:
                    event_type = event_data.get('e', '')
                    if event_type == 'depthUpdate':
                        stream = 'depth'
                    elif event_type == 'trade':
                        stream = 'trade'
                    elif event_type == '24hrTicker':
                        stream = 'ticker'
            
            if 'depth' in stream or event_data.get('e') == 'depthUpdate':
                await self._handle_orderbook(event_data)
            elif 'trade' in stream or event_data.get('e') == 'trade':
                await self._handle_trade(event_data)
            elif 'ticker' in stream or event_data.get('e') == '24hrTicker':
                await self._handle_ticker(event_data)
            
            # Periodic save
            if time.time() - self.last_save_time >= self.save_interval:
                await self._save_buffers()
                self._print_stats()
                self.last_save_time = time.time()
                
        except Exception as e:
            print(f"Error handling message: {e}")
            import traceback
            traceback.print_exc()
            import traceback
            traceback.print_exc()
    
    async def _handle_orderbook(self, data: dict):
        """Handle order book update."""
        try:
            timestamp = data.get('E', int(time.time() * 1000))
            bids = data.get('bids', [])
            asks = data.get('asks', [])
            
            if not bids or not asks:
                return
            
            # Extract best bid/ask
            best_bid_price = float(bids[0][0])
            best_bid_qty = float(bids[0][1])
            best_ask_price = float(asks[0][0])
            best_ask_qty = float(asks[0][1])
            
            # Calculate spread
            spread = best_ask_price - best_bid_price
            mid_price = (best_bid_price + best_ask_price) / 2
            
            # Calculate order book imbalance (top 5 levels)
            bid_volume = sum(float(bid[1]) for bid in bids[:5])
            ask_volume = sum(float(ask[1]) for ask in asks[:5])
            total_volume = bid_volume + ask_volume
            imbalance = (bid_volume - ask_volume) / total_volume if total_volume > 0 else 0
            
            record = {
                'timestamp': timestamp,
                'datetime': datetime.fromtimestamp(timestamp / 1000).isoformat(),
                'best_bid_price': best_bid_price,
                'best_bid_qty': best_bid_qty,
                'best_ask_price': best_ask_price,
                'best_ask_qty': best_ask_qty,
                'mid_price': mid_price,
                'spread': spread,
                'spread_bps': (spread / mid_price) * 10000,
                'bid_volume_5': bid_volume,
                'ask_volume_5': ask_volume,
                'imbalance': imbalance
            }
            
            self.orderbook_buffer.append(record)
            self.orderbook_count += 1
            
        except Exception as e:
            print(f"Error processing orderbook: {e}")
    
    async def _handle_trade(self, data: dict):
        """Handle trade update."""
        try:
            record = {
                'timestamp': data.get('T', int(time.time() * 1000)),
                'datetime': datetime.fromtimestamp(data.get('T', time.time() * 1000) / 1000).isoformat(),
                'trade_id': data.get('t'),
                'price': float(data.get('p', 0)),
                'quantity': float(data.get('q', 0)),
                'buyer_maker': data.get('m', False),
                'side': 'sell' if data.get('m', False) else 'buy'
            }
            
            self.trade_buffer.append(record)
            self.trade_count += 1
            
        except Exception as e:
            print(f"Error processing trade: {e}")
    
    async def _handle_ticker(self, data: dict):
        """Handle ticker update."""
        try:
            record = {
                'timestamp': data.get('E', int(time.time() * 1000)),
                'datetime': datetime.fromtimestamp(data.get('E', time.time() * 1000) / 1000).isoformat(),
                'price': float(data.get('c', 0)),
                'price_change': float(data.get('p', 0)),
                'price_change_pct': float(data.get('P', 0)),
                'volume': float(data.get('v', 0)),
                'quote_volume': float(data.get('q', 0)),
                'high': float(data.get('h', 0)),
                'low': float(data.get('l', 0)),
                'open': float(data.get('o', 0))
            }
            
            self.ticker_buffer.append(record)
            self.ticker_count += 1
            
        except Exception as e:
            print(f"Error processing ticker: {e}")
    
    async def _save_buffers(self):
        """Save buffered data to CSV files."""
        try:
            # Save order book data
            if self.orderbook_buffer:
                df = pd.DataFrame(list(self.orderbook_buffer))
                if self.orderbook_file.exists():
                    df.to_csv(self.orderbook_file, mode='a', header=False, index=False)
                else:
                    df.to_csv(self.orderbook_file, index=False)
                self.orderbook_buffer.clear()
            
            # Save trade data
            if self.trade_buffer:
                df = pd.DataFrame(list(self.trade_buffer))
                if self.trade_file.exists():
                    df.to_csv(self.trade_file, mode='a', header=False, index=False)
                else:
                    df.to_csv(self.trade_file, index=False)
                self.trade_buffer.clear()
            
            # Save ticker data
            if self.ticker_buffer:
                df = pd.DataFrame(list(self.ticker_buffer))
                if self.ticker_file.exists():
                    df.to_csv(self.ticker_file, mode='a', header=False, index=False)
                else:
                    df.to_csv(self.ticker_file, index=False)
                self.ticker_buffer.clear()
            
        except Exception as e:
            print(f"Error saving buffers: {e}")
    
    def _print_stats(self):
        """Print recording statistics."""
        uptime = time.time() - self.start_time
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        seconds = int(uptime % 60)
        
        print(f"\n{'='*60}")
        print(f"Recording Statistics - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        print(f"Uptime: {hours:02d}:{minutes:02d}:{seconds:02d}")
        print(f"Order Book Updates: {self.orderbook_count:,}")
        print(f"Trades: {self.trade_count:,}")
        print(f"Ticker Updates: {self.ticker_count:,}")
        print(f"Total Events: {self.orderbook_count + self.trade_count + self.ticker_count:,}")
        print(f"{'='*60}\n")
    
    async def start(self):
        """Start recording data."""
        # Define streams
        streams = [
            f'{self.symbol}@depth20@100ms',  # Order book (100ms updates)
            f'{self.symbol}@trade',           # Trades
            f'{self.symbol}@ticker'           # 24h ticker
        ]
        
        print(f"\nStarting data recording...")
        print(f"Streams: {', '.join(streams)}")
        print(f"Press Ctrl+C to stop\n")
        
        # Create WebSocket client
        client = BinanceWebSocketClient(
            streams=streams,
            callback=self.handle_message,
            testnet=False,  # Use mainnet for real data
            max_reconnect_attempts=999999,
            reconnect_delay=5
        )
        
        try:
            await client.start()
        except KeyboardInterrupt:
            print("\n\nStopping recorder...")
            await self._save_buffers()
            self._print_stats()
            print("Data saved. Exiting.")
        except Exception as e:
            print(f"\nError: {e}")
            await self._save_buffers()
            raise


async def main():
    """Main entry point."""
    print("="*60)
    print("Live Data Recorder - Phase 6 Stage 1")
    print("="*60)
    print("\nThis will record real market data from Binance.")
    print("Run this 24/7 for 1-2 weeks to collect training data.")
    print("\nData will be saved to: data/live/")
    print("\nPress Ctrl+C to stop recording")
    print("="*60)
    
    # Create recorder
    recorder = LiveDataRecorder(
        symbol='btcusdt',
        output_dir='data/live',
        buffer_size=1000
    )
    
    # Start recording
    await recorder.start()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nRecording stopped by user")
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
