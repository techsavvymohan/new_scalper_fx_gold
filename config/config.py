import os

# Simple .env parser to avoid external dependencies
def load_dotenv(path):
    if os.path.exists(path):
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, val = line.split('=', 1)
                    os.environ[key.strip()] = val.strip()

# Load .env relative to config directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(project_root, '.env'))

MT5_LOGIN = int(os.environ.get("MT5_LOGIN", 123456))
MT5_PASSWORD = os.environ.get("MT5_PASSWORD", "your_password")
MT5_SERVER = os.environ.get("MT5_SERVER", "MetaQuotes-Demo")
MT5_PATH = os.environ.get("MT5_PATH", "C:\\Program Files\\MetaTrader 5\\terminal64.exe")

SYMBOL = "XAUUSD"
# Confluence Timeframes
MACRO_TREND_TIMEFRAME = "M15"  # Higher timeframe for trend filter (confluence bias)
CONF_TREND_TIMEFRAME = "M5"    # Intermediate timeframe for signal verification
ENTRY_TIMEFRAME = "M1"         # Entry timeframe for SATS signals, breakout probabilities, and entry triggers

# Risk Management
RISK_PER_TRADE_PERCENT = 0.005  # 0.5% risk per trade
MAX_SL_ATR_MULTIPLIER = 4  # Maximum Stop Loss of 4 ATR

# Take Profit
TP_MODE = "FIXED"
TP1_MULTIPLIER = 0.5  # Target 0.5R for TP1 (reduced size for quicker take-profit execution)
TP1_PARTIAL_CLOSE_PERCENT = 0.5  # Close 50% of position at TP1

# Trade Timeout
TRADE_TIMEOUT_BARS = 100

# SATS Indicator Parameters (from PRD)
ATR_LENGTH = 13
EFFICIENCY_WINDOW = 20
ADAPTATION_STRENGTH = 0.5
ATR_BASELINE = 100
QUALITY_INFLUENCE = 0.4
QUALITY_CURVE_POWER = 1.5
ASYMMETRIC_BANDS_STRENGTH = 0.5
ASYMMETRIC_BANDS_ENABLED = True
EFFICIENCY_WEIGHTED_ATR_ENABLED = True
CHARACTER_FLIP_ENABLED = True
CHARACTER_FLIP_MIN_AGE = 5
CHARACTER_FLIP_HIGH_TQI = 0.55
CHARACTER_FLIP_LOW_TQI = 0.25
TQI_WEIGHTS = {
    "efficiency": 0.35,
    "volatility": 0.20,
    "structure": 0.25,
    "momentum_persistence": 0.20,
}
STRUCTURE_WINDOW = 20
MOMENTUM_PERSISTENCE_BARS = 10

# Signal Scoring Engine (for filtering/confirmation)
PIVOT_STRENGTH = 3
RSI_LENGTH = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
RSI_MEMORY_BARS = 20
VOLUME_WINDOW = 20

# Risk Filters
SESSION_FILTER_ENABLED = False
SESSION_START_HOUR = 9  # Example: 9 AM UTC
SESSION_END_HOUR = 17  # Example: 5 PM UTC

ECONOMIC_CALENDAR_CHECK_ENABLED = False
NEWS_EVENT_PAUSE_WINDOW_MINUTES = 15 # 15 minutes before/after

VOLATILITY_FILTER_ENABLED = False
ATR_PERCENTILE_LOW_THRESHOLD = 0.1  # Example: Avoid bottom 10% volatility
ATR_PERCENTILE_HIGH_THRESHOLD = 0.9  # Example: Avoid top 10% volatility

DAILY_MAX_LOSS_PERCENT = 0.02  # 2% daily max loss
MAX_CONSECUTIVE_LOSSES = 5

WEEKLY_MONTHLY_DRAWDOWN_KILL_SWITCH_ENABLED = False
MAX_DRAWDOWN_PERCENT = 0.1  # 10% max drawdown

# Backtesting & Validation
MIN_FORWARD_TEST_DURATION_DAYS = 30
MIN_FORWARD_TEST_TRADE_COUNT = 100

# Breakout Probability Indicator
BREAKOUT_PROBABILITY_ENABLED = True
BREAKOUT_PERCENTAGE_STEP = 0.0005  # 0.05% step between levels for XAUUSD CFD (smaller step size for scalping)
BREAKOUT_NUM_LINES = 4
BREAKOUT_MIN_PROBABILITY_THRESHOLD = 0.60  # Minimum probability threshold to confirm bias (e.g. 60% for higher accuracy)

# Data Storage
TRADE_LOG_FILE = "trade_log.csv"

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "bot.log"
