"""
Market microstructure feature calculators — IMPROVED v2.
Computes real-time features from order book and trade data.

Fixes applied:
- VWAP bug fixed: volumes now correctly tracked
- Level 2 order book depth features added
- Tape-reading aggressor features added
- EMA-50 added
"""

import numpy as np
from collections import deque
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FeatureState:
    """Maintains state for rolling window calculations."""

    buy_volume:   deque = field(default_factory=lambda: deque(maxlen=100))
    sell_volume:  deque = field(default_factory=lambda: deque(maxlen=100))
    trade_sizes:  deque = field(default_factory=lambda: deque(maxlen=100))
    is_buy_flags: deque = field(default_factory=lambda: deque(maxlen=100))

    prices:     deque = field(default_factory=lambda: deque(maxlen=100))
    volumes:    deque = field(default_factory=lambda: deque(maxlen=100))   # FIX: was never populated
    timestamps: deque = field(default_factory=lambda: deque(maxlen=100))

    vpin_buy_volume:  deque = field(default_factory=lambda: deque(maxlen=50))
    vpin_sell_volume: deque = field(default_factory=lambda: deque(maxlen=50))

    ema_9:  Optional[float] = None
    ema_21: Optional[float] = None
    ema_50: Optional[float] = None

    gains:      deque = field(default_factory=lambda: deque(maxlen=14))
    losses:     deque = field(default_factory=lambda: deque(maxlen=14))
    last_price: Optional[float] = None

    consecutive_buy:  int = 0
    consecutive_sell: int = 0


class FeatureCalculator:
    """
    Real-time feature calculator for market microstructure analysis.
    Target latency: <2ms per update.

    v2 improvements:
    - VWAP correctly volume-weighted (was SMA before — bug fixed)
    - L2 order book depth imbalance, wall detection, spread_bps
    - Tape-reading: aggressor streak, large-trade ratio, delta acceleration
    - EMA-50 added for longer-term trend context
    """

    def __init__(
        self,
        order_flow_window: int = 100,
        vpin_window: int = 50,
        ema_periods: List[int] = None,
        rsi_period: int = 14,
        depth_levels: int = 10,
    ):
        self.order_flow_window = order_flow_window
        self.vpin_window       = vpin_window
        self.ema_periods       = ema_periods or [9, 21, 50]
        self.rsi_period        = rsi_period
        self.depth_levels      = depth_levels

        self.state            = FeatureState()
        self.cumulative_delta = 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(
        self,
        timestamp: datetime,
        price: float,
        bid_volume: float,
        ask_volume: float,
        trade_volume: Optional[float] = None,
        is_buy: Optional[bool] = None,
        order_book: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        self.state.timestamps.append(timestamp)
        self.state.prices.append(price)

        # FIX: populate volumes (was missing in v1 — broke VWAP)
        eff_vol = trade_volume if trade_volume else (bid_volume + ask_volume) * 0.01
        self.state.volumes.append(eff_vol)

        if trade_volume is not None and is_buy is not None:
            self.state.trade_sizes.append(trade_volume)
            self.state.is_buy_flags.append(is_buy)
            if is_buy:
                self.state.buy_volume.append(trade_volume)
                self.state.sell_volume.append(0.0)
                self.state.vpin_buy_volume.append(trade_volume)
                self.state.vpin_sell_volume.append(0.0)
                self.cumulative_delta += trade_volume
                self.state.consecutive_buy  += 1
                self.state.consecutive_sell  = 0
            else:
                self.state.buy_volume.append(0.0)
                self.state.sell_volume.append(trade_volume)
                self.state.vpin_buy_volume.append(0.0)
                self.state.vpin_sell_volume.append(trade_volume)
                self.cumulative_delta -= trade_volume
                self.state.consecutive_sell += 1
                self.state.consecutive_buy   = 0

        features: Dict[str, Any] = {
            "timestamp":            timestamp,
            "price":                price,
            "bid_volume":           bid_volume,
            "ask_volume":           ask_volume,
            "order_flow_imbalance": self._compute_ofi(bid_volume, ask_volume),
            "cumulative_delta":     self.cumulative_delta,
            "vpin":                 self._compute_vpin(),
            "vwap":                 self._compute_vwap(),
            "ema_9":                self._compute_ema(9),
            "ema_21":               self._compute_ema(21),
            "ema_50":               self._compute_ema(50),
            "rsi":                  self._compute_rsi(price),
        }

        features.update(self._compute_tape_features())

        if order_book:
            features.update(self._compute_depth_features(order_book))
            features["liquidity_heatmap"] = self.get_liquidity_heatmap(order_book)

        return features

    # ------------------------------------------------------------------
    # Core indicators
    # ------------------------------------------------------------------

    def _compute_ofi(self, bid_volume: float, ask_volume: float) -> float:
        total = bid_volume + ask_volume
        return (bid_volume - ask_volume) / total if total else 0.0

    def _compute_vpin(self) -> float:
        if len(self.state.vpin_buy_volume) < self.vpin_window:
            return 0.0
        bv = sum(list(self.state.vpin_buy_volume)[-self.vpin_window:])
        sv = sum(list(self.state.vpin_sell_volume)[-self.vpin_window:])
        tot = bv + sv
        return abs(bv - sv) / tot if tot else 0.0

    def _compute_vwap(self) -> Optional[float]:
        """FIX: now truly volume-weighted."""
        p = list(self.state.prices)
        v = list(self.state.volumes)
        if not p:
            return None
        if not v or len(p) != len(v):
            return float(np.mean(p))
        pa, va = np.array(p), np.array(v)
        return float(np.sum(pa * va) / np.sum(va)) if va.sum() else float(np.mean(pa))

    def _compute_ema(self, period: int) -> Optional[float]:
        if not self.state.prices:
            return None
        price = self.state.prices[-1]
        k = 2.0 / (period + 1)
        if period == 9:
            self.state.ema_9 = price if self.state.ema_9 is None else price * k + self.state.ema_9 * (1 - k)
            return self.state.ema_9
        elif period == 21:
            self.state.ema_21 = price if self.state.ema_21 is None else price * k + self.state.ema_21 * (1 - k)
            return self.state.ema_21
        elif period == 50:
            self.state.ema_50 = price if self.state.ema_50 is None else price * k + self.state.ema_50 * (1 - k)
            return self.state.ema_50
        return None

    def _compute_rsi(self, price: float) -> Optional[float]:
        if self.state.last_price is None:
            self.state.last_price = price
            return None
        change = price - self.state.last_price
        self.state.last_price = price
        self.state.gains.append(max(change, 0))
        self.state.losses.append(max(-change, 0))
        if len(self.state.gains) < self.rsi_period:
            return None
        ag = float(np.mean(self.state.gains))
        al = float(np.mean(self.state.losses))
        if al == 0:
            return 100.0
        return 100.0 - (100.0 / (1.0 + ag / al))

    # ------------------------------------------------------------------
    # NEW: Tape-reading features
    # ------------------------------------------------------------------

    def _compute_tape_features(self) -> Dict[str, Any]:
        sizes = list(self.state.trade_sizes)
        flags = list(self.state.is_buy_flags)
        if len(sizes) < 5:
            return {"aggressor_streak": 0, "large_trade_ratio": 0.0,
                    "trade_intensity": 0, "buy_sell_ratio_20": 0.5, "delta_acceleration": 0.0}

        w = min(20, len(sizes))
        rs, rf = sizes[-w:], flags[-w:]

        streak = 0
        for f in reversed(rf):
            if f is True:
                if streak >= 0: streak += 1
                else: break
            else:
                if streak <= 0: streak -= 1
                else: break

        avg_sz = float(np.mean(rs)) if rs else 1.0
        large_ratio = sum(1 for s in rs if s > avg_sz * 2) / len(rs) if rs else 0.0
        bsr = sum(1 for f in rf if f is True) / len(rf) if rf else 0.5

        buys  = list(self.state.buy_volume)
        sells = list(self.state.sell_volume)
        if len(buys) >= 10:
            delta_accel = (sum(buys[-5:]) - sum(sells[-5:])) - (sum(buys[-10:-5]) - sum(sells[-10:-5]))
        else:
            delta_accel = 0.0

        return {
            "aggressor_streak":  int(streak),
            "large_trade_ratio": round(float(large_ratio), 4),
            "trade_intensity":   len(rs),
            "buy_sell_ratio_20": round(float(bsr), 4),
            "delta_acceleration": round(float(delta_accel), 4),
        }

    # ------------------------------------------------------------------
    # NEW: L2 depth features
    # ------------------------------------------------------------------

    def _compute_depth_features(self, order_book: Dict[str, Any], levels: int = None) -> Dict[str, Any]:
        n    = levels or self.depth_levels
        bids = order_book.get("bids", [])[:n]
        asks = order_book.get("asks", [])[:n]

        bv = [float(b[1]) for b in bids]
        av = [float(a[1]) for a in asks]
        bp = [float(b[0]) for b in bids]
        ap = [float(a[0]) for a in asks]

        tb = sum(bv) + 1e-9
        ta = sum(av) + 1e-9

        avg_bv = float(np.mean(bv)) if bv else 1.0
        avg_av = float(np.mean(av)) if av else 1.0

        best_bid = bp[0] if bp else 0.0
        best_ask = ap[0] if ap else 0.0
        mid = (best_bid + best_ask) / 2
        spread_bps = ((best_ask - best_bid) / mid * 10000) if mid else 0.0

        return {
            "depth_imbalance":    round(float((tb - ta) / (tb + ta)), 4),
            "bid_wall_strength":  round(float(max(bv)) / (avg_bv + 1e-9), 3) if bv else 0.0,
            "ask_wall_strength":  round(float(max(av)) / (avg_av + 1e-9), 3) if av else 0.0,
            "bid_ask_depth_ratio": round(float(tb / ta), 4),
            "spread_bps":         round(float(spread_bps), 2),
        }

    def get_liquidity_heatmap(self, order_book: Dict[str, Any], num_levels: int = 20) -> Dict[str, Any]:
        bids = order_book.get("bids", [])[:num_levels]
        asks = order_book.get("asks", [])[:num_levels]
        bv = [float(b[1]) for b in bids]
        av = [float(a[1]) for a in asks]
        tb = sum(bv) + 1e-9
        ta = sum(av) + 1e-9
        return {
            "bid_prices": [float(b[0]) for b in bids],
            "bid_volumes": bv,
            "ask_prices": [float(a[0]) for a in asks],
            "ask_volumes": av,
            "total_bid_liquidity": tb,
            "total_ask_liquidity": ta,
            "liquidity_imbalance": (tb - ta) / (tb + ta),
        }

    def reset(self):
        self.state = FeatureState()
        self.cumulative_delta = 0.0
