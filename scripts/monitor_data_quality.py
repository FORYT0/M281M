"""
Data Quality Monitor - Validates recorded live data.
Checks for gaps, anomalies, and data integrity.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np


class DataQualityMonitor:
    """Monitor and validate recorded market data quality."""
    
    def __init__(self, data_dir: str = 'data/live'):
        """Initialize monitor."""
        self.data_dir = Path(data_dir)
        self.issues = []
    
    def check_orderbook_data(self, file_path: Path) -> dict:
        """Check order book data quality."""
        print(f"\nChecking: {file_path.name}")
        print("-" * 60)
        
        try:
            df = pd.read_csv(file_path)
            
            stats = {
                'file': file_path.name,
                'rows': len(df),
                'start_time': df['datetime'].iloc[0] if len(df) > 0 else None,
                'end_time': df['datetime'].iloc[-1] if len(df) > 0 else None,
                'duration_hours': 0,
                'gaps': 0,
                'anomalies': 0,
                'issues': []
            }
            
            if len(df) == 0:
                stats['issues'].append("Empty file")
                return stats
            
            # Convert timestamp to datetime (handle both with and without milliseconds)
            df['datetime'] = pd.to_datetime(df['datetime'], format='mixed')
            
            # Calculate duration
            duration = (df['datetime'].iloc[-1] - df['datetime'].iloc[0]).total_seconds() / 3600
            stats['duration_hours'] = round(duration, 2)
            
            # Check for gaps (>1 second between updates)
            df['time_diff'] = df['datetime'].diff().dt.total_seconds()
            gaps = df[df['time_diff'] > 1.0]
            stats['gaps'] = len(gaps)
            
            if len(gaps) > 0:
                stats['issues'].append(f"{len(gaps)} gaps detected (>1s between updates)")
                print(f"  [WARNING] {len(gaps)} gaps detected")
            
            # Check for price anomalies (>5% jump)
            df['price_change'] = df['mid_price'].pct_change().abs()
            anomalies = df[df['price_change'] > 0.05]
            stats['anomalies'] = len(anomalies)
            
            if len(anomalies) > 0:
                stats['issues'].append(f"{len(anomalies)} price anomalies (>5% jump)")
                print(f"  [WARNING] {len(anomalies)} price anomalies")
            
            # Check for negative spreads
            negative_spreads = df[df['spread'] < 0]
            if len(negative_spreads) > 0:
                stats['issues'].append(f"{len(negative_spreads)} negative spreads")
                print(f"  [ERROR] {len(negative_spreads)} negative spreads")
            
            # Check for zero volumes
            zero_volumes = df[(df['bid_volume_5'] == 0) | (df['ask_volume_5'] == 0)]
            if len(zero_volumes) > 0:
                stats['issues'].append(f"{len(zero_volumes)} zero volume records")
                print(f"  [WARNING] {len(zero_volumes)} zero volume records")
            
            # Summary
            print(f"  Rows: {len(df):,}")
            print(f"  Duration: {stats['duration_hours']:.2f} hours")
            print(f"  Start: {stats['start_time']}")
            print(f"  End: {stats['end_time']}")
            print(f"  Avg spread: {df['spread_bps'].mean():.2f} bps")
            print(f"  Avg imbalance: {df['imbalance'].mean():.3f}")
            
            if len(stats['issues']) == 0:
                print(f"  [PASS] No issues detected")
            
            return stats
            
        except Exception as e:
            print(f"  [ERROR] Failed to check file: {e}")
            return {'file': file_path.name, 'error': str(e)}
    
    def check_trade_data(self, file_path: Path) -> dict:
        """Check trade data quality."""
        print(f"\nChecking: {file_path.name}")
        print("-" * 60)
        
        try:
            df = pd.read_csv(file_path)
            
            stats = {
                'file': file_path.name,
                'rows': len(df),
                'start_time': df['datetime'].iloc[0] if len(df) > 0 else None,
                'end_time': df['datetime'].iloc[-1] if len(df) > 0 else None,
                'duration_hours': 0,
                'issues': []
            }
            
            if len(df) == 0:
                stats['issues'].append("Empty file")
                return stats
            
            # Convert timestamp (handle both with and without milliseconds)
            df['datetime'] = pd.to_datetime(df['datetime'], format='mixed')
            
            # Calculate duration
            duration = (df['datetime'].iloc[-1] - df['datetime'].iloc[0]).total_seconds() / 3600
            stats['duration_hours'] = round(duration, 2)
            
            # Check for duplicate trade IDs
            duplicates = df[df.duplicated(subset=['trade_id'], keep=False)]
            if len(duplicates) > 0:
                stats['issues'].append(f"{len(duplicates)} duplicate trade IDs")
                print(f"  [WARNING] {len(duplicates)} duplicate trade IDs")
            
            # Check for zero prices/quantities
            zero_price = df[df['price'] == 0]
            zero_qty = df[df['quantity'] == 0]
            
            if len(zero_price) > 0:
                stats['issues'].append(f"{len(zero_price)} zero price trades")
                print(f"  [ERROR] {len(zero_price)} zero price trades")
            
            if len(zero_qty) > 0:
                stats['issues'].append(f"{len(zero_qty)} zero quantity trades")
                print(f"  [ERROR] {len(zero_qty)} zero quantity trades")
            
            # Calculate trade statistics
            buy_trades = df[df['side'] == 'buy']
            sell_trades = df[df['side'] == 'sell']
            
            print(f"  Rows: {len(df):,}")
            print(f"  Duration: {stats['duration_hours']:.2f} hours")
            print(f"  Buy trades: {len(buy_trades):,} ({len(buy_trades)/len(df)*100:.1f}%)")
            print(f"  Sell trades: {len(sell_trades):,} ({len(sell_trades)/len(df)*100:.1f}%)")
            print(f"  Avg price: ${df['price'].mean():.2f}")
            print(f"  Avg quantity: {df['quantity'].mean():.6f}")
            print(f"  Total volume: {df['quantity'].sum():.2f}")
            
            if len(stats['issues']) == 0:
                print(f"  [PASS] No issues detected")
            
            return stats
            
        except Exception as e:
            print(f"  [ERROR] Failed to check file: {e}")
            return {'file': file_path.name, 'error': str(e)}
    
    def check_ticker_data(self, file_path: Path) -> dict:
        """Check ticker data quality."""
        print(f"\nChecking: {file_path.name}")
        print("-" * 60)
        
        try:
            df = pd.read_csv(file_path)
            
            stats = {
                'file': file_path.name,
                'rows': len(df),
                'start_time': df['datetime'].iloc[0] if len(df) > 0 else None,
                'end_time': df['datetime'].iloc[-1] if len(df) > 0 else None,
                'duration_hours': 0,
                'issues': []
            }
            
            if len(df) == 0:
                stats['issues'].append("Empty file")
                return stats
            
            # Convert timestamp (handle both with and without milliseconds)
            df['datetime'] = pd.to_datetime(df['datetime'], format='mixed')
            
            # Calculate duration
            duration = (df['datetime'].iloc[-1] - df['datetime'].iloc[0]).total_seconds() / 3600
            stats['duration_hours'] = round(duration, 2)
            
            # Check for invalid OHLC relationships
            invalid_ohlc = df[(df['high'] < df['low']) | 
                             (df['high'] < df['open']) | 
                             (df['high'] < df['price']) |
                             (df['low'] > df['open']) |
                             (df['low'] > df['price'])]
            
            if len(invalid_ohlc) > 0:
                stats['issues'].append(f"{len(invalid_ohlc)} invalid OHLC records")
                print(f"  [ERROR] {len(invalid_ohlc)} invalid OHLC records")
            
            print(f"  Rows: {len(df):,}")
            print(f"  Duration: {stats['duration_hours']:.2f} hours")
            print(f"  Price range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
            print(f"  Avg volume: {df['volume'].mean():.2f}")
            print(f"  Total volume: {df['volume'].sum():.2f}")
            
            if len(stats['issues']) == 0:
                print(f"  [PASS] No issues detected")
            
            return stats
            
        except Exception as e:
            print(f"  [ERROR] Failed to check file: {e}")
            return {'file': file_path.name, 'error': str(e)}
    
    def generate_report(self):
        """Generate comprehensive quality report."""
        print("\n" + "="*60)
        print("Data Quality Report")
        print("="*60)
        
        # Find all data files
        orderbook_files = sorted(self.data_dir.glob('*_orderbook_*.csv'))
        trade_files = sorted(self.data_dir.glob('*_trades_*.csv'))
        ticker_files = sorted(self.data_dir.glob('*_ticker_*.csv'))
        
        print(f"\nFiles found:")
        print(f"  Order book: {len(orderbook_files)}")
        print(f"  Trades: {len(trade_files)}")
        print(f"  Ticker: {len(ticker_files)}")
        
        all_stats = []
        
        # Check order book files
        if orderbook_files:
            print("\n" + "="*60)
            print("ORDER BOOK DATA")
            print("="*60)
            for file in orderbook_files:
                stats = self.check_orderbook_data(file)
                all_stats.append(stats)
        
        # Check trade files
        if trade_files:
            print("\n" + "="*60)
            print("TRADE DATA")
            print("="*60)
            for file in trade_files:
                stats = self.check_trade_data(file)
                all_stats.append(stats)
        
        # Check ticker files
        if ticker_files:
            print("\n" + "="*60)
            print("TICKER DATA")
            print("="*60)
            for file in ticker_files:
                stats = self.check_ticker_data(file)
                all_stats.append(stats)
        
        # Summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        
        total_rows = sum(s.get('rows', 0) for s in all_stats)
        total_issues = sum(len(s.get('issues', [])) for s in all_stats)
        files_with_issues = sum(1 for s in all_stats if len(s.get('issues', [])) > 0)
        
        print(f"\nTotal files checked: {len(all_stats)}")
        print(f"Total rows: {total_rows:,}")
        print(f"Files with issues: {files_with_issues}")
        print(f"Total issues: {total_issues}")
        
        if total_issues == 0:
            print("\n[PASS] All data quality checks passed!")
        else:
            print(f"\n[WARNING] {total_issues} issues detected")
            print("\nIssues by file:")
            for stats in all_stats:
                if stats.get('issues'):
                    print(f"\n  {stats['file']}:")
                    for issue in stats['issues']:
                        print(f"    - {issue}")
        
        # Data coverage
        if all_stats:
            total_hours = sum(s.get('duration_hours', 0) for s in all_stats if 'duration_hours' in s)
            avg_hours = total_hours / len([s for s in all_stats if 'duration_hours' in s]) if all_stats else 0
            
            print(f"\nData Coverage:")
            print(f"  Total duration: {total_hours:.2f} hours ({total_hours/24:.2f} days)")
            print(f"  Avg per file: {avg_hours:.2f} hours")
            
            if total_hours >= 168:  # 1 week
                print(f"  [PASS] Sufficient data for training (>1 week)")
            elif total_hours >= 24:
                print(f"  [WARNING] Limited data ({total_hours/24:.1f} days)")
            else:
                print(f"  [ERROR] Insufficient data ({total_hours:.1f} hours)")
        
        print("\n" + "="*60)


def main():
    """Main entry point."""
    print("="*60)
    print("Data Quality Monitor")
    print("="*60)
    
    monitor = DataQualityMonitor(data_dir='data/live')
    monitor.generate_report()


if __name__ == '__main__':
    main()
