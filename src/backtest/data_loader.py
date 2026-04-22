"""
Historical Data Loader - Loads and validates historical market data.
Supports CSV, Parquet, and synthetic data generation.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass


class DataSource(Enum):
    """Data source types."""
    CSV = "csv"
    PARQUET = "parquet"
    INFLUXDB = "influxdb"
    SYNTHETIC = "synthetic"


@dataclass
class DataValidationResult:
    """Result of data validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    row_count: int
    date_range: tuple
    
    def __str__(self) -> str:
        status = "✓ VALID" if self.is_valid else "✗ INVALID"
        return f"{status}: {self.row_count} rows, {len(self.errors)} errors, {len(self.warnings)} warnings"


class HistoricalDataLoader:
    """
    Loads historical market data from various sources.
    
    Supports:
    - OHLCV data (candlesticks)
    - Trade data (tick-by-tick)
    - Order book snapshots
    - Synthetic data generation
    """
    
    def __init__(self, data_dir: str = "data/historical"):
        """
        Initialize data loader.
        
        Args:
            data_dir: Directory containing historical data files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def load_ohlcv(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        timeframe: str = "1h",
        source: DataSource = DataSource.CSV
    ) -> pd.DataFrame:
        """
        Load OHLCV (candlestick) data.
        
        Args:
            symbol: Trading symbol
            start_date: Start date (optional)
            end_date: End date (optional)
            timeframe: Timeframe (1m, 5m, 1h, 1d, etc.)
            source: Data source type
        
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        if source == DataSource.CSV:
            return self._load_ohlcv_csv(symbol, start_date, end_date, timeframe)
        elif source == DataSource.PARQUET:
            return self._load_ohlcv_parquet(symbol, start_date, end_date, timeframe)
        elif source == DataSource.SYNTHETIC:
            return self._generate_synthetic_ohlcv(symbol, start_date, end_date, timeframe)
        else:
            raise ValueError(f"Unsupported data source: {source}")
    
    def _load_ohlcv_csv(
        self,
        symbol: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        timeframe: str
    ) -> pd.DataFrame:
        """Load OHLCV data from CSV."""
        filename = f"synthetic_{symbol.lower()}_{timeframe}.csv"
        filepath = self.data_dir / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"Data file not found: {filepath}")
        
        # Load CSV
        df = pd.read_csv(filepath)
        
        # Parse timestamp
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        elif 'date' in df.columns:
            df['timestamp'] = pd.to_datetime(df['date'])
            df = df.drop('date', axis=1)
        
        # Filter by date range
        if start_date:
            df = df[df['timestamp'] >= start_date]
        if end_date:
            df = df[df['timestamp'] <= end_date]
        
        # Ensure required columns
        required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
        
        return df.sort_values('timestamp').reset_index(drop=True)
    
    def _load_ohlcv_parquet(
        self,
        symbol: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        timeframe: str
    ) -> pd.DataFrame:
        """Load OHLCV data from Parquet."""
        filename = f"{symbol.lower()}_{timeframe}.parquet"
        filepath = self.data_dir / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"Data file not found: {filepath}")
        
        df = pd.read_parquet(filepath)
        
        # Filter by date range
        if start_date:
            df = df[df['timestamp'] >= start_date]
        if end_date:
            df = df[df['timestamp'] <= end_date]
        
        return df.sort_values('timestamp').reset_index(drop=True)
    
    def _generate_synthetic_ohlcv(
        self,
        symbol: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        timeframe: str
    ) -> pd.DataFrame:
        """Generate synthetic OHLCV data for testing."""
        if not start_date:
            start_date = datetime.now() - timedelta(days=365)
        if not end_date:
            end_date = datetime.now()
        
        # Parse timeframe
        timeframe_minutes = self._parse_timeframe(timeframe)
        
        # Generate timestamps
        timestamps = pd.date_range(
            start=start_date,
            end=end_date,
            freq=f"{timeframe_minutes}min"
        )
        
        n = len(timestamps)
        
        # Generate price data with random walk
        base_price = 50000.0
        returns = np.random.randn(n) * 0.02  # 2% volatility
        prices = base_price * np.exp(np.cumsum(returns))
        
        # Generate OHLCV
        data = []
        for i, ts in enumerate(timestamps):
            close = prices[i]
            open_price = prices[i-1] if i > 0 else close
            
            # High/low with some randomness
            high = max(open_price, close) * (1 + abs(np.random.randn()) * 0.005)
            low = min(open_price, close) * (1 - abs(np.random.randn()) * 0.005)
            
            # Volume
            volume = abs(np.random.randn() * 10 + 50)
            
            data.append({
                'timestamp': ts,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })
        
        return pd.DataFrame(data)
    
    def _parse_timeframe(self, timeframe: str) -> int:
        """Parse timeframe string to minutes."""
        timeframe = timeframe.lower()
        
        if timeframe.endswith('m'):
            return int(timeframe[:-1])
        elif timeframe.endswith('h'):
            return int(timeframe[:-1]) * 60
        elif timeframe.endswith('d'):
            return int(timeframe[:-1]) * 1440
        else:
            raise ValueError(f"Invalid timeframe: {timeframe}")
    
    def load_trades(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Load trade (tick) data.
        
        Args:
            symbol: Trading symbol
            start_date: Start date (optional)
            end_date: End date (optional)
        
        Returns:
            DataFrame with columns: timestamp, price, quantity, is_buyer_maker
        """
        # For now, generate synthetic trades from OHLCV
        ohlcv = self.load_ohlcv(symbol, start_date, end_date, timeframe="5min")
        
        trades = []
        for _, row in ohlcv.iterrows():
            # Generate multiple trades per candle
            n_trades = np.random.randint(5, 20)
            
            for _ in range(n_trades):
                price = np.random.uniform(row['low'], row['high'])
                quantity = abs(np.random.randn() * 0.1 + 0.5)
                is_buyer_maker = np.random.random() > 0.5
                
                trades.append({
                    'timestamp': row['timestamp'],
                    'price': price,
                    'quantity': quantity,
                    'is_buyer_maker': is_buyer_maker
                })
        
        return pd.DataFrame(trades).sort_values('timestamp').reset_index(drop=True)
    
    def validate_data(self, df: pd.DataFrame, data_type: str = "ohlcv") -> DataValidationResult:
        """
        Validate loaded data.
        
        Args:
            df: DataFrame to validate
            data_type: Type of data ('ohlcv', 'trades', 'orderbook')
        
        Returns:
            DataValidationResult with validation outcome
        """
        errors = []
        warnings = []
        
        # Check if empty
        if df.empty:
            errors.append("DataFrame is empty")
            return DataValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                row_count=0,
                date_range=(None, None)
            )
        
        # Check required columns
        if data_type == "ohlcv":
            required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        elif data_type == "trades":
            required_cols = ['timestamp', 'price', 'quantity']
        else:
            required_cols = ['timestamp']
        
        for col in required_cols:
            if col not in df.columns:
                errors.append(f"Missing required column: {col}")
        
        if errors:
            return DataValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                row_count=len(df),
                date_range=(None, None)
            )
        
        # Check for NaN values
        nan_cols = df.columns[df.isna().any()].tolist()
        if nan_cols:
            warnings.append(f"NaN values found in columns: {nan_cols}")
        
        # Check for negative values in price/volume
        if data_type == "ohlcv":
            price_cols = ['open', 'high', 'low', 'close']
            for col in price_cols:
                if (df[col] <= 0).any():
                    errors.append(f"Non-positive values found in {col}")
            
            if (df['volume'] < 0).any():
                errors.append("Negative volume values found")
            
            # Check OHLC consistency
            if ((df['high'] < df['low']) | 
                (df['high'] < df['open']) | 
                (df['high'] < df['close']) |
                (df['low'] > df['open']) |
                (df['low'] > df['close'])).any():
                errors.append("OHLC consistency violated")
        
        # Check timestamp ordering
        if not df['timestamp'].is_monotonic_increasing:
            warnings.append("Timestamps are not monotonically increasing")
        
        # Check for duplicates
        if df['timestamp'].duplicated().any():
            warnings.append("Duplicate timestamps found")
        
        # Get date range
        date_range = (df['timestamp'].min(), df['timestamp'].max())
        
        is_valid = len(errors) == 0
        
        return DataValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            row_count=len(df),
            date_range=date_range
        )
    
    def get_available_data(self) -> Dict[str, List[str]]:
        """
        Get list of available data files.
        
        Returns:
            Dictionary mapping data types to available files
        """
        available = {
            'csv': [],
            'parquet': []
        }
        
        if self.data_dir.exists():
            for file in self.data_dir.iterdir():
                if file.suffix == '.csv':
                    available['csv'].append(file.name)
                elif file.suffix == '.parquet':
                    available['parquet'].append(file.name)
        
        return available
    
    def save_data(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str,
        format: str = "csv"
    ):
        """
        Save data to file.
        
        Args:
            df: DataFrame to save
            symbol: Trading symbol
            timeframe: Timeframe
            format: File format ('csv' or 'parquet')
        """
        filename = f"{symbol.lower()}_{timeframe}.{format}"
        filepath = self.data_dir / filename
        
        if format == "csv":
            df.to_csv(filepath, index=False)
        elif format == "parquet":
            df.to_parquet(filepath, index=False)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        print(f"✓ Saved {len(df)} rows to {filepath}")
