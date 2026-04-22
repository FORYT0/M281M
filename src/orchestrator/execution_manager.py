"""
Execution Manager - Manages order execution and position tracking.
Tracks trades, positions, and calculates PnL.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import uuid


class OrderSide(Enum):
    """Order side."""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order status."""
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class Trade:
    """Represents a completed trade."""
    
    trade_id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    size: float
    price: float
    timestamp: datetime
    signal_confidence: float
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'trade_id': self.trade_id,
            'symbol': self.symbol,
            'side': self.side,
            'size': self.size,
            'price': self.price,
            'timestamp': self.timestamp.isoformat(),
            'signal_confidence': self.signal_confidence,
            'pnl': self.pnl,
            'pnl_pct': self.pnl_pct,
            'metadata': self.metadata
        }


@dataclass
class Position:
    """Represents a current position."""
    
    symbol: str
    size: float  # Positive for long, negative for short
    entry_price: float
    current_price: float
    entry_time: datetime
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0
    
    def update_price(self, new_price: float):
        """Update current price and recalculate PnL."""
        self.current_price = new_price
        
        if self.size > 0:  # Long position
            self.unrealized_pnl = (new_price - self.entry_price) * self.size
        else:  # Short position
            self.unrealized_pnl = (self.entry_price - new_price) * abs(self.size)
        
        self.unrealized_pnl_pct = self.unrealized_pnl / (self.entry_price * abs(self.size))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'symbol': self.symbol,
            'size': self.size,
            'entry_price': self.entry_price,
            'current_price': self.current_price,
            'entry_time': self.entry_time.isoformat(),
            'unrealized_pnl': self.unrealized_pnl,
            'unrealized_pnl_pct': self.unrealized_pnl_pct
        }


class ExecutionManager:
    """
    Manages order execution and position tracking.
    
    Note: This is a simulation/paper trading implementation.
    For live trading, integrate with exchange API.
    """
    
    def __init__(
        self,
        initial_balance: float = 10000.0,
        commission_rate: float = 0.001
    ):
        """
        Initialize execution manager.
        
        Args:
            initial_balance: Starting account balance
            commission_rate: Commission rate per trade (0.001 = 0.1%)
        """
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.commission_rate = commission_rate
        
        # Positions: symbol -> Position
        self.positions: Dict[str, Position] = {}
        
        # Trade history
        self.trades: List[Trade] = []
        
        # Performance tracking
        self.total_pnl = 0.0
        self.total_commission = 0.0
        self.winning_trades = 0
        self.losing_trades = 0
    
    def execute_signal(
        self,
        symbol: str,
        direction: str,
        size: float,
        current_price: float,
        signal_confidence: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Trade:
        """
        Execute a trading signal.
        
        Args:
            symbol: Trading symbol
            direction: 'long' or 'short'
            size: Position size
            current_price: Current market price
            signal_confidence: Signal confidence
            metadata: Additional metadata
        
        Returns:
            Trade object
        """
        # Determine order side
        side = OrderSide.BUY.value if direction == 'long' else OrderSide.SELL.value
        
        # Calculate commission
        commission = size * current_price * self.commission_rate
        self.total_commission += commission
        
        # Check if we have an existing position
        existing_position = self.positions.get(symbol)
        
        if existing_position:
            # Close or modify existing position
            trade = self._modify_position(
                symbol, direction, size, current_price,
                signal_confidence, metadata
            )
        else:
            # Open new position
            trade = self._open_position(
                symbol, direction, size, current_price,
                signal_confidence, metadata
            )
        
        # Update balance
        self.current_balance -= commission
        
        return trade
    
    def _open_position(
        self,
        symbol: str,
        direction: str,
        size: float,
        price: float,
        confidence: float,
        metadata: Optional[Dict[str, Any]]
    ) -> Trade:
        """Open a new position."""
        position_size = size if direction == 'long' else -size
        
        self.positions[symbol] = Position(
            symbol=symbol,
            size=position_size,
            entry_price=price,
            current_price=price,
            entry_time=datetime.now()
        )
        
        trade = Trade(
            trade_id=str(uuid.uuid4()),
            symbol=symbol,
            side=OrderSide.BUY.value if direction == 'long' else OrderSide.SELL.value,
            size=size,
            price=price,
            timestamp=datetime.now(),
            signal_confidence=confidence,
            metadata=metadata or {}
        )
        
        self.trades.append(trade)
        return trade
    
    def _modify_position(
        self,
        symbol: str,
        direction: str,
        size: float,
        price: float,
        confidence: float,
        metadata: Optional[Dict[str, Any]]
    ) -> Trade:
        """Modify or close existing position."""
        position = self.positions[symbol]
        
        # Calculate PnL on existing position
        if position.size > 0:  # Closing long
            pnl = (price - position.entry_price) * position.size
        else:  # Closing short
            pnl = (position.entry_price - price) * abs(position.size)
        
        pnl_pct = pnl / (position.entry_price * abs(position.size))
        
        # Update statistics
        self.total_pnl += pnl
        if pnl > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1
        
        # Create trade
        trade = Trade(
            trade_id=str(uuid.uuid4()),
            symbol=symbol,
            side=OrderSide.SELL.value if position.size > 0 else OrderSide.BUY.value,
            size=abs(position.size),
            price=price,
            timestamp=datetime.now(),
            signal_confidence=confidence,
            pnl=pnl,
            pnl_pct=pnl_pct,
            metadata=metadata or {}
        )
        
        self.trades.append(trade)
        
        # Update balance
        self.current_balance += pnl
        
        # Check if reversing or closing
        new_size = size if direction == 'long' else -size
        
        if (position.size > 0 and new_size < 0) or (position.size < 0 and new_size > 0):
            # Reversing position
            if abs(new_size) > abs(position.size):
                # Reverse and open new position
                remaining_size = abs(new_size) - abs(position.size)
                self.positions[symbol] = Position(
                    symbol=symbol,
                    size=new_size / abs(new_size) * remaining_size,
                    entry_price=price,
                    current_price=price,
                    entry_time=datetime.now()
                )
            else:
                # Just close
                del self.positions[symbol]
        else:
            # Same direction - close position
            del self.positions[symbol]
        
        return trade
    
    def update_position_prices(self, prices: Dict[str, float]):
        """
        Update current prices for all positions.
        
        Args:
            prices: Dictionary of symbol -> current_price
        """
        for symbol, position in self.positions.items():
            if symbol in prices:
                position.update_price(prices[symbol])
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get current position for a symbol."""
        return self.positions.get(symbol)
    
    def get_all_positions(self) -> Dict[str, Position]:
        """Get all current positions."""
        return self.positions.copy()
    
    def close_position(self, symbol: str, current_price: float) -> Optional[Trade]:
        """
        Close a position.
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
        
        Returns:
            Trade object if position existed, None otherwise
        """
        if symbol not in self.positions:
            return None
        
        position = self.positions[symbol]
        direction = 'short' if position.size > 0 else 'long'
        
        return self.execute_signal(
            symbol=symbol,
            direction=direction,
            size=abs(position.size),
            current_price=current_price,
            signal_confidence=0.0,
            metadata={'reason': 'manual_close'}
        )
    
    def close_all_positions(self, prices: Dict[str, float]) -> List[Trade]:
        """
        Close all positions.
        
        Args:
            prices: Dictionary of symbol -> current_price
        
        Returns:
            List of trades
        """
        trades = []
        symbols = list(self.positions.keys())
        
        for symbol in symbols:
            if symbol in prices:
                trade = self.close_position(symbol, prices[symbol])
                if trade:
                    trades.append(trade)
        
        return trades
    
    def calculate_total_pnl(self) -> float:
        """Calculate total PnL (realized + unrealized)."""
        unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        return self.total_pnl + unrealized_pnl
    
    def calculate_equity(self) -> float:
        """Calculate current equity (balance + unrealized PnL)."""
        return self.current_balance + sum(
            pos.unrealized_pnl for pos in self.positions.values()
        )
    
    def get_trade_history(
        self,
        symbol: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Trade]:
        """
        Get trade history.
        
        Args:
            symbol: Filter by symbol (optional)
            limit: Maximum number of trades to return
        
        Returns:
            List of trades
        """
        trades = self.trades
        
        if symbol:
            trades = [t for t in trades if t.symbol == symbol]
        
        if limit:
            trades = trades[-limit:]
        
        return trades
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        total_trades = len(self.trades)
        win_rate = self.winning_trades / total_trades if total_trades > 0 else 0.0
        
        # Calculate average win/loss
        winning_pnls = [t.pnl for t in self.trades if t.pnl and t.pnl > 0]
        losing_pnls = [t.pnl for t in self.trades if t.pnl and t.pnl < 0]
        
        avg_win = sum(winning_pnls) / len(winning_pnls) if winning_pnls else 0.0
        avg_loss = sum(losing_pnls) / len(losing_pnls) if losing_pnls else 0.0
        
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0.0
        
        # Calculate returns
        total_return = (self.calculate_equity() - self.initial_balance) / self.initial_balance
        
        return {
            'initial_balance': self.initial_balance,
            'current_balance': self.current_balance,
            'equity': self.calculate_equity(),
            'total_pnl': self.calculate_total_pnl(),
            'realized_pnl': self.total_pnl,
            'unrealized_pnl': sum(pos.unrealized_pnl for pos in self.positions.values()),
            'total_return': total_return,
            'total_trades': total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'total_commission': self.total_commission,
            'open_positions': len(self.positions)
        }
    
    def reset(self):
        """Reset execution manager to initial state."""
        self.current_balance = self.initial_balance
        self.positions.clear()
        self.trades.clear()
        self.total_pnl = 0.0
        self.total_commission = 0.0
        self.winning_trades = 0
        self.losing_trades = 0
