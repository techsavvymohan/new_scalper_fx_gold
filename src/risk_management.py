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
        sl_atr_mult = getattr(self.config, 'SL_ATR_MULTIPLIER', 2.0) # V1 default was 2.0
        sl_dist = atr * sl_atr_mult
        # Cap SL at MAX_SL_ATR_MULTIPLIER ATR
        sl_dist = min(sl_dist, atr * self.config.MAX_SL_ATR_MULTIPLIER)
        
        # Cap SL dynamically based on config (each pip on XAUUSD is $0.10 price distance)
        max_sl_pips = getattr(self.config, 'MAX_SL_PIPS', None)
        if max_sl_pips is not None:
            max_sl_dist = max_sl_pips * 0.10
            sl_dist = min(sl_dist, max_sl_dist)
        
        # Calculate raw TP distance dynamically based on SL and TP multiplier
        tp_mult = getattr(self.config, 'TP_MULTIPLIER', None)
        if tp_mult is None:
            tp_mult = getattr(self.config, 'TP1_MULTIPLIER', 0.5) # V1 default was TP1_MULTIPLIER (0.5)
        raw_tp_dist = sl_dist * tp_mult
        
        # Cap the TP distance dynamically based on config (each pip on XAUUSD is $0.10 price distance)
        max_tp_pips = getattr(self.config, 'MAX_TP_PIPS', 30)
        max_tp_dist = max_tp_pips * 0.10
        final_tp_dist = min(raw_tp_dist, max_tp_dist)
        
        if direction == 1: # Buy
            sl = entry_price - sl_dist
            tp = entry_price + final_tp_dist
        else: # Sell
            sl = entry_price + sl_dist
            tp = entry_price - final_tp_dist
            
        return round(sl, 2), round(tp, 2)
