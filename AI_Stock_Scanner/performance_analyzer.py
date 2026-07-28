import pandas as pd


class PerformanceAnalyzer:

    def __init__(self, file_name="trade_history.csv"):
        self.file_name = file_name

    # =====================================
    # LOAD DATA
    # =====================================

    def load(self):

        return pd.read_csv(self.file_name)

    # =====================================
    # TOTAL STATS
    # =====================================

    def summary(self):

        df = self.load()

        total = len(df)

        wins = len(df[df["PnL"] > 0])

        losses = len(df[df["PnL"] <= 0])

        winrate = 0

        if total > 0:
            winrate = round((wins / total) * 100, 2)

        return {
            "TotalTrades": total,
            "Wins": wins,
            "Losses": losses,
            "WinRate": winrate
        }

    # =====================================
    # AVERAGE PROFIT
    # =====================================

    def average_profit(self):

        df = self.load()

        profit = df[df["PnL"] > 0]

        if len(profit) == 0:
            return 0

        return round(profit["PnL"].mean(), 2)

    # =====================================
    # AVERAGE LOSS
    # =====================================

    def average_loss(self):

        df = self.load()

        loss = df[df["PnL"] <= 0]

        if len(loss) == 0:
            return 0

        return round(loss["PnL"].mean(), 2)

    # =====================================
    # BEST PATTERN
    # =====================================

    def best_pattern(self):

        df = self.load()

        if len(df) == 0:
            return None

        return (
            df.groupby("Pattern")["PnL"]
            .mean()
            .sort_values(ascending=False)
            .head(5)
        )

    # =====================================
    # LOSS REASONS
    # =====================================

    def loss_reason(self):

        df = self.load()

        loss = df[df["PnL"] <= 0]

        if len(loss) == 0:
            return None

        return loss["Reason"].value_counts()

    # =====================================
    # MONTHLY REPORT
    # =====================================

    def monthly_report(self):

        df = self.load()

        if len(df) == 0:
            return None

        df["Month"] = pd.to_datetime(df["Date"]).dt.to_period("M")

        return df.groupby("Month")["PnL"].sum()
      
