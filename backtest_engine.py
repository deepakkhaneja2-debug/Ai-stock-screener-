import pandas as pd


class BacktestEngine:

    def __init__(self):

        self.lookahead_days = 15

    # =========================================
    # BACKTEST
    # =========================================

    def run(self, data):

        results = []

        if data.empty:
            return self.summary(results)

        data = data.copy()

        required = [
            "Close",
            "High",
            "Low",
            "EMA20",
            "EMA50",
            "RSI",
            "MACD",
            "MACD_SIGNAL",
            "ATR",
            "VWAP",
        ]

        for column in required:

            if column not in data.columns:
                return self.summary(results)

        # =====================================
        # HISTORICAL SCAN
        # =====================================

        for i in range(60, len(data) - 1):

            row = data.iloc[i]

            # =================================
            # BUY SETUP
            # =================================

            buy_setup = (

                row["EMA20"] > row["EMA50"]

                and row["MACD"] > row["MACD_SIGNAL"]

                and 55 < row["RSI"] < 75

                and row["Close"] > row["VWAP"]

            )

            if not buy_setup:
                continue

            current_price = float(row["Close"])

            atr = float(row["ATR"])

            if atr <= 0:
                continue

            # =================================
            # ENTRY
            # =================================

            entry = round(
                current_price + atr * 0.25,
                2
            )

            stoploss = round(
                entry - atr * 1.5,
                2
            )

            risk = entry - stoploss

            if risk <= 0:
                continue

            # =================================
            # TARGETS
            # =================================

            target1 = round(
                entry + risk * 1.5,
                2
            )

            target2 = round(
                entry + risk * 2.5,
                2
            )

            target3 = round(
                entry + risk * 4.0,
                2
            )

            # =================================
            # WAIT FOR ENTRY TRIGGER
            # =================================

            entry_index = None

            for j in range(i + 1, len(data)):

                candle = data.iloc[j]

                if float(candle["High"]) >= entry:

                    entry_index = j

                    break

            if entry_index is None:
                continue

            # =================================
            # TRADE MANAGEMENT
            # =================================

            status = "OPEN"

            exit_price = None

            exit_date = None

            target_hit = "NONE"

            end_index = min(
                entry_index + self.lookahead_days,
                len(data)
            )

            for j in range(
                entry_index,
                end_index
            ):

                candle = data.iloc[j]

                low = float(candle["Low"])

                high = float(candle["High"])

                # ---------------------------------
                # STOP LOSS
                # ---------------------------------

                if low <= stoploss:

                    status = "LOSS"

                    exit_price = stoploss

                    exit_date = candle.name

                    target_hit = "NONE"

                    break

                # ---------------------------------
                # TARGET 3
                # ---------------------------------

                if high >= target3:

                    status = "WIN"

                    exit_price = target3

                    exit_date = candle.name

                    target_hit = "TARGET3"

                    break

                # ---------------------------------
                # TARGET 2
                # ---------------------------------

                if high >= target2:

                    status = "WIN"

                    exit_price = target2

                    exit_date = candle.name

                    target_hit = "TARGET2"

                    break

                # ---------------------------------
                # TARGET 1
                # ---------------------------------

                if high >= target1:

                    status = "WIN"

                    exit_price = target1

                    exit_date = candle.name

                    target_hit = "TARGET1"

                    break

            # =================================
            # P&L
            # =================================

            pnl = 0

            pnl_percent = 0

            if exit_price is not None:

                pnl = round(
                    exit_price - entry,
                    2
                )

                pnl_percent = round(
                    (pnl / entry) * 100,
                    2
                )

            # =================================
            # SAVE TRADE
            # =================================

            results.append({

                "Date":
                    data.iloc[entry_index].name,

                "Entry":
                    entry,

                "CurrentPrice":
                    current_price,

                "StopLoss":
                    stoploss,

                "Target1":
                    target1,

                "Target2":
                    target2,

                "Target3":
                    target3,

                "RR":
                    round(
                        (target2 - entry) / risk,
                        2
                    ),

                "ExitPrice":
                    exit_price,

                "ExitDate":
                    exit_date,

                "TargetHit":
                    target_hit,

                "Status":
                    status,

                "PnL":
                    pnl,

                "PnLPercent":
                    pnl_percent,

            })

        return self.summary(results)

    # =========================================
    # SUMMARY
    # =========================================

    def summary(self, results):

        total = len(results)

        wins = sum(
            1
            for trade in results
            if trade["Status"] == "WIN"
        )

        losses = sum(
            1
            for trade in results
            if trade["Status"] == "LOSS"
        )

        opens = sum(
            1
            for trade in results
            if trade["Status"] == "OPEN"
        )

        closed = wins + losses

        # =====================================
        # WIN RATE
        # =====================================

        win_rate = (

            round(
                (wins / closed) * 100,
                2
            )

            if closed > 0

            else 0

        )

        # =====================================
        # P&L
        # =====================================

        total_pnl = round(
            sum(
                trade["PnL"]
                for trade in results
            ),
            2
        )

        # =====================================
        # AVERAGE PROFIT
        # =====================================

        profits = [

            trade["PnL"]

            for trade in results

            if trade["PnL"] > 0

        ]

        average_profit = (

            round(
                sum(profits) / len(profits),
                2
            )

            if profits

            else 0

        )

        # =====================================
        # AVERAGE LOSS
        # =====================================

        losses_list = [

            trade["PnL"]

            for trade in results

            if trade["PnL"] < 0

        ]

        average_loss = (

            round(
                sum(losses_list) / len(losses_list),
                2
            )

            if losses_list

            else 0

        )

        # =====================================
        # PROFIT FACTOR
        # =====================================

        gross_profit = sum(profits)

        gross_loss = abs(
            sum(losses_list)
        )

        profit_factor = (

            round(
                gross_profit / gross_loss,
                2
            )

            if gross_loss > 0

            else 0

        )

        # =====================================
        # MAX DRAWDOWN
        # =====================================

        equity = 0

        peak = 0

        max_drawdown = 0

        for trade in results:

            equity += trade["PnL"]

            peak = max(
                peak,
                equity
            )

            drawdown = equity - peak

            max_drawdown = min(
                max_drawdown,
                drawdown
            )

        max_drawdown = round(
            max_drawdown,
            2
        )

                # =====================================
# TARGET PERFORMANCE
# =====================================

target1_wins = sum(
    1
    for trade in results
    if trade["TargetHit"] == "TARGET1"
)

target2_wins = sum(
    1
    for trade in results
    if trade["TargetHit"] == "TARGET2"
)

target3_wins = sum(
    1
    for trade in results
    if trade["TargetHit"] == "TARGET3"
)