import MetaTrader5 as mt5
from datetime import datetime
from src.breakout_probability import BreakoutProbability

class StrategyExecution:
    def __init__(self, config, mt5_connector, sats_logic, risk_management, data_logger):
        self.config = config
        self.mt5_connector = mt5_connector
        self.sats_logic = sats_logic
        self.risk_management = risk_management
        self.data_logger = data_logger
        self.breakout_prob = BreakoutProbability(config)

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
            return

        # 2. Calculate SATS states
        df_macro = self.sats_logic.get_signals(df_macro)
        df_conf = self.sats_logic.get_signals(df_conf)
        df_entry = self.sats_logic.get_signals(df_entry)

        macro_trend = df_macro['trend'].iloc[-1]
        conf_trend = df_conf['trend'].iloc[-1]
        entry_signal = df_entry['signal'].iloc[-1]
        entry_atr = self.sats_logic.calculate_atr(df_entry, self.config.ATR_LENGTH).iloc[-1]

        # 2.5. Calculate Breakout Probabilities
        new_high_prob = 1.0
        new_low_prob = 1.0
        if getattr(self.config, 'BREAKOUT_PROBABILITY_ENABLED', False):
            probs = self.breakout_prob.calculate_probabilities(df_entry)
            new_high_prob = probs.get('new_high_prob', 0.5)
            new_low_prob = probs.get('new_low_prob', 0.5)

        # 3. Check for entries
        if entry_signal != 0:
            min_prob = getattr(self.config, 'BREAKOUT_MIN_PROBABILITY_THRESHOLD', 0.60)
            if entry_signal == 1 and conf_trend == 1 and macro_trend == 1: # Bullish Confluence
                if new_high_prob >= min_prob:
                    self.execute_trade(mt5.ORDER_TYPE_BUY, df_entry.iloc[-1], entry_atr, macro_trend)
                else:
                    print(f"Buy signal filtered: Breakout probability of new high ({new_high_prob:.2%}) below threshold ({min_prob:.2%})")
            elif entry_signal == -1 and conf_trend == -1 and macro_trend == -1: # Bearish Confluence
                if new_low_prob >= min_prob:
                    self.execute_trade(mt5.ORDER_TYPE_SELL, df_entry.iloc[-1], entry_atr, macro_trend)
                else:
                    print(f"Sell signal filtered: Breakout probability of new low ({new_low_prob:.2%}) below threshold ({min_prob:.2%})")

        # 4. Monitor open positions and sync closed trades
        self.monitor_positions(df_entry, entry_tf)
        self.sync_closed_trades()

    def execute_trade(self, order_type, current_bar, atr, m15_trend):
        symbol = self.config.SYMBOL
        entry_price = current_bar['close']
        
        sl, tp = self.risk_management.calculate_sl_tp(symbol, 1 if order_type == mt5.ORDER_TYPE_BUY else -1, entry_price, atr)
        
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
                    "entry_price": entry_price,
                    "sl": sl,
                    "tp": tp,
                    "lot": lot,
                    "m15_trend": m15_trend,
                    "status": "OPEN",
                    "ticket": result.order
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
            
            # Check for Partial TP1
            if self.config.TP_MODE == "FIXED":
                # Calculate TP1 price (1R target)
                sl_dist = abs(pos.price_open - pos.sl)
                if pos.type == mt5.ORDER_TYPE_BUY:
                    tp1_price = pos.price_open + sl_dist
                    is_tp1_hit = pos.price_current >= tp1_price
                else:
                    tp1_price = pos.price_open - sl_dist
                    is_tp1_hit = pos.price_current <= tp1_price
                    
                # If TP1 hit and volume hasn't been reduced yet
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
        yesterday = now - timedelta(days=2)
        
        if not self.mt5_connector.ensure_connected():
            return
            
        deals = mt5.history_deals_get(yesterday, now)
        if deals is None or len(deals) == 0:
            return
            
        closed_deals = [d for d in deals if getattr(d, 'magic', 0) == 123456 and getattr(d, 'entry', -1) in [1, 2]]
        
        log_path = self.data_logger.log_path
        if not os.path.exists(log_path):
            return
            
        try:
            df = pd.read_csv(log_path)
            if df.empty:
                return
                
            updated = False
            for deal in closed_deals:
                ticket = getattr(deal, 'position_id', None)
                if ticket is None:
                    continue
                mask = (df['ticket'] == ticket) & (df['status'] == 'OPEN')
                if mask.any():
                    df.loc[mask, 'exit_price'] = deal.price
                    df.loc[mask, 'exit_time'] = datetime.fromtimestamp(deal.time)
                    df.loc[mask, 'profit'] = deal.profit + deal.commission + deal.swap
                    df.loc[mask, 'status'] = 'CLOSED'
                    updated = True
                    print(f"Synced closed trade for ticket {ticket}. Profit: {deal.profit:.2f}")
                    
            if updated:
                df.to_csv(log_path, index=False)
        except Exception as e:
            print(f"Error syncing closed trades: {e}")
