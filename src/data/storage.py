"""
Data Storage - Save and load historical data.
"""

import pandas as pd
import os
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DataStorage:
    """
    Store and retrieve historical market data.
    
    Supports:
    - CSV storage
    - Parquet storage (compressed)
    - Data versioning
    - Metadata tracking
    """
    
    def __init__(self, data_dir: str = "data/historical"):
        """
        Initialize data storage.
        
        Args:
            data_dir: Directory for storing data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized data storage at {self.data_dir}")
    
    def save_ohlcv(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str,
        format: str = 'csv'
    ) -> str:
        """
        Save OHLCV data.
        
        Args:
            df: DataFrame with OHLCV data
            symbol: Trading pair
            timeframe: Timeframe
            format: File format ('csv' or 'parquet')
        
        Returns:
            Path to saved file
        """
        # Clean symbol for filename
        clean_symbol = symbol.replace('/', '').lower()
        
        # Create filename
        filename = f"{clean_symbol}_{timeframe}.{format}"
        filepath = self.data_dir / filename
        
        # Save data
        if format == 'csv':
            df.to_csv(filepath, index=False)
        elif format == 'parquet':
            df.to_parquet(filepath, index=False, compression='snappy')
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"Saved {len(df)} rows to {filepath}")
        
        return str(filepath)
    
    def load_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        format: str = 'csv'
    ) -> Optional[pd.DataFrame]:
        """
        Load OHLCV data.
        
        Args:
            symbol: Trading pair
            timeframe: Timeframe
            format: File format
        
        Returns:
            DataFrame or None if not found
        """
        clean_symbol = symbol.replace('/', '').lower()
        filename = f"{clean_symbol}_{timeframe}.{format}"
        filepath = self.data_dir / filename
        
        if not filepath.exists():
            logger.warning(f"Data file not found: {filepath}")
            return None
        
        # Load data
        if format == 'csv':
            df = pd.read_csv(filepath)
        elif format == 'parquet':
            df = pd.read_parquet(filepath)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        # Parse timestamp
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        logger.info(f"Loaded {len(df)} rows from {filepath}")
        
        return df
    
    def list_available_data(self) -> list:
        """
        List all available data files.
        
        Returns:
            List of (symbol, timeframe, format) tuples
        """
        available = []
        
        for filepath in self.data_dir.glob('*'):
            if filepath.is_file():
                name = filepath.stem
                ext = filepath.suffix[1:]
                
                # Parse filename
                parts = name.split('_')
                if len(parts) >= 2:
                    symbol = parts[0].upper()
                    timeframe = parts[1]
                    available.append((symbol, timeframe, ext))
        
        return sorted(available)
    
    def get_data_info(self, symbol: str, timeframe: str) -> dict:
        """
        Get information about stored data.
        
        Args:
            symbol: Trading pair
            timeframe: Timeframe
        
        Returns:
            Dictionary with data info
        """
        df = self.load_ohlcv(symbol, timeframe)
        
        if df is None:
            return {'exists': False}
        
        return {
            'exists': True,
            'rows': len(df),
            'start_date': df['timestamp'].min(),
            'end_date': df['timestamp'].max(),
            'columns': list(df.columns),
            'memory_usage': df.memory_usage(deep=True).sum() / 1024 / 1024  # MB
        }
    
    def delete_data(self, symbol: str, timeframe: str, format: str = 'csv'):
        """
        Delete stored data.
        
        Args:
            symbol: Trading pair
            timeframe: Timeframe
            format: File format
        """
        clean_symbol = symbol.replace('/', '').lower()
        filename = f"{clean_symbol}_{timeframe}.{format}"
        filepath = self.data_dir / filename
        
        if filepath.exists():
            filepath.unlink()
            logger.info(f"Deleted {filepath}")
        else:
            logger.warning(f"File not found: {filepath}")
