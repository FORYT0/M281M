"""Unit tests for feature calculators."""

import pytest
import numpy as np
from datetime import datetime, timedelta
from src.pipeline.features import FeatureCalculator


class TestFeatureCalculator:
    """Test suite for FeatureCalculator."""
    
    def test_initialization(self):
        """Test calculator initializes correctly."""
        calc = FeatureCalculator()
        assert calc.order_flow_window == 100
        assert calc.vpin_window == 50
        assert calc.rsi_period == 14
        assert calc.cumulative_delta == 0.0
    
    def test_order_flow_imbalance(self):
        """Test order flow imbalance calculation."""
        calc = FeatureCalculator()
        
        # All buying pressure
        features = calc.update(
            timestamp=datetime.now(),
            price=50000.0,
            bid_volume=10.0,
            ask_volume=0.0
        )
        assert features['order_flow_imbalance'] == 1.0
        
        # All selling pressure
        features = calc.update(
            timestamp=datetime.now(),
            price=50000.0,
            bid_volume=0.0,
            ask_volume=10.0
        )
        assert features['order_flow_imbalance'] == -1.0
        
        # Balanced
        features = calc.update(
            timestamp=datetime.now(),
            price=50000.0,
            bid_volume=5.0,
            ask_volume=5.0
        )
        assert features['order_flow_imbalance'] == 0.0
    
    def test_cumulative_delta(self):
        """Test cumulative delta tracking."""
        calc = FeatureCalculator()
        
        # Buy trade
        features = calc.update(
            timestamp=datetime.now(),
            price=50000.0,
            bid_volume=5.0,
            ask_volume=5.0,
            trade_volume=1.0,
            is_buy=True
        )
        assert features['cumulative_delta'] == 1.0
        
        # Sell trade
        features = calc.update(
            timestamp=datetime.now(),
            price=50000.0,
            bid_volume=5.0,
            ask_volume=5.0,
            trade_volume=0.5,
            is_buy=False
        )
        assert features['cumulative_delta'] == 0.5
    
    def test_ema_calculation(self):
        """Test EMA calculation."""
        calc = FeatureCalculator()
        
        # Feed prices
        prices = [50000, 50100, 50200, 50300, 50400]
        
        for price in prices:
            features = calc.update(
                timestamp=datetime.now(),
                price=price,
                bid_volume=1.0,
                ask_volume=1.0
            )
        
        # EMA should be initialized
        assert features['ema_9'] is not None
        assert features['ema_21'] is not None
        
        # EMA should be close to recent prices
        assert 50000 <= features['ema_9'] <= 50400
        assert 50000 <= features['ema_21'] <= 50400
    
    def test_rsi_calculation(self):
        """Test RSI calculation."""
        calc = FeatureCalculator()
        
        # Create uptrend (should result in high RSI)
        base_price = 50000
        for i in range(20):
            price = base_price + (i * 100)  # Increasing prices
            features = calc.update(
                timestamp=datetime.now(),
                price=price,
                bid_volume=1.0,
                ask_volume=1.0
            )
        
        # RSI should be high (overbought)
        if features['rsi'] is not None:
            assert features['rsi'] > 50
    
    def test_vpin_calculation(self):
        """Test VPIN calculation."""
        calc = FeatureCalculator()
        
        # Feed enough trades for VPIN
        for i in range(60):
            features = calc.update(
                timestamp=datetime.now(),
                price=50000.0,
                bid_volume=1.0,
                ask_volume=1.0,
                trade_volume=1.0,
                is_buy=(i % 2 == 0)  # Alternate buy/sell
            )
        
        # VPIN should be calculated
        assert features['vpin'] is not None
        assert 0.0 <= features['vpin'] <= 1.0
    
    def test_liquidity_heatmap(self):
        """Test liquidity heatmap generation."""
        calc = FeatureCalculator()
        
        order_book = {
            'bids': [
                ['50000', '1.0'],
                ['49999', '2.0'],
                ['49998', '1.5']
            ],
            'asks': [
                ['50001', '1.2'],
                ['50002', '1.8'],
                ['50003', '2.0']
            ]
        }
        
        heatmap = calc.get_liquidity_heatmap(order_book)
        
        assert len(heatmap['bid_prices']) == 3
        assert len(heatmap['ask_prices']) == 3
        assert heatmap['total_bid_liquidity'] == 4.5
        assert heatmap['total_ask_liquidity'] == 5.0
        assert 'liquidity_imbalance' in heatmap
    
    def test_reset(self):
        """Test state reset."""
        calc = FeatureCalculator()
        
        # Add some data
        for i in range(10):
            calc.update(
                timestamp=datetime.now(),
                price=50000.0 + i,
                bid_volume=1.0,
                ask_volume=1.0,
                trade_volume=1.0,
                is_buy=True
            )
        
        assert calc.cumulative_delta > 0
        
        # Reset
        calc.reset()
        
        assert calc.cumulative_delta == 0.0
        assert len(calc.state.prices) == 0
    
    def test_performance(self):
        """Test feature calculation performance."""
        import time
        
        calc = FeatureCalculator()
        
        # Warm up
        for i in range(100):
            calc.update(
                timestamp=datetime.now(),
                price=50000.0,
                bid_volume=1.0,
                ask_volume=1.0,
                trade_volume=1.0,
                is_buy=(i % 2 == 0)
            )
        
        # Measure performance
        iterations = 1000
        start = time.perf_counter()
        
        for i in range(iterations):
            calc.update(
                timestamp=datetime.now(),
                price=50000.0 + (i % 100),
                bid_volume=1.0,
                ask_volume=1.0,
                trade_volume=1.0,
                is_buy=(i % 2 == 0)
            )
        
        elapsed = time.perf_counter() - start
        avg_time_ms = (elapsed / iterations) * 1000
        
        # Should be well under 50ms per update
        assert avg_time_ms < 1.0, f"Average time {avg_time_ms:.3f}ms exceeds target"
        
        print(f"\nPerformance: {avg_time_ms:.3f}ms per update")
        print(f"Throughput: {iterations/elapsed:.0f} updates/second")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
