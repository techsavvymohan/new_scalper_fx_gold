import unittest
import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.sats_logic import SATSLogic
from src.risk_filters import RiskFilters

class MockConfig:
    ATR_LENGTH = 13
    EFFICIENCY_WINDOW = 20
    ADAPTATION_STRENGTH = 0.5
    ATR_BASELINE = 100
    QUALITY_INFLUENCE = 0.4
    QUALITY_CURVE_POWER = 1.5
    ASYMMETRIC_BANDS_STRENGTH = 0.5
    ASYMMETRIC_BANDS_ENABLED = True
    EFFICIENCY_WEIGHTED_ATR_ENABLED = True
    CHARACTER_FLIP_ENABLED = True
    CHARACTER_FLIP_MIN_AGE = 5
    CHARACTER_FLIP_HIGH_TQI = 0.55
    CHARACTER_FLIP_LOW_TQI = 0.25
    TQI_WEIGHTS = {
        "efficiency": 0.35,
        "volatility": 0.20,
        "structure": 0.25,
        "momentum_persistence": 0.20,
    }
    STRUCTURE_WINDOW = 20
    MOMENTUM_PERSISTENCE_BARS = 10
    
    VOLATILITY_FILTER_ENABLED = True
    ATR_PERCENTILE_LOW_THRESHOLD = 0.1
    ATR_PERCENTILE_HIGH_THRESHOLD = 0.9
    DAILY_MAX_LOSS_PERCENT = 0.02
    MAX_CONSECUTIVE_LOSSES = 5
    SYMBOL = "XAUUSD"

class MockAccountInfo:
    balance = 10000.0
    equity = 10000.0

class MockMT5Connector:
    def __init__(self):
        self.connected = True
    def ensure_connected(self):
        return self.connected
    def get_account_info(self):
        return MockAccountInfo()
    def get_open_positions(self, symbol):
        return []

class TestPRDGaps(unittest.TestCase):
    def setUp(self):
        self.config = MockConfig()
        self.sats = SATSLogic(self.config)
        self.mt5 = MockMT5Connector()
        self.risk_filters = RiskFilters(self.config, self.mt5)

    def test_volatility_filter_pass(self):
        # Generate some mock data
        np.random.seed(42)
        closes = np.random.uniform(100, 105, 50)
        highs = closes + 1.0
        lows = closes - 1.0
        df = pd.DataFrame({'high': highs, 'low': lows, 'close': closes})
        
        res = self.risk_filters.check_volatility_filter(df, 13)
        self.assertIsInstance(res, bool)

    def test_character_flip_logic_detection(self):
        closes = np.arange(100, 120)
        opens = closes - 0.5
        highs = closes + 0.5
        lows = closes - 0.5
        df = pd.DataFrame({'open': opens, 'high': highs, 'low': lows, 'close': closes})
        
        df = self.sats.get_signals(df)
        self.assertIn('trend', df.columns)
        self.assertIn('signal', df.columns)

if __name__ == '__main__':
    unittest.main()
