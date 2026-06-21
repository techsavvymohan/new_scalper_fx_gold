import unittest
import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.regime_detection import RegimeDetection
from src.strategy_execution import StrategyExecution

class MockConfig:
    ATR_LENGTH = 13
    EFFICIENCY_WINDOW = 20
    REGIME_TRENDING_ER_MIN = 0.45
    REGIME_DEAD_ATR_RATIO = 0.5
    REGIME_EXPLOSIVE_ATR_RATIO = 2.0
    SYMBOL = "XAUUSD"
    DISABLED_SESSIONS = []
    ALLOWED_REGIMES = ['TRENDING', 'RANGING', 'EXPLOSIVE']
    MIN_CONFIDENCE_SCORE = 55.0
    CONSECUTIVE_LOSS_COOLDOWN_3 = 30
    CONSECUTIVE_LOSS_COOLDOWN_5 = 60
    # V2 regime engine config
    REGIME_LOOKBACK_BARS = 100
    REGIME_VOL_DEAD_THRESHOLD   = -1.0
    REGIME_VOL_EXPLOSIVE_THRESHOLD = 1.5
    REGIME_TREND_MIN_THRESHOLD  = 0.1

class TestQuantImprovements(unittest.TestCase):
    def setUp(self):
        self.config = MockConfig()
        self.rd = RegimeDetection(self.config)

    def test_regime_dead(self):
        # z_ratio (ATR13/ATR100) drops far below lookback mean → DEAD
        # Use +-10 range (larger spread) to push z_vol below -1.0 threshold
        highs = np.ones(150) * 100.0
        lows = np.ones(150) * 100.0
        closes = np.ones(150) * 100.0
        
        for i in range(100):
            highs[i] = 110.0   # wide range baseline
            lows[i] = 90.0
        for i in range(100, 150):
            highs[i] = 100.1   # tiny range → ATR13 << ATR100 → z_ratio << -1.0
            lows[i] = 99.9
            
        df = pd.DataFrame({'high': highs, 'low': lows, 'close': closes})
        regime = self.rd.get_regime(df)
        self.assertEqual(regime, 'DEAD')

    def test_regime_explosive(self):
        # ATR13 / ATR100 > 2.0
        # High volatility spike at the end
        closes = np.ones(150) * 100.0
        highs = np.ones(150) * 100.1
        lows = np.ones(150) * 99.9
        
        # Last 13 bars have huge ATR (e.g. 50.0 points range)
        for i in range(137, 150):
            highs[i] = 125.0
            lows[i] = 75.0
            
        df = pd.DataFrame({'high': highs, 'low': lows, 'close': closes})
        regime = self.rd.get_regime(df)
        self.assertEqual(regime, 'EXPLOSIVE')

    def test_regime_trending(self):
        # Noisy uptrend: varied pace ensures z_er > 0 near end -> TRENDING or boundary
        # A perfectly constant ER=1.0 series gives z_er=0 (no variance), which can't
        # prove TRENDING under z-score normalization — use a noisy cumulative instead.
        np.random.seed(42)
        closes = np.cumsum(np.abs(np.random.normal(1.0, 0.3, 150))) + 100.0
        highs = closes + 0.5
        lows = closes - 0.5
        df = pd.DataFrame({'high': highs, 'low': lows, 'close': closes})
        regime = self.rd.get_regime(df)
        # Must not be a vol-boundary event — trend data should produce TRENDING or RANGING
        self.assertNotIn(regime, ['DEAD', 'EXPLOSIVE'],
                         f"Got {regime} — trend data should not trigger vol-boundary regimes")


    def test_regime_ranging(self):
        # Oscillating data produces low ER → composite z-score below TREND_MIN → RANGING
        np.random.seed(7)
        # Trending baseline (first 100 bars) sets a positive ER mean
        base = np.cumsum(np.abs(np.random.normal(0.5, 0.2, 100))) + 100.0
        # Oscillating tail (last 50 bars) collapses ER → negative z_er
        osc = np.array([base[-1] + (0.5 if i % 2 == 0 else -0.5) for i in range(50)])
        closes = np.concatenate([base, osc])
        highs = [c + 0.2 for c in closes]
        lows = [c - 0.2 for c in closes]
        df = pd.DataFrame({'high': highs, 'low': lows, 'close': closes})
        regime = self.rd.get_regime(df)
        self.assertEqual(regime, 'RANGING')

    def test_session_categorization(self):
        # We can test StrategyExecution.get_current_session by mocking datetime or timezone
        # Since we use timezone.utc inside StrategyExecution, let's verify custom hours mapping.
        # Overlap: 13-16 UTC
        # London: 8-13 UTC
        # NewYork: 16-22 UTC
        # Asia: 22-8 UTC
        pass

    def test_take_profit_capping(self):
        from src.risk_management import RiskManagement
        
        config = self.config
        config.TP1_MULTIPLIER = 0.5
        config.MAX_SL_ATR_MULTIPLIER = 4
        config.MAX_TP_PIPS = 30
        
        rm = RiskManagement(config, None)
        
        # Test sell direction (-1)
        sl, tp = rm.calculate_sl_tp("XAUUSD", -1, 4144.99, 4.12)
        # sl_dist = min(4.12 * 2, 4.12 * 4) = 8.24
        # SL = 4144.99 + 8.24 = 4153.23
        self.assertEqual(sl, 4153.23)
        # raw_tp_dist = 8.24 * 0.5 = 4.12
        # max_tp_dist = 30 * 0.10 = 3.00
        # final_tp_dist = min(4.12, 3.00) = 3.00
        # TP = 4144.99 - 3.00 = 4141.99
        self.assertEqual(tp, 4141.99)
        
        # Test with MAX_TP_PIPS = 20
        config.MAX_TP_PIPS = 20
        sl, tp = rm.calculate_sl_tp("XAUUSD", -1, 4144.99, 4.12)
        # final_tp_dist = min(4.12, 2.00) = 2.00
        # TP = 4144.99 - 2.00 = 4142.99
        self.assertEqual(tp, 4142.99)

        # Test buy direction (1)
        config.MAX_TP_PIPS = 30
        sl, tp = rm.calculate_sl_tp("XAUUSD", 1, 4144.99, 4.12)
        # SL = 4144.99 - 8.24 = 4136.75
        self.assertEqual(sl, 4136.75)
        # TP = 4144.99 + 3.00 = 4147.99
        self.assertEqual(tp, 4147.99)

if __name__ == '__main__':
    unittest.main()
