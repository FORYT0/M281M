"""
Test script for WebSocket client.
Connects to Binance testnet and displays real-time order book updates.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline.websocket_client import BinanceWebSocketClient, OrderBookTracker
from loguru import logger

# Configure logger
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)


async def main():
    """Main test function."""
    logger.info("=" * 60)
    logger.info("M281M WebSocket Client Test")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Connecting to Binance testnet...")
    logger.info("Stream: btcusdt@depth20@100ms")
    logger.info("Press Ctrl+C to stop")
    logger.info("")
    
    # Create order book tracker
    tracker = OrderBookTracker()
    
    # Create WebSocket client
    client = BinanceWebSocketClient(
        streams=["btcusdt@depth20@100ms"],
        callback=tracker.process_depth_update,
        testnet=True,
        max_reconnect_attempts=5,
        reconnect_delay=3
    )
    
    try:
        # Start receiving data
        await client.start()
        
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
        await client.disconnect()
        
        # Print final statistics
        stats = client.get_stats()
        logger.info("")
        logger.info("=" * 60)
        logger.info("Session Statistics:")
        logger.info(f"  Messages received: {stats['messages_received']}")
        logger.info(f"  Uptime: {stats['uptime_seconds']:.1f}s")
        logger.info(f"  Reconnections: {stats['reconnect_count']}")
        logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
