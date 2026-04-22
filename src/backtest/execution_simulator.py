"""
Execution Simulator - Simulates realistic order execution.
Models slippage, latency, and market impact for backtesting.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum


class SlippageModel(Enum):
    """Slippage modeling approaches."""
    FIXED = "fixed"
    PERCENTAGE = "percentage"
    VOLUME_BASED = "volume_based"
    SPREAD_BASED = "spread_based"


class OrderType(Enum):
    """Order types."""
    MARKET = "market"
    LIMIT = "limit"


@dataclass
class Fill:
    """Represents an order fill."""
    
    order_id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    requested_size: float
    filled_size: float
    requested_price: float
    filled_price: float
    slippage: float
    slippage_bps: float
    commission: float
    timestamp: datetime
    latency_ms: float
    is_partial: bool
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'order_id': self.order_id,
            'symbol': self.symbol,
            'side': self.side,
            'requested_size': self.requested_size,
            'filled_size': self.filled_size,
            'requested_price': self.requested_price,
            'filled_price': self.filled_price,
            'slippage': self.slippage,
            'slippage_bps': self.slippage_bps,
            'commission': self.commission,
            'timestamp': self.timestamp.isoformat(),
            'latency_ms': self.latency_ms,
            'is_partial': self.is_partial,
            'metadata': self.metadata
        }


class ExecutionSimulator:
    """
    Simulates realistic order execution for backtesting.
    
    Features:
    - Multiple slippage models
    - Latency simulation
    - Market impact modeling
    - Partial fills
    - Commission calculation
    """
    
    def __init__(
        self,
        slippage_model: SlippageModel = SlippageModel.VOLUME_BASED,
        base_slippage_bps: float = 2.0,
        impact_factor: float = 0.1,
        commission_rate: float = 0.001,
        latency_mean_ms: float = 50.0,
        latency_std_ms: float = 10.0,
        enable_partial_fills: bool = False,
        min_fill_pct: float = 0.5
    ):
        """
        Initialize execution simulator.
        
        Args:
            slippage_model: Slippage calculation method
            base_slippage_bps: Base slippage in basis points
            impact_factor: Market impact factor
            commission_rate: Commission rate (0.001 = 0.1%)
            latency_mean_ms: Mean latency in milliseconds
            latency_std_ms: Latency standard deviation
            enable_partial_fills: Allow partial order fills
            min_fill_pct: Minimum fill percentage
        """
        self.slippage_model = slippage_model
        self.base_slippage_bps = base_slippage_bps
        self.impact_factor = impact_factor
        self.commission_rate = commission_rate
        self.latency_mean_ms = latency_mean_ms
        self.latency_std_ms = latency_std_ms
        self.enable_partial_fills = enable_partial_fills
        self.min_fill_pct = min_fill_pct
        
        # Statistics
        self.total_fills = 0
        self.total_slippage = 0.0
        self.total_commission = 0.0
    
    def simulate_execution(
        self,
        order_id: str,
        symbol: str,
        side: str,
        size: float,
        price: float,
        order_type: OrderType = OrderType.MARKET,
        market_state: Optional[Dict[str, Any]] = None
    ) -> Fill:
        """
        Simulate order execution.
        
        Args:
            order_id: Unique order identifier
            symbol: Trading symbol
            side: 'buy' or 'sell'
            size: Order size
            price: Current market price
            order_type: Order type
            market_state: Current market state (volume, spread, etc.)
        
        Returns:
            Fill object with execution details
        """
        # Simulate latency
        latency_ms = self._simulate_latency()
        
        # Calculate slippage
        slippage_bps = self._calculate_slippage(
            size=size,
            price=price,
            side=side,
            market_state=market_state
        )
        
        # Apply slippage to price
        slippage_factor = slippage_bps / 10000.0
        if side == 'buy':
            filled_price = price * (1 + slippage_factor)
        else:  # sell
            filled_price = price * (1 - slippage_factor)
        
        slippage = abs(filled_price - price) * size
        
        # Determine fill size
        if self.enable_partial_fills and np.random.random() < 0.1:
            # 10% chance of partial fill
            fill_pct = np.random.uniform(self.min_fill_pct, 1.0)
            filled_size = size * fill_pct
            is_partial = True
        else:
            filled_size = size
            is_partial = False
        
        # Calculate commission
        commission = filled_size * filled_price * self.commission_rate
        
        # Update statistics
        self.total_fills += 1
        self.total_slippage += slippage
        self.total_commission += commission
        
        # Create fill
        fill = Fill(
            order_id=order_id,
            symbol=symbol,
            side=side,
            requested_size=size,
            filled_size=filled_size,
            requested_price=price,
            filled_price=filled_price,
            slippage=slippage,
            slippage_bps=slippage_bps,
            commission=commission,
            timestamp=datetime.now() + timedelta(milliseconds=latency_ms),
            latency_ms=latency_ms,
            is_partial=is_partial,
            metadata={
                'order_type': order_type.value,
                'slippage_model': self.slippage_model.value
            }
        )
        
        return fill
    
    def _calculate_slippage(
        self,
        size: float,
        price: float,
        side: str,
        market_state: Optional[Dict[str, Any]]
    ) -> float:
        """
        Calculate slippage in basis points.
        
        Args:
            size: Order size
            price: Current price
            side: 'buy' or 'sell'
            market_state: Market state information
        
        Returns:
            Slippage in basis points
        """
        if self.slippage_model == SlippageModel.FIXED:
            return self.base_slippage_bps
        
        elif self.slippage_model == SlippageModel.PERCENTAGE:
            # Random slippage around base
            return self.base_slippage_bps * (1 + np.random.randn() * 0.5)
        
        elif self.slippage_model == SlippageModel.VOLUME_BASED:
            # Slippage increases with order size
            if market_state and 'volume' in market_state:
                volume = market_state['volume']
                order_value = size * price
                volume_impact = (order_value / volume) if volume > 0 else 0
            else:
                # Assume order is 1% of volume
                volume_impact = 0.01
            
            impact_slippage = volume_impact * self.impact_factor * 10000
            total_slippage = self.base_slippage_bps + impact_slippage
            
            return max(0, total_slippage)
        
        elif self.slippage_model == SlippageModel.SPREAD_BASED:
            # Slippage based on bid-ask spread
            if market_state and 'spread' in market_state:
                spread_bps = (market_state['spread'] / price) * 10000
            else:
                # Assume 5 bps spread
                spread_bps = 5.0
            
            # Pay half the spread plus base slippage
            return self.base_slippage_bps + (spread_bps / 2)
        
        else:
            return self.base_slippage_bps
    
    def _simulate_latency(self) -> float:
        """
        Simulate execution latency.
        
        Returns:
            Latency in milliseconds
        """
        latency = np.random.normal(self.latency_mean_ms, self.latency_std_ms)
        return max(0, latency)
    
    def calculate_market_impact(
        self,
        size: float,
        price: float,
        liquidity: float
    ) -> float:
        """
        Calculate market impact of an order.
        
        Args:
            size: Order size
            price: Current price
            liquidity: Available liquidity
        
        Returns:
            Price impact as percentage
        """
        order_value = size * price
        impact_pct = (order_value / liquidity) * self.impact_factor
        return impact_pct
    
    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        avg_slippage = self.total_slippage / self.total_fills if self.total_fills > 0 else 0
        avg_commission = self.total_commission / self.total_fills if self.total_fills > 0 else 0
        
        return {
            'total_fills': self.total_fills,
            'total_slippage': self.total_slippage,
            'total_commission': self.total_commission,
            'avg_slippage': avg_slippage,
            'avg_commission': avg_commission,
            'slippage_model': self.slippage_model.value,
            'base_slippage_bps': self.base_slippage_bps,
            'commission_rate': self.commission_rate
        }
    
    def reset_stats(self):
        """Reset execution statistics."""
        self.total_fills = 0
        self.total_slippage = 0.0
        self.total_commission = 0.0
    
    def set_slippage_model(self, model: SlippageModel):
        """Change slippage model."""
        self.slippage_model = model
    
    def set_commission_rate(self, rate: float):
        """Change commission rate."""
        self.commission_rate = rate
    
    def set_latency(self, mean_ms: float, std_ms: float):
        """
        Update latency parameters.
        
        Args:
            mean_ms: Mean latency in milliseconds
            std_ms: Standard deviation in milliseconds
        """
        self.latency_mean_ms = mean_ms
        self.latency_std_ms = std_ms
