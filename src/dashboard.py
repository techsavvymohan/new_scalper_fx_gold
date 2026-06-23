import pandas as pd
import os
import sys

# Ensure config can be imported if running directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
from src.report_generator import ReportGenerator

def display_dashboard(exclude_manual=False):
    log_path = os.path.join("data", "trade_log.csv")
    if not os.path.exists(log_path):
        print("No trade logs found.")
        return

    df = pd.read_csv(log_path)
    if df.empty:
        print("Trade log is empty.")
        return

    # Filter out manual trades if requested
    if exclude_manual and 'exit_type' in df.columns:
        manual_count = (df['exit_type'] == 'MANUAL').sum()
        df = df[df['exit_type'] != 'MANUAL']
        print(f"Excluding {manual_count} manually closed trades from the dashboard view.")

    print("=== XAUUSD Scalping Bot Performance Dashboard ===")
    print(f"Total Trades: {len(df)}")
    
    if 'profit' in df.columns:
        # calculate sum of completed ones or all
        total_profit = df['profit'].fillna(0.0).sum()
        closed_trades = df[df['status'] == 'CLOSED']
        win_rate = (closed_trades['profit'] > 0).mean() if len(closed_trades) > 0 else 0.0
        print(f"Total Profit: {total_profit:.2f}")
        print(f"Win Rate (Closed): {win_rate:.2%}")
    
    print("\nRecent Trades:")
    # Dynamically select columns that exist in the csv
    cols = ['entry_time', 'direction', 'entry_price', 'status', 'profit', 'exit_type']
    existing_cols = [c for c in cols if c in df.columns]
    print(df.tail(10)[existing_cols])
    print("==================================================")
    
    print("\nGenerating Quantitative Analytics Report...")
    rg = ReportGenerator(config, exclude_manual=exclude_manual)
    print(rg.generate_report())

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Performance Dashboard")
    parser.add_argument("--exclude-manual", action="store_true", help="Exclude manual trades from analytics")
    args = parser.parse_args()
    display_dashboard(exclude_manual=args.exclude_manual)
