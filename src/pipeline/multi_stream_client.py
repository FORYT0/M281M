"""
Multi-stream WebSocket client for aggregating multiple data sources.
Handles order book, trades, and ticker data simultaneously.
"""

import asyncio
import json
from typing import Dict, Any, Callable, List, Optional
from datetime import datetime
from loguru import logger

from .websocket_client import BinanceWebSocketClient
from .features import FeatureCalculator


class MultiStreamAggregator:
    """
    Aggregates multiple WebSocket streams and computes features in real-time.
    Designed for low-latency operation (<50ms target).
    """
    
    def __init__(
        self,
        symbols: List[str],
        feature_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        testnet: bool = False
    ):
        """
        Initialize multi-stream aggregator.
        
        Args:
            symbols: List of trading symbols (e.g., ['BTCUSDT', 'ETHUSDT'])
            feature_callback: Callback function for computed features
            testnet: Use testnet if True
        """
        self.symbols = [s.upper() for s in symbols]
        self.feature_callback = feature_callback
        self.testnet = testnet
        
        # Feature calculators per symbol
        self.calculators: Dict[str, FeatureCalculator] = {
            symbol: FeatureCalculator() for symbol in self.symbols
        }
        
        # Latest data per symbol
        self.latest_data: Dict[str, Dict[str, Any]] = {
            symbol: {
                'order_book': None,
                'last_trade': None,
                'ticker': None
            } for symbol in self.symbols
        }
        
        # WebSocket clients
        self.clients: List[BinanceWebSocketClient] = []
        
        # Statistics
        self.feature_count = 0
        self.start_time = None
    
    def _create_streams(self) -> List[str]:
        """Create stream names for all symbols."""
        streams = []
        for symbol in self.symbols:
            symbol_lower = symbol.lower()
            streams.extend([
                f"{symbol_lower}@depth20@100ms",  # Order book
                f"{symbol_lower}@trade",           # Trades
                f"{symbol_lower}@ticker"           # 24h ticker
            ])
        return streams
    
    async def _handle_message(self, data: Dict[str, Any]):
        """
        Process incoming WebSocket message and compute features.
        
        Args:
            data: WebSocket message data
        """
        try:
            # Binance combined streams don't have 'stream' field
            # Identify message type by event type 'e' or presence of specific fields
            event_type = data.get('e', '')
            symbol = data.get('s', '').upper()
            
            if not symbol or symbol not in self.symbols:
                # Try to extract from order book (no 'e' field)
                if 'lastUpdateId' in data and 'bids' in data:
                    # This is a depth update, but we need to infer symbol
                    # For single symbol, use the first one
                    if len(self.symbols) == 1:
                        symbol = self.symbols[0]
                    else:
                        return  # Can't determine symbol for multi-symbol
                else:
                    return
            
            # Route to appropriate handler
            if event_type == 'depthUpdate' or 'lastUpdateId' in data:
                await self._handle_depth(symbol, data)
            elif event_type == 'trade':
                await self._handle_trade(symbol, data)
            elif event_type == '24hrTicker':
                await self._handle_ticker(symbol, data)
        
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def _handle_depth(self, symbol: str, data: Dict[str, Any]):
        """Handle order book depth update."""
        self.latest_data[symbol]['order_book'] = {
            'bids': data.get('bids', []),
            'asks': data.get('asks', []),
            'timestamp': datetime.now()
        }
        
        # Compute features if we have enough data
        await self._compute_features(symbol)
    
    async def _handle_trade(self, symbol: str, data: Dict[str, Any]):
        """Handle trade event."""
        self.latest_data[symbol]['last_trade'] = {
            'price': float(data.get('p', 0)),
            'quantity': float(data.get('q', 0)),
            'is_buyer_maker': data.get('m', False),
            'timestamp': datetime.fromtimestamp(data.get('T', 0) / 1000)
        }
        
        # Compute features
        await self._compute_features(symbol)
    
    async def _handle_ticker(self, symbol: str, data: Dict[str, Any]):
        """Handle ticker update."""
        self.latest_data[symbol]['ticker'] = {
            'last_price': float(data.get('c', 0)),
            'volume': float(data.get('v', 0)),
            'quote_volume': float(data.get('q', 0)),
            'price_change_percent': float(data.get('P', 0)),
            'timestamp': datetime.now()
        }
    
    async def _compute_features(self, symbol: str):
        """
        Compute features for a symbol using latest data.
        
        Args:
            symbol: Trading symbol
        """
        data = self.latest_data[symbol]
        order_book = data['order_book']
        trade = data['last_trade']
        
        if not order_book or not trade:
            return
        
        # Extract order book data
        bids = order_book['bids']
        asks = order_book['asks']
        
        if not bids or not asks:
            return
        
        best_bid = float(bids[0][0])
        best_ask = float(asks[0][0])
        mid_price = (best_bid + best_ask) / 2
        
        bid_volume = float(bids[0][1])
        ask_volume = float(asks[0][1])
        
        # Update feature calculator
        calculator = self.calculators[symbol]
        features = calculator.update(
            timestamp=trade['timestamp'],
            price=mid_price,
            bid_volume=bid_volume,
            ask_volume=ask_volume,
            trade_volume=trade['quantity'],
            is_buy=not trade['is_buyer_maker']  # Buyer maker = sell order filled
        )
        
        # Add liquidity heatmap
        features['liquidity_heatmap'] = calculator.get_liquidity_heatmap({
            'bids': bids,
            'asks': asks
        })
        
        # Add symbol
        features['symbol'] = symbol
        
        # Update statistics
        self.feature_count += 1
        
        # Call user callback
        if self.feature_callback:
            try:
                if asyncio.iscoroutinefunction(self.feature_callback):
                    await self.feature_callback(symbol, features)
                else:
                    await asyncio.to_thread(self.feature_callback, symbol, features)
            except Exception as e:
                logger.error(f"Error in feature callback: {e}")
    
    async def start(self):
        """Start all WebSocket streams."""
        self.start_time = datetime.now()
        
        logger.info(f"Starting multi-stream aggregator for {len(self.symbols)} symbols")
        
        # Create combined stream
        streams = self._create_streams()
        logger.info(f"Subscribing to {len(streams)} streams")
        
        # Create WebSocket client
        client = BinanceWebSocketClient(
            streams=streams,
            callback=self._handle_message,
            testnet=self.testnet
        )
        
        self.clients.append(client)
        
        # Start client
        await client.start()
    
    async def stop(self):
        """Stop all WebSocket streams."""
        logger.info("Stopping multi-stream aggregator")
        
        for client in self.clients:
            await client.disconnect()
        
        self.clients.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get aggregator statistics."""
        uptime = None
        if self.start_time:
            uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            'symbols': self.symbols,
            'feature_count': self.feature_count,
            'uptime_seconds': uptime,
            'features_per_second': (
                self.feature_count / uptime if uptime and uptime > 0 else 0
            ),
            'clients': len(self.clients)
        }
