import numpy as np
import pandas as pd

class RegimeDetection:
    def __init__(self, config):
        self.config = config

    def calculate_atr(self, df, length):
        tr = np.maximum(df['high'] - df['low'], 
                        np.maximum(abs(df['high'] - df['close'].shift(1)), 
                                   abs(df['low'] - df['close'].shift(1))))
        return tr.rolling(window=length).mean()

    def calculate_efficiency_ratio(self, df, window):
        change = abs(df['close'] - df['close'].shift(window))
        volatility = abs(df['close'] - df['close'].shift(1)).rolling(window=window).sum()
        # Prevent division by zero
        er = change / volatility.replace(0, np.nan)
        return er.fillna(0.5)

    def calculate_tqi_series(self, df, efficiency_window, atr_length):
        """
        Lightweight TQI series for use inside regime detection.
        Uses ER + vol_ratio (two components) to avoid circular dependency
        with SATSLogic while including quality information in the regime score.
        Output is clipped to [0, 1].
        """
        er = self.calculate_efficiency_ratio(df, efficiency_window)

        atr13 = self.calculate_atr(df, atr_length)
        atr_avg = atr13.rolling(window=100).mean().bfill()
        vol_ratio = (atr13 / atr_avg.replace(0, np.nan)).fillna(1.0).clip(0, 2)

        # Simplified TQI: 60% ER + 40% normalised vol_ratio (both 0-1 range)
        tqi = er * 0.6 + (vol_ratio / 2.0) * 0.4
        return tqi.clip(0, 1)

    def get_regime_detailed(self, df):
        """
        Calculates normalized components and classifies the regime.

        Inputs (all normalized via rolling z-score, 100-bar lookback):
          - z_ratio   : ATR13 / ATR100  — short-term volatility level
          - z_er      : Efficiency Ratio — trend directionality
          - z_tqi     : Trend Quality Index — composite signal quality

        Composite score = mean(z_ratio, z_er, z_tqi)

        Regime boundaries (non-overlapping, explicit, priority order):
          DEAD      : z_ratio < dead_threshold      (very suppressed volatility)
          EXPLOSIVE : z_ratio > explosive_threshold  (extreme volatility spike)
          TRENDING  : composite >= trend_min         (directional, quality confirmed)
          RANGING   : everything else

        Returns: (regime_name, norm_vol, norm_trend, raw_atr_ratio, raw_er)
        """
        if df is None or len(df) < 100:
            return 'RANGING', 0.0, 0.0, 1.0, 0.5

        efficiency_window = getattr(self.config, 'EFFICIENCY_WINDOW', 20)
        atr_length        = getattr(self.config, 'ATR_LENGTH', 13)
        lookback          = getattr(self.config, 'REGIME_LOOKBACK_BARS', 100)

        # 1. Calculate raw metric series
        atr13_series   = self.calculate_atr(df, atr_length)
        atr100_series  = self.calculate_atr(df, 100)
        er_series      = self.calculate_efficiency_ratio(df, efficiency_window)
        tqi_series     = self.calculate_tqi_series(df, efficiency_window, atr_length)

        atr_ratio_series = (atr13_series / atr100_series.replace(0, np.nan)).fillna(1.0)

        # 2. Rolling z-scores for all three inputs (100-bar lookback)
        def z_score(series, window):
            mean = series.rolling(window=window).mean()
            std  = series.rolling(window=window).std().replace(0, 1e-6)
            return (series - mean) / std

        z_ratio = z_score(atr_ratio_series, lookback)
        z_er    = z_score(er_series,         lookback)
        z_tqi   = z_score(tqi_series,        lookback)

        # 3. Composite = mean of all three normalized inputs
        composite = (z_ratio + z_er + z_tqi) / 3.0

        # 4. Extract last values
        norm_vol       = float(z_ratio.iloc[-1])
        norm_trend     = float(z_er.iloc[-1])
        raw_atr_ratio  = float(atr_ratio_series.iloc[-1])
        raw_er         = float(er_series.iloc[-1])
        composite_last = float(composite.iloc[-1])

        # Guard against NaN (not enough bars after warm-up)
        if pd.isna(norm_vol):       norm_vol       = 0.0
        if pd.isna(norm_trend):     norm_trend     = 0.0
        if pd.isna(composite_last): composite_last = 0.0

        # 5. Classify with non-overlapping explicit boundaries
        #    DEAD / EXPLOSIVE are decided on vol z-score alone (vol-regime events).
        #    TRENDING vs RANGING decided by full composite score.
        dead_threshold      = getattr(self.config, 'REGIME_VOL_DEAD_THRESHOLD',      -1.5)
        explosive_threshold = getattr(self.config, 'REGIME_VOL_EXPLOSIVE_THRESHOLD',   1.5)
        trend_min           = getattr(self.config, 'REGIME_TREND_MIN_THRESHOLD',       0.0)

        if norm_vol < dead_threshold:
            regime = 'DEAD'
        elif norm_vol > explosive_threshold:
            regime = 'EXPLOSIVE'
        elif composite_last >= trend_min:
            regime = 'TRENDING'
        else:
            regime = 'RANGING'

        return regime, norm_vol, norm_trend, raw_atr_ratio, raw_er

    def get_regime(self, df):
        """
        Convenience wrapper — returns regime label only.
        Returns one of: 'TRENDING', 'RANGING', 'DEAD', 'EXPLOSIVE'
        """
        regime, _, _, _, _ = self.get_regime_detailed(df)
        return regime
