"""
Test script for tick replay simulator.
Generates synthetic data and replays it.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline.tick_simulator import TickReplaySimulator, generate_synthetic_orderbook_data
from loguru import logger

# Configure logger
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level="INFO"
)


def main():
    """Main test function."""
    logger.info("=" * 60)
    logger.info("M281M Tick Replay Simulator Test")
    logger.info("=" * 60)
    logger.info("")
    
    # Generate synthetic data
    data_path = "data/historical/synthetic_btcusdt_1h.csv"
    generate_synthetic_orderbook_data(
        output_path=data_path,
        symbol="BTCUSDT",
        duration_minutes=60,
        tick_interval_ms=100,
        base_price=50000.0,
        volatility=0.001
    )
    
    logger.info("")
    logger.info("Starting replay at 10x speed...")
    logger.info("Press Ctrl+C to stop")
    logger.info("")
    
    # Create simulator
    simulator = TickReplaySimulator(
        data_path=data_path,
        speed_multiplier=10.0
    )
    
    try:
        tick_count = 0
        for tick in simulator.replay():
            tick_count += 1
            
            # Print every 100 ticks
            if tick_count % 100 == 0:
                progress = simulator.get_progress()
                logger.info(
                    f"Tick {tick_count}: "
                    f"Price={tick['mid_price']:.2f}, "
                    f"Spread={tick['best_ask'] - tick['best_bid']:.2f}, "
                    f"Progress={progress['progress_percent']:.1f}%"
                )
        
        logger.info("")
        logger.info(f"Replay completed! Processed {tick_count} ticks")
        
    except KeyboardInterrupt:
        logger.info("\nStopped by user")
        progress = simulator.get_progress()
        logger.info(f"Progress: {progress['progress_percent']:.1f}%")


if __name__ == "__main__":
    main()
