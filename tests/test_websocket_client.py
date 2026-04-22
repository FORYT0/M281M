"""Unit tests for WebSocket client."""

import pytest
import asyncio
from src.pipeline.websocket_client import BinanceWebSocketClient, OrderBookTracker


@pytest.mark.asyncio
async def test_orderbook_tracker():
    """Test order book tracker processes updates correctly."""
    tracker = OrderBookTracker()
    
    # Simulate depth update
    mock_data = {
        'lastUpdateId': 12345,
        'bids': [['50000.00', '1.5'], ['49999.00', '2.0']],
        'asks': [['50001.00', '1.2'], ['50002.00', '1.8']]
    }
    
    tracker.process_depth_update(mock_data)
    
    assert tracker.best_bid == 50000.00
    assert tracker.best_ask == 50001.00
    assert tracker.update_count == 1


def test_websocket_initialization():
    """Test WebSocket client initializes correctly."""
    client = BinanceWebSocketClient(
        streams=['btcusdt@depth20@100ms'],
        callback=lambda x: None,
        testnet=True
    )
    
    assert client.testnet is True
    assert len(client.streams) == 1
    assert client.messages_received == 0
