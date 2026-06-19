import pandas as pd
import os
from datetime import datetime

class DataLogger:
    def __init__(self, config):
        self.config = config
        self.log_path = os.path.join("data", self.config.TRADE_LOG_FILE)
        self._initialize_log()

    def _initialize_log(self):
        if not os.path.exists(self.log_path):
            df = pd.DataFrame(columns=[
                "entry_time", "exit_time", "symbol", "direction", "entry_price", 
                "exit_price", "sl", "tp", "lot", "m15_trend", "profit", "status", "ticket"
            ])
            df.to_csv(self.log_path, index=False)

    def log_trade(self, trade_data):
        df = pd.read_csv(self.log_path)
        new_row = pd.DataFrame([trade_data])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(self.log_path, index=False)

    def update_trade_exit(self, ticket, exit_price, exit_time, profit):
        df = pd.read_csv(self.log_path)
        if ticket in df['ticket'].values:
            df.loc[df['ticket'] == ticket, 'exit_price'] = exit_price
            df.loc[df['ticket'] == ticket, 'exit_time'] = exit_time
            df.loc[df['ticket'] == ticket, 'profit'] = profit
            df.loc[df['ticket'] == ticket, 'status'] = "CLOSED"
            df.to_csv(self.log_path, index=False)
