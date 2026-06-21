import MetaTrader5 as mt5
from datetime import datetime
from src.breakout_probability import BreakoutProbability
from src.regime_detection import RegimeDetection

class StrategyExecution:
    def __init__(self, config, mt5_connector, sats_logic, risk_management, data_logger):
        self.config = config
        self.mt5_connector = mt5_connector
        self.sats_logic = sats_logic
        self.risk_management = risk_management
        self.data_logger = data_logger
        self.breakout_prob = BreakoutProbability(config)
        self.regime_detector = RegimeDetection(config)

    def get_current_session(self):
        from datetime import datetime, timezone
        utc_hour = datetime.now(timezone.utc).hour
        
        # Overlap: 1 PM to 4 PM UTC
        if 13 <= utc_hour < 16:
            return 'OVERLAP'
        # London: 8 AM to 1 PM UTC
        elif 8 <= utc_hour < 13:
            return 'LONDON'
        # New York: 4 PM to 10 PM UTC
        elif 16 <= utc_hour < 22:
            return 'NEW_YORK'
        # Asia: 10 PM to 8 AM UTC
        else:
            return 'ASIA'

    def run_iteration(self):
        # Map string timeframes to MT5 constants
        tf_map = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "M30": mt5.TIMEFRAME_M30,
            "H1": mt5.TIMEFRAME_H1
        }
        macro_tf = tf_map.get(getattr(self.config, 'MACRO_TREND_TIMEFRAME', 'M15'), mt5.TIMEFRAME_M15)
        conf_tf = tf_map.get(getattr(self.config, 'CONF_TREND_TIMEFRAME', 'M5'), mt5.TIMEFRAME_M5)
        entry_tf = tf_map.get(getattr(self.config, 'ENTRY_TIMEFRAME', 'M1'), mt5.TIMEFRAME_M1)

        # 1. Retrieve market data
        df_macro = self.mt5_connector.get_market_data(self.config.SYMBOL, macro_tf, 200)
        df_conf = self.mt5_connector.get_market_data(self.config.SYMBOL, conf_tf, 200)
        df_entry = self.mt5_connector.get_market_data(self.config.SYMBOL, entry_tf, 200)

        if df_macro is None or df_conf is None or df_entry is None:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error: Failed to retrieve market data for {self.config.SYMBOL}")
            return

        # 2. Calculate SATS states
        df_macro = self.sats_logic.get_signals(df_macro)
        df_conf = self.sats_logic.get_signals(df_conf)
        df_entry = self.sats_logic.get_signals(df_entry)

        macro_trend = df_macro['trend'].iloc[-1]
        conf_trend = df_conf['trend'].iloc[-1]
        entry_signal = df_entry['signal'].iloc[-1]
        entry_atr = self.sats_logic.calculate_atr(df_entry, self.config.ATR_LENGTH).iloc[-1]
        entry_atr_avg = self.sats_logic.calculate_atr(df_entry, 100).iloc[-1]
        entry_er = self.sats_logic.calculate_efficiency_ratio(df_entry, self.config.EFFICIENCY_WINDOW).iloc[-1]
        entry_tqi = self.sats_logic.calculate_tqi(df_entry).iloc[-1]

        # M15 Trend Engine checks
        macro_tqi = self.sats_logic.calculate_tqi(df_macro).iloc[-1]
        macro_er = self.sats_logic.calculate_efficiency_ratio(df_macro, self.config.EFFICIENCY_WINDOW).iloc[-1]
        macro_atr = self.sats_logic.calculate_atr(df_macro, self.config.ATR_LENGTH).iloc[-1]
        macro_atr_avg = self.sats_logic.calculate_atr(df_macro, 100).iloc[-1]
        macro_atr_ratio = macro_atr / macro_atr_avg if macro_atr_avg > 0 else 1.0
        
        macro_filter_ok = (macro_tqi >= 0.60) and (macro_er >= 0.50) and (macro_atr_ratio >= 1.0)
        entry_filter_ok = (entry_tqi >= 0.60)

        # 2.5. Calculate Breakout Probabilities
        new_high_prob = 1.0
        new_low_prob = 1.0
        if getattr(self.config, 'BREAKOUT_PROBABILITY_ENABLED', False):
            probs = self.breakout_prob.calculate_probabilities(df_entry)
            new_high_prob = probs.get('new_high_prob', 0.5)
            new_low_prob = probs.get('new_low_prob', 0.5)

        # Calculate session, regime, and confidence score
        session = self.get_current_session()
        regime, norm_vol, norm_trend, raw_atr_ratio, raw_er = self.regime_detector.get_regime_detailed(df_entry)
        
        active_breakout_prob = new_high_prob if entry_signal == 1 else (new_low_prob if entry_signal == -1 else 0.5)
        atr_ratio = entry_atr / entry_atr_avg if entry_atr_avg > 0 else 1.0
        atr_regime_score = min(1.0, atr_ratio)
        confidence_score = (0.4 * entry_tqi + 0.3 * entry_er + 0.2 * atr_regime_score + 0.1 * active_breakout_prob) * 100.0

        # Log current status/decision data
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        trend_desc = {1: "Bullish", -1: "Bearish", 0: "Neutral"}
        macro_desc = trend_desc.get(macro_trend, "Neutral")
        conf_desc = trend_desc.get(conf_trend, "Neutral")
        
        print(f"\n[{now_str}] --- Iteration Start ---")
        print(f"[{now_str}] Symbol: {self.config.SYMBOL} | Price: {df_entry['close'].iloc[-1]:.2f} | ATR: {entry_atr:.2f} | VolRatio: {atr_ratio:.2f}")
        print(f"[{now_str}] Market Regime: {regime} (Vol Z: {norm_vol:.2f}, Trend Z: {norm_trend:.2f}) | Session: {session} | TQI: {entry_tqi:.2f} | Confidence: {confidence_score:.1f}")
        print(f"[{now_str}] Trend Confluence Check:")
        print(f"   - Macro Trend (M15): {macro_desc} (TQI: {macro_tqi:.2f}, ER: {macro_er:.2f}, ATR_Ratio: {macro_atr_ratio:.2f}, OK: {macro_filter_ok})")
        print(f"   - Intermediate (M5): {conf_desc}")
        print(f"   - Entry Timeframe Signal (M5): {'BUY' if entry_signal == 1 else 'SELL' if entry_signal == -1 else 'No Signal (0)'}")
        
        if getattr(self.config, 'BREAKOUT_PROBABILITY_ENABLED', False):
            min_prob = getattr(self.config, 'BREAKOUT_MIN_PROBABILITY_THRESHOLD', 0.60)
            print(f"[{now_str}] Breakout Probability: New High: {new_high_prob:.2%} | New Low: {new_low_prob:.2%} (Min Req: {min_prob:.2%})")

        # 3. Check for entries
        if entry_signal != 0:
            min_prob = getattr(self.config, 'BREAKOUT_MIN_PROBABILITY_THRESHOLD', 0.60)
            if entry_signal == 1:
                if conf_trend == 1 and macro_trend == 1: # Bullish Confluence
                    # Apply Session Filter
                    disabled_sessions = getattr(self.config, 'DISABLED_SESSIONS', [])
                    # Apply Regime Filter
                    allowed_regimes = getattr(self.config, 'ALLOWED_REGIMES', ['TRENDING', 'RANGING', 'DEAD', 'EXPLOSIVE'])
                    # Apply Confidence Filter
                    min_confidence = getattr(self.config, 'MIN_CONFIDENCE_SCORE', 55.0)

                    is_session_disabled = session in disabled_sessions or session.title() in disabled_sessions
                    
                    if is_session_disabled and getattr(self.config, 'SESSION_TEST_FILTER_ENABLED', False):
                        print(f"[{now_str}] BUY signal ignored: Session '{session}' is disabled.")
                    elif not macro_filter_ok:
                        print(f"[{now_str}] BUY signal ignored: M15 trend filter failed (TQI: {macro_tqi:.2f}, ER: {macro_er:.2f}, ATR_Ratio: {macro_atr_ratio:.2f})")
                    elif not entry_filter_ok:
                        print(f"[{now_str}] BUY signal ignored: M5 entry TQI filter failed (TQI: {entry_tqi:.2f})")
                    elif regime not in allowed_regimes:
                        print(f"[{now_str}] BUY signal ignored: Regime '{regime}' is not in allowed regimes.")
                    elif confidence_score < min_confidence:
                        print(f"[{now_str}] BUY signal ignored: Confidence score {confidence_score:.1f} < min {min_confidence:.1f}.")
                    elif new_high_prob >= min_prob:
                        print(f"[{now_str}] CONFLUENCE ALIGNED: Executing BUY order...")
                        self.execute_trade(mt5.ORDER_TYPE_BUY, df_entry.iloc[-1], entry_atr, macro_trend, session, regime, norm_vol, norm_trend, entry_tqi, atr_ratio, active_breakout_prob, confidence_score)
                    else:
                        print(f"[{now_str}] BUY signal filtered: Breakout probability of new high ({new_high_prob:.2%}) below threshold ({min_prob:.2%})")
                else:
                    print(f"[{now_str}] BUY signal ignored: Trends not aligned. M15: {macro_desc}, M5: {conf_desc}")
            elif entry_signal == -1:
                if conf_trend == -1 and macro_trend == -1: # Bearish Confluence
                    # Apply Session Filter
                    disabled_sessions = getattr(self.config, 'DISABLED_SESSIONS', [])
                    # Apply Regime Filter
                    allowed_regimes = getattr(self.config, 'ALLOWED_REGIMES', ['TRENDING', 'RANGING', 'DEAD', 'EXPLOSIVE'])
                    # Apply Confidence Filter
                    min_confidence = getattr(self.config, 'MIN_CONFIDENCE_SCORE', 55.0)

                    is_session_disabled = session in disabled_sessions or session.title() in disabled_sessions

                    if is_session_disabled and getattr(self.config, 'SESSION_TEST_FILTER_ENABLED', False):
                        print(f"[{now_str}] SELL signal ignored: Session '{session}' is disabled.")
                    elif not macro_filter_ok:
                        print(f"[{now_str}] SELL signal ignored: M15 trend filter failed (TQI: {macro_tqi:.2f}, ER: {macro_er:.2f}, ATR_Ratio: {macro_atr_ratio:.2f})")
                    elif not entry_filter_ok:
                        print(f"[{now_str}] SELL signal ignored: M5 entry TQI filter failed (TQI: {entry_tqi:.2f})")
                    elif regime not in allowed_regimes:
                        print(f"[{now_str}] SELL signal ignored: Regime '{regime}' is not in allowed regimes.")
                    elif confidence_score < min_confidence:
                        print(f"[{now_str}] SELL signal ignored: Confidence score {confidence_score:.1f} < min {min_confidence:.1f}.")
                    elif new_low_prob >= min_prob:
                        print(f"[{now_str}] CONFLUENCE ALIGNED: Executing SELL order...")
                        self.execute_trade(mt5.ORDER_TYPE_SELL, df_entry.iloc[-1], entry_atr, macro_trend, session, regime, norm_vol, norm_trend, entry_tqi, atr_ratio, active_breakout_prob, confidence_score)
                    else:
                        print(f"[{now_str}] SELL signal filtered: Breakout probability of new low ({new_low_prob:.2%}) below threshold ({min_prob:.2%})")
                else:
                    print(f"[{now_str}] SELL signal ignored: Trends not aligned. M15: {macro_desc}, M5: {conf_desc}")
        else:
            print(f"[{now_str}] No trade action taken (awaiting entry signal).")

        # 4. Monitor open positions and sync closed trades
        self.monitor_positions(df_entry, entry_tf)
        self.sync_closed_trades()

    def execute_trade(self, order_type, current_bar, atr, m15_trend, session, regime, norm_vol, norm_trend, tqi, atr_ratio, breakout_prob, confidence_score):
        symbol = self.config.SYMBOL
        entry_price = current_bar['close']
        
        direction_val = 1 if order_type == mt5.ORDER_TYPE_BUY else -1
        sl, tp = self.risk_management.calculate_sl_tp(symbol, direction_val, entry_price, atr)
        
        account_info = self.mt5_connector.get_account_info()
        risk_amount = self.risk_management.get_risk_amount(account_info.balance)
        sl_pips = abs(entry_price - sl)
        
        lot = self.risk_management.calculate_lot_size(symbol, risk_amount, sl_pips)
        
        if lot:
            result = self.mt5_connector.place_order(symbol, order_type, lot, price=entry_price, sl=sl, tp=tp, comment="SATS Scalper")
            if result:
                self.data_logger.log_trade({
                    "entry_time": datetime.now(),
                    "symbol": symbol,
                    "direction": "BUY" if order_type == mt5.ORDER_TYPE_BUY else "SELL",
                    "entry_price": result.price,
                    "sl": sl,
                    "tp": tp,
                    "lot": lot,
                    "m15_trend": m15_trend,
                    "status": "OPEN",
                    "ticket": result.order,
                    "session": session,
                    "regime": regime,
                    "regime_norm_vol": norm_vol,
                    "regime_norm_trend": norm_trend,
                    "tqi": tqi,
                    "atr_ratio": atr_ratio,
                    "volume_score": None,
                    "confidence_score": confidence_score,
                    "box_size": None,
                    "exit_type": None,
                    "rr_achieved": None,
                    "intended_entry_price": entry_price,
                    "realized_slippage": round(result.price - entry_price if order_type == mt5.ORDER_TYPE_BUY else entry_price - result.price, 2),
                    "breakout_prob": breakout_prob
                })

    def monitor_positions(self, df_signal, signal_tf):
        import MetaTrader5 as mt5
        positions = self.mt5_connector.get_open_positions(self.config.SYMBOL)
        
        # Load trade log to check original volumes
        import os
        import pandas as pd
        log_path = self.data_logger.log_path
        trade_log = None
        if os.path.exists(log_path):
            try:
                trade_log = pd.read_csv(log_path)
            except Exception:
                pass

        for pos in positions:
            if getattr(pos, 'magic', 0) != 123456:
                continue
                
            # Get original volume
            original_volume = pos.volume
            if trade_log is not None and not trade_log.empty:
                match = trade_log[trade_log['ticket'] == pos.ticket]
                if not match.empty:
                    original_volume = float(match['lot'].values[0])
            
            # Check for Partial TP1 and Breakeven Stop Move
            if self.config.TP_MODE == "FIXED":
                # 1R distance = distance from entry to original SL
                sl_dist = abs(pos.price_open - pos.sl)

                if pos.type == mt5.ORDER_TYPE_BUY:
                    tp1_price = pos.price_open + sl_dist       # +1R trigger
                    is_tp1_hit = pos.price_current >= tp1_price
                    breakeven_price = pos.price_open           # move SL to entry
                    sl_already_at_be = pos.sl >= breakeven_price - 0.01  # within 1 pip tolerance
                else:
                    tp1_price = pos.price_open - sl_dist
                    is_tp1_hit = pos.price_current <= tp1_price
                    breakeven_price = pos.price_open
                    sl_already_at_be = pos.sl <= breakeven_price + 0.01

                # --- Breakeven stop move (Phase 0 fix: prevents avg loser > avg winner) ---
                # Trigger: price has reached +1R. Move SL to entry price (breakeven).
                # Only fires once (guarded by sl_already_at_be).
                if is_tp1_hit and not sl_already_at_be:
                    print(f"[BE] Price at +1R for ticket {pos.ticket}. Moving SL to breakeven {breakeven_price:.2f}.")
                    self.mt5_connector.modify_position_sl(pos.ticket, breakeven_price)

                # --- Partial TP1 close (50% at +1R) ---
                # Only fires once (guarded by volume comparison)
                if is_tp1_hit and pos.volume >= original_volume - 0.001:
                    partial_lot = round(original_volume * 0.5, 2)
                    # Constrain to valid MT5 steps
                    symbol_info = self.mt5_connector.get_symbol_info(pos.symbol)
                    if symbol_info:
                        partial_lot = max(min(partial_lot, symbol_info.volume_max), symbol_info.volume_min)
                        partial_lot = round(partial_lot / symbol_info.volume_step) * symbol_info.volume_step

                    print(f"TP1 hit. Partially closing position {pos.ticket} for {partial_lot} lots.")
                    self.mt5_connector.close_partial_position(pos.ticket, partial_lot)

            # Check for Trade Timeout (100 bars on signal TF)
            try:
                open_time = datetime.fromtimestamp(pos.time)
                rates = mt5.copy_rates_from(pos.symbol, signal_tf, open_time, datetime.now())
                if rates is not None:
                    bars_elapsed = len(rates)
                    if bars_elapsed >= self.config.TRADE_TIMEOUT_BARS:
                        print(f"Position {pos.ticket} timed out after {bars_elapsed} bars. Closing remaining volume.")
                        self.mt5_connector.close_partial_position(pos.ticket, pos.volume)
            except Exception as e:
                print(f"Error checking timeout for position {pos.ticket}: {e}")

    def sync_closed_trades(self):
        import MetaTrader5 as mt5
        import os
        import pandas as pd
        from datetime import timedelta
        
        now = datetime.now()
        yesterday = now - timedelta(days=3) # Look back 3 days to cover weekends
        
        if not self.mt5_connector.ensure_connected():
            return
            
        deals = mt5.history_deals_get(yesterday, now)
        if deals is None or len(deals) == 0:
            return
            
        closed_deals = [d for d in deals if getattr(d, 'magic', 0) == 123456]
        
        log_path = self.data_logger.log_path
        if not os.path.exists(log_path):
            return
            
        try:
            df = pd.read_csv(log_path)
            if df.empty:
                return
                
            # Cast empty/target columns to avoid dtype warnings/errors
            for col in ['exit_time', 'status', 'exit_type', 'rr_achieved', 'realized_slippage']:
                if col in df.columns:
                    df[col] = df[col].astype(object)
                
            # Build maps of deals
            deal_by_order = {d.order: d for d in closed_deals}
            deals_by_pos = {}
            for d in closed_deals:
                pos_id = d.position_id
                if pos_id not in deals_by_pos:
                    deals_by_pos[pos_id] = []
                deals_by_pos[pos_id].append(d)

            csv_tickets = set(df['ticket'].dropna().unique())
            updated = False

            for idx, row in df.iterrows():
                if row['status'] != 'OPEN':
                    continue
                ticket = row['ticket']
                if pd.isna(ticket):
                    continue
                ticket = int(ticket)
                
                if ticket in deal_by_order:
                    d = deal_by_order[ticket]
                    pos_id = d.position_id
                    pos_deals = deals_by_pos.get(pos_id, [])
                    
                    # If the deal is an OUT deal (entry == 1 or 2)
                    if d.entry in [1, 2]:
                        profit = d.profit + d.commission + d.swap
                        exit_time = datetime.fromtimestamp(d.time).strftime('%Y-%m-%d %H:%M:%S')
                        df.at[idx, 'exit_price'] = d.price
                        df.at[idx, 'exit_time'] = exit_time
                        df.at[idx, 'profit'] = profit
                        df.at[idx, 'status'] = 'CLOSED'
                        df.at[idx, 'exit_type'] = "SL" if profit < 0 else "TP"
                        
                        entry_p = float(row['entry_price'])
                        sl_dist = abs(entry_p - float(row['sl'])) if not pd.isna(row['sl']) else 1.0
                        df.at[idx, 'rr_achieved'] = round((d.price - entry_p) / sl_dist if row['direction'] == 'BUY' else (entry_p - d.price) / sl_dist, 2)
                        updated = True
                        print(f"Synced closed OUT trade for ticket {ticket}. Profit: {profit:.2f}")
                    
                    # If the deal is an IN deal (entry == 0)
                    elif d.entry == 0:
                        out_deals = [od for od in pos_deals if od.entry in [1, 2]]
                        unmapped_out_deals = [od for od in out_deals if od.order not in csv_tickets]
                        
                        if unmapped_out_deals:
                            exit_deal = unmapped_out_deals[0]
                            direction_factor = 1 if row['direction'] == 'BUY' else -1
                            profit = (exit_deal.price - row['entry_price']) * row['lot'] * 100 * direction_factor
                            exit_time = datetime.fromtimestamp(exit_deal.time).strftime('%Y-%m-%d %H:%M:%S')
                            
                            df.at[idx, 'exit_price'] = exit_deal.price
                            df.at[idx, 'exit_time'] = exit_time
                            df.at[idx, 'profit'] = round(profit, 2)
                            df.at[idx, 'status'] = 'CLOSED'
                            
                            # Determine exit type based on price proximity
                            exit_type = "TIMEOUT"
                            if not pd.isna(row['sl']) and not pd.isna(row['tp']):
                                sl_p = float(row['sl'])
                                tp_p = float(row['tp'])
                                if row['direction'] == 'BUY':
                                    if exit_deal.price <= sl_p + 0.05:
                                        exit_type = "SL"
                                    elif exit_deal.price >= tp_p - 0.05:
                                        exit_type = "TP"
                                else:
                                    if exit_deal.price >= sl_p - 0.05:
                                        exit_type = "SL"
                                    elif exit_deal.price <= tp_p + 0.05:
                                        exit_type = "TP"
                            df.at[idx, 'exit_type'] = exit_type
                            
                            sl_dist = abs(row['entry_price'] - row['sl']) if not pd.isna(row['sl']) else 1.0
                            df.at[idx, 'rr_achieved'] = round((exit_deal.price - row['entry_price']) / sl_dist if row['direction'] == 'BUY' else (row['entry_price'] - exit_deal.price) / sl_dist, 2)
                            updated = True
                            print(f"Synced closed IN trade for ticket {ticket} via proportional matching. Profit: {profit:.2f}")
                        elif out_deals:
                            # The OUT deals are mapped to separate rows in the CSV, so this IN row realizes 0.0 profit directly
                            df.at[idx, 'profit'] = 0.0
                            df.at[idx, 'status'] = 'CLOSED'
                            df.at[idx, 'exit_type'] = "TIMEOUT"
                            df.at[idx, 'rr_achieved'] = 0.0
                            updated = True
                            print(f"Synced closed IN trade for ticket {ticket} with 0.0 profit (exit mapped separately).")
                            
            if updated:
                df.to_csv(log_path, index=False)
        except Exception as e:
            print(f"Error syncing closed trades: {e}")
