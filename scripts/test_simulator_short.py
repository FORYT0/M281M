"""
Short test for tick replay simulator - 5 minutes of data.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline.tick_simulator import TickReplaySimulator, generate_synthetic_orderbook_data
from loguru import logger

logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)


def main():
    logger.info("=" * 60)
    logger.info("M281M Tick Replay Simulator - Short Test (5 minutes)")
    logger.info("=" * 60)
    logger.info("")
    
    # Generate 5 minutes of synthetic data
    data_path = "data/historical/synthetic_btcusdt_5min.csv"
    generate_synthetic_orderbook_data(
        output_path=data_path,
        symbol="BTCUSDT",
        duration_minutes=5,
        tick_interval_ms=100,
        base_price=50000.0,
        volatility=0.001
    )
    
    logger.info("")
    logger.info("Starting replay at 50x speed...")
    logger.info("")
    
    # Create simulator with faster speed
    simulator = TickReplaySimulator(
        data_path=data_path,
        speed_multiplier=50.0
    )
    
    tick_count = 0
    for tick in simulator.replay():
        tick_count += 1
        
        # Print every 500 ticks
        if tick_count % 500 == 0:
            progress = simulator.get_progress()
            logger.info(
                f"Tick {tick_count}: "
                f"Price={tick['mid_price']:.2f}, "
                f"Spread={tick['best_ask'] - tick['best_bid']:.2f}, "
                f"Progress={progress['progress_percent']:.1f}%"
            )
    
    logger.info("")
    logger.info(f"✓ Replay completed! Processed {tick_count} ticks")
    logger.info("")
    logger.info("=" * 60)
    logger.info("Tick Simulator Test: PASSED")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
