import os
import pandas as pd
from datetime import datetime


class TradeLogger:

    def __init__(self, file_name="trade_history.csv"):
        self.file_name = file_name

        if not os.path.exists(self.file_name):

            df = pd.DataFrame(columns=[
                "Date",
                "Time",
                "Symbol",
                "Signal",
                "Entry",
                "Exit",
                "StopLoss",
                "Target",
                "Quantity",
                "PnL",
                "PnLPercent",
                "Reason",
                "Confidence",
                "EMA",
                "MACD",
                "RSI",
                "Pattern",
                "TrendScore"
            ])

            df.to_csv(self.file_name, index=False)

    # =====================================
    # SAVE TRADE
    # =====================================

    def save_trade(
            self,
            symbol,
            signal,
            entry,
            exit_price,
            sl,
            target,
            qty,
            pnl,
            pnl_percent,
            reason,
            confidence,
            ema,
            macd,
            rsi,
            pattern,
            trend):

        df = pd.read_csv(self.file_name)

        now = datetime.now()

        df.loc[len(df)] = [

            now.strftime("%Y-%m-%d"),

            now.strftime("%H:%M:%S"),

            symbol,

            signal,

            entry,

            exit_price,

            sl,

            target,

            qty,

            pnl,

            pnl_percent,

            reason,

            confidence,

            ema,

            macd,

            rsi,

            pattern,

            trend

        ]

        df.to_csv(self.file_name, index=False)

    # =====================================
    # LOAD HISTORY
    # =====================================

    def history(self):

        return pd.read_csv(self.file_name)

    # =====================================
    # TOTAL TRADES
    # =====================================

    def total_trades(self):

        return len(self.history())
