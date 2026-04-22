"""
Short test for WebSocket client - connects for 10 seconds.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline.websocket_client import BinanceWebSocketClient, OrderBookTracker
from loguru import logger

logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)


async def main():
    logger.info("=" * 60)
    logger.info("M281M WebSocket Client - Short Test (10 seconds)")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Connecting to Binance mainnet...")
    logger.info("Stream: btcusdt@depth20@100ms")
    logger.info("")
    
    # Create order book tracker
    tracker = OrderBookTracker()
    
    # Create WebSocket client
    client = BinanceWebSocketClient(
        streams=["btcusdt@depth20@100ms"],
        callback=tracker.process_depth_update,
        testnet=False,  # Use mainnet since testnet endpoint changed
        max_reconnect_attempts=3,
        reconnect_delay=2
    )
    
    try:
        # Start client in background
        client_task = asyncio.create_task(client.start())
        
        # Run for 10 seconds
        await asyncio.sleep(10)
        
        # Stop client
        await client.disconnect()
        
        # Cancel the task
        client_task.cancel()
        try:
            await client_task
        except asyncio.CancelledError:
            pass
        
        # Print statistics
        stats = client.get_stats()
        logger.info("")
        logger.info("=" * 60)
        logger.info("Session Statistics:")
        logger.info(f"  Messages received: {stats['messages_received']}")
        uptime = stats.get('uptime_seconds')
        if uptime is not None:
            logger.info(f"  Uptime: {uptime:.1f}s")
        else:
            logger.info(f"  Uptime: N/A")
        logger.info(f"  Reconnections: {stats['reconnect_count']}")
        logger.info(f"  Is connected: {stats['is_connected']}")
        
        if stats['messages_received'] > 0:
            logger.info("")
            logger.info("✓ WebSocket Client Test: PASSED")
        else:
            logger.warning("")
            logger.warning("⚠ No messages received - check internet connection")
        
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        await client.disconnect()
        raise


if __name__ == "__main__":
    asyncio.run(main())
