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
    print("=" * 60)
    print("  XAUUSD Scalping Bot — Starting Up")
    print("=" * 60)

    # Initialize MT5 connector
    mt5_conn = MT5Connector(
        login=config.MT5_LOGIN,
        password=config.MT5_PASSWORD,
        server=config.MT5_SERVER,
        path=config.MT5_PATH
    )

    # Keep retrying until connected
    while not mt5_conn.connect(auto_launch=True, max_retries=5, retry_delay=5):
        print("[BOT] Connection failed. Will retry in 30 seconds... (Press Ctrl+C to quit)")
        try:
            time.sleep(30)
        except KeyboardInterrupt:
            print("[BOT] Interrupted by user. Exiting.")
            return

    # Once connected, initialize strategy components
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

    print("\n[BOT] Bot is running Baby. Press Ctrl+C to stop.\n")

    try:
        while True:
            # 1. Check if trading is allowed by filters
            if risk_filters.is_trading_allowed():
                # 2. Run strategy iteration
                strategy.run_iteration()
            else:
                print("[BOT] Trading currently paused by risk filters.")

            # 3. Wait for next check (every 60 seconds)
            time.sleep(60)

    except KeyboardInterrupt:
        print("\n[BOT] Stopping bot...")
    finally:
        mt5_conn.disconnect()
        print("[BOT] Shutdown complete.")

if __name__ == "__main__":
    main()
