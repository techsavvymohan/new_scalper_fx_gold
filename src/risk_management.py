import MetaTrader5 as mt5

class RiskManagement:
    def __init__(self, config, mt5_connector):
        self.config = config
        self.mt5_connector = mt5_connector

    def calculate_lot_size(self, symbol, risk_amount, sl_pips):
        symbol_info = self.mt5_connector.get_symbol_info(symbol)
        if symbol_info is None:
            return None
        
        # Get point value and tick size
        point = symbol_info.point
        tick_size = symbol_info.trade_tick_size
        tick_value = symbol_info.trade_tick_value
        
        if sl_pips == 0:
            return symbol_info.volume_min

        # Lot size = Risk Amount / (SL in points * Point Value per lot)
        # For XAUUSD, tick_value is usually for 1 lot per tick_size
        lot_size = risk_amount / (sl_pips * (tick_value / tick_size))
        
        # Align with MT5 volume steps
        lot_size = round(lot_size / symbol_info.volume_step) * symbol_info.volume_step
        
        # Constrain by min/max lot
        lot_size = max(min(lot_size, symbol_info.volume_max), symbol_info.volume_min)
        
        return round(lot_size, 2)

    def get_risk_amount(self, balance):
        return balance * self.config.RISK_PER_TRADE_PERCENT

    def calculate_sl_tp(self, symbol, direction, entry_price, atr):
        sl_dist = atr * 2 # Default SuperTrend SL distance
        # Cap SL at 4 ATR
        sl_dist = min(sl_dist, atr * self.config.MAX_SL_ATR_MULTIPLIER)
        
        if direction == 1: # Buy
            sl = entry_price - sl_dist
            tp = entry_price + sl_dist * self.config.TP1_MULTIPLIER
        else: # Sell
            sl = entry_price + sl_dist
            tp = entry_price - sl_dist * self.config.TP1_MULTIPLIER
            
        return round(sl, 2), round(tp, 2)
