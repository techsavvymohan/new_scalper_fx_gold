import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import subprocess
import time
import os

class MT5Connector:
    def __init__(self, login, password, server, path=None):
        self.login = login
        self.password = password
        self.server = server
        self.path = path
        self._symbol_info_cache = {}

    def _resolve_exe_path(self):
        """Find the terminal64.exe path from configured path or known defaults."""
        candidates = []
        if self.path:
            candidates.append(self.path)
            candidates.append(os.path.join(self.path, "terminal64.exe"))
        candidates += [
            "C:\\Program Files\\MetaTrader 5\\terminal64.exe",
            "C:\\Program Files (x86)\\MetaTrader 5\\terminal64.exe",
        ]
        for candidate in candidates:
            if os.path.isfile(candidate):
                return candidate
        return None

    def _launch_mt5(self):
        """Launch the MT5 terminal process if not already running."""
        exe = self._resolve_exe_path()
        if not exe:
            print("[MT5] Cannot find terminal64.exe — check MT5_PATH in .env")
            return False
        print(f"[MT5] Launching MT5 terminal: {exe}")
        try:
            subprocess.Popen([exe])
            print("[MT5] MT5 process started. Waiting 15 seconds for it to load...")
            for i in range(15, 0, -1):
                print(f"[MT5] Starting up... {i}s remaining", end="\r")
                time.sleep(1)
            print()
            return True
        except Exception as e:
            print(f"[MT5] Failed to launch MT5: {e}")
            return False

    def connect(self, auto_launch=True, max_retries=5, retry_delay=5):
        """
        Connect to MetaTrader 5.
        - If MT5 is not running and auto_launch=True, attempts to launch it.
        - Retries up to max_retries times with retry_delay seconds between attempts.
        """
        exe = self._resolve_exe_path()

        for attempt in range(1, max_retries + 1):
            print(f"[MT5] Connection attempt {attempt}/{max_retries}...")

            # Try initialising with explicit path first, then without
            success = False
            if exe:
                success = mt5.initialize(
                    path=exe,
                    login=self.login,
                    server=self.server,
                    password=self.password
                )
            if not success:
                success = mt5.initialize(
                    login=self.login,
                    server=self.server,
                    password=self.password
                )

            if success:
                print("[MT5] Connected successfully!")
                info = mt5.terminal_info()
                if info:
                    print(f"[MT5] Terminal: {info.name}  |  Build: {info.build}  |  Connected: {info.connected}")
                acct = mt5.account_info()
                if acct:
                    print(f"[MT5] Account: #{acct.login}  |  Server: {acct.server}  |  Balance: {acct.balance} {acct.currency}")
                return True

            error = mt5.last_error()
            print(f"[MT5] Attempt {attempt} failed — error: {error}")

            # On first failure, try launching MT5 if auto_launch is enabled
            if attempt == 1 and auto_launch:
                launched = self._launch_mt5()
                if not launched:
                    print("[MT5] Could not auto-launch MT5. Please open it manually.")
            elif attempt < max_retries:
                print(f"[MT5] Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)

        print("[MT5] All connection attempts failed.")
        return False

    def ensure_connected(self):
        """Check connection health; reconnect if dropped."""
        try:
            info = mt5.terminal_info()
            if info is None:
                raise Exception("Not connected")
            return True
        except Exception:
            print("[MT5] Connection lost. Attempting to reconnect...")
            for i in range(5):
                print(f"[MT5] Reconnection attempt {i+1}/5...")
                if self.connect(auto_launch=(i == 0), max_retries=1, retry_delay=0):
                    return True
                time.sleep(5)
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

    def modify_position_sl(self, ticket, new_sl):
        """
        Modify the stop-loss of an open position server-side.
        Used to move SL to breakeven once price reaches +1R.

        Args:
            ticket  : MT5 position ticket
            new_sl  : New stop-loss price (server-side, absolute price)

        Returns:
            MT5 order_send result or None on failure.
        """
        if not self.ensure_connected():
            return None
        position_list = mt5.positions_get(ticket=ticket)
        if not position_list:
            print(f"[MT5] modify_position_sl: Position {ticket} not found.")
            return None

        pos = position_list[0]
        request = {
            "action"   : mt5.TRADE_ACTION_MODIFY,
            "position" : ticket,
            "symbol"   : pos.symbol,
            "sl"       : round(new_sl, 2),
            "tp"       : pos.tp,          # keep TP unchanged
            "type_time": mt5.ORDER_TIME_GTC,
        }
        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            err = result.retcode if result else mt5.last_error()
            print(f"[MT5] SL modify failed for ticket {ticket}, error: {err}")
            return None
        print(f"[MT5] Breakeven SL set for ticket {ticket} → {new_sl:.2f}")
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
        if symbol in self._symbol_info_cache:
            return self._symbol_info_cache[symbol]
        if not self.ensure_connected():
            return None
        info = mt5.symbol_info(symbol)
        if info is None:
            print(f"Failed to retrieve symbol info for {symbol}, error code: {mt5.last_error()}")
            return None
        self._symbol_info_cache[symbol] = info
        return info

    def get_account_info(self):
        if not self.ensure_connected():
            return None
        info = mt5.account_info()
        if info is None:
            print(f"Failed to retrieve account info, error code: {mt5.last_error()}")
            return None
        return info
