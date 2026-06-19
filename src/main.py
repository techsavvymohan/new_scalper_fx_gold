import time
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config
from src.mt5_connector import MT5Connector
from src.sats_logic import SATSLogic
from src.risk_management import RiskManagement
from src.strategy_execution import StrategyExecution
from src.data_logger import DataLogger
from src.risk_filters import RiskFilters

def main():
    print("Starting XAUUSD Scalping Bot...")
    
    # Initialize components
    mt5_conn = MT5Connector(
        login=config.MT5_LOGIN,
        password=config.MT5_PASSWORD,
        server=config.MT5_SERVER,
        path=config.MT5_PATH
    )
    
    if not mt5_conn.connect():
        print("Failed to connect to MT5. Exiting.")
        return

    sats_logic = SATSLogic(config)
    risk_mgmt = RiskManagement(config, mt5_conn)
    data_logger = DataLogger(config)
    risk_filters = RiskFilters(config, mt5_conn)
    
    strategy = StrategyExecution(
        config=config,
        mt5_connector=mt5_conn,
        sats_logic=sats_logic,
        risk_management=risk_mgmt,
        data_logger=data_logger
    )

    print("Bot is running. Press Ctrl+C to stop.")
    
    try:
        while True:
            # 1. Check if trading is allowed by filters
            if risk_filters.is_trading_allowed():
                # 2. Run strategy iteration
                strategy.run_iteration()
            else:
                print("Trading currently paused by risk filters.")
            
            # 3. Wait for next M5 bar (simplified)
            # In production, use a more precise timer aligned with bar close
            time.sleep(60) # Check every minute
            
    except KeyboardInterrupt:
        print("Stopping bot...")
    finally:
        mt5_conn.disconnect()

if __name__ == "__main__":
    main()
