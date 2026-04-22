"""
Performance Analyzer - Calculates comprehensive performance metrics.
Provides detailed analysis of backtest results.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics."""
    
    # Returns
    total_return: float
    annualized_return: float
    daily_return_mean: float
    daily_return_std: float
    
    # Risk metrics
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float
    max_drawdown_duration: int
    avg_drawdown: float
    
    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    avg_trade_duration: float
    
    # Time-based
    total_days: int
    trading_days: int
    trades_per_day: float
    
    # Additional metrics
    recovery_factor: float
    ulcer_index: float
    
    # Metadata
    start_date: datetime
    end_date: datetime
    initial_balance: float
    final_balance: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'returns': {
                'total_return': self.total_return,
                'annualized_return': self.annualized_return,
                'daily_return_mean': self.daily_return_mean,
                'daily_return_std': self.daily_return_std
            },
            'risk': {
                'sharpe_ratio': self.sharpe_ratio,
                'sortino_ratio': self.sortino_ratio,
                'calmar_ratio': self.calmar_ratio,
                'max_drawdown': self.max_drawdown,
                'max_drawdown_duration': self.max_drawdown_duration,
                'avg_drawdown': self.avg_drawdown,
                'recovery_factor': self.recovery_factor,
                'ulcer_index': self.ulcer_index
            },
            'trades': {
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades,
                'win_rate': self.win_rate,
                'profit_factor': self.profit_factor,
                'avg_win': self.avg_win,
                'avg_loss': self.avg_loss,
                'largest_win': self.largest_win,
                'largest_loss': self.largest_loss,
                'avg_trade_duration': self.avg_trade_duration,
                'trades_per_day': self.trades_per_day
            },
            'summary': {
                'start_date': self.start_date.isoformat(),
                'end_date': self.end_date.isoformat(),
                'total_days': self.total_days,
                'trading_days': self.trading_days,
                'initial_balance': self.initial_balance,
                'final_balance': self.final_balance
            }
        }


class PerformanceAnalyzer:
    """
    Analyzes backtest performance and calculates metrics.
    
    Calculates:
    - Return metrics (total, annualized, daily)
    - Risk metrics (Sharpe, Sortino, drawdown)
    - Trade statistics (win rate, profit factor)
    - Time-based analysis
    """
    
    def __init__(
        self,
        risk_free_rate: float = 0.02,
        periods_per_year: int = 365
    ):
        """
        Initialize performance analyzer.
        
        Args:
            risk_free_rate: Annual risk-free rate (default 2%)
            periods_per_year: Trading periods per year
        """
        self.risk_free_rate = risk_free_rate
        self.periods_per_year = periods_per_year
    
    def analyze(
        self,
        equity_curve: pd.Series,
        trades: List[Dict[str, Any]],
        initial_balance: float
    ) -> PerformanceMetrics:
        """
        Perform comprehensive performance analysis.
        
        Args:
            equity_curve: Time series of account equity
            trades: List of trade dictionaries
            initial_balance: Starting account balance
        
        Returns:
            PerformanceMetrics with all calculated metrics
        """
        # Calculate returns
        returns_metrics = self._calculate_returns(equity_curve, initial_balance)
        
        # Calculate risk metrics
        risk_metrics = self._calculate_risk_metrics(equity_curve, returns_metrics['daily_returns'])
        
        # Calculate trade statistics
        trade_metrics = self._calculate_trade_stats(trades)
        
        # Time-based metrics
        start_date = equity_curve.index[0]
        end_date = equity_curve.index[-1]
        total_days = (end_date - start_date).days
        trading_days = len(equity_curve)
        
        # Create metrics object
        metrics = PerformanceMetrics(
            # Returns
            total_return=returns_metrics['total_return'],
            annualized_return=returns_metrics['annualized_return'],
            daily_return_mean=returns_metrics['daily_return_mean'],
            daily_return_std=returns_metrics['daily_return_std'],
            
            # Risk
            sharpe_ratio=risk_metrics['sharpe_ratio'],
            sortino_ratio=risk_metrics['sortino_ratio'],
            calmar_ratio=risk_metrics['calmar_ratio'],
            max_drawdown=risk_metrics['max_drawdown'],
            max_drawdown_duration=risk_metrics['max_drawdown_duration'],
            avg_drawdown=risk_metrics['avg_drawdown'],
            recovery_factor=risk_metrics['recovery_factor'],
            ulcer_index=risk_metrics['ulcer_index'],
            
            # Trades
            total_trades=trade_metrics['total_trades'],
            winning_trades=trade_metrics['winning_trades'],
            losing_trades=trade_metrics['losing_trades'],
            win_rate=trade_metrics['win_rate'],
            profit_factor=trade_metrics['profit_factor'],
            avg_win=trade_metrics['avg_win'],
            avg_loss=trade_metrics['avg_loss'],
            largest_win=trade_metrics['largest_win'],
            largest_loss=trade_metrics['largest_loss'],
            avg_trade_duration=trade_metrics['avg_trade_duration'],
            
            # Time-based
            total_days=total_days,
            trading_days=trading_days,
            trades_per_day=trade_metrics['total_trades'] / trading_days if trading_days > 0 else 0,
            
            # Metadata
            start_date=start_date,
            end_date=end_date,
            initial_balance=initial_balance,
            final_balance=equity_curve.iloc[-1]
        )
        
        return metrics
    
    def _calculate_returns(
        self,
        equity_curve: pd.Series,
        initial_balance: float
    ) -> Dict[str, float]:
        """Calculate return metrics."""
        final_balance = equity_curve.iloc[-1]
        total_return = (final_balance - initial_balance) / initial_balance
        
        # Daily returns
        daily_returns = equity_curve.pct_change().dropna()
        daily_return_mean = daily_returns.mean()
        daily_return_std = daily_returns.std()
        
        # Annualized return
        n_periods = len(equity_curve)
        if n_periods > 0:
            annualized_return = (1 + total_return) ** (self.periods_per_year / n_periods) - 1
        else:
            annualized_return = 0.0
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'daily_return_mean': daily_return_mean,
            'daily_return_std': daily_return_std,
            'daily_returns': daily_returns
        }
    
    def _calculate_risk_metrics(
        self,
        equity_curve: pd.Series,
        daily_returns: pd.Series
    ) -> Dict[str, float]:
        """Calculate risk-adjusted metrics."""
        # Sharpe Ratio
        excess_returns = daily_returns - (self.risk_free_rate / self.periods_per_year)
        sharpe_ratio = np.sqrt(self.periods_per_year) * excess_returns.mean() / daily_returns.std() if daily_returns.std() > 0 else 0
        
        # Sortino Ratio (only downside deviation)
        downside_returns = daily_returns[daily_returns < 0]
        downside_std = downside_returns.std() if len(downside_returns) > 0 else daily_returns.std()
        sortino_ratio = np.sqrt(self.periods_per_year) * excess_returns.mean() / downside_std if downside_std > 0 else 0
        
        # Drawdown metrics
        drawdown_metrics = self._calculate_drawdown(equity_curve)
        
        # Calmar Ratio
        annualized_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) ** (self.periods_per_year / len(equity_curve)) - 1
        calmar_ratio = annualized_return / abs(drawdown_metrics['max_drawdown']) if drawdown_metrics['max_drawdown'] != 0 else 0
        
        # Recovery Factor
        total_return = (equity_curve.iloc[-1] - equity_curve.iloc[0]) / equity_curve.iloc[0]
        recovery_factor = total_return / abs(drawdown_metrics['max_drawdown']) if drawdown_metrics['max_drawdown'] != 0 else 0
        
        # Ulcer Index (measure of downside volatility)
        ulcer_index = self._calculate_ulcer_index(equity_curve)
        
        return {
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'max_drawdown': drawdown_metrics['max_drawdown'],
            'max_drawdown_duration': drawdown_metrics['max_drawdown_duration'],
            'avg_drawdown': drawdown_metrics['avg_drawdown'],
            'recovery_factor': recovery_factor,
            'ulcer_index': ulcer_index
        }
    
    def _calculate_drawdown(self, equity_curve: pd.Series) -> Dict[str, Any]:
        """Calculate drawdown metrics."""
        # Calculate running maximum
        running_max = equity_curve.expanding().max()
        
        # Calculate drawdown
        drawdown = (equity_curve - running_max) / running_max
        
        # Max drawdown
        max_drawdown = drawdown.min()
        
        # Average drawdown
        avg_drawdown = drawdown[drawdown < 0].mean() if (drawdown < 0).any() else 0
        
        # Max drawdown duration
        is_drawdown = drawdown < 0
        drawdown_periods = is_drawdown.astype(int).groupby((is_drawdown != is_drawdown.shift()).cumsum()).sum()
        max_drawdown_duration = drawdown_periods.max() if len(drawdown_periods) > 0 else 0
        
        return {
            'max_drawdown': max_drawdown,
            'avg_drawdown': avg_drawdown,
            'max_drawdown_duration': int(max_drawdown_duration),
            'drawdown_series': drawdown
        }
    
    def _calculate_ulcer_index(self, equity_curve: pd.Series) -> float:
        """Calculate Ulcer Index (downside volatility measure)."""
        running_max = equity_curve.expanding().max()
        drawdown_pct = ((equity_curve - running_max) / running_max) * 100
        ulcer_index = np.sqrt((drawdown_pct ** 2).mean())
        return ulcer_index
    
    def _calculate_trade_stats(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate trade statistics."""
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'largest_win': 0.0,
                'largest_loss': 0.0,
                'avg_trade_duration': 0.0
            }
        
        # Extract PnLs
        pnls = [t.get('pnl', 0) for t in trades if t.get('pnl') is not None]
        
        if not pnls:
            return {
                'total_trades': len(trades),
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'largest_win': 0.0,
                'largest_loss': 0.0,
                'avg_trade_duration': 0.0
            }
        
        # Winning and losing trades
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        
        winning_trades = len(wins)
        losing_trades = len(losses)
        total_trades = len(pnls)
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # Average win/loss
        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0
        
        # Largest win/loss
        largest_win = max(wins) if wins else 0
        largest_loss = min(losses) if losses else 0
        
        # Profit factor
        total_wins = sum(wins) if wins else 0
        total_losses = abs(sum(losses)) if losses else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else 0
        
        # Average trade duration (if timestamps available)
        durations = []
        for trade in trades:
            if 'entry_time' in trade and 'exit_time' in trade:
                duration = (trade['exit_time'] - trade['entry_time']).total_seconds() / 3600  # hours
                durations.append(duration)
        
        avg_trade_duration = np.mean(durations) if durations else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'avg_trade_duration': avg_trade_duration
        }
    
    def calculate_monthly_returns(self, equity_curve: pd.Series) -> pd.DataFrame:
        """
        Calculate monthly returns.
        
        Args:
            equity_curve: Time series of account equity
        
        Returns:
            DataFrame with monthly returns
        """
        # Resample to monthly
        monthly_equity = equity_curve.resample('M').last()
        monthly_returns = monthly_equity.pct_change().dropna()
        
        # Create DataFrame with year and month
        df = pd.DataFrame({
            'year': monthly_returns.index.year,
            'month': monthly_returns.index.month,
            'return': monthly_returns.values
        })
        
        # Pivot to heatmap format
        heatmap = df.pivot(index='year', columns='month', values='return')
        
        return heatmap
    
    def calculate_rolling_metrics(
        self,
        equity_curve: pd.Series,
        window: int = 30
    ) -> pd.DataFrame:
        """
        Calculate rolling performance metrics.
        
        Args:
            equity_curve: Time series of account equity
            window: Rolling window size
        
        Returns:
            DataFrame with rolling metrics
        """
        returns = equity_curve.pct_change().dropna()
        
        rolling_metrics = pd.DataFrame({
            'return_mean': returns.rolling(window).mean(),
            'return_std': returns.rolling(window).std(),
            'sharpe': returns.rolling(window).mean() / returns.rolling(window).std() * np.sqrt(self.periods_per_year)
        })
        
        return rolling_metrics
