import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import time

class MT5Connector:
    def __init__(self, login, password, server, path=None):
        self.login = login
        self.password = password
        self.server = server
        self.path = path

    def connect(self):
        import os
        resolved_path = self.path
        if self.path and os.path.exists(self.path):
            if os.path.isdir(self.path):
                t_exe = os.path.join(self.path, "terminal64.exe")
                if os.path.exists(t_exe):
                    resolved_path = t_exe
                else:
                    default_exe = "C:\\Program Files\\MetaTrader 5\\terminal64.exe"
                    if os.path.exists(default_exe):
                        resolved_path = default_exe
                    else:
                        resolved_path = None
            else:
                resolved_path = self.path
        else:
            default_exe = "C:\\Program Files\\MetaTrader 5\\terminal64.exe"
            if os.path.exists(default_exe):
                resolved_path = default_exe
            else:
                resolved_path = None

        if not mt5.initialize(path=resolved_path, login=self.login, server=self.server, password=self.password):
            # Try once with auto-detection on failure
            if not mt5.initialize(login=self.login, server=self.server, password=self.password):
                print(f"MT5 initialization failed, error code: {mt5.last_error()}")
                return False
        print("MT5 initialized successfully")
        return True

    def ensure_connected(self):
        try:
            info = mt5.terminal_info()
            if info is None:
                raise Exception("Not connected")
            return True
        except Exception:
            print("MT5 connection lost. Attempting to reconnect...")
            for i in range(3):
                print(f"Reconnection attempt {i+1}/3...")
                if self.connect():
                    return True
                time.sleep(2)
            return False

    def disconnect(self):
        mt5.shutdown()
        print("MT5 connection closed")

    def get_market_data(self, symbol, timeframe, count):
        if not self.ensure_connected():
            return None
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
        if rates is None:
            print(f"Failed to retrieve market data for {symbol}, error code: {mt5.last_error()}")
            return None
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

    def place_order(self, symbol, order_type, lot, price=None, sl=None, tp=None, comment=""):
        if not self.ensure_connected():
            return None
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": order_type,
            "price": price if price else (mt5.symbol_info_tick(symbol).ask if order_type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).bid),
            "sl": sl if sl is not None else 0.0,
            "tp": tp if tp is not None else 0.0,
            "deviation": 20,
            "magic": 123456,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            err = result.retcode if result else mt5.last_error()
            print(f"Order placement failed, error code: {err}")
            return None
        print(f"Order placed successfully: {result.order}")
        return result

    def close_partial_position(self, ticket, volume):
        if not self.ensure_connected():
            return None
        position = mt5.positions_get(ticket=ticket)
        if not position:
            print(f"Position {ticket} not found")
            return None
        
        position = position[0]
        symbol = position.symbol
        order_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(symbol).bid if order_type == mt5.ORDER_TYPE_SELL else mt5.symbol_info_tick(symbol).ask

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "position": ticket,
            "price": price,
            "deviation": 20,
            "magic": 123456,
            "comment": "Partial Close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            err = result.retcode if result else mt5.last_error()
            print(f"Partial close failed, error code: {err}")
            return None
        print(f"Partial close successful: {result.order}")
        return result

    def get_open_positions(self, symbol=None):
        if not self.ensure_connected():
            return []
        positions = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
        if positions is None:
            print(f"Failed to retrieve open positions, error code: {mt5.last_error()}")
            return []
        return positions

    def get_symbol_info(self, symbol):
        if not self.ensure_connected():
            return None
        info = mt5.symbol_info(symbol)
        if info is None:
            print(f"Failed to retrieve symbol info for {symbol}, error code: {mt5.last_error()}")
            return None
        return info

    def get_account_info(self):
        if not self.ensure_connected():
            return None
        info = mt5.account_info()
        if info is None:
            print(f"Failed to retrieve account info, error code: {mt5.last_error()}")
            return None
        return info
