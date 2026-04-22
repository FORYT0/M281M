"""
Data Fetcher - Fetch historical market data from exchanges.
"""

import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import time
import logging

logger = logging.getLogger(__name__)


class DataFetcher:
    """
    Fetch historical market data from cryptocurrency exchanges.
    
    Supports:
    - Multiple exchanges (Binance, Coinbase, etc.)
    - Multiple timeframes
    - Rate limiting
    - Data validation
    - Retry logic
    """
    
    def __init__(
        self,
        exchange_id: str = 'binance',
        rate_limit: bool = True,
        timeout: int = 30000
    ):
        """
        Initialize data fetcher.
        
        Args:
            exchange_id: Exchange identifier (e.g., 'binance', 'coinbase')
            rate_limit: Enable rate limiting
            timeout: Request timeout in milliseconds
        """
        self.exchange_id = exchange_id
        
        # Create exchange instance
        exchange_class = getattr(ccxt, exchange_id)
        self.exchange = exchange_class({
            'enableRateLimit': rate_limit,
            'timeout': timeout,
            'options': {
                'defaultType': 'spot'
            }
        })
        
        logger.info(f"Initialized {exchange_id} data fetcher")
    
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = '1h',
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data.
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Timeframe ('1m', '5m', '15m', '1h', '4h', '1d')
            start_date: Start date (None = 1000 candles ago)
            end_date: End date (None = now)
            limit: Max candles per request
        
        Returns:
            DataFrame with OHLCV data
        """
        logger.info(f"Fetching {symbol} {timeframe} data from {self.exchange_id}")
        
        # Convert dates to timestamps
        if end_date is None:
            end_date = datetime.now()
        
        if start_date is None:
            # Default to 1000 candles ago
            timeframe_ms = self._timeframe_to_ms(timeframe)
            start_date = end_date - timedelta(milliseconds=timeframe_ms * 1000)
        
        since = int(start_date.timestamp() * 1000)
        end_ts = int(end_date.timestamp() * 1000)
        
        # Fetch data in chunks
        all_candles = []
        current_since = since
        
        while current_since < end_ts:
            try:
                # Fetch candles
                candles = self.exchange.fetch_ohlcv(
                    symbol=symbol,
                    timeframe=timeframe,
                    since=current_since,
                    limit=limit
                )
                
                if not candles:
                    break
                
                all_candles.extend(candles)
                
                # Update since for next batch
                current_since = candles[-1][0] + 1
                
                # Stop if we've reached the end
                if candles[-1][0] >= end_ts:
                    break
                
                logger.debug(f"Fetched {len(candles)} candles, total: {len(all_candles)}")
                
                # Rate limiting
                time.sleep(self.exchange.rateLimit / 1000)
                
            except Exception as e:
                logger.error(f"Error fetching data: {e}")
                raise
        
        # Convert to DataFrame
        df = pd.DataFrame(
            all_candles,
            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
        )
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Filter by date range
        df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
        
        # Sort by timestamp
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        logger.info(f"Fetched {len(df)} candles from {df['timestamp'].min()} to {df['timestamp'].max()}")
        
        return df
    
    def fetch_trades(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """
        Fetch trade data.
        
        Args:
            symbol: Trading pair
            start_date: Start date
            end_date: End date
            limit: Max trades per request
        
        Returns:
            DataFrame with trade data
        """
        logger.info(f"Fetching {symbol} trades from {self.exchange_id}")
        
        if end_date is None:
            end_date = datetime.now()
        
        if start_date is None:
            start_date = end_date - timedelta(hours=1)
        
        since = int(start_date.timestamp() * 1000)
        end_ts = int(end_date.timestamp() * 1000)
        
        all_trades = []
        current_since = since
        
        while current_since < end_ts:
            try:
                trades = self.exchange.fetch_trades(
                    symbol=symbol,
                    since=current_since,
                    limit=limit
                )
                
                if not trades:
                    break
                
                all_trades.extend(trades)
                current_since = trades[-1]['timestamp'] + 1
                
                if trades[-1]['timestamp'] >= end_ts:
                    break
                
                time.sleep(self.exchange.rateLimit / 1000)
                
            except Exception as e:
                logger.error(f"Error fetching trades: {e}")
                raise
        
        # Convert to DataFrame
        df = pd.DataFrame(all_trades)
        
        if not df.empty:
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df[(df['timestamp'] >= since) & (df['timestamp'] <= end_ts)]
            df = df.sort_values('timestamp').reset_index(drop=True)
        
        logger.info(f"Fetched {len(df)} trades")
        
        return df
    
    def fetch_multiple_symbols(
        self,
        symbols: List[str],
        timeframe: str = '1h',
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple symbols.
        
        Args:
            symbols: List of trading pairs
            timeframe: Timeframe
            start_date: Start date
            end_date: End date
        
        Returns:
            Dictionary mapping symbol to DataFrame
        """
        data = {}
        
        for symbol in symbols:
            try:
                df = self.fetch_ohlcv(
                    symbol=symbol,
                    timeframe=timeframe,
                    start_date=start_date,
                    end_date=end_date
                )
                data[symbol] = df
                
            except Exception as e:
                logger.error(f"Error fetching {symbol}: {e}")
                continue
        
        return data
    
    def get_available_symbols(self) -> List[str]:
        """
        Get list of available trading pairs.
        
        Returns:
            List of symbol strings
        """
        try:
            markets = self.exchange.load_markets()
            symbols = [symbol for symbol in markets.keys() if '/USDT' in symbol]
            return sorted(symbols)
        except Exception as e:
            logger.error(f"Error loading markets: {e}")
            return []
    
    def get_available_timeframes(self) -> List[str]:
        """
        Get list of available timeframes.
        
        Returns:
            List of timeframe strings
        """
        return list(self.exchange.timeframes.keys())
    
    def _timeframe_to_ms(self, timeframe: str) -> int:
        """Convert timeframe string to milliseconds."""
        units = {
            'm': 60 * 1000,
            'h': 60 * 60 * 1000,
            'd': 24 * 60 * 60 * 1000,
            'w': 7 * 24 * 60 * 60 * 1000
        }
        
        unit = timeframe[-1]
        amount = int(timeframe[:-1])
        
        return amount * units.get(unit, 60000)
    
    def validate_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate fetched data.
        
        Args:
            df: DataFrame to validate
        
        Returns:
            Validation results
        """
        issues = []
        
        # Check for missing values
        missing = df.isnull().sum()
        if missing.any():
            issues.append(f"Missing values: {missing[missing > 0].to_dict()}")
        
        # Check for duplicates
        duplicates = df.duplicated(subset=['timestamp']).sum()
        if duplicates > 0:
            issues.append(f"Duplicate timestamps: {duplicates}")
        
        # Check for gaps
        if len(df) > 1:
            time_diffs = df['timestamp'].diff().dropna()
            expected_diff = time_diffs.mode()[0] if not time_diffs.empty else None
            
            if expected_diff:
                gaps = time_diffs[time_diffs > expected_diff * 1.5]
                if len(gaps) > 0:
                    issues.append(f"Time gaps detected: {len(gaps)} gaps")
        
        # Check for invalid prices
        if (df['high'] < df['low']).any():
            issues.append("Invalid OHLC: high < low")
        
        if (df['high'] < df['open']).any() or (df['high'] < df['close']).any():
            issues.append("Invalid OHLC: high < open/close")
        
        if (df['low'] > df['open']).any() or (df['low'] > df['close']).any():
            issues.append("Invalid OHLC: low > open/close")
        
        # Check for zero/negative values
        if (df[['open', 'high', 'low', 'close', 'volume']] <= 0).any().any():
            issues.append("Zero or negative values detected")
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'rows': len(df),
            'date_range': (df['timestamp'].min(), df['timestamp'].max()) if len(df) > 0 else None,
            'symbols': df['timestamp'].nunique() if 'symbol' in df.columns else 1
        }
