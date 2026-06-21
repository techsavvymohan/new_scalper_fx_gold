import pandas as pd
import numpy as np

class SATSLogic:
    def __init__(self, config):
        self.config = config

    def calculate_atr(self, df, length):
        df['tr'] = np.maximum(df['high'] - df['low'], 
                              np.maximum(abs(df['high'] - df['close'].shift(1)), 
                                         abs(df['low'] - df['close'].shift(1))))
        return df['tr'].rolling(window=length).mean()

    def calculate_efficiency_ratio(self, df, window):
        change = abs(df['close'] - df['close'].shift(window))
        volatility = abs(df['close'] - df['close'].shift(1)).rolling(window=window).sum()
        return (change / volatility.replace(0, np.nan)).fillna(0.5)

    def calculate_tqi(self, df):
        # Efficiency (35%)
        er = self.calculate_efficiency_ratio(df, self.config.EFFICIENCY_WINDOW)
        
        # Volatility (20%) - Current ATR vs Baseline
        atr = self.calculate_atr(df, self.config.ATR_LENGTH)
        atr_avg = atr.rolling(window=100).mean()
        vol_score = np.clip((atr / atr_avg.replace(0, np.nan)).fillna(1.0), 0, 1)

        # Structure (25%) - Highs/Lows analysis (Simplified)
        structure_score = self.calculate_structure_score(df, self.config.STRUCTURE_WINDOW)

        # Momentum Persistence (20%)
        momentum_persistence = self.calculate_momentum_persistence(df, self.config.MOMENTUM_PERSISTENCE_BARS)

        tqi = (er * self.config.TQI_WEIGHTS['efficiency'] +
               vol_score * self.config.TQI_WEIGHTS['volatility'] +
               structure_score * self.config.TQI_WEIGHTS['structure'] +
               momentum_persistence * self.config.TQI_WEIGHTS['momentum_persistence'])
        
        return tqi

    def calculate_structure_score(self, df, window):
        # Simplified structure score: ratio of bars making higher highs/lower lows
        higher_highs = (df['high'] > df['high'].shift(1)).rolling(window=window).sum()
        lower_lows = (df['low'] < df['low'].shift(1)).rolling(window=window).sum()
        return (higher_highs + lower_lows) / (2 * window)

    def calculate_momentum_persistence(self, df, bars):
        # Simplified momentum persistence: consistency of price direction
        returns = df['close'].diff()
        positive_returns = (returns > 0).rolling(window=bars).sum()
        negative_returns = (returns < 0).rolling(window=bars).sum()
        return abs(positive_returns - negative_returns) / bars

    def calculate_supertrend_bands(self, df):
        atr = self.calculate_atr(df, self.config.ATR_LENGTH)
        tqi = self.calculate_tqi(df)
        
        # Adaptive Engine: Kaufman Efficiency Ratio & Volatility Ratio (FR-SATS-009)
        er = self.calculate_efficiency_ratio(df, self.config.EFFICIENCY_WINDOW)
        atr_avg = atr.rolling(window=100).mean().bfill()
        
        # Kaufman regime-based multiplier: Tighter bands in efficient trending markets (high ER),
        # wider/adaptive bands in ranging or noisy markets (low ER).
        regime_multiplier = np.where(er > 0.5, 
                                     1.0 - (er - 0.5) * self.config.ADAPTATION_STRENGTH, 
                                     1.0 + (0.5 - er) * self.config.ADAPTATION_STRENGTH)
        
        # Volatility ratio adjusts band width relative to the 100-bar baseline
        vol_ratio = (atr / atr_avg.replace(0, np.nan)).fillna(1.0)
        adaptation_factor = regime_multiplier * vol_ratio
        
        # Trend Quality Influence
        quality_factor = np.power(tqi, self.config.QUALITY_CURVE_POWER) * self.config.QUALITY_INFLUENCE
        
        # Efficiency Weighted ATR (FR-SATS-014)
        weighted_atr = atr * er if self.config.EFFICIENCY_WEIGHTED_ATR_ENABLED else atr
        
        # Base Band Width
        band_width = weighted_atr * 2 * adaptation_factor * (1 + quality_factor)
        
        df['upper_band'] = df['close'] + band_width
        df['lower_band'] = df['close'] - band_width
        
        # Asymmetric Bands
        if self.config.ASYMMETRIC_BANDS_ENABLED:
            # Tighter trailing stop in trend direction
            df['upper_band'] = np.where(df['close'] > df['close'].shift(1), 
                                        df['upper_band'] * (1 - self.config.ASYMMETRIC_BANDS_STRENGTH * 0.1), 
                                        df['upper_band'])
            df['lower_band'] = np.where(df['close'] < df['close'].shift(1), 
                                        df['lower_band'] * (1 + self.config.ASYMMETRIC_BANDS_STRENGTH * 0.1), 
                                        df['lower_band'])
            
        return df

    def get_signals(self, df):
        df = self.calculate_supertrend_bands(df)
        tqi = self.calculate_tqi(df)
        
        df['trend'] = 0
        df['signal'] = 0
        
        trend_age = 0
        for i in range(1, len(df)):
            prev_trend = df['trend'].iloc[i-1]
            
            # Character Flip Detection
            early_flip = False
            if self.config.CHARACTER_FLIP_ENABLED and abs(prev_trend) == 1 and trend_age >= self.config.CHARACTER_FLIP_MIN_AGE:
                # Look back up to 5 bars to see if TQI went from > High TQI to < Low TQI
                lookback = min(5, trend_age)
                current_tqi = tqi.iloc[i]
                if current_tqi < self.config.CHARACTER_FLIP_LOW_TQI:
                    was_high = False
                    for j in range(1, lookback + 1):
                        if tqi.iloc[i-j] > self.config.CHARACTER_FLIP_HIGH_TQI:
                            was_high = True
                            break
                    if was_high:
                        early_flip = True
            
            if early_flip:
                df.at[df.index[i], 'trend'] = -prev_trend
                df.at[df.index[i], 'signal'] = -prev_trend
                trend_age = 1
            else:
                # Standard SuperTrend Flip
                if df['close'].iloc[i] > df['upper_band'].iloc[i-1]:
                    df.at[df.index[i], 'trend'] = 1 # Bullish
                    if prev_trend != 1:
                        df.at[df.index[i], 'signal'] = 1 # Buy Signal
                        trend_age = 1
                    else:
                        trend_age += 1
                elif df['close'].iloc[i] < df['lower_band'].iloc[i-1]:
                    df.at[df.index[i], 'trend'] = -1 # Bearish
                    if prev_trend != -1:
                        df.at[df.index[i], 'signal'] = -1 # Sell Signal
                        trend_age = 1
                    else:
                        trend_age += 1
                else:
                    df.at[df.index[i], 'trend'] = prev_trend
                    if prev_trend != 0:
                        trend_age += 1
                    else:
                        trend_age = 0
                
        return df
