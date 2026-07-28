# ============================================
# AI STOCK SCANNER V1.1
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

# Scanner Results
TOP_BUY_RESULTS = 10
TOP_SELL_RESULTS = 10

# Risk Management
RISK_PER_TRADE = 1.0         # Percentage
DEFAULT_RR = 3.0             # Risk : Reward

# Capital
DEFAULT_CAPITAL = 100000

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

# ===========================
# Capital Settings
# ===========================

STARTING_CAPITAL = 100000
