"""
Paper Trading Engine - Stage 3 of Phase 6.
Simulates live trading on Binance testnet.
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field
import ccxt
from loguru import logger


@dataclass
class PaperPosition:
    """Paper trading position."""
    symbol: str
    side: str  # 'long' or 'short'
    size: float
    entry_price: float
    entry_time: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    unrealized_pnl: float = 0.0
    
    def update_pnl(self, current_price: float):
        """Update unrealized PnL."""
        if self.side == 'long':
            self.unrealized_pnl = (current_price - self.entry_price) * self.size
        else:
            self.unrealized_pnl = (self.entry_price - current_price) * self.size


@dataclass
class PaperTrade:
    """Paper trading trade record."""
    trade_id: int
    symbol: str
    side: str
    size: float
    price: float
    timestamp: float
    pnl: float = 0.0
    commission: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class PaperTradingEngine:
    """
    Paper trading engine for Binance testnet.
    
    Simulates real trading without risking capital.
    """
    
    def __init__(
        self,
        initial_balance: float = 10000.0,
        commission_rate: float = 0.001,  # 0.1%
        use_testnet: bool = True
    ):
        """
        Initialize paper trading engine.
        
        Args:
            initial_balance: Starting balance in USDT
            commission_rate: Trading commission (0.001 = 0.1%)
            use_testnet: Use Binance testnet if True
        """
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.commission_rate = commission_rate
        self.use_testnet = use_testnet
        
        # Positions and trades
        self.positions: Dict[str, PaperPosition] = {}
        self.trades: List[PaperTrade] = []
        self.trade_counter = 0
        
        # Statistics
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0.0
        self.total_commission = 0.0
        self.peak_balance = initial_balance
        self.max_drawdown = 0.0
        
        # Exchange connection
        self.exchange = None
        self._initialize_exchange()
        
        logger.info(f"Paper Trading Engine initialized")
        logger.info(f"Initial balance: ${initial_balance:,.2f}")
        logger.info(f"Commission rate: {commission_rate:.2%}")
    
    def _initialize_exchange(self):
        """Initialize exchange connection."""
        try:
            if self.use_testnet:
                self.exchange = ccxt.binance({
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': 'future',
                        'test': True
                    }
                })
                logger.info("Connected to Binance testnet")
            else:
                self.exchange = ccxt.binance({
                    'enableRateLimit': True
                })
                logger.info("Connected to Binance mainnet (read-only)")
                
        except Exception as e:
            logger.error(f"Failed to initialize exchange: {e}")
            self.exchange = None
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current market price."""
        try:
            if not self.exchange:
                return None
            
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker['last']
            
        except Exception as e:
            logger.error(f"Failed to fetch price for {symbol}: {e}")
            return None
    
    def open_position(
        self,
        symbol: str,
        side: str,
        size: float,
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[PaperTrade]:
        """
        Open a new position.
        
        Args:
            symbol: Trading symbol (e.g., 'BTC/USDT')
            side: 'long' or 'short'
            size: Position size
            price: Entry price (None = market price)
            stop_loss: Stop loss price
            take_profit: Take profit price
            metadata: Additional metadata
        
        Returns:
            PaperTrade if successful, None otherwise
        """
        # Get current price if not provided
        if price is None:
            price = self.get_current_price(symbol)
            if price is None:
                logger.error(f"Cannot open position: no price for {symbol}")
                return None
        
        # Check if position already exists
        if symbol in self.positions:
            logger.warning(f"Position already exists for {symbol}")
            return None
        
        # Calculate position value
        position_value = size * price
        
        # Check if we have enough balance
        if position_value > self.balance:
            logger.warning(f"Insufficient balance: need ${position_value:.2f}, have ${self.balance:.2f}")
            return None
        
        # Calculate commission
        commission = position_value * self.commission_rate
        
        # Create position
        position = PaperPosition(
            symbol=symbol,
            side=side,
            size=size,
            entry_price=price,
            entry_time=time.time(),
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        self.positions[symbol] = position
        
        # Deduct from balance (margin)
        self.balance -= commission
        self.total_commission += commission
        
        # Create trade record
        self.trade_counter += 1
        trade = PaperTrade(
            trade_id=self.trade_counter,
            symbol=symbol,
            side=side,
            size=size,
            price=price,
            timestamp=time.time(),
            commission=commission,
            metadata=metadata or {}
        )
        
        self.trades.append(trade)
        self.total_trades += 1
        
        logger.info(
            f"Opened {side.upper()} position: {size:.6f} {symbol} @ ${price:.2f} "
            f"(commission: ${commission:.2f})"
        )
        
        return trade
    
    def close_position(
        self,
        symbol: str,
        price: Optional[float] = None
    ) -> Optional[PaperTrade]:
        """
        Close an existing position.
        
        Args:
            symbol: Trading symbol
            price: Exit price (None = market price)
        
        Returns:
            PaperTrade if successful, None otherwise
        """
        # Check if position exists
        if symbol not in self.positions:
            logger.warning(f"No position to close for {symbol}")
            return None
        
        position = self.positions[symbol]
        
        # Get current price if not provided
        if price is None:
            price = self.get_current_price(symbol)
            if price is None:
                logger.error(f"Cannot close position: no price for {symbol}")
                return None
        
        # Calculate PnL
        if position.side == 'long':
            pnl = (price - position.entry_price) * position.size
        else:
            pnl = (position.entry_price - price) * position.size
        
        # Calculate commission
        position_value = position.size * price
        commission = position_value * self.commission_rate
        
        # Net PnL after commission
        net_pnl = pnl - commission
        
        # Update balance
        self.balance += net_pnl
        self.total_pnl += net_pnl
        self.total_commission += commission
        
        # Update statistics
        if net_pnl > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1
        
        # Update peak and drawdown
        if self.balance > self.peak_balance:
            self.peak_balance = self.balance
        
        drawdown = (self.peak_balance - self.balance) / self.peak_balance
        if drawdown > self.max_drawdown:
            self.max_drawdown = drawdown
        
        # Create trade record
        self.trade_counter += 1
        trade = PaperTrade(
            trade_id=self.trade_counter,
            symbol=symbol,
            side='close_' + position.side,
            size=position.size,
            price=price,
            timestamp=time.time(),
            pnl=net_pnl,
            commission=commission,
            metadata={
                'entry_price': position.entry_price,
                'entry_time': position.entry_time,
                'hold_time': time.time() - position.entry_time
            }
        )
        
        self.trades.append(trade)
        
        # Remove position
        del self.positions[symbol]
        
        logger.info(
            f"Closed {position.side.upper()} position: {position.size:.6f} {symbol} @ ${price:.2f} "
            f"(PnL: ${net_pnl:+.2f}, commission: ${commission:.2f})"
        )
        
        return trade
    
    def update_positions(self, prices: Dict[str, float]):
        """
        Update all positions with current prices.
        
        Args:
            prices: Dictionary of symbol -> current_price
        """
        for symbol, position in self.positions.items():
            if symbol in prices:
                position.update_pnl(prices[symbol])
                
                # Check stop loss
                if position.stop_loss:
                    if (position.side == 'long' and prices[symbol] <= position.stop_loss) or \
                       (position.side == 'short' and prices[symbol] >= position.stop_loss):
                        logger.warning(f"Stop loss hit for {symbol}")
                        self.close_position(symbol, prices[symbol])
                        continue
                
                # Check take profit
                if position.take_profit:
                    if (position.side == 'long' and prices[symbol] >= position.take_profit) or \
                       (position.side == 'short' and prices[symbol] <= position.take_profit):
                        logger.info(f"Take profit hit for {symbol}")
                        self.close_position(symbol, prices[symbol])
    
    def get_equity(self) -> float:
        """Calculate total equity (balance + unrealized PnL)."""
        unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        return self.balance + unrealized_pnl
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get trading statistics."""
        equity = self.get_equity()
        total_return = (equity - self.initial_balance) / self.initial_balance
        
        win_rate = self.winning_trades / self.total_trades if self.total_trades > 0 else 0
        
        return {
            'initial_balance': self.initial_balance,
            'current_balance': self.balance,
            'equity': equity,
            'total_pnl': self.total_pnl,
            'total_return': total_return,
            'total_return_pct': total_return * 100,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate,
            'total_commission': self.total_commission,
            'open_positions': len(self.positions),
            'peak_balance': self.peak_balance,
            'max_drawdown': self.max_drawdown,
            'max_drawdown_pct': self.max_drawdown * 100
        }
    
    def print_status(self):
        """Print current status."""
        stats = self.get_statistics()
        
        print("\n" + "="*60)
        print("Paper Trading Status")
        print("="*60)
        print(f"Balance: ${stats['current_balance']:,.2f}")
        print(f"Equity: ${stats['equity']:,.2f}")
        print(f"Total PnL: ${stats['total_pnl']:+,.2f} ({stats['total_return_pct']:+.2f}%)")
        print(f"Open Positions: {stats['open_positions']}")
        print(f"\nTrades: {stats['total_trades']}")
        print(f"  Winning: {stats['winning_trades']} ({stats['win_rate']:.1%})")
        print(f"  Losing: {stats['losing_trades']}")
        print(f"\nCommissions: ${stats['total_commission']:,.2f}")
        print(f"Max Drawdown: {stats['max_drawdown_pct']:.2f}%")
        print("="*60 + "\n")
    
    def get_position(self, symbol: str) -> Optional[PaperPosition]:
        """Get position for symbol."""
        return self.positions.get(symbol)
    
    def get_all_positions(self) -> Dict[str, PaperPosition]:
        """Get all positions."""
        return self.positions.copy()
    
    def get_trade_history(self, limit: Optional[int] = None) -> List[PaperTrade]:
        """Get trade history."""
        if limit:
            return self.trades[-limit:]
        return self.trades.copy()
    
    def reset(self):
        """Reset to initial state."""
        self.balance = self.initial_balance
        self.positions.clear()
        self.trades.clear()
        self.trade_counter = 0
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0.0
        self.total_commission = 0.0
        self.peak_balance = self.initial_balance
        self.max_drawdown = 0.0
        
        logger.info("Paper trading engine reset")
