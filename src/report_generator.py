import pandas as pd
import numpy as np
import os

class ReportGenerator:
    def __init__(self, config, exclude_manual=False):
        self.config = config
        self.log_path = os.path.join("data", self.config.TRADE_LOG_FILE)
        self.exclude_manual = exclude_manual

    def load_data(self):
        if not os.path.exists(self.log_path):
            return None
        try:
            df = pd.read_csv(self.log_path)
            # Filter out open trades for metrics, keep closed ones
            df_closed = df[df['status'] == 'CLOSED'].copy()
            # Exclude manual trades if requested
            if self.exclude_manual and 'exit_type' in df_closed.columns:
                df_closed = df_closed[df_closed['exit_type'] != 'MANUAL']
            # Ensure profit is numeric
            df_closed['profit'] = pd.to_numeric(df_closed['profit'], errors='coerce').fillna(0.0)
            return df_closed
        except Exception as e:
            print(f"Error loading trade logs for report: {e}")
            return None

    def calculate_max_drawdown(self, df):
        if df is None or df.empty:
            return 0.0
        cum_profit = df['profit'].cumsum()
        cum_max = cum_profit.cummax()
        # If no profit has been made, baseline at 0
        cum_max = np.maximum(0.0, cum_max)
        drawdown = cum_max - cum_profit
        return float(drawdown.max())

    def generate_report(self):
        df = self.load_data()
        if df is None or df.empty:
            return "No closed trade history available to generate report."

        total_trades = len(df)
        wins = df[df['profit'] > 0]
        losses = df[df['profit'] < 0]
        win_count = len(wins)
        loss_count = len(losses)
        
        win_rate = win_count / total_trades if total_trades > 0 else 0.0
        avg_winner = wins['profit'].mean() if win_count > 0 else 0.0
        avg_loser = losses['profit'].mean() if loss_count > 0 else 0.0
        
        gross_profit = wins['profit'].sum()
        gross_loss = abs(losses['profit'].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else (gross_profit if gross_profit > 0 else 1.0)
        expectancy = (win_rate * avg_winner) + ((1.0 - win_rate) * avg_loser)
        max_dd = self.calculate_max_drawdown(df)
        net_profit = df['profit'].sum()

        # Additional headline metrics
        avg_confidence = pd.to_numeric(df.get('confidence_score', pd.Series(dtype=float)), errors='coerce').mean()
        avg_box_size   = pd.to_numeric(df.get('box_size',         pd.Series(dtype=float)), errors='coerce').mean()

        report = []
        report.append("======================================================================")
        report.append("                   QUANT PERFORMANCE ANALYSIS REPORT                  ")
        report.append("======================================================================")
        report.append(f"Total Trades Analyzed: {total_trades}")
        report.append(f"Net Profit:            ${net_profit:.2f}")
        report.append(f"Win Rate:              {win_rate:.2%}")
        report.append(f"Profit Factor:         {profit_factor:.2f}")
        report.append(f"Expectancy (Per Trade):${expectancy:.2f}")
        report.append(f"Max Drawdown:          ${max_dd:.2f}")
        report.append(f"Average Winner:        ${avg_winner:.2f} (Count: {win_count})")
        report.append(f"Average Loser:         ${avg_loser:.2f} (Count: {loss_count})")
        if not pd.isna(avg_confidence):
            report.append(f"Avg Confidence Score:  {avg_confidence:.1f}/100")
        if not pd.isna(avg_box_size):
            report.append(f"Avg Box Size:          {avg_box_size:.4f}")
        report.append("----------------------------------------------------------------------")

        # 0. Exit Type Aggregate Breakdown (new — Phase 0 requirement)
        report.append("\n[EXIT TYPE BREAKDOWN]")
        if 'exit_type' in df.columns:
            exit_types = ['SL', 'TP', 'TIMEOUT']
            for etype in exit_types:
                edf = df[df['exit_type'] == etype]
                e_count = len(edf)
                if e_count > 0:
                    e_pct    = e_count / total_trades
                    e_wins   = len(edf[edf['profit'] > 0])
                    e_wr     = e_wins / e_count
                    e_net    = edf['profit'].sum()
                    e_avg    = edf['profit'].mean()
                    report.append(
                        f"  {etype:<8} | Count: {e_count:<3} ({e_pct:.1%}) | "
                        f"Win Rate: {e_wr:<6.1%} | Avg: ${e_avg:>7.2f} | Net: ${e_net:.2f}"
                    )
                else:
                    report.append(f"  {etype:<8} | No trades recorded")
            # Unclassified / None
            unclassified = df[~df['exit_type'].isin(exit_types)]
            if not unclassified.empty:
                report.append(f"  {'OTHER':<8} | Count: {len(unclassified)} | Net: ${unclassified['profit'].sum():.2f}")
        else:
            report.append("  [WARN] 'exit_type' column not in trade log.")


        # 1. Session Analytics
        report.append("\n[SESSION ANALYTICS]")
        sessions = ['Asia', 'London', 'Overlap', 'NewYork']
        session_stats = []
        for s in sessions:
            sdf = df[df['session'] == s]
            s_trades = len(sdf)
            if s_trades > 0:
                s_wins = len(sdf[sdf['profit'] > 0])
                s_win_rate = s_wins / s_trades
                s_gross_profit = sdf[sdf['profit'] > 0]['profit'].sum()
                s_gross_loss = abs(sdf[sdf['profit'] < 0]['profit'].sum())
                s_pf = s_gross_profit / s_gross_loss if s_gross_loss > 0 else (s_gross_profit if s_gross_profit > 0 else 1.0)
                s_net = sdf['profit'].sum()
                report.append(f"  {s:<8} | Trades: {s_trades:<3} | Win Rate: {s_win_rate:<6.1%} | PF: {s_pf:<5.2f} | Net: ${s_net:<7.2f}")
                session_stats.append({'session': s, 'trades': s_trades, 'win_rate': s_win_rate, 'pf': s_pf, 'net': s_net})
            else:
                report.append(f"  {s:<8} | No trades recorded")

        # 2. Regime Analytics
        report.append("\n[REGIME ANALYTICS]")
        regimes = ['TRENDING', 'RANGING', 'DEAD', 'EXPLOSIVE']
        regime_stats = []
        for r in regimes:
            rdf = df[df['regime'] == r]
            r_trades = len(rdf)
            if r_trades > 0:
                r_wins = len(rdf[rdf['profit'] > 0])
                r_win_rate = r_wins / r_trades
                r_gross_profit = rdf[rdf['profit'] > 0]['profit'].sum()
                r_gross_loss = abs(rdf[rdf['profit'] < 0]['profit'].sum())
                r_pf = r_gross_profit / r_gross_loss if r_gross_loss > 0 else (r_gross_profit if r_gross_profit > 0 else 1.0)
                r_net = rdf['profit'].sum()
                report.append(f"  {r:<9} | Trades: {r_trades:<3} | Win Rate: {r_win_rate:<6.1%} | PF: {r_pf:<5.2f} | Net: ${r_net:<7.2f}")
                regime_stats.append({'regime': r, 'trades': r_trades, 'win_rate': r_win_rate, 'pf': r_pf, 'net': r_net})
            else:
                report.append(f"  {r:<9} | No trades recorded")

        # 3. Dynamic Breakout Quality Threshold Analysis
        report.append("\n[DYNAMIC BREAKOUT PROBABILITY SENSITIVITY]")
        thresholds = [0.60, 0.65, 0.70, 0.75]
        for t in thresholds:
            tdf = df[df['breakout_prob'] >= t]
            t_trades = len(tdf)
            if t_trades > 0:
                t_wins = len(tdf[tdf['profit'] > 0])
                t_win_rate = t_wins / t_trades
                t_gross_profit = tdf[tdf['profit'] > 0]['profit'].sum()
                t_gross_loss = abs(tdf[tdf['profit'] < 0]['profit'].sum())
                t_pf = t_gross_profit / t_gross_loss if t_gross_loss > 0 else (t_gross_profit if t_gross_profit > 0 else 1.0)
                report.append(f"  Prob >= {t:<4.0%} | Trades: {t_trades:<3} | Win Rate: {t_win_rate:<6.1%} | PF: {t_pf:<5.2f}")
            else:
                report.append(f"  Prob >= {t:<4.0%} | No trades qualified")

        # 4. Confidence Score Analysis
        report.append("\n[CONFIDENCE SCORE BUCKETS]")
        if 'confidence_score' in df.columns:
            buckets = [(0, 50), (50, 60), (60, 70), (70, 100)]
            for low, high in buckets:
                bdf = df[(df['confidence_score'] >= low) & (df['confidence_score'] < high)]
                b_trades = len(bdf)
                if b_trades > 0:
                    b_wins = len(bdf[bdf['profit'] > 0])
                    b_win_rate = b_wins / b_trades
                    b_net = bdf['profit'].sum()
                    report.append(f"  Score {low}-{high:<3} | Trades: {b_trades:<3} | Win Rate: {b_win_rate:<6.1%} | Net: ${b_net:.2f}")
                else:
                    report.append(f"  Score {low}-{high:<3} | No trades qualified")

        # 5. Backtest Comparison Table (Simulated filtering on current log)
        report.append("\n[FILTER SIMULATION COMPARISON]")
        report.append("  " + "-" * 75)
        report.append(f"  {'Configuration Group':<32} | {'Trades':<6} | {'Win Rate':<8} | {'PF':<5} | {'Net Profit':<10}")
        report.append("  " + "-" * 75)

        # Base Group A
        report.append(f"  {'A) Base (Current Bot)':<32} | {total_trades:<6} | {win_rate:<8.1%} | {profit_factor:<5.2f} | ${net_profit:<10.2f}")

        # Regime Filter Group B (Exclude DEAD)
        allowed_regimes = getattr(self.config, 'ALLOWED_REGIMES', ['TRENDING', 'RANGING', 'EXPLOSIVE'])
        b_df = df[df['regime'].fillna('RANGING').isin(allowed_regimes)]
        b_trades = len(b_df)
        b_win_rate = len(b_df[b_df['profit'] > 0]) / b_trades if b_trades > 0 else 0.0
        b_gp = b_df[b_df['profit'] > 0]['profit'].sum()
        b_gl = abs(b_df[b_df['profit'] < 0]['profit'].sum())
        b_pf = b_gp / b_gl if b_gl > 0 else (b_gp if b_gp > 0 else 1.0)
        b_net = b_df['profit'].sum()
        report.append(f"  {'B) Regime Filter Enabled':<32} | {b_trades:<6} | {b_win_rate:<8.1%} | {b_pf:<5.2f} | ${b_net:<10.2f}")

        # Session Filter Group C (Exclude Asia or specific disabled ones)
        disabled_sessions = getattr(self.config, 'DISABLED_SESSIONS', [])
        c_df = df[~df['session'].fillna('Overlap').isin(disabled_sessions)]
        c_trades = len(c_df)
        c_win_rate = len(c_df[c_df['profit'] > 0]) / c_trades if c_trades > 0 else 0.0
        c_gp = c_df[c_df['profit'] > 0]['profit'].sum()
        c_gl = abs(c_df[c_df['profit'] < 0]['profit'].sum())
        c_pf = c_gp / c_gl if c_gl > 0 else (c_gp if c_gp > 0 else 1.0)
        c_net = c_df['profit'].sum()
        report.append(f"  {'C) Session Filter Enabled':<32} | {c_trades:<6} | {c_win_rate:<8.1%} | {c_pf:<5.2f} | ${c_net:<10.2f}")

        # Both Enabled Group D
        d_df = df[df['regime'].fillna('RANGING').isin(allowed_regimes) & (~df['session'].fillna('Overlap').isin(disabled_sessions))]
        d_trades = len(d_df)
        d_win_rate = len(d_df[d_df['profit'] > 0]) / d_trades if d_trades > 0 else 0.0
        d_gp = d_df[d_df['profit'] > 0]['profit'].sum()
        d_gl = abs(d_df[d_df['profit'] < 0]['profit'].sum())
        d_pf = d_gp / d_gl if d_gl > 0 else (d_gp if d_gp > 0 else 1.0)
        d_net = d_df['profit'].sum()
        report.append(f"  {'D) Both Filters Enabled':<32} | {d_trades:<6} | {d_win_rate:<8.1%} | {d_pf:<5.2f} | ${d_net:<10.2f}")
        report.append("  " + "-" * 75)

        # 6. Strategic Recommendations & Diagnosis
        report.append("\n[STRATEGIC DIAGNOSIS & REVIEWS]")
        diagnoses = []
        if win_rate < 0.40:
            diagnoses.append("- SIGNAL QUALITY: The overall win rate is below 40%. Signal accuracy needs enhancement, or you are taking high-noise trades.")
        if abs(avg_loser) > 1.8 * abs(avg_winner) and avg_winner > 0:
            diagnoses.append(f"- STOP LOSS SIZE: Your average loss (${abs(avg_loser):.2f}) is significantly larger than your average win (${avg_winner:.2f}). Consider tightening Stop Losses or executing trailing stops earlier.")
        if profit_factor < 1.0:
            diagnoses.append("- NEGATIVE EXPECTANCY: The strategy has negative expectancy. Review session stats above to see if a specific time window is draining profits.")

        # Best/worst regime (explicit — always shown)
        if regime_stats:
            best_regime  = max(regime_stats, key=lambda x: x['net'])
            worst_regime = min(regime_stats, key=lambda x: x['net'])
            diagnoses.append(
                f"- BEST REGIME:  '{best_regime['regime']}' "
                f"({best_regime['trades']} trades, {best_regime['win_rate']:.1%} WR, net ${best_regime['net']:.2f})"
            )
            diagnoses.append(
                f"- WORST REGIME: '{worst_regime['regime']}' "
                f"({worst_regime['trades']} trades, {worst_regime['win_rate']:.1%} WR, net ${worst_regime['net']:.2f})"
            )
            if worst_regime['net'] < 0:
                diagnoses.append(
                    f"  → Consider removing '{worst_regime['regime']}' from ALLOWED_REGIMES "
                    f"once ≥30 trades in that bucket are available."
                )

        # Best/worst session (explicit — always shown)
        if session_stats:
            best_session  = max(session_stats, key=lambda x: x['net'])
            worst_session = min(session_stats, key=lambda x: x['net'])
            diagnoses.append(
                f"- BEST SESSION:  '{best_session['session']}' "
                f"({best_session['trades']} trades, {best_session['win_rate']:.1%} WR, net ${best_session['net']:.2f})"
            )
            diagnoses.append(
                f"- WORST SESSION: '{worst_session['session']}' "
                f"({worst_session['trades']} trades, {worst_session['win_rate']:.1%} WR, net ${worst_session['net']:.2f})"
            )
            if worst_session['net'] < 0:
                diagnoses.append(
                    f"  → Consider adding '{worst_session['session']}' to DISABLED_SESSIONS "
                    f"once ≥30 trades in that session are available."
                )

        if not diagnoses:
            diagnoses.append("- All performance metrics are within normal, healthy parameters. System shows active edge.")
            
        report.extend(diagnoses)
        report.append("======================================================================\n")
        
        return "\n".join(report)

