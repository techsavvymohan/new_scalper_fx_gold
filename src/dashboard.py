import pandas as pd
import os

def display_dashboard():
    log_path = os.path.join("data", "trade_log.csv")
    if not os.path.exists(log_path):
        print("No trade logs found.")
        return

    df = pd.read_csv(log_path)
    if df.empty:
        print("Trade log is empty.")
        return

    print("=== XAUUSD Scalping Bot Performance Dashboard ===")
    print(f"Total Trades: {len(df)}")
    
    if 'profit' in df.columns:
        total_profit = df['profit'].sum()
        win_rate = (df['profit'] > 0).mean()
        print(f"Total Profit: {total_profit:.2f}")
        print(f"Win Rate: {win_rate:.2%}")
    
    print("\nRecent Trades:")
    print(df.tail(10)[['entry_time', 'direction', 'entry_price', 'status', 'profit']])
    print("==================================================")

if __name__ == "__main__":
    display_dashboard()
