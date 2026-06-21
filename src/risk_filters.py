from datetime import datetime, timedelta
import pandas as pd

class RiskFilters:
    def __init__(self, config, mt5_connector):
        self.config = config
        self.mt5_connector = mt5_connector

    def is_trading_allowed(self, df_m5=None):
        if not self.check_session_filter():
            return False
        if not self.check_daily_loss_limit():
            return False
        if not self.check_consecutive_losses():
            return False
        if not self.check_consecutive_loss_cooldown():
            return False
            
        # Volatility Filter
        if getattr(self.config, 'VOLATILITY_FILTER_ENABLED', False):
            if df_m5 is None:
                import MetaTrader5 as mt5
                df_m5 = self.mt5_connector.get_market_data(self.config.SYMBOL, mt5.TIMEFRAME_M5, 200)
            if df_m5 is not None:
                if not self.check_volatility_filter(df_m5, self.config.ATR_LENGTH):
                    print("Trading paused by volatility filter.")
                    return False
        return True

    def check_session_filter(self):
        if not self.config.SESSION_FILTER_ENABLED:
            return True
        from datetime import timezone
        current_hour = datetime.now(timezone.utc).hour
        return self.config.SESSION_START_HOUR <= current_hour < self.config.SESSION_END_HOUR

    def check_daily_loss_limit(self):
        if not hasattr(self.config, 'DAILY_MAX_LOSS_PERCENT'):
            return True
        import MetaTrader5 as mt5
        account_info = self.mt5_connector.get_account_info()
        if account_info is None:
            return False
        
        # Calculate daily realized loss from today's closed deals
        now = datetime.now()
        start_of_day = datetime(now.year, now.month, now.day)
        
        if not self.mt5_connector.ensure_connected():
            return False
            
        deals = mt5.history_deals_get(start_of_day, now)
        realized_loss = 0.0
        if deals is not None:
            for deal in deals:
                if getattr(deal, 'magic', 0) == 123456:
                    realized_loss += (deal.profit + deal.commission + deal.swap)
                    
        # Floating loss from currently open positions
        positions = self.mt5_connector.get_open_positions(self.config.SYMBOL)
        floating_loss = 0.0
        for pos in positions:
            if getattr(pos, 'magic', 0) == 123456:
                floating_loss += pos.profit
                
        total_loss = -(realized_loss + floating_loss)
        max_loss = account_info.balance * self.config.DAILY_MAX_LOSS_PERCENT
        
        if total_loss >= max_loss:
            print(f"Daily loss limit breached: {total_loss:.2f} >= max {max_loss:.2f}")
            return False
        return True

    def check_consecutive_losses(self):
        import MetaTrader5 as mt5
        if not self.mt5_connector.ensure_connected():
            return False
            
        from_date = datetime.now() - timedelta(days=7)
        deals = mt5.history_deals_get(from_date, datetime.now())
        if deals is None or len(deals) == 0:
            return True
            
        # Filter deals by magic number and closed entry type (1 = out, 2 = inout)
        bot_deals = [d for d in deals if getattr(d, 'magic', 0) == 123456 and getattr(d, 'entry', -1) in [1, 2]]
        bot_deals.sort(key=lambda x: x.time, reverse=True)
        
        consecutive_losses = 0
        max_losses = getattr(self.config, 'MAX_CONSECUTIVE_LOSSES', 5)
        
        for deal in bot_deals:
            net_profit = deal.profit + deal.commission + deal.swap
            if net_profit < 0:
                consecutive_losses += 1
                if consecutive_losses >= max_losses:
                    print(f"Consecutive loss circuit breaker triggered: {consecutive_losses} consecutive losses")
                    return False
            else:
                break
                
        return True

    def check_volatility_filter(self, df, atr_length):
        if not self.config.VOLATILITY_FILTER_ENABLED:
            return True
        
        # Calculate ATR and its percentile
        df['atr'] = df['high'].rolling(window=atr_length).max() - df['low'].rolling(window=atr_length).min()
        current_atr = df['atr'].iloc[-1]
        
        # Calculate percentile of current ATR in recent history
        atr_percentile = (df['atr'] < current_atr).mean()
        
        return bool(self.config.ATR_PERCENTILE_LOW_THRESHOLD <= atr_percentile <= self.config.ATR_PERCENTILE_HIGH_THRESHOLD)

    def check_consecutive_loss_cooldown(self):
        import MetaTrader5 as mt5
        import time
        if not self.mt5_connector.ensure_connected():
            return False
            
        from_date = datetime.now() - timedelta(days=2)
        deals = mt5.history_deals_get(from_date, datetime.now())
        if deals is None or len(deals) == 0:
            return True
            
        # Filter deals by magic number and closed entry type (1 = out, 2 = inout)
        bot_deals = [d for d in deals if getattr(d, 'magic', 0) == 123456 and getattr(d, 'entry', -1) in [1, 2]]
        bot_deals.sort(key=lambda x: x.time, reverse=True)
        
        consecutive_losses = 0
        last_loss_time = None
        
        for deal in bot_deals:
            net_profit = deal.profit + deal.commission + deal.swap
            if net_profit < 0:
                if consecutive_losses == 0:
                    last_loss_time = deal.time
                consecutive_losses += 1
            else:
                break
                
        if consecutive_losses >= 3:
            # Get current MT5 server time from symbol tick to avoid local timezone mismatches
            tick = mt5.symbol_info_tick(self.config.SYMBOL)
            current_server_time = tick.time if tick else int(time.time())
            
            if consecutive_losses >= 5:
                cooldown_min = getattr(self.config, 'CONSECUTIVE_LOSS_COOLDOWN_5', 60)
                elapsed_min = (current_server_time - last_loss_time) / 60.0
                if elapsed_min < cooldown_min:
                    print(f"[Risk Control] Paused due to {consecutive_losses} consecutive losses. Cooldown remaining: {cooldown_min - elapsed_min:.1f} mins.")
                    return False
            else:
                cooldown_min = getattr(self.config, 'CONSECUTIVE_LOSS_COOLDOWN_3', 30)
                elapsed_min = (current_server_time - last_loss_time) / 60.0
                if elapsed_min < cooldown_min:
                    print(f"[Risk Control] Paused due to {consecutive_losses} consecutive losses. Cooldown remaining: {cooldown_min - elapsed_min:.1f} mins.")
                    return False
                
        return True
