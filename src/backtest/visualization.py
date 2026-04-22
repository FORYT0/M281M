"""
Backtest Visualization - Generate charts and reports.
Creates visual analysis of backtest results.
"""

import pandas as pd
import numpy as np
from typing import List, Optional
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

from .backtest_engine import BacktestResult


class BacktestVisualizer:
    """
    Creates visualizations for backtest results.
    
    Generates:
    - Equity curve
    - Drawdown chart
    - Monthly returns heatmap
    - Trade distribution
    - Performance summary
    """
    
    def __init__(self, style: str = 'seaborn-v0_8-darkgrid'):
        """
        Initialize visualizer.
        
        Args:
            style: Matplotlib style
        """
        try:
            plt.style.use(style)
        except:
            plt.style.use('default')
        
        sns.set_palette("husl")
    
    def plot_equity_curve(
        self,
        result: BacktestResult,
        show_drawdown: bool = True,
        figsize: tuple = (12, 6)
    ) -> plt.Figure:
        """
        Plot equity curve with optional drawdown overlay.
        
        Args:
            result: Backtest result
            show_drawdown: Show drawdown on secondary axis
            figsize: Figure size
        
        Returns:
            Matplotlib figure
        """
        fig, ax1 = plt.subplots(figsize=figsize)
        
        # Plot equity curve
        equity = result.equity_curve
        ax1.plot(equity.index, equity.values, label='Equity', linewidth=2, color='#2E86AB')
        ax1.axhline(y=result.config.initial_balance, color='gray', linestyle='--', alpha=0.5, label='Initial Balance')
        
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Equity ($)', color='#2E86AB')
        ax1.tick_params(axis='y', labelcolor='#2E86AB')
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='upper left')
        
        # Plot drawdown on secondary axis
        if show_drawdown:
            ax2 = ax1.twinx()
            
            # Calculate drawdown
            running_max = equity.expanding().max()
            drawdown = (equity - running_max) / running_max * 100
            
            ax2.fill_between(drawdown.index, 0, drawdown.values, alpha=0.3, color='#A23B72', label='Drawdown')
            ax2.set_ylabel('Drawdown (%)', color='#A23B72')
            ax2.tick_params(axis='y', labelcolor='#A23B72')
            ax2.legend(loc='upper right')
        
        plt.title(f'Equity Curve - {result.config.symbol}\n{result.metrics.start_date.date()} to {result.metrics.end_date.date()}')
        plt.tight_layout()
        
        return fig
    
    def plot_drawdown(
        self,
        result: BacktestResult,
        figsize: tuple = (12, 4)
    ) -> plt.Figure:
        """
        Plot underwater equity curve (drawdown).
        
        Args:
            result: Backtest result
            figsize: Figure size
        
        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        # Calculate drawdown
        equity = result.equity_curve
        running_max = equity.expanding().max()
        drawdown = (equity - running_max) / running_max * 100
        
        # Plot
        ax.fill_between(drawdown.index, 0, drawdown.values, alpha=0.5, color='#A23B72')
        ax.plot(drawdown.index, drawdown.values, linewidth=1, color='#A23B72')
        
        ax.set_xlabel('Date')
        ax.set_ylabel('Drawdown (%)')
        ax.set_title(f'Drawdown - {result.config.symbol}')
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        
        # Highlight max drawdown
        max_dd_idx = drawdown.idxmin()
        max_dd_val = drawdown.min()
        ax.plot(max_dd_idx, max_dd_val, 'ro', markersize=8, label=f'Max DD: {max_dd_val:.2f}%')
        ax.legend()
        
        plt.tight_layout()
        
        return fig
    
    def plot_monthly_returns(
        self,
        result: BacktestResult,
        figsize: tuple = (12, 6)
    ) -> plt.Figure:
        """
        Plot monthly returns heatmap.
        
        Args:
            result: Backtest result
            figsize: Figure size
        
        Returns:
            Matplotlib figure
        """
        # Calculate monthly returns
        equity = result.equity_curve
        monthly = equity.resample('M').last()
        monthly_returns = monthly.pct_change().dropna() * 100
        
        # Create pivot table
        df = pd.DataFrame({
            'year': monthly_returns.index.year,
            'month': monthly_returns.index.month,
            'return': monthly_returns.values
        })
        
        pivot = df.pivot(index='year', columns='month', values='return')
        
        # Plot heatmap
        fig, ax = plt.subplots(figsize=figsize)
        
        sns.heatmap(
            pivot,
            annot=True,
            fmt='.1f',
            cmap='RdYlGn',
            center=0,
            cbar_kws={'label': 'Return (%)'},
            ax=ax
        )
        
        ax.set_title(f'Monthly Returns (%) - {result.config.symbol}')
        ax.set_xlabel('Month')
        ax.set_ylabel('Year')
        
        # Month labels
        month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        ax.set_xticklabels(month_labels)
        
        plt.tight_layout()
        
        return fig
    
    def plot_trade_distribution(
        self,
        result: BacktestResult,
        figsize: tuple = (12, 5)
    ) -> plt.Figure:
        """
        Plot trade PnL distribution.
        
        Args:
            result: Backtest result
            figsize: Figure size
        
        Returns:
            Matplotlib figure
        """
        if not result.trades:
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(0.5, 0.5, 'No trades to display', ha='center', va='center')
            return fig
        
        # Extract PnLs
        pnls = [t['pnl'] for t in result.trades if 'pnl' in t]
        
        if not pnls:
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(0.5, 0.5, 'No PnL data available', ha='center', va='center')
            return fig
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
        
        # Histogram
        ax1.hist(pnls, bins=30, alpha=0.7, color='#2E86AB', edgecolor='black')
        ax1.axvline(x=0, color='red', linestyle='--', linewidth=2)
        ax1.axvline(x=np.mean(pnls), color='green', linestyle='--', linewidth=2, label=f'Mean: ${np.mean(pnls):.2f}')
        ax1.set_xlabel('PnL ($)')
        ax1.set_ylabel('Frequency')
        ax1.set_title('Trade PnL Distribution')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Cumulative PnL
        cumulative_pnl = np.cumsum(pnls)
        ax2.plot(range(len(cumulative_pnl)), cumulative_pnl, linewidth=2, color='#2E86AB')
        ax2.axhline(y=0, color='red', linestyle='--', linewidth=1)
        ax2.set_xlabel('Trade Number')
        ax2.set_ylabel('Cumulative PnL ($)')
        ax2.set_title('Cumulative PnL')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        return fig
    
    def create_summary_report(
        self,
        result: BacktestResult,
        output_path: Optional[str] = None
    ) -> str:
        """
        Create comprehensive HTML report.
        
        Args:
            result: Backtest result
            output_path: Path to save HTML file (optional)
        
        Returns:
            HTML string
        """
        m = result.metrics
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Backtest Report - {result.config.symbol}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2E86AB; border-bottom: 3px solid #2E86AB; padding-bottom: 10px; }}
        h2 {{ color: #333; margin-top: 30px; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 20px 0; }}
        .metric-box {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; border-left: 4px solid #2E86AB; }}
        .metric-label {{ font-size: 12px; color: #666; text-transform: uppercase; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #333; margin-top: 5px; }}
        .positive {{ color: #28a745; }}
        .negative {{ color: #dc3545; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #2E86AB; color: white; }}
        tr:hover {{ background-color: #f5f5f5; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Backtest Report</h1>
        <p><strong>Symbol:</strong> {result.config.symbol}</p>
        <p><strong>Period:</strong> {m.start_date.date()} to {m.end_date.date()} ({m.total_days} days)</p>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h2>Performance Summary</h2>
        <div class="metric-grid">
            <div class="metric-box">
                <div class="metric-label">Total Return</div>
                <div class="metric-value {'positive' if m.total_return > 0 else 'negative'}">{m.total_return:+.2%}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">Sharpe Ratio</div>
                <div class="metric-value">{m.sharpe_ratio:.2f}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">Max Drawdown</div>
                <div class="metric-value negative">{m.max_drawdown:.2%}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">Win Rate</div>
                <div class="metric-value">{m.win_rate:.2%}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">Profit Factor</div>
                <div class="metric-value">{m.profit_factor:.2f}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">Total Trades</div>
                <div class="metric-value">{m.total_trades}</div>
            </div>
        </div>
        
        <h2>Detailed Metrics</h2>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Initial Balance</td><td>${m.initial_balance:,.2f}</td></tr>
            <tr><td>Final Balance</td><td>${m.final_balance:,.2f}</td></tr>
            <tr><td>Annualized Return</td><td>{m.annualized_return:+.2%}</td></tr>
            <tr><td>Sortino Ratio</td><td>{m.sortino_ratio:.2f}</td></tr>
            <tr><td>Calmar Ratio</td><td>{m.calmar_ratio:.2f}</td></tr>
            <tr><td>Recovery Factor</td><td>{m.recovery_factor:.2f}</td></tr>
            <tr><td>Winning Trades</td><td>{m.winning_trades}</td></tr>
            <tr><td>Losing Trades</td><td>{m.losing_trades}</td></tr>
            <tr><td>Average Win</td><td>${m.avg_win:+,.2f}</td></tr>
            <tr><td>Average Loss</td><td>${m.avg_loss:+,.2f}</td></tr>
            <tr><td>Largest Win</td><td>${m.largest_win:+,.2f}</td></tr>
            <tr><td>Largest Loss</td><td>${m.largest_loss:+,.2f}</td></tr>
        </table>
        
        <h2>Configuration</h2>
        <table>
            <tr><th>Parameter</th><th>Value</th></tr>
            <tr><td>Slippage Model</td><td>{result.config.slippage_model.value}</td></tr>
            <tr><td>Base Slippage</td><td>{result.config.base_slippage_bps} bps</td></tr>
            <tr><td>Commission Rate</td><td>{result.config.commission_rate:.3%}</td></tr>
            <tr><td>Latency</td><td>{result.config.latency_mean_ms} ms</td></tr>
        </table>
    </div>
</body>
</html>
"""
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(html)
            print(f"✓ Report saved to {output_path}")
        
        return html
    
    def save_all_charts(
        self,
        result: BacktestResult,
        output_dir: str = "backtest_results"
    ):
        """
        Save all charts to files.
        
        Args:
            result: Backtest result
            output_dir: Output directory
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Equity curve
        fig = self.plot_equity_curve(result)
        fig.savefig(f"{output_dir}/equity_curve.png", dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        # Drawdown
        fig = self.plot_drawdown(result)
        fig.savefig(f"{output_dir}/drawdown.png", dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        # Monthly returns
        try:
            fig = self.plot_monthly_returns(result)
            fig.savefig(f"{output_dir}/monthly_returns.png", dpi=150, bbox_inches='tight')
            plt.close(fig)
        except:
            pass  # Skip if not enough data
        
        # Trade distribution
        fig = self.plot_trade_distribution(result)
        fig.savefig(f"{output_dir}/trade_distribution.png", dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        # HTML report
        self.create_summary_report(result, f"{output_dir}/report.html")
        
        print(f"✓ All charts saved to {output_dir}/")
