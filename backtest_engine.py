class BacktestEngine:

    def __init__(self):

        self.lookahead_days = 15

        # V1.3 Risk Management
        self.break_even_after_target1 = True
        self.trailing_after_target1 = True

        # Trailing stop distance
        self.trailing_atr_multiplier = 1.0

    # =========================================
    # BACKTEST
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

        for column in required:

            if column not in data.columns:
                return self.summary(results)

        # =====================================
        # HISTORICAL SCAN
        # =====================================

        for i in range(60, len(data) - 1):

            row = data.iloc[i]

            try:

                ema20 = float(row["EMA20"])
                ema50 = float(row["EMA50"])
                rsi = float(row["RSI"])
                macd = float(row["MACD"])
                macd_signal = float(row["MACD_SIGNAL"])
                close = float(row["Close"])
                atr = float(row["ATR"])
                vwap = float(row["VWAP"])

            except (TypeError, ValueError):

                continue

            if atr <= 0:
                continue

            # =================================
            # V1.3 BUY SETUP
            # =================================

            trend_ok = ema20 > ema50

            momentum_ok = macd > macd_signal

            rsi_ok = 55 < rsi < 70

            price_ok = close > vwap

            buy_setup = (
                trend_ok
                and momentum_ok
                and rsi_ok
                and price_ok
            )

            if not buy_setup:
                continue

            # =================================
            # ENTRY
            # =================================

            entry = round(
                close + atr * 0.25,
                2
            )

            initial_stoploss = round(
                entry - atr * 1.5,
                2
            )

            stoploss = initial_stoploss

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
            # ENTRY TRIGGER
            # =================================

            entry_index = None

            for j in range(i + 1, len(data)):

                candle = data.iloc[j]

                try:

                    high = float(candle["High"])

                except (TypeError, ValueError):

                    continue

                if high >= entry:

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

            target1_reached = False
            target2_reached = False
            target3_reached = False

            current_stoploss = stoploss

            end_index = min(
                entry_index + self.lookahead_days,
                len(data)
            )

            # =================================
            # TRADE LOOP
            # =================================

            for j in range(
                entry_index,
                end_index
            ):

                candle = data.iloc[j]

                try:

                    low = float(candle["Low"])

                    high = float(candle["High"])

                    candle_atr = float(candle["ATR"])

                except (TypeError, ValueError):

                    continue

                if candle_atr <= 0:

                    candle_atr = atr

                # =================================
                # TARGET 3
                # =================================

                if high >= target3:

                    target3_reached = True

                    status = "WIN"

                    exit_price = target3

                    exit_date = candle.name

                    target_hit = "TARGET3"

                    break

                # =================================
                # TARGET 2
                # =================================

                if high >= target2:

                    target2_reached = True

                    # Move SL to Target1
                    current_stoploss = max(
                        current_stoploss,
                        target1
                    )

                # =================================
                # TARGET 1
                # =================================

                if high >= target1:

                    target1_reached = True

                    # Break-even
                    if self.break_even_after_target1:

                        current_stoploss = max(
                            current_stoploss,
                            entry
                        )

                # =================================
                # TRAILING STOP
                # =================================

                if (
                    target1_reached
                    and self.trailing_after_target1
                ):

                    trailing_stop = round(
                        high
                        - candle_atr
                        * self.trailing_atr_multiplier,
                        2
                    )

                    current_stoploss = max(
                        current_stoploss,
                        trailing_stop
                    )

                # =================================
                # STOP LOSS
                # =================================

                if low <= current_stoploss:

                    exit_price = current_stoploss

                    exit_date = candle.name

                    if current_stoploss >= entry:

                        status = "WIN"

                        if target2_reached:

                            target_hit = "TARGET2"

                        elif target1_reached:

                            target_hit = "TARGET1"

                        else:

                            target_hit = "BREAKEVEN"

                    else:

                        status = "LOSS"

                        target_hit = "NONE"

                    break

            # =================================
            # OPEN TRADE
            # =================================

            if exit_price is None:

                status = "OPEN"

                exit_price = None

                exit_date = None

                target_hit = "NONE"

            # =================================
            # P&L
            # =================================

            pnl = 0.0

            pnl_percent = 0.0

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
                    close,

                "InitialSL":
                    initial_stoploss,

                "FinalSL":
                    current_stoploss,

                "StopLoss":
                    current_stoploss,

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

                "Target1Reached":
                    target1_reached,

                "Target2Reached":
                    target2_reached,

                "Target3Reached":
                    target3_reached,

                "TargetHit":
                    target_hit,

                "Status":
                    status,

                "PnL":
                    pnl,

                "PnLPercent":
                    pnl_percent
            })

        return self.summary(results)

    # =========================================
    # SUMMARY
    # =========================================

    def summary(self, results):

        total = len(results)

        # =====================================
        # WINS
        # =====================================

        wins = sum(
            1
            for trade in results
            if trade["Status"] == "WIN"
        )

        # =====================================
        # LOSSES
        # =====================================

        losses = sum(
            1
            for trade in results
            if trade["Status"] == "LOSS"
        )

        # =====================================
        # OPEN
        # =====================================

        opens = sum(
            1
            for trade in results
            if trade["Status"] == "OPEN"
        )

        # =====================================
        # CLOSED
        # =====================================

        closed = wins + losses

        # =====================================
        # WIN RATE
        # =====================================

        if closed > 0:

            win_rate = round(
                (wins / closed) * 100,
                2
            )

        else:

            win_rate = 0.0

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
        # PROFITS
        # =====================================

        profits = [

            trade["PnL"]

            for trade in results

            if trade["PnL"] > 0
        ]

        if profits:

            average_profit = round(
                sum(profits)
                / len(profits),
                2
            )

        else:

            average_profit = 0.0

        # =====================================
        # LOSSES
        # =====================================

        losses_list = [

            trade["PnL"]

            for trade in results

            if trade["PnL"] < 0
        ]

        if losses_list:

            average_loss = round(
                sum(losses_list)
                / len(losses_list),
                2
            )

        else:

            average_loss = 0.0

        # =====================================
        # PROFIT FACTOR
        # =====================================

        gross_profit = sum(profits)

        gross_loss = abs(
            sum(losses_list)
        )

        if gross_loss > 0:

            profit_factor = round(
                gross_profit
                / gross_loss,
                2
            )

        elif gross_profit > 0:

            profit_factor = float("inf")

        else:

            profit_factor = 0.0

        # =====================================
        # MAX DRAWDOWN
        # =====================================

        equity = 0.0

        peak = 0.0

        max_drawdown = 0.0

        for trade in results:

            equity += trade["PnL"]

            if equity > peak:

                peak = equity

            drawdown = equity - peak

            if drawdown < max_drawdown:

                max_drawdown = drawdown

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
            if trade["TargetHit"]
            in ["TARGET1", "BREAKEVEN"]
        )

        target2_wins = sum(
            1
            for trade in results
            if trade["TargetHit"]
            == "TARGET2"
        )

        target3_wins = sum(
            1
            for trade in results
            if trade["TargetHit"]
            == "TARGET3"
        )

        # =====================================
        # BREAKEVEN
        # =====================================

        breakeven_trades = sum(
            1
            for trade in results
            if trade["TargetHit"]
            == "BREAKEVEN"
        )

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

            "Breakeven":
                breakeven_trades,

            "Win Rate":
                win_rate,

            "Total PnL":
                total_pnl,

            "Average Profit":
                average_profit,

            "Average Loss":
                average_loss,

            "Profit Factor":
                profit_factor,

            "Max Drawdown":
                max_drawdown,

            "Target1 Wins":
                target1_wins,

            "Target2 Wins":
                target2_wins,

            "Target3 Wins":
                target3_wins,

            "Trades":
                results
        }