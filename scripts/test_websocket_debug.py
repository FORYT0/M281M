"""
Debug WebSocket connection to see what messages we're receiving.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import json
from src.pipeline.websocket_client import BinanceWebSocketClient


message_count = 0

async def debug_callback(data: dict):
    """Print received messages."""
    global message_count
    message_count += 1
    
    if message_count <= 5:
        print(f"\n[Message {message_count}]")
        print(f"Type: {type(data)}")
        print(f"Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
        if isinstance(data, dict):
            if 'stream' in data:
                print(f"Stream: {data.get('stream')}")
            if 'e' in data:
                print(f"Event: {data.get('e')}")
            if 'data' in data:
                print(f"Has 'data' field: Yes")
                if isinstance(data['data'], dict):
                    print(f"Data keys: {list(data['data'].keys())[:10]}")
        print(json.dumps(data, indent=2)[:500])  # First 500 chars
    
    if message_count % 100 == 0:
        print(f"\n[Total messages received: {message_count}]")


async def main():
    """Test WebSocket connection."""
    print("="*60)
    print("WebSocket Debug Test")
    print("="*60)
    print("\nConnecting to Binance...")
    print("Will show first 5 messages in detail")
    print("Press Ctrl+C to stop\n")
    
    streams = [
        'btcusdt@depth20@100ms',
        'btcusdt@trade',
        'btcusdt@ticker'
    ]
    
    client = BinanceWebSocketClient(
        streams=streams,
        callback=debug_callback,
        testnet=False
    )
    
    try:
        await client.start()
    except KeyboardInterrupt:
        print(f"\n\nStopped. Total messages: {message_count}")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest stopped")
