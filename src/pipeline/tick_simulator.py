"""
Tick replay simulator for backtesting and offline testing.
Reads historical data and replays it with accurate timing.
"""

import pandas as pd
import time
from pathlib import Path
from typing import Generator, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger


class TickReplaySimulator:
    """
    Replays historical tick data with accurate timing for backtesting.
    Supports CSV and Parquet formats.
    """
    
    def __init__(
        self,
        data_path: str,
        speed_multiplier: float = 1.0,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ):
        """
        Initialize tick replay simulator.
        
        Args:
            data_path: Path to historical data file (CSV or Parquet)
            speed_multiplier: Replay speed (1.0 = real-time, 2.0 = 2x speed)
            start_time: Start replay from this timestamp
            end_time: End replay at this timestamp
        """
        self.data_path = Path(data_path)
        self.speed_multiplier = speed_multiplier
        self.start_time = start_time
        self.end_time = end_time
        
        self.data: Optional[pd.DataFrame] = None
        self.current_index = 0
        self.replay_start_time = None
        self.data_start_time = None
        
        self._load_data()
    
    def _load_data(self):
        """Load historical data from file."""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_path}")
        
        logger.info(f"Loading data from {self.data_path}")
        
        # Load based on file extension
        if self.data_path.suffix == '.csv':
            self.data = pd.read_csv(self.data_path)
        elif self.data_path.suffix == '.parquet':
            self.data = pd.read_parquet(self.data_path)
        else:
            raise ValueError(f"Unsupported file format: {self.data_path.suffix}")
        
        # Ensure timestamp column exists
        if 'timestamp' not in self.data.columns:
            raise ValueError("Data must have a 'timestamp' column")
        
        # Convert timestamp to datetime
        self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
        
        # Sort by timestamp
        self.data = self.data.sort_values('timestamp').reset_index(drop=True)
        
        # Filter by time range if specified
        if self.start_time:
            self.data = self.data[self.data['timestamp'] >= self.start_time]
        if self.end_time:
            self.data = self.data[self.data['timestamp'] <= self.end_time]
        
        self.data = self.data.reset_index(drop=True)
        
        logger.info(
            f"Loaded {len(self.data)} ticks from "
            f"{self.data['timestamp'].min()} to {self.data['timestamp'].max()}"
        )
    
    def replay(self) -> Generator[Dict[str, Any], None, None]:
        """
        Replay ticks with accurate timing.
        
        Yields:
            Dictionary containing tick data
        """
        if self.data is None or len(self.data) == 0:
            logger.warning("No data to replay")
            return
        
        self.replay_start_time = time.time()
        self.data_start_time = self.data['timestamp'].iloc[0]
        
        logger.info(f"Starting replay at {self.speed_multiplier}x speed")
        
        for idx, row in self.data.iterrows():
            # Calculate when this tick should be emitted
            data_elapsed = (row['timestamp'] - self.data_start_time).total_seconds()
            target_elapsed = data_elapsed / self.speed_multiplier
            
            # Wait until the right time
            actual_elapsed = time.time() - self.replay_start_time
            sleep_time = target_elapsed - actual_elapsed
            
            if sleep_time > 0:
                time.sleep(sleep_time)
            
            # Convert row to dict and yield
            tick = row.to_dict()
            tick['timestamp'] = tick['timestamp'].isoformat()
            
            self.current_index = idx
            yield tick
        
        logger.info("Replay completed")
    
    def get_progress(self) -> Dict[str, Any]:
        """Get replay progress statistics."""
        if self.data is None:
            return {}
        
        total_ticks = len(self.data)
        progress_pct = (self.current_index / total_ticks * 100) if total_ticks > 0 else 0
        
        elapsed_time = None
        if self.replay_start_time:
            elapsed_time = time.time() - self.replay_start_time
        
        return {
            "current_index": self.current_index,
            "total_ticks": total_ticks,
            "progress_percent": progress_pct,
            "elapsed_seconds": elapsed_time,
            "speed_multiplier": self.speed_multiplier
        }


def generate_synthetic_orderbook_data(
    output_path: str,
    symbol: str = "BTCUSDT",
    duration_minutes: int = 60,
    tick_interval_ms: int = 100,
    base_price: float = 50000.0,
    volatility: float = 0.001
) -> str:
    """
    Generate synthetic order book data for testing.
    
    Args:
        output_path: Where to save the generated data
        symbol: Trading symbol
        duration_minutes: How many minutes of data to generate
        tick_interval_ms: Milliseconds between ticks
        base_price: Starting price
        volatility: Price volatility (std dev as fraction of price)
    
    Returns:
        Path to generated file
    """
    import numpy as np
    
    logger.info(f"Generating {duration_minutes} minutes of synthetic data...")
    
    # Calculate number of ticks
    num_ticks = int(duration_minutes * 60 * 1000 / tick_interval_ms)
    
    # Generate timestamps
    start_time = datetime.now() - timedelta(minutes=duration_minutes)
    timestamps = [
        start_time + timedelta(milliseconds=i * tick_interval_ms)
        for i in range(num_ticks)
    ]
    
    # Generate price walk
    returns = np.random.normal(0, volatility, num_ticks)
    prices = base_price * np.exp(np.cumsum(returns))
    
    # Generate bid/ask with spread
    spreads = np.random.uniform(0.0001, 0.0005, num_ticks) * prices
    bids = prices - spreads / 2
    asks = prices + spreads / 2
    
    # Generate volumes
    bid_volumes = np.random.uniform(0.1, 5.0, num_ticks)
    ask_volumes = np.random.uniform(0.1, 5.0, num_ticks)
    
    # Create DataFrame
    data = pd.DataFrame({
        'timestamp': timestamps,
        'symbol': symbol,
        'best_bid': bids,
        'best_ask': asks,
        'bid_volume': bid_volumes,
        'ask_volume': ask_volumes,
        'mid_price': prices
    })
    
    # Save to file
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if output_path.suffix == '.csv':
        data.to_csv(output_path, index=False)
    elif output_path.suffix == '.parquet':
        data.to_parquet(output_path, index=False)
    else:
        raise ValueError(f"Unsupported format: {output_path.suffix}")
    
    logger.info(f"Generated {len(data)} ticks, saved to {output_path}")
    return str(output_path)
