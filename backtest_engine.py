import pandas as pd


class BacktestEngine:

    def __init__(self):
        self.lookahead_days = 15
        self.risk_per_trade = 0.01
        self.min_trades_for_ranking = 3

    # =========================================
    # BACKTEST ENGINE
    # =========================================

    def run(self, data):

        results = []

        if data is None or data.empty:
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
            "VWAP"
        ]

        # Check required columns
        for column in required:

            if column not in data.columns:
                return self.summary(results)

        # Clean data
        data = data.dropna(
            subset=required
        ).copy()

        if len(data) < 61:
            return self.summary(results)

        # =========================================
        # HISTORICAL SCAN
        # =========================================

        next_available_index = 60

        for i in range(60, len(data) - 1):

            if i < next_available_index:
                continue

            row = data.iloc[i]

            try:

                ema20 = float(row["EMA20"])
                ema50 = float(row["EMA50"])
                rsi = float(row["RSI"])
                macd = float(row["MACD"])
                macd_signal = float(
                    row["MACD_SIGNAL"]
                )
                close = float(row["Close"])
                atr = float(row["ATR"])
                vwap = float(row["VWAP"])

            except (TypeError, ValueError):

                continue

            if atr <= 0 or close <= 0:
                continue

            # =====================================
            # BUY SETUP
            # =====================================

            trend_ok = ema20 > ema50

            momentum_ok = (
                macd > macd_signal
            )

            rsi_ok = (
                55 < rsi < 70
            )

            price_ok = (
                close > vwap
            )

            buy_setup = (
                trend_ok
                and momentum_ok
                and rsi_ok
                and price_ok
            )

            if not buy_setup:
                continue

            # =====================================
            # ENTRY
            # =====================================

            entry = round(
                close + (atr * 0.25),
                2
            )

            stoploss = round(
                entry - (atr * 1.5),
                2
            )

            risk = round(
                entry - stoploss,
                2
            )

            if risk <= 0:
                continue

            # =====================================
            # TARGETS
            # =====================================

            target1 = round(
                entry + (risk * 1.5),
                2
            )

            target2 = round(
                entry + (risk * 2.5),
                2
            )

            target3 = round(
                entry + (risk * 4.0),
                2
            )

            # =====================================
            # FIND ENTRY TRIGGER
            # =====================================

            entry_index = None

            for j in range(
                i + 1,
                len(data)
            ):

                candle = data.iloc[j]

                try:

                    high = float(
                        candle["High"]
                    )

                except (TypeError, ValueError):

                    continue

                if high >= entry:

                    entry_index = j
                    break

            if entry_index is None:
                continue

            # =====================================
            # TRADE MANAGEMENT
            # =====================================

            status = "OPEN"

            exit_price = None
            exit_date = None

            target_hit = "NONE"

            highest_price = entry
            lowest_price = entry

            end_index = min(
                entry_index + self.lookahead_days,
                len(data)
            )

            last_index = end_index - 1

            for j in range(
                entry_index,
                end_index
            ):

                candle = data.iloc[j]

                try:

                    low = float(
                        candle["Low"]
                    )

                    high = float(
                        candle["High"]
                    )

                except (TypeError, ValueError):

                    continue

                highest_price = max(
                    highest_price,
                    high
                )

                lowest_price = min(
                    lowest_price,
                    low
                )

                # =================================
                # STOP LOSS
                # =================================

                if low <= stoploss:

                    status = "LOSS"

                    exit_price = stoploss

                    exit_date = candle.name

                    target_hit = "NONE"

                    break

                # =================================
                # TARGET 3
                # =================================

                if high >= target3:

                    status = "WIN"

                    exit_price = target3

                    exit_date = candle.name

                    target_hit = "TARGET3"

                    break

                # =================================
                # TARGET 2
                # =================================

                if high >= target2:

                    status = "WIN"

                    exit_price = target2

                    exit_date = candle.name

                    target_hit = "TARGET2"

                    break

                # =================================
                # TARGET 1
                # =================================

                if high >= target1:

                    status = "WIN"

                    exit_price = target1

                    exit_date = candle.name

                    target_hit = "TARGET1"

                    break

            # =====================================
            # OPEN TRADE
            # =====================================

            if status == "OPEN":

                try:

                    mark_price = float(
                        data.iloc[last_index]["Close"]
                    )

                except (TypeError, ValueError):

                    mark_price = close

                unrealized_pnl = round(
                    mark_price - entry,
                    2
                )

                current_price = mark_price

            else:

                unrealized_pnl = 0.0

                current_price = (
                    exit_price
                    if exit_price is not None
                    else close
                )

            # =====================================
            # REALIZED P&L
            # =====================================

            pnl = 0.0

            pnl_percent = 0.0

            r_multiple = 0.0

            if exit_price is not None:

                pnl = round(
                    exit_price - entry,
                    2
                )

                pnl_percent = round(
                    (pnl / entry) * 100,
                    2
                )

                r_multiple = round(
                    pnl / risk,
                    2
                )

            else:

                r_multiple = round(
                    unrealized_pnl / risk,
                    2
                )

            # =====================================
            # MFE / MAE
            # =====================================

            mfe = round(
                highest_price - entry,
                2
            )

            mae = round(
                lowest_price - entry,
                2
            )

            mfe_r = round(
                mfe / risk,
                2
            )

            mae_r = round(
                mae / risk,
                2
            )

            # =====================================
            # SAVE TRADE
            # =====================================

            results.append({

                "Date":
                    data.iloc[
                        entry_index
                    ].name,

                "SignalDate":
                    row.name,

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

                "RiskPerTrade":
                    self.risk_per_trade,

                "Quantity":
                    1,

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

                "UnrealizedPnL":
                    unrealized_pnl,

                "TotalPnL":
                    round(
                        pnl + unrealized_pnl,
                        2
                    ),

                "PnLPercent":
                    pnl_percent,

                "RMultiple":
                    r_multiple,

                "MFE":
                    mfe,

                "MAE":
                    mae,

                "MFE_R":
                    mfe_r,

                "MAE_R":
                    mae_r
            })

            # =====================================
            # PREVENT OVERLAPPING TRADES
            # =====================================

            next_available_index = max(
                entry_index + 1,
                end_index
            )

        return self.summary(results)

    # =========================================
    # SUMMARY
    # =========================================

    def summary(self, results):

        total = len(results)

        wins = sum(
            1
            for trade in results
            if trade.get("Status") == "WIN"
        )

        losses = sum(
            1
            for trade in results
            if trade.get("Status") == "LOSS"
        )

        opens = sum(
            1
            for trade in results
            if trade.get("Status") == "OPEN"
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

            else 0.0
        )

        # =====================================
        # P&L
        # =====================================

        realized_pnl = round(
            sum(
                float(
                    trade.get(
                        "PnL",
                        0
                    )
                )
                for trade in results
            ),
            2
        )

        unrealized_pnl = round(
            sum(
                float(
                    trade.get(
                        "UnrealizedPnL",
                        0
                    )
                )
                for trade in results
            ),
            2
        )

        total_pnl = round(
            realized_pnl +
            unrealized_pnl,
            2
        )

        # =====================================
        # PROFITS
        # =====================================

        profits = [

            float(
                trade.get(
                    "PnL",
                    0
                )
            )

            for trade in results

            if float(
                trade.get(
                    "PnL",
                    0
                )
            ) > 0
        ]

        # =====================================
        # LOSSES
        # =====================================

        losses_list = [

            float(
                trade.get(
                    "PnL",
                    0
                )
            )

            for trade in results

            if float(
                trade.get(
                    "PnL",
                    0
                )
            ) < 0
        ]

        average_profit = (

            round(
                sum(profits) /
                len(profits),
                2
            )

            if profits

            else 0.0
        )

        average_loss = (

            round(
                sum(losses_list) /
                len(losses_list),
                2
            )

            if losses_list

            else 0.0
        )

        # =====================================
        # PROFIT FACTOR
        # =====================================

        gross_profit = sum(
            profits
        )

        gross_loss = abs(
            sum(
                losses_list
            )
        )

        if gross_loss > 0:

            profit_factor = round(
                gross_profit /
                gross_loss,
                2
            )

        elif gross_profit > 0:

            profit_factor = 999.0

        else:

            profit_factor = 0.0

        # =====================================
        # EXPECTANCY
        # =====================================

        expectancy = (

            round(
                (
                    (
                        wins /
                        closed
                    )
                    *
                    average_profit
                )
                +
                (
                    (
                        losses /
                        closed
                    )
                    *
                    average_loss
                ),
                2
            )

            if closed > 0

            else 0.0
        )

        # =====================================
        # AVERAGE R
        # =====================================

        closed_r = [

            float(
                trade.get(
                    "RMultiple",
                    0
                )
            )

            for trade in results

            if trade.get(
                "Status"
            ) in (
                "WIN",
                "LOSS"
            )
        ]

        average_r = (

            round(
                sum(closed_r) /
                len(closed_r),
                2
            )

            if closed_r

            else 0.0
        )

        # =====================================
        # MAX DRAWDOWN
        # =====================================

        equity = 0.0

        peak = 0.0

        max_drawdown = 0.0

        for trade in results:

            equity += float(
                trade.get(
                    "PnL",
                    0
                )
            )

            peak = max(
                peak,
                equity
            )

            drawdown = (
                equity -
                peak
            )

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

            if trade.get(
                "TargetHit"
            ) == "TARGET1"
        )

        target2_wins = sum(

            1

            for trade in results

            if trade.get(
                "TargetHit"
            ) == "TARGET2"
        )

        target3_wins = sum(

            1

            for trade in results

            if trade.get(
                "TargetHit"
            ) == "TARGET3"
        )

        # =====================================
        # RISK-ADJUSTED SCORE
        # =====================================

        if total > 0:

            pf_component = (
                min(
                    profit_factor,
                    5.0
                )
                * 15.0
            )

            win_component = (
                win_rate *
                0.35
            )

            pnl_component = (

                max(
                    min(
                        total_pnl,
                        500.0
                    ),
                    -500.0
                )
                * 0.05
            )

            drawdown_penalty = (
                abs(
                    max_drawdown
                )
                * 0.05
            )

            expectancy_component = (
                expectancy *
                2.0
            )

            sample_factor = min(

                total /
                max(
                    self.min_trades_for_ranking,
                    1
                ),

                1.0
            )

            raw_score = (

                pf_component

                + win_component

                + pnl_component

                + expectancy_component

                - drawdown_penalty
            )

            risk_adjusted_score = round(

                raw_score *
                sample_factor,

                2
            )

        else:

            risk_adjusted_score = 0.0

        # =====================================
        # FINAL REPORT
        # =====================================

        return {

            "Total Trades":
                total,

            "Wins":
                wins,

            "Losses":
                losses,

            "Open":
                opens,

            "Closed Trades":
                closed,

            "Win Rate":
                win_rate,

            "Realized PnL":
                realized_pnl,

            "Unrealized PnL":
                unrealized_pnl,

            "Total PnL":
                total_pnl,

            "Average Profit":
                average_profit,

            "Average Loss":
                average_loss,

            "Profit Factor":
                profit_factor,

            "Expectancy":
                expectancy,

            "Average R":
                average_r,

            "Max Drawdown":
                max_drawdown,

            "Target1 Wins":
                target1_wins,

            "Target2 Wins":
                target2_wins,

            "Target3 Wins":
                target3_wins,

            "Risk Adjusted Score":
                risk_adjusted_score,

            "Trades":
                results
        }