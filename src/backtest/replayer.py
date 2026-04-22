"""
Data Replayer - Replays historical data as real-time events.
Simulates live trading conditions for backtesting.
"""

import pandas as pd
import asyncio
import time
from typing import Callable, Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum


class EventType(Enum):
    """Event types for replay."""
    OHLCV = "ohlcv"
    TRADE = "trade"
    ORDER_BOOK = "order_book"
    TICK = "tick"


@dataclass
class ReplayEvent:
    """Event during data replay."""
    
    timestamp: datetime
    event_type: EventType
    symbol: str
    data: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp,
            'event_type': self.event_type.value,
            'symbol': self.symbol,
            'data': self.data
        }


class DataReplayer:
    """
    Replays historical data as real-time events.
    
    Features:
    - Event-driven replay
    - Configurable speed (1x to max)
    - Progress tracking
    - Pause/resume support
    """
    
    def __init__(
        self,
        speed: float = 1.0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ):
        """
        Initialize data replayer.
        
        Args:
            speed: Replay speed multiplier (1.0 = real-time, 0 = max speed)
            start_date: Start date for replay (optional)
            end_date: End date for replay (optional)
        """
        self.speed = speed
        self.start_date = start_date
        self.end_date = end_date
        
        # State
        self.is_running = False
        self.is_paused = False
        self.current_time = None
        self.events_processed = 0
        self.total_events = 0
        
        # Timing
        self.replay_start_time = None
        self.simulated_start_time = None
    
    def replay(
        self,
        data: pd.DataFrame,
        callback: Callable[[ReplayEvent], None],
        symbol: str = "BTCUSDT",
        event_type: EventType = EventType.OHLCV
    ):
        """
        Replay data synchronously.
        
        Args:
            data: DataFrame with timestamp column
            callback: Function to call for each event
            symbol: Trading symbol
            event_type: Type of events to generate
        """
        # Filter by date range
        if self.start_date:
            data = data[data['timestamp'] >= self.start_date]
        if self.end_date:
            data = data[data['timestamp'] <= self.end_date]
        
        if data.empty:
            print("⚠ No data to replay")
            return
        
        self.total_events = len(data)
        self.is_running = True
        self.replay_start_time = time.time()
        self.simulated_start_time = data['timestamp'].iloc[0]
        
        print(f"Starting replay: {self.total_events} events")
        print(f"Date range: {data['timestamp'].min()} to {data['timestamp'].max()}")
        print(f"Speed: {self.speed}x" if self.speed > 0 else "Speed: MAX")
        
        last_timestamp = None
        
        for idx, row in data.iterrows():
            if not self.is_running:
                break
            
            # Handle pause
            while self.is_paused:
                time.sleep(0.1)
            
            current_timestamp = row['timestamp']
            self.current_time = current_timestamp
            
            # Simulate time delay
            if self.speed > 0 and last_timestamp is not None:
                time_diff = (current_timestamp - last_timestamp).total_seconds()
                sleep_time = time_diff / self.speed
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
            # Create event
            event = ReplayEvent(
                timestamp=current_timestamp,
                event_type=event_type,
                symbol=symbol,
                data=row.to_dict()
            )
            
            # Call callback
            try:
                callback(event)
            except Exception as e:
                print(f"✗ Error in callback: {e}")
            
            self.events_processed += 1
            last_timestamp = current_timestamp
            
            # Progress update
            if self.events_processed % 100 == 0:
                self._print_progress()
        
        self.is_running = False
        self._print_summary()
    
    async def replay_async(
        self,
        data: pd.DataFrame,
        callback: Callable[[ReplayEvent], Any],
        symbol: str = "BTCUSDT",
        event_type: EventType = EventType.OHLCV
    ):
        """
        Replay data asynchronously.
        
        Args:
            data: DataFrame with timestamp column
            callback: Async function to call for each event
            symbol: Trading symbol
            event_type: Type of events to generate
        """
        # Filter by date range
        if self.start_date:
            data = data[data['timestamp'] >= self.start_date]
        if self.end_date:
            data = data[data['timestamp'] <= self.end_date]
        
        if data.empty:
            print("⚠ No data to replay")
            return
        
        self.total_events = len(data)
        self.is_running = True
        self.replay_start_time = time.time()
        self.simulated_start_time = data['timestamp'].iloc[0]
        
        print(f"Starting async replay: {self.total_events} events")
        print(f"Speed: {self.speed}x" if self.speed > 0 else "Speed: MAX")
        
        last_timestamp = None
        
        for idx, row in data.iterrows():
            if not self.is_running:
                break
            
            # Handle pause
            while self.is_paused:
                await asyncio.sleep(0.1)
            
            current_timestamp = row['timestamp']
            self.current_time = current_timestamp
            
            # Simulate time delay
            if self.speed > 0 and last_timestamp is not None:
                time_diff = (current_timestamp - last_timestamp).total_seconds()
                sleep_time = time_diff / self.speed
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
            
            # Create event
            event = ReplayEvent(
                timestamp=current_timestamp,
                event_type=event_type,
                symbol=symbol,
                data=row.to_dict()
            )
            
            # Call callback
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                print(f"✗ Error in callback: {e}")
            
            self.events_processed += 1
            last_timestamp = current_timestamp
            
            # Progress update
            if self.events_processed % 100 == 0:
                self._print_progress()
        
        self.is_running = False
        self._print_summary()
    
    def pause(self):
        """Pause replay."""
        self.is_paused = True
        print("⏸️  Replay paused")
    
    def resume(self):
        """Resume replay."""
        self.is_paused = False
        print("▶️  Replay resumed")
    
    def stop(self):
        """Stop replay."""
        self.is_running = False
        print("⏹️  Replay stopped")
    
    def get_progress(self) -> float:
        """
        Get replay progress.
        
        Returns:
            Progress as percentage (0-100)
        """
        if self.total_events == 0:
            return 0.0
        return (self.events_processed / self.total_events) * 100
    
    def get_stats(self) -> Dict[str, Any]:
        """Get replay statistics."""
        if not self.replay_start_time:
            return {}
        
        elapsed_real = time.time() - self.replay_start_time
        
        if self.current_time and self.simulated_start_time:
            elapsed_sim = (self.current_time - self.simulated_start_time).total_seconds()
            actual_speed = elapsed_sim / elapsed_real if elapsed_real > 0 else 0
        else:
            elapsed_sim = 0
            actual_speed = 0
        
        events_per_sec = self.events_processed / elapsed_real if elapsed_real > 0 else 0
        
        return {
            'events_processed': self.events_processed,
            'total_events': self.total_events,
            'progress_pct': self.get_progress(),
            'elapsed_real_seconds': elapsed_real,
            'elapsed_sim_seconds': elapsed_sim,
            'actual_speed': actual_speed,
            'events_per_second': events_per_sec,
            'current_time': self.current_time
        }
    
    def _print_progress(self):
        """Print progress update."""
        progress = self.get_progress()
        stats = self.get_stats()
        
        print(
            f"Progress: {progress:.1f}% | "
            f"Events: {self.events_processed}/{self.total_events} | "
            f"Speed: {stats['actual_speed']:.1f}x | "
            f"Time: {self.current_time}"
        )
    
    def _print_summary(self):
        """Print replay summary."""
        stats = self.get_stats()
        
        print("\n" + "=" * 60)
        print("Replay Summary")
        print("=" * 60)
        print(f"Events processed: {self.events_processed}/{self.total_events}")
        print(f"Real time elapsed: {stats['elapsed_real_seconds']:.1f}s")
        print(f"Simulated time: {stats['elapsed_sim_seconds']:.1f}s")
        print(f"Average speed: {stats['actual_speed']:.1f}x")
        print(f"Events per second: {stats['events_per_second']:.1f}")
        print("=" * 60)
    
    def reset(self):
        """Reset replayer state."""
        self.is_running = False
        self.is_paused = False
        self.current_time = None
        self.events_processed = 0
        self.total_events = 0
        self.replay_start_time = None
        self.simulated_start_time = None


class MultiSymbolReplayer:
    """
    Replays data for multiple symbols simultaneously.
    Merges events from multiple sources in chronological order.
    """
    
    def __init__(self, speed: float = 1.0):
        """
        Initialize multi-symbol replayer.
        
        Args:
            speed: Replay speed multiplier
        """
        self.speed = speed
        self.replayers: Dict[str, DataReplayer] = {}
    
    def add_symbol(
        self,
        symbol: str,
        data: pd.DataFrame,
        event_type: EventType = EventType.OHLCV
    ):
        """
        Add symbol data for replay.
        
        Args:
            symbol: Trading symbol
            data: Historical data
            event_type: Event type
        """
        replayer = DataReplayer(speed=self.speed)
        self.replayers[symbol] = {
            'replayer': replayer,
            'data': data,
            'event_type': event_type
        }
    
    def replay_all(self, callback: Callable[[ReplayEvent], None]):
        """
        Replay all symbols in chronological order.
        
        Args:
            callback: Function to call for each event
        """
        # Merge all data
        all_events = []
        
        for symbol, config in self.replayers.items():
            data = config['data']
            event_type = config['event_type']
            
            for _, row in data.iterrows():
                event = ReplayEvent(
                    timestamp=row['timestamp'],
                    event_type=event_type,
                    symbol=symbol,
                    data=row.to_dict()
                )
                all_events.append(event)
        
        # Sort by timestamp
        all_events.sort(key=lambda e: e.timestamp)
        
        print(f"Replaying {len(all_events)} events from {len(self.replayers)} symbols")
        
        # Replay in order
        last_timestamp = None
        
        for event in all_events:
            # Simulate time delay
            if self.speed > 0 and last_timestamp is not None:
                time_diff = (event.timestamp - last_timestamp).total_seconds()
                sleep_time = time_diff / self.speed
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
            callback(event)
            last_timestamp = event.timestamp
