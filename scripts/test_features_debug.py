"""
Debug script to see raw WebSocket messages.
"""

import asyncio
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline.websocket_client import BinanceWebSocketClient
from loguru import logger

logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)

message_count = 0

def message_callback(data: dict):
    """Print raw messages."""
    global message_count
    message_count += 1
    
    if message_count <= 5:  # Only print first 5
        logger.info(f"Message {message_count}:")
        logger.info(json.dumps(data, indent=2)[:500])  # First 500 chars


async def main():
    logger.info("Connecting to Binance combined stream...")
    logger.info("Will show first 5 messages")
    logger.info("")
    
    client = BinanceWebSocketClient(
        streams=["btcusdt@depth20@100ms", "btcusdt@trade"],
        callback=message_callback,
        testnet=False
    )
    
    try:
        task = asyncio.create_task(client.start())
        await asyncio.sleep(10)
        await client.disconnect()
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        logger.info(f"\nTotal messages: {message_count}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
