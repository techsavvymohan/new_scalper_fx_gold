import pandas as pd
from src.sats_logic import SATSLogic

class Backtester:
    def __init__(self, config):
        self.config = config
        self.sats_logic = SATSLogic(config)

    def run_backtest(self, data):
        """
        Simple vectorized backtest for the SATS strategy.
        """
        df = self.sats_logic.get_signals(data)
        
        # Calculate returns
        df['returns'] = df['close'].pct_change()
        df['strategy_returns'] = df['trend'].shift(1) * df['returns']
        
        # Calculate performance metrics
        total_return = (1 + df['strategy_returns']).prod() - 1
        sharpe_ratio = df['strategy_returns'].mean() / df['strategy_returns'].std() * (252**0.5)
        
        print(f"Backtest Results:")
        print(f"Total Return: {total_return:.2%}")
        print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
        
        return df

    def perform_ablation_test(self, data):
        """
        FR-VAL-001: Ablation test for SATS sub-modules.
        """
        print("Starting ablation tests...")
        results = {}
        
        # Base/Control Run
        print("Running Control backtest...")
        df_control = self.run_backtest(data.copy())
        control_ret = (1 + df_control['strategy_returns']).prod() - 1
        results['Control'] = control_ret
        
        # Disable Asymmetric Bands
        print("Running Ablation: Asymmetric Bands disabled...")
        orig_asym = self.config.ASYMMETRIC_BANDS_ENABLED
        self.config.ASYMMETRIC_BANDS_ENABLED = False
        df_no_asym = self.run_backtest(data.copy())
        results['No_Asymmetric_Bands'] = (1 + df_no_asym['strategy_returns']).prod() - 1
        self.config.ASYMMETRIC_BANDS_ENABLED = orig_asym
        
        # Disable Efficiency Weighted ATR
        print("Running Ablation: Efficiency Weighted ATR disabled...")
        orig_weighted = self.config.EFFICIENCY_WEIGHTED_ATR_ENABLED
        self.config.EFFICIENCY_WEIGHTED_ATR_ENABLED = False
        df_no_weighted = self.run_backtest(data.copy())
        results['No_Efficiency_Weighted_ATR'] = (1 + df_no_weighted['strategy_returns']).prod() - 1
        self.config.EFFICIENCY_WEIGHTED_ATR_ENABLED = orig_weighted

        # Disable Character Flip
        print("Running Ablation: Character Flip disabled...")
        orig_flip = self.config.CHARACTER_FLIP_ENABLED
        self.config.CHARACTER_FLIP_ENABLED = False
        df_no_flip = self.run_backtest(data.copy())
        results['No_Character_Flip'] = (1 + df_no_flip['strategy_returns']).prod() - 1
        self.config.CHARACTER_FLIP_ENABLED = orig_flip
        
        print("\nAblation Test Results (Total Returns):")
        for k, v in results.items():
            print(f"  - {k}: {v:.2%}")
        return results

    def perform_stress_test(self, data):
        """
        FR-VAL-002: Stress test for core parameters.
        """
        print("Starting stress tests...")
        results = {}
        
        # Control Run
        df_control = self.run_backtest(data.copy())
        control_ret = (1 + df_control['strategy_returns']).prod() - 1
        results['Control'] = control_ret
        
        stress_params = [
            ('ATR_LENGTH', [10, 16]),
            ('EFFICIENCY_WINDOW', [16, 24]),
            ('ADAPTATION_STRENGTH', [0.4, 0.6])
        ]
        
        for param, values in stress_params:
            orig_val = getattr(self.config, param)
            for val in values:
                setattr(self.config, param, val)
                print(f"Stress testing parameter {param} set to {val}...")
                df_stress = self.run_backtest(data.copy())
                stress_ret = (1 + df_stress['strategy_returns']).prod() - 1
                results[f"{param}_{val}"] = stress_ret
            setattr(self.config, param, orig_val)
            
        print("\nStress Test Results (Total Returns):")
        for k, v in results.items():
            print(f"  - {k}: {v:.2%}")
        return results
