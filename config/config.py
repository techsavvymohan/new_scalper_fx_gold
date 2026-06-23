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
MACRO_TREND_TIMEFRAME = "M5"  # Higher timeframe for trend filter (confluence bias)
CONF_TREND_TIMEFRAME = "M5"    # Intermediate trend filter (since we only use M15 and M5 now)
ENTRY_TIMEFRAME = "M1"         # Primary signal generator, entry trigger, and SL/TP timeframe


# Risk Management
RISK_PER_TRADE_PERCENT = 0.005  # 0.5% risk per trade
SL_ATR_MULTIPLIER = 1.2        # Default Stop Loss ATR multiplier for V2
MAX_SL_ATR_MULTIPLIER = 4  # Maximum Stop Loss of 4 ATR
MAX_SL_PIPS = 25  # Maximum Stop Loss in pips (e.g. 25 pips is $2.50 distance on XAUUSD)

# Take Profit
TP_MODE = "FIXED"
TP_MULTIPLIER = 0.5           # Default TP multiplier (0.5R) for tight scalping
TP1_MULTIPLIER = 0.5  # Target 0.5R for TP1
TP1_PARTIAL_CLOSE_PERCENT = 0.5  # Close 50% of position at TP1
MAX_TP_PIPS = 10  # Maximum Take Profit in pips (e.g. 10 pips is $1.00 distance on XAUUSD)

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
SESSION_START_HOUR = 7  # 07:00 UTC (12:30 PM IST)
SESSION_END_HOUR = 16   # 16:00 UTC (09:30 PM IST)

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
BREAKOUT_PROBABILITY_ENABLED = False
BREAKOUT_PERCENTAGE_STEP = 0.0005  # 0.05% step between levels for XAUUSD CFD (smaller step size for scalping)
BREAKOUT_NUM_LINES = 4
BREAKOUT_MIN_PROBABILITY_THRESHOLD = 0.50  # Minimum probability threshold to confirm bias (e.g. 60% for higher accuracy)

# Data Storage
TRADE_LOG_FILE = "trade_log.csv"

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "bot.log"

# SATS Scalper Upgrades (Regimes, Sessions, Cooldowns, Confidence Score)
REGIME_TRENDING_ER_MIN = 0.45
REGIME_DEAD_ATR_RATIO = 0.5
REGIME_EXPLOSIVE_ATR_RATIO = 2.0
ALLOWED_REGIMES = ['TRENDING', 'RANGING', 'DEAD', 'EXPLOSIVE']  # Log only: allow all by default in Phase 1

REGIME_LOOKBACK_BARS = 100
# Composite regime score = mean(z_ratio, z_er, z_tqi) — three rolling z-scores over REGIME_LOOKBACK_BARS.
# DEAD/EXPLOSIVE are anchored to z_ratio (vol) only; TRENDING/RANGING use the composite.
REGIME_VOL_DEAD_THRESHOLD = -1.0       # z_ratio below this → DEAD (suppressed vol)
REGIME_VOL_EXPLOSIVE_THRESHOLD = 1.5   # z_ratio above this → EXPLOSIVE (vol spike)
REGIME_TREND_MIN_THRESHOLD = 0.1       # composite score >= this → TRENDING (slight positive bias required)

SESSION_TEST_FILTER_ENABLED = False

SESSION_HOURS = {
    'Asia': (22, 8),          # 10 PM to 8 AM UTC
    'London': (8, 13),        # 8 AM to 1 PM UTC
    'Overlap': (13, 16),      # 1 PM to 4 PM UTC
    'NewYork': (16, 22)       # 4 PM to 10 PM UTC
}
DISABLED_SESSIONS = []        # Disallowed trading sessions

MIN_CONFIDENCE_SCORE = 0.0   # Confidence threshold (0-100)
MIN_MACRO_TQI = 0.0
MIN_MACRO_ER = 0.0
MIN_MACRO_ATR_RATIO = 0.0
MIN_ENTRY_TQI = 0.0

CONSECUTIVE_LOSS_COOLDOWN_3 = 30  # Minutes to pause after 3 losses
CONSECUTIVE_LOSS_COOLDOWN_5 = 60  # Minutes to pause after 5 losses

