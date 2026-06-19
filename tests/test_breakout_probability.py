import unittest
import pandas as pd
import numpy as np
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.breakout_probability import BreakoutProbability

class MockConfig:
    BREAKOUT_PERCENTAGE_STEP = 0.01
    BREAKOUT_NUM_LINES = 4

class TestBreakoutProbability(unittest.TestCase):
    def setUp(self):
        self.config = MockConfig()
        self.bp = BreakoutProbability(self.config)

    def test_default_probabilities_on_short_data(self):
        # Data too short (less than 50 rows)
        df = pd.DataFrame({
            'open': [100.0] * 10,
            'high': [101.0] * 10,
            'low': [99.0] * 10,
            'close': [100.5] * 10
        })
        res = self.bp.calculate_probabilities(df)
        self.assertEqual(res['current_bias'], 'neutral')
        self.assertEqual(res['last_candle_direction'], 'neutral')
        self.assertEqual(res['new_high_prob'], 0.50)

    def test_probability_calculation(self):
        # Generate 60 candles
        # Let's make every alternate candle green (close > open)
        # and configure them so we can test the probability calculations.
        np.random.seed(42)
        opens = np.random.uniform(100, 105, 60)
        closes = opens + np.random.choice([-1.0, 1.0], 60) # half green, half red
        highs = np.maximum(opens, closes) + 0.5
        lows = np.minimum(opens, closes) - 0.5

        df = pd.DataFrame({
            'open': opens,
            'high': highs,
            'low': lows,
            'close': closes
        })

        res = self.bp.calculate_probabilities(df)
        
        # Check output structure
        self.assertIn('new_high_prob', res)
        self.assertIn('new_low_prob', res)
        self.assertIn('levels_above_prob', res)
        self.assertIn('levels_below_prob', res)
        self.assertIn('current_bias', res)
        self.assertIn('all_stats', res)
        self.assertIn('last_candle_direction', res)

        # Check all_stats has green, red, doji
        self.assertIn('green', res['all_stats'])
        self.assertIn('red', res['all_stats'])
        self.assertIn('doji', res['all_stats'])

        # Probabilities should be floats between 0 and 1
        self.assertTrue(0.0 <= res['new_high_prob'] <= 1.0)
        self.assertTrue(0.0 <= res['new_low_prob'] <= 1.0)
        self.assertEqual(len(res['levels_above_prob']), self.config.BREAKOUT_NUM_LINES)
        self.assertEqual(len(res['levels_below_prob']), self.config.BREAKOUT_NUM_LINES)

if __name__ == '__main__':
    unittest.main()
