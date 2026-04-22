"""
Real-time WebSocket client for Binance market data.
Handles connection, reconnection, and data streaming.
"""

import asyncio
import json
import time
from typing import Callable, Optional, Dict, Any
from datetime import datetime
import websockets
from loguru import logger


class BinanceWebSocketClient:
    """
    WebSocket client for Binance market data streams.
    Supports automatic reconnection and multiple stream subscriptions.
    """
    
    TESTNET_WS_URL = "wss://testnet.binance.vision/ws"
    MAINNET_WS_URL = "wss://stream.binance.com:9443/ws"
    MAINNET_COMBINED_URL = "wss://stream.binance.com:9443/stream"
    
    def __init__(
        self,
        streams: list[str],
        callback: Callable[[Dict[str, Any]], None],
        testnet: bool = True,
        max_reconnect_attempts: int = 10,
        reconnect_delay: int = 5
    ):
        """
        Initialize WebSocket client.
        
        Args:
            streams: List of stream names (e.g., ['btcusdt@depth20@100ms', 'btcusdt@trade'])
            callback: Function to call with each message
            testnet: Use testnet if True, mainnet if False
            max_reconnect_attempts: Maximum reconnection attempts
            reconnect_delay: Delay between reconnection attempts (seconds)
        """
        self.streams = streams
        self.callback = callback
        self.testnet = testnet
        self.max_reconnect_attempts = max_reconnect_attempts
        self.reconnect_delay = reconnect_delay
        
        # Use combined stream URL for multiple streams
        if testnet:
            self.ws_url = self.TESTNET_WS_URL
        else:
            if len(streams) > 1:
                self.ws_url = self.MAINNET_COMBINED_URL
            else:
                self.ws_url = self.MAINNET_WS_URL
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.is_running = False
        self.reconnect_count = 0
        
        # Statistics
        self.messages_received = 0
        self.last_message_time = None
        self.connection_start_time = None
        
    async def connect(self):
        """Establish WebSocket connection."""
        # For combined streams (multiple), use ?streams= parameter
        if len(self.streams) > 1 and not self.testnet:
            stream_path = "/".join(self.streams)
            url = f"{self.ws_url}?streams={stream_path}"
        else:
            # For single stream or testnet, use direct path
            stream_path = "/".join(self.streams)
            url = f"{self.ws_url}/{stream_path}"
        
        logger.info(f"Connecting to {url}")
        
        try:
            self.websocket = await websockets.connect(
                url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )
            self.connection_start_time = time.time()
            self.reconnect_count = 0
            logger.info("WebSocket connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Close WebSocket connection gracefully."""
        self.is_running = False
        if self.websocket:
            await self.websocket.close()
            logger.info("WebSocket disconnected")
    
    async def _handle_message(self, message: str):
        """Process incoming message."""
        try:
            data = json.loads(message)
            self.messages_received += 1
            self.last_message_time = time.time()
            
            # Call user callback
            if asyncio.iscoroutinefunction(self.callback):
                await self.callback(data)
            else:
                await asyncio.to_thread(self.callback, data)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def _reconnect(self):
        """Attempt to reconnect with exponential backoff."""
        while self.reconnect_count < self.max_reconnect_attempts:
            self.reconnect_count += 1
            delay = self.reconnect_delay * (2 ** (self.reconnect_count - 1))
            
            logger.warning(
                f"Reconnection attempt {self.reconnect_count}/{self.max_reconnect_attempts} "
                f"in {delay}s"
            )
            
            await asyncio.sleep(delay)
            
            if await self.connect():
                logger.info("Reconnection successful")
                return True
        
        logger.error("Max reconnection attempts reached")
        return False
    
    async def start(self):
        """Start receiving messages with automatic reconnection."""
        self.is_running = True
        
        while self.is_running:
            # Connect if not connected
            if not self.websocket:
                if not await self.connect():
                    if not await self._reconnect():
                        break
                    continue
            
            try:
                # Receive and process messages
                async for message in self.websocket:
                    if not self.is_running:
                        break
                    await self._handle_message(message)
                    
            except websockets.exceptions.ConnectionClosed:
                logger.warning("Connection closed, attempting reconnect...")
                self.websocket = None
                if not await self._reconnect():
                    break
                    
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                self.websocket = None
                if not await self._reconnect():
                    break
        
        await self.disconnect()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        uptime = None
        if self.connection_start_time:
            uptime = time.time() - self.connection_start_time
        
        return {
            "messages_received": self.messages_received,
            "last_message_time": self.last_message_time,
            "uptime_seconds": uptime,
            "reconnect_count": self.reconnect_count,
            "is_connected": self.websocket is not None
        }


class OrderBookTracker:
    """Track and display order book updates."""
    
    def __init__(self):
        self.last_update_id = None
        self.best_bid = None
        self.best_ask = None
        self.update_count = 0
        self.last_print_time = time.time()
        
    def process_depth_update(self, data: Dict[str, Any]):
        """Process depth update message."""
        if 'lastUpdateId' not in data:
            return
        
        self.last_update_id = data['lastUpdateId']
        self.update_count += 1
        
        # Extract best bid and ask
        bids = data.get('bids', [])
        asks = data.get('asks', [])
        
        if bids:
            self.best_bid = float(bids[0][0])
        if asks:
            self.best_ask = float(asks[0][0])
        
        # Print every second
        current_time = time.time()
        if current_time - self.last_print_time >= 1.0:
            self._print_status()
            self.last_print_time = current_time
    
    def _print_status(self):
        """Print current order book status."""
        if self.best_bid and self.best_ask:
            spread = self.best_ask - self.best_bid
            spread_bps = (spread / self.best_bid) * 10000
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            logger.info(
                f"[{timestamp}] Bid: {self.best_bid:.2f} | "
                f"Ask: {self.best_ask:.2f} | "
                f"Spread: {spread:.2f} ({spread_bps:.2f} bps) | "
                f"Updates: {self.update_count}"
            )
