# ============================================
# AI STOCK SCANNER V1.4
# CONFIGURATION FILE
# ============================================

# Scanner Mode
SCANNER_MODE = "BOTH"        # CASH / FNO / BOTH

# Trading Style
TRADING_STYLE = "SWING"      # SWING / POSITION

# Accuracy Mode
ACCURACY_MODE = "BALANCED"   # AGGRESSIVE / BALANCED / CONSERVATIVE

# Timeframes
PRIMARY_TIMEFRAME = "1d"
CONFIRMATION_TIMEFRAME = "4h"

# Results
TOP_BUY_RESULTS = 10
TOP_SELL_RESULTS = 10

# Risk Management
RISK_PER_TRADE = 1.0         # Percentage
DEFAULT_RR = 3.0             # Risk : Reward

# Backtest Cost Settings
SLIPPAGE = 0.001             # 0.1% Slippage
BROKERAGE_PER_TRADE = 20     # ₹20 per completed trade

# Backtest Cost Settings
SLIPPAGE = 0.001             # 0.1% Slippage
BROKERAGE_PER_TRADE = 20     # ₹20 per completed trade
ENABLE_TRANSACTION_COST = True

# Capital
STARTING_CAPITAL = 100000

# Alerts
ENABLE_SOUND_ALERT = True
ENABLE_POPUP_ALERT = True
ENABLE_WATCHLIST_ALERT = True

# Market Filter
USE_NIFTY_FILTER = True
USE_BANKNIFTY_FILTER = True

# Indicators
EMA_FAST = 20
EMA_SLOW = 50
RSI_PERIOD = 14
ATR_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# Watchlist
WATCHLIST_ONLY = False

# Signal Thresholds
BUY_SCORE = 60
SELL_SCORE = 60

# Strategy Engine Thresholds
STRATEGY_BUY_THRESHOLD = 65
STRATEGY_SELL_THRESHOLD = 65

# Confidence Engine Weights
CONFIDENCE_WEIGHT_STRATEGY = 0.40
CONFIDENCE_WEIGHT_TREND = 0.25
CONFIDENCE_WEIGHT_PATTERN = 0.20
CONFIDENCE_WEIGHT_VOLUME = 0.10
CONFIDENCE_WEIGHT_ATR = 0.05

# Backtest Settings
BACKTEST_LOOKAHEAD = 30
MIN_TRADES_FOR_RANKING = 5

# Trading Settings
ENTRY_ATR_BUFFER = 0.25
STOP_ATR_MULTIPLIER = 1.5
TRAILING_STOP_ATR = 2.0
BREAK_EVEN_AT_TARGET1 = True
TARGET1_R = 1.5
TARGET2_R = 2.5
TARGET3_R = 4.0