import numpy as np
import pandas as pd

class BreakoutProbability:
    def __init__(self, config):
        self.config = config

    def calculate_probabilities(self, df):
        """
        Calculates breakout probabilities based on historical candles.
        
        Given a historical DataFrame of OHLCV bars:
        1. Classifies each bar's previous bar as Green (close > open) or Red (close < open).
        2. Computes:
           - Probability of next candle making a new high (high > prev_high)
           - Probability of next candle making a new low (low < prev_low)
           - Probabilities of hitting N levels above (relative to prev_close)
           - Probabilities of hitting N levels below (relative to prev_close)
           
        Returns a dictionary containing the calculated probabilities for the next/current bar
        based on the immediately preceding bar's direction.
        """
        if df is None or len(df) < 50:
            # Not enough history for reliable statistics
            return self._default_probabilities()

        # Ensure we have clean data columns
        required_cols = ['open', 'high', 'low', 'close']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"DataFrame must contain '{col}' column")

        # Determine candle directions
        # df['direction'] = 1 for green (close > open), -1 for red (close < open), 0 for doji
        direction = np.where(df['close'] > df['open'], 1, np.where(df['close'] < df['open'], -1, 0))
        
        # Shift direction to align previous candle direction with the current candle's outcomes
        prev_direction = pd.Series(direction).shift(1)
        
        # Outcomes for current candle
        high = df['high']
        low = df['low']
        prev_high = df['high'].shift(1)
        prev_low = df['low'].shift(1)
        prev_close = df['close'].shift(1)
        
        # 1. Did current candle make a new high relative to previous?
        new_high = (high > prev_high).astype(int)
        # 2. Did current candle make a new low relative to previous?
        new_low = (low < prev_low).astype(int)
        
        # Levels calculations
        num_lines = self.config.BREAKOUT_NUM_LINES
        pct_step = self.config.BREAKOUT_PERCENTAGE_STEP
        
        levels_above_hit = []
        levels_below_hit = []
        
        for i in range(1, num_lines + 1):
            # level above = prev_close * (1 + i * pct_step)
            # level below = prev_close * (1 - i * pct_step)
            level_above = prev_close * (1 + i * pct_step)
            level_below = prev_close * (1 - i * pct_step)
            
            levels_above_hit.append((high >= level_above).astype(int))
            levels_below_hit.append((low <= level_below).astype(int))
            
        # Create a temp DataFrame for calculations
        calc_df = pd.DataFrame({
            'prev_dir': prev_direction,
            'new_high': new_high,
            'new_low': new_low
        })
        
        for i in range(num_lines):
            calc_df[f'above_{i+1}'] = levels_above_hit[i]
            calc_df[f'below_{i+1}'] = levels_below_hit[i]
            
        # Drop the first row since it has NaN shifted values
        calc_df = calc_df.dropna()
        
        # Group by previous candle direction
        stats = {}
        for dir_val, dir_name in [(1, 'green'), (-1, 'red'), (0, 'doji')]:
            subset = calc_df[calc_df['prev_dir'] == dir_val]
            if len(subset) > 0:
                p_new_high = subset['new_high'].mean()
                p_new_low = subset['new_low'].mean()
                
                p_above = []
                p_below = []
                for i in range(num_lines):
                    p_above.append(subset[f'above_{i+1}'].mean())
                    p_below.append(subset[f'below_{i+1}'].mean())
                    
                stats[dir_name] = {
                    'count': len(subset),
                    'new_high_prob': float(p_new_high),
                    'new_low_prob': float(p_new_low),
                    'levels_above_prob': [float(x) for x in p_above],
                    'levels_below_prob': [float(x) for x in p_below]
                }
            else:
                stats[dir_name] = self._empty_stats()
                
        # Determine the direction of the last closed candle (the very last candle in df)
        last_candle = df.iloc[-1]
        last_dir = 1 if last_candle['close'] > last_candle['open'] else (-1 if last_candle['close'] < last_candle['open'] else 0)
        last_dir_name = 'green' if last_dir == 1 else ('red' if last_dir == -1 else 'doji')
        
        # The breakout probabilities for the incoming candle
        result = stats.get(last_dir_name, self._empty_stats()).copy()
        result['current_bias'] = 'bullish' if result['new_high_prob'] > result['new_low_prob'] else 'bearish'
        result['all_stats'] = stats
        result['last_candle_direction'] = last_dir_name
        
        return result

    def _default_probabilities(self):
        empty = self._empty_stats()
        empty['current_bias'] = 'neutral'
        empty['all_stats'] = {'green': self._empty_stats(), 'red': self._empty_stats(), 'doji': self._empty_stats()}
        empty['last_candle_direction'] = 'neutral'
        return empty

    def _empty_stats(self):
        num_lines = self.config.BREAKOUT_NUM_LINES
        return {
            'count': 0,
            'new_high_prob': 0.50,
            'new_low_prob': 0.50,
            'levels_above_prob': [0.0] * num_lines,
            'levels_below_prob': [0.0] * num_lines
        }
