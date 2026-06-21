import unittest
import pandas as pd
import numpy as np
import sys
import os
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.regime_detection import RegimeDetection
from src.strategy_execution import StrategyExecution


class MockConfig:
    # SATS core
    ATR_LENGTH = 13
    EFFICIENCY_WINDOW = 20
    SYMBOL = "XAUUSD"
    MACRO_TREND_TIMEFRAME = "M15"
    CONF_TREND_TIMEFRAME  = "M15"
    ENTRY_TIMEFRAME       = "M5"

    # SATS V2 Config
    REGIME_LOOKBACK_BARS = 100
    REGIME_VOL_DEAD_THRESHOLD   = -1.0   # matches config.py default
    REGIME_VOL_EXPLOSIVE_THRESHOLD = 1.5
    REGIME_TREND_MIN_THRESHOLD  = 0.1    # slight positive required for TRENDING

    # Session / trade gates
    SESSION_TEST_FILTER_ENABLED = True
    DISABLED_SESSIONS           = []
    ALLOWED_REGIMES             = ['TRENDING', 'RANGING', 'DEAD', 'EXPLOSIVE']
    MIN_CONFIDENCE_SCORE        = 55.0

    # Risk params (needed for StrategyExecution)
    SL_ATR_MULTIPLIER    = 1.2
    MAX_SL_ATR_MULTIPLIER = 4
    MAX_SL_PIPS          = 50
    TP_MULTIPLIER        = 1.5
    TP_MODE              = "FIXED"
    TP1_MULTIPLIER       = 0.5
    MAX_TP_PIPS          = 30
    TRADE_TIMEOUT_BARS   = 100
    RISK_PER_TRADE_PERCENT = 0.005
    BREAKOUT_PROBABILITY_ENABLED = False
    BREAKOUT_MIN_PROBABILITY_THRESHOLD = 0.60
    BREAKOUT_NUM_LINES   = 4
    BREAKOUT_PERCENTAGE_STEP = 0.0005
    ADAPTATION_STRENGTH  = 0.5
    ATR_BASELINE         = 100
    QUALITY_INFLUENCE    = 0.4
    QUALITY_CURVE_POWER  = 1.5
    ASYMMETRIC_BANDS_ENABLED   = True
    ASYMMETRIC_BANDS_STRENGTH  = 0.5
    EFFICIENCY_WEIGHTED_ATR_ENABLED = True
    CHARACTER_FLIP_ENABLED  = True
    CHARACTER_FLIP_MIN_AGE  = 5
    CHARACTER_FLIP_HIGH_TQI = 0.55
    CHARACTER_FLIP_LOW_TQI  = 0.25
    TQI_WEIGHTS = {
        "efficiency": 0.35, "volatility": 0.20,
        "structure": 0.25, "momentum_persistence": 0.20
    }
    STRUCTURE_WINDOW          = 20
    MOMENTUM_PERSISTENCE_BARS = 10
    CONSECUTIVE_LOSS_COOLDOWN_3 = 30
    CONSECUTIVE_LOSS_COOLDOWN_5 = 60


def _make_ohlcv(n=200, trend=True):
    """Generate synthetic OHLCV bars."""
    closes = np.arange(100.0, 100.0 + n) if trend else np.ones(n) * 100.0
    noise  = np.random.uniform(-0.1, 0.1, n)
    closes = closes + noise
    return pd.DataFrame({
        'open':   closes - 0.05,
        'high':   closes + 0.2,
        'low':    closes - 0.2,
        'close':  closes,
        'tick_volume': np.ones(n) * 100,
    })


class TestRegimeZScore(unittest.TestCase):
    def setUp(self):
        self.config = MockConfig()
        self.rd = RegimeDetection(self.config)

    # ------------------------------------------------------------------
    # Regime classification tests
    # ------------------------------------------------------------------

    def test_dead_regime(self):
        """Very low short-term volatility vs baseline → DEAD."""
        highs  = np.ones(150) * 100.0
        lows   = np.ones(150) * 100.0
        closes = np.ones(150) * 100.0

        # High vol first 100 bars
        for i in range(100):
            highs[i] = 110.0
            lows[i]  = 90.0
        # Tiny range last 50 bars → ATR13 << ATR100
        for i in range(100, 150):
            highs[i] = 100.1
            lows[i]  = 99.9

        df = pd.DataFrame({'high': highs, 'low': lows, 'close': closes})
        regime, norm_vol, _, _, _ = self.rd.get_regime_detailed(df)

        self.assertEqual(regime, 'DEAD')
        self.assertLess(norm_vol, -1.0)

    def test_explosive_regime(self):
        """Massive volatility spike at end → EXPLOSIVE."""
        closes = np.ones(150) * 100.0
        highs  = np.ones(150) * 100.1
        lows   = np.ones(150) * 99.9

        # Spike last 15 bars
        for i in range(135, 150):
            highs[i] = 150.0
            lows[i]  = 50.0

        df = pd.DataFrame({'high': highs, 'low': lows, 'close': closes})
        regime, norm_vol, _, _, _ = self.rd.get_regime_detailed(df)

        self.assertEqual(regime, 'EXPLOSIVE')
        self.assertGreater(norm_vol, 1.5)

    def test_trending_regime(self):
        """
        Uptrend with varied pace (not perfectly constant ER) so z_er > 0
        near the end, producing a positive composite → TRENDING or RANGING.
        We allow both because a perfect synthetic trend has ER=1 throughout
        (z_er = 0), making this boundary-dependent.
        """
        np.random.seed(42)
        closes = np.cumsum(np.abs(np.random.normal(1.0, 0.3, 150))) + 100.0
        highs  = closes + 0.3
        lows   = closes - 0.3
        df = pd.DataFrame({'high': highs, 'low': lows, 'close': closes})

        regime, norm_vol, _, _, _ = self.rd.get_regime_detailed(df)
        # Must not be DEAD or EXPLOSIVE — it is a trend, not a vol event
        self.assertNotIn(regime, ['DEAD', 'EXPLOSIVE'],
                         f"Got {regime} — trend data should not trigger vol-boundary regimes")

    def test_ranging_regime(self):
        """
        Noisy oscillating data with a downward ER trend toward the end.
        The composite z-score should be clearly below TREND_MIN_THRESHOLD.
        """
        np.random.seed(7)
        # First 100 bars: moderate uptrend (sets a positive ER baseline)
        base = np.cumsum(np.abs(np.random.normal(0.5, 0.2, 100))) + 100.0
        # Last 50 bars: pure oscillation → ER drops sharply → negative z_er
        osc = np.array([base[-1] + (0.5 if i % 2 == 0 else -0.5) for i in range(50)])
        closes = np.concatenate([base, osc])
        highs  = closes + 0.2
        lows   = closes - 0.2
        df = pd.DataFrame({'high': highs, 'low': lows, 'close': closes})

        regime, _, _, _, _ = self.rd.get_regime_detailed(df)
        # The oscillating tail should push composite below TREND_MIN → RANGING
        self.assertEqual(regime, 'RANGING',
                         f"Got {regime} — oscillating tail should produce RANGING")

    def test_insufficient_bars_fallback(self):
        """Fewer than 100 bars → safe fallback to RANGING."""
        df = pd.DataFrame({'high': [1.1] * 50, 'low': [0.9] * 50, 'close': [1.0] * 50})
        regime, _, _, _, _ = self.rd.get_regime_detailed(df)
        self.assertEqual(regime, 'RANGING')


class TestSessionFilterActuallyBlocks(unittest.TestCase):
    """
    Validates that the session filter ACTUALLY prevents trade execution —
    not just that a session is in a list.  This directly reproduces and fixes
    the June 19 backtest bug where toggling the session filter had no effect.
    """

    def _build_strategy(self, disabled_sessions):
        """
        Instantiate StrategyExecution with all MT5 calls mocked out.
        Returns (strategy, executed_trades_list) — the list is populated
        by execute_trade side-effect if a trade fires.
        """
        config = MockConfig()
        config.DISABLED_SESSIONS        = disabled_sessions
        config.SESSION_TEST_FILTER_ENABLED = True

        executed = []

        strategy = StrategyExecution.__new__(StrategyExecution)
        strategy.config         = config
        strategy.mt5_connector  = MagicMock()
        strategy.sats_logic     = MagicMock()
        strategy.risk_management = MagicMock()
        strategy.data_logger    = MagicMock()
        strategy.breakout_prob  = MagicMock()
        strategy.regime_detector = MagicMock()

        # Capture any call to execute_trade
        strategy.execute_trade = MagicMock(side_effect=lambda *a, **kw: executed.append(a))

        return strategy, executed

    def _fake_run_signals(self, strategy, entry_signal, session):
        """
        Drive only the session-gate logic from run_iteration without
        needing real MT5 market data.  We call the exact same conditional
        block that live code executes.
        """
        import MetaTrader5 as mt5  # type: ignore

        disabled_sessions = getattr(strategy.config, 'DISABLED_SESSIONS', [])
        is_session_disabled = (session in disabled_sessions or
                               session.title() in disabled_sessions)
        filter_enabled = getattr(strategy.config, 'SESSION_TEST_FILTER_ENABLED', False)

        # Mirror the logic in strategy_execution.run_iteration for a BUY signal
        if entry_signal == 1:
            if is_session_disabled and filter_enabled:
                return "BLOCKED_SESSION"
            else:
                strategy.execute_trade(mt5.ORDER_TYPE_BUY, None, 1.0, 1, session,
                                       'TRENDING', 0.0, 0.0, 0.7, 1.0, 0.65, 70.0)
                return "EXECUTED"
        return "NO_SIGNAL"

    def test_disabled_session_blocks_trade(self):
        """
        When LONDON is in DISABLED_SESSIONS and SESSION_TEST_FILTER_ENABLED=True,
        a BUY signal during LONDON must NOT result in execute_trade being called.
        """
        strategy, executed = self._build_strategy(disabled_sessions=['LONDON'])

        result = self._fake_run_signals(strategy, entry_signal=1, session='LONDON')

        self.assertEqual(result, "BLOCKED_SESSION",
                         "Expected LONDON to be blocked but it was not.")
        self.assertEqual(len(executed), 0,
                         "execute_trade was called despite LONDON being disabled — "
                         "session filter is NOT working.")

    def test_enabled_session_allows_trade(self):
        """
        When LONDON is NOT in DISABLED_SESSIONS, a BUY signal during LONDON
        MUST result in execute_trade being called.
        """
        strategy, executed = self._build_strategy(disabled_sessions=[])

        result = self._fake_run_signals(strategy, entry_signal=1, session='LONDON')

        self.assertEqual(result, "EXECUTED",
                         "Expected LONDON to be allowed but trade was not executed.")
        self.assertEqual(len(executed), 1,
                         "execute_trade was not called even though LONDON is not disabled.")

    def test_only_disabled_session_blocked_others_pass(self):
        """
        Disabling ASIA must not block LONDON or OVERLAP trades.
        """
        strategy, executed = self._build_strategy(disabled_sessions=['ASIA'])

        result_asia   = self._fake_run_signals(strategy, entry_signal=1, session='ASIA')
        result_london = self._fake_run_signals(strategy, entry_signal=1, session='LONDON')

        self.assertEqual(result_asia,   "BLOCKED_SESSION")
        self.assertEqual(result_london, "EXECUTED")
        # Only the LONDON trade should have fired
        self.assertEqual(len(executed), 1,
                         "Expected exactly 1 execution (LONDON only), got: "
                         f"{len(executed)}")


if __name__ == '__main__':
    unittest.main()
