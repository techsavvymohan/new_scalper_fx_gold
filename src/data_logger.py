import pandas as pd
import os
from datetime import datetime

class DataLogger:
    def __init__(self, config):
        self.config = config
        self.log_path = os.path.join("data", self.config.TRADE_LOG_FILE)
        self._initialize_log()

    def _initialize_log(self):
        columns = [
            "entry_time", "exit_time", "symbol", "direction", "entry_price", 
            "exit_price", "sl", "tp", "lot", "m15_trend", "profit", "status", "ticket",
            "session", "regime", "regime_norm_vol", "regime_norm_trend", "tqi", "atr_ratio", 
            "volume_score", "confidence_score", "box_size", "exit_type", "rr_achieved", 
            "intended_entry_price", "realized_slippage", "breakout_prob"
        ]
        if not os.path.exists(self.log_path):
            df = pd.DataFrame(columns=columns)
            df.to_csv(self.log_path, index=False)
        else:
            try:
                df = pd.read_csv(self.log_path)
                modified = False
                for col in columns:
                    if col not in df.columns:
                        df[col] = None
                        modified = True
                if modified:
                    # preserve columns order
                    df = df[columns]
                    df.to_csv(self.log_path, index=False)
            except Exception as e:
                print(f"Error checking/upgrading trade log columns: {e}")

    def log_trade(self, trade_data):
        df = pd.read_csv(self.log_path)
        new_row = pd.DataFrame([trade_data])
        # Ensure all columns exist
        for col in df.columns:
            if col not in new_row.columns:
                new_row[col] = None
        new_row = new_row[df.columns]
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(self.log_path, index=False)

    def update_trade_exit(self, ticket, exit_price, exit_time, profit, exit_type=None, rr_achieved=None, realized_slippage=None):
        df = pd.read_csv(self.log_path)
        if ticket in df['ticket'].values:
            mask = df['ticket'] == ticket
            df.loc[mask, 'exit_price'] = exit_price
            df.loc[mask, 'exit_time'] = exit_time
            df.loc[mask, 'profit'] = profit
            df.loc[mask, 'status'] = "CLOSED"
            if exit_type is not None:
                df.loc[mask, 'exit_type'] = exit_type
            if rr_achieved is not None:
                df.loc[mask, 'rr_achieved'] = rr_achieved
            if realized_slippage is not None:
                df.loc[mask, 'realized_slippage'] = realized_slippage
            df.to_csv(self.log_path, index=False)
