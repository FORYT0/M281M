"""
Test script for feature calculator with live data.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline.multi_stream_client import MultiStreamAggregator
from loguru import logger

logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)


def feature_callback(symbol: str, features: dict):
    """Callback to display computed features."""
    timestamp = features['timestamp'].strftime("%H:%M:%S.%f")[:-3]
    
    logger.info(
        f"[{symbol}] "
        f"Price={features['price']:.2f} | "
        f"OFI={features['order_flow_imbalance']:+.3f} | "
        f"CumDelta={features['cumulative_delta']:+.2f} | "
        f"VPIN={features.get('vpin', 0) or 0:.3f} | "
        f"RSI={features.get('rsi', 0) or 0:.1f}"
    )


async def main():
    logger.info("=" * 70)
    logger.info("M281M Feature Calculator Test - Live Data")
    logger.info("=" * 70)
    logger.info("")
    logger.info("Testing real-time feature computation with BTC/USDT")
    logger.info("Running for 15 seconds...")
    logger.info("")
    
    # Create aggregator
    aggregator = MultiStreamAggregator(
        symbols=['BTCUSDT'],
        feature_callback=feature_callback,
        testnet=False
    )
    
    try:
        # Start in background
        task = asyncio.create_task(aggregator.start())
        
        # Run for 15 seconds
        await asyncio.sleep(15)
        
        # Stop
        await aggregator.stop()
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Print statistics
        stats = aggregator.get_stats()
        logger.info("")
        logger.info("=" * 70)
        logger.info("Statistics:")
        logger.info(f"  Features computed: {stats['feature_count']}")
        logger.info(f"  Uptime: {stats['uptime_seconds']:.1f}s")
        logger.info(f"  Throughput: {stats['features_per_second']:.1f} features/sec")
        
        if stats['features_per_second'] > 0:
            latency_ms = 1000 / stats['features_per_second']
            logger.info(f"  Avg latency: {latency_ms:.1f}ms per feature")
            
            if latency_ms < 50:
                logger.info("")
                logger.info("✓ Feature Calculator Test: PASSED (<50ms target)")
            else:
                logger.warning("")
                logger.warning(f"⚠ Latency {latency_ms:.1f}ms exceeds 50ms target")
        
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        await aggregator.stop()
        raise


if __name__ == "__main__":
    asyncio.run(main())
