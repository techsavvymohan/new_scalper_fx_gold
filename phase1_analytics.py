import os
import sys
import argparse
import pandas as pd
import numpy as np

def calculate_win_rate(group):
    """Calculate the percentage of trades with profit > 0."""
    total_trades = len(group)
    if total_trades == 0:
        return 0.0
    series = group['profit'] if isinstance(group, pd.DataFrame) else group
    winning_trades = (series > 0).sum()
    return winning_trades / total_trades

def calculate_profit_factor(group):
    """Calculate profit factor (gross profits / gross losses)."""
    gross_profits = group[group['profit'] > 0]['profit'].sum()
    gross_losses = abs(group[group['profit'] < 0]['profit'].sum())
    if gross_losses == 0:
        if gross_profits > 0:
            return float('inf')
        return 0.0
    return gross_profits / gross_losses

def format_rr(val):
    """Format R:R achieved to a clean string, handling NaNs gracefully."""
    if pd.isna(val) or (isinstance(val, float) and np.isnan(val)):
        return "N/A"
    return f"{val:,.2f}R"

def run_analytics(file_path, exclude_manual=False):
    print("=" * 70)
    print("SATS V2 POST-TRADE ANALYTICS SUMMARY")
    print(f"Target File: {file_path}")
    print("=" * 70)

    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' does not exist.")
        return

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    if df.empty:
        print("Warning: The trade log file is empty. No trades to analyze.")
        return

    # Filter out active/open trades or rows without profit/exit information
    df_closed = df[df['profit'].notna() & (df['status'] != 'OPEN')].copy()

    if exclude_manual and 'exit_type' in df_closed.columns:
        manual_count = (df_closed['exit_type'] == 'MANUAL').sum()
        df_closed = df_closed[df_closed['exit_type'] != 'MANUAL']
        print(f"Excluded {manual_count} manually closed trades from analytics.")

    total_all = len(df)
    total_closed = len(df_closed)
    print(f"Total Logged Trades: {total_all} (Closed: {total_closed}, Open/Unsynced: {total_all - total_closed})")
    
    if total_closed == 0:
        print("Warning: No closed trades available for analysis.")
        return

    # 1. Exit Diagnostics
    print("\n" + "-" * 50)
    print("EXIT DIAGNOSTICS")
    print("-" * 50)
    exit_diag = df_closed.groupby('exit_type').agg(
        Count=('profit', 'count'),
        Avg_Profit=('profit', 'mean'),
        Avg_RR=('rr_achieved', 'mean')
    )
    # Add a Total row
    total_row = pd.DataFrame({
        'Count': [total_closed],
        'Avg_Profit': [df_closed['profit'].mean()],
        'Avg_RR': [df_closed['rr_achieved'].mean()]
    }, index=['TOTAL'])
    exit_diag = pd.concat([exit_diag, total_row])
    
    # Format
    exit_diag['Avg_Profit'] = exit_diag['Avg_Profit'].map("${:,.2f}".format)
    exit_diag['Avg_RR'] = exit_diag['Avg_RR'].apply(format_rr)
    print(exit_diag.to_string())


    # 2. Context Heatmap (Win Rate % by Session & Regime)
    print("\n" + "-" * 50)
    print("SESSION vs REGIME WIN RATE HEATMAP")
    print("-" * 50)
    
    def win_rate_pivot_func(x):
        return f"{calculate_win_rate(x):.1%}"
        
    try:
        heatmap = df_closed.pivot_table(
            index='session',
            columns='regime',
            values='profit',
            aggfunc=win_rate_pivot_func,
            fill_value="0.0%"
        )
        print(heatmap.to_string())
    except Exception as e:
        print(f"Could not build session/regime heatmap: {e}")


    # 2b. Profit Factor & Win Rate by Regime
    print("\n" + "-" * 50)
    print("REGIME PERFORMANCE METRICS")
    print("-" * 50)
    
    regime_metrics = []
    for regime_name, group in df_closed.groupby('regime'):
        count = len(group)
        win_rate = calculate_win_rate(group)
        pf = calculate_profit_factor(group)
        avg_profit = group['profit'].mean()
        regime_metrics.append({
            'Regime': regime_name,
            'Count': count,
            'Win Rate': f"{win_rate:.1%}",
            'Profit Factor': f"{pf:.2f}" if pf != float('inf') else "inf",
            'Avg Profit': f"${avg_profit:,.2f}"
        })
    df_regime = pd.DataFrame(regime_metrics).set_index('Regime')
    print(df_regime.to_string())


    # 3. Confidence Curve Analysis
    print("\n" + "-" * 50)
    print("CONFIDENCE CURVE ANALYSIS")
    print("-" * 50)
    if 'confidence_score' in df_closed.columns:
        bins = [-float('inf'), 55, 60, 65, 70, float('inf')]
        labels = ['< 55', '55-60', '60-65', '65-70', '70+']
        df_closed['confidence_bucket'] = pd.cut(df_closed['confidence_score'], bins=bins, labels=labels, right=False)
        
        conf_metrics = []
        for bucket, group in df_closed.groupby('confidence_bucket', observed=False):
            count = len(group)
            win_rate = calculate_win_rate(group)
            pf = calculate_profit_factor(group)
            avg_rr = group['rr_achieved'].mean() if 'rr_achieved' in group.columns else np.nan
            conf_metrics.append({
                'Confidence': bucket,
                'Count': count,
                'Win Rate': f"{win_rate:.1%}",
                'Profit Factor': f"{pf:.2f}" if pf != float('inf') else "inf",
                'Avg R:R': format_rr(avg_rr)
            })
        df_conf = pd.DataFrame(conf_metrics).set_index('Confidence')
        print(df_conf.to_string())
    else:
        print("confidence_score column not found in log.")


    # 4. Location Interaction
    print("\n" + "-" * 50)
    print("KEY LEVEL PROXIMITY ANALYSIS (near PDH/PDL < 10 pips)")
    print("-" * 50)
    
    # Check if necessary columns exist
    if 'dist_to_pdh_pips' in df_closed.columns and 'dist_to_pdl_pips' in df_closed.columns:
        # Fill NaN with large distance so they aren't marked as "near"
        d_pdh = df_closed['dist_to_pdh_pips'].fillna(9999.0)
        d_pdl = df_closed['dist_to_pdl_pips'].fillna(9999.0)
        
        df_closed['near_level'] = (d_pdh < 10.0) | (d_pdl < 10.0)
        
        loc_metrics = []
        for near, group in df_closed.groupby('near_level'):
            count = len(group)
            win_rate = calculate_win_rate(group)
            pf = calculate_profit_factor(group)
            avg_rr = group['rr_achieved'].mean()
            loc_metrics.append({
                'Near Level (<10 pips)': "YES" if near else "NO",
                'Count': count,
                'Win Rate': f"{win_rate:.1%}",
                'Profit Factor': f"{pf:.2f}" if pf != float('inf') else "inf",
                'Avg R:R': format_rr(avg_rr)
            })
        df_loc = pd.DataFrame(loc_metrics).set_index('Near Level (<10 pips)')
        print(df_loc.to_string())
    else:
        print("dist_to_pdh_pips or dist_to_pdl_pips columns not found in log.")


    # 5. Hourly Analysis
    print("\n" + "-" * 50)
    print("HOURLY PERFORMANCE ANALYSIS (UTC)")
    print("-" * 50)
    if 'entry_hour_utc' in df_closed.columns and df_closed['entry_hour_utc'].notna().any():
        hour_metrics = []
        for hour, group in df_closed.groupby('entry_hour_utc'):
            count = len(group)
            win_rate = calculate_win_rate(group)
            pf = calculate_profit_factor(group)
            avg_profit = group['profit'].mean()
            hour_metrics.append({
                'Hour (UTC)': int(hour),
                'Count': count,
                'Win Rate': f"{win_rate:.1%}",
                'Profit Factor': f"{pf:.2f}" if pf != float('inf') else "inf",
                'Avg Profit': f"${avg_profit:,.2f}"
            })
        df_hour = pd.DataFrame(hour_metrics).set_index('Hour (UTC)')
        # Sort by hour
        df_hour = df_hour.sort_index()
        print(df_hour.to_string())
    else:
        # Fallback to parsing from entry_time if it exists
        if 'entry_time' in df_closed.columns and df_closed['entry_time'].notna().any():
            try:
                df_closed['parsed_hour'] = pd.to_datetime(df_closed['entry_time']).dt.hour
                hour_metrics = []
                for hour, group in df_closed.groupby('parsed_hour'):
                    count = len(group)
                    win_rate = calculate_win_rate(group)
                    pf = calculate_profit_factor(group)
                    avg_profit = group['profit'].mean()
                    hour_metrics.append({
                        'Hour (UTC - parsed)': int(hour),
                        'Count': count,
                        'Win Rate': f"{win_rate:.1%}",
                        'Profit Factor': f"{pf:.2f}" if pf != float('inf') else "inf",
                        'Avg Profit': f"${avg_profit:,.2f}"
                    })
                df_hour = pd.DataFrame(hour_metrics).set_index('Hour (UTC - parsed)').sort_index()
                print(df_hour.to_string())
            except Exception as e:
                print(f"Could not parse entry_time for hourly analysis: {e}")
        else:
            print("No valid entry_hour_utc or entry_time found in log.")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SATS V2 Post-Trade Analytics")
    parser.add_argument(
        "--file", 
        type=str, 
        default=os.path.join("data", "trade_log.csv"), 
        help="Path to the trade log CSV file"
    )
    parser.add_argument(
        "--exclude-manual",
        action="store_true",
        help="Exclude manually closed trades (exit_type == 'MANUAL') from analytics"
    )
    args = parser.parse_args()
    run_analytics(args.file, exclude_manual=args.exclude_manual)
