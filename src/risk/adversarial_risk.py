"""
Adversarial Risk Manager - Layer 4.
Detects market manipulation and spoofing.
"""

import logging
from typing import Dict, Any, Optional, List
from collections import deque

from .risk_config import RiskConfig

logger = logging.getLogger(__name__)


class AdversarialRiskManager:
    """
    Layer 4: Adversarial risk management.
    
    Detects:
    - Order book spoofing
    - Sudden volume spikes
    - Price manipulation
    """
    
    def __init__(self, config: RiskConfig):
        """Initialize adversarial risk manager."""
        self.config = config
        self.volume_history: deque = deque(maxlen=100)
        self.price_history: deque = deque(maxlen=60)  # 1 minute at 1s intervals
    
    def check(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check for adversarial market conditions.
        
        Args:
            market_data: Market data (price, volume, orderbook, bid, ask)
        
        Returns:
            Dict with approved, warnings, reasons
        """
        result = {
            'approved': True,
            'warnings': [],
            'reasons': []
        }
        
        price = market_data.get('price')
        volume = market_data.get('volume', 0)
        orderbook = market_data.get('orderbook', {})
        
        # Check order book imbalance
        if orderbook and self.config.spoofing_detection_enabled:
            imbalance = self._check_orderbook_imbalance(orderbook)
            if imbalance > self.config.order_book_imbalance_threshold:
                result['approved'] = False
                result['reasons'].append(
                    f"Order book imbalance detected: {imbalance:.1%} (threshold: {self.config.order_book_imbalance_threshold:.1%})"
                )
        
        # Check volume spike
        if volume > 0:
            self.volume_history.append(volume)
            if len(self.volume_history) >= 10:
                avg_volume = sum(self.volume_history) / len(self.volume_history)
                if volume > avg_volume * self.config.sudden_volume_spike_threshold:
                    result['warnings'].append(
                        f"Sudden volume spike: {volume / avg_volume:.1f}x average"
                    )
        
        # Check price manipulation
        if price:
            self.price_history.append(price)
            if len(self.price_history) >= 2:
                price_change = abs(price - self.price_history[0]) / self.price_history[0]
                if price_change > self.config.price_manipulation_threshold:
                    result['approved'] = False
                    result['reasons'].append(
                        f"Suspicious price movement: {price_change:.2%} in 1 minute"
                    )
        
        return result
    
    def _check_orderbook_imbalance(self, orderbook: Dict[str, Any]) -> float:
        """
        Calculate order book imbalance.
        
        Args:
            orderbook: Order book with 'bids' and 'asks'
        
        Returns:
            Imbalance ratio (0 to 1)
        """
        bids = orderbook.get('bids', [])
        asks = orderbook.get('asks', [])
        
        if not bids or not asks:
            return 0.0
        
        # Sum top 5 levels
        bid_volume = sum(bid[1] for bid in bids[:5])
        ask_volume = sum(ask[1] for ask in asks[:5])
        
        total_volume = bid_volume + ask_volume
        if total_volume == 0:
            return 0.0
        
        # Calculate imbalance
        imbalance = abs(bid_volume - ask_volume) / total_volume
        return imbalance
