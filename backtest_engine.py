import math


class BacktestEngine:

    def __init__(self):
        self.lookahead_days = 15
        self.risk_per_trade = 0.01
        self.min_trades_for_ranking = 3

        # Risk : Reward
        self.target1_rr = 1.5
        self.target2_rr = 2.5
        self.target3_rr = 4.0

        # ATR settings
        self.entry_atr = 0.25
        self.stop_atr = 1.5

        # Starting capital
        self.starting_capital = 100000

    # =========================================
    # POSITION SIZE
    # =========================================

    def position_size(self, entry, stoploss, capital):

        risk_amount = capital * self.risk_per_trade

        risk_per_share = abs(entry - stoploss)

        if risk_per_share <= 0:
            return 0

        quantity = math.floor(
            risk_amount / risk_per_share
        )

        return max(quantity, 1)

    # =========================================
    # BUY SETUP
    # =========================================

    def buy_setup(self, row):

        try:

            ema20 = float(row["EMA20"])
            ema50 = float(row["EMA50"])
            rsi = float(row["RSI"])
            macd = float(row["MACD"])
            macd_signal = float(row["MACD_SIGNAL"])
            close = float(row["Close"])
            vwap = float(row["VWAP"])

        except (TypeError, ValueError):

            return False

        return (
            ema20 > ema50
            and macd > macd_signal
            and 55 < rsi < 70
            and close > vwap
        )

    # =========================================
    # SELL SETUP
    # =========================================

    def sell_setup(self, row):

        try:

            ema20 = float(row["EMA20"])
            ema50 = float(row["EMA50"])
            rsi = float(row["RSI"])
            macd = float(row["MACD"])
            macd_signal = float(row["MACD_SIGNAL"])
            close = float(row["Close"])
            vwap = float(row["VWAP"])

        except (TypeError, ValueError):

            return False

        return (
            ema20 < ema50
            and macd < macd_signal
            and 30 < rsi < 45
            and close < vwap
        )

    # =========================================
    # BACKTEST
    # =========================================

    def run(self, data, capital=None):

        results = []

        if data is None or data.empty:
            return self.summary(results)

        data = data.copy()

        if capital is None:
            capital = self.starting_capital

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

        data = data.dropna(
            subset=required
        ).copy()

        if len(data) < 61:
            return self.summary(results)

        next_available_index = 60

        # =====================================
        # HISTORICAL SCAN
        # =====================================

        for i in range(60, len(data) - 1):

            if i < next_available_index:
                continue

            row = data.iloc[i]

            try:

                close = float(row["Close"])
                atr = float(row["ATR"])

            except (TypeError, ValueError):

                continue

            if close <= 0 or atr <= 0:
                continue

            # =================================
            # SIGNAL
            # =================================

            is_buy = self.buy_setup(row)

            is_sell = self.sell_setup(row)

            if not is_buy and not is_sell:
                continue

            signal = "BUY" if is_buy else "SELL"

            # =================================
            # ENTRY
            # =================================

            if signal == "BUY":

                entry = round(
                    close + atr * self.entry_atr,
                    2
                )

                stoploss = round(
                    entry - atr * self.stop_atr,
                    2
                )

            else:

                entry = round(
                    close - atr * self.entry_atr,
                    2
                )

                stoploss = round(
                    entry + atr * self.stop_atr,
                    2
                )

            risk_per_share = abs(
                entry - stoploss
            )

            if risk_per_share <= 0:
                continue

            # =================================
            # TARGETS
            # =================================

            if signal == "BUY":

                target1 = round(
                    entry + risk_per_share * self.target1_rr,
                    2
                )

                target2 = round(
                    entry + risk_per_share * self.target2_rr,
                    2
                )

                target3 = round(
                    entry + risk_per_share * self.target3_rr,
                    2
                )

            else:

                target1 = round(
                    entry - risk_per_share * self.target1_rr,
                    2
                )

                target2 = round(
                    entry - risk_per_share * self.target2_rr,
                    2
                )

                target3 = round(
                    entry - risk_per_share * self.target3_rr,
                    2
                )

            # =================================
            # QUANTITY
            # =================================

            quantity = self.position_size(
                entry,
                stoploss,
                capital
            )

            if quantity <= 0:
                continue

            # =================================
            # ENTRY TRIGGER
            # =================================

            entry_index = None

            for j in range(
                i + 1,
                len(data)
            ):

                candle = data.iloc[j]

                try:

                    high = float(candle["High"])
                    low = float(candle["Low"])

                except (TypeError, ValueError):

                    continue

                if signal == "BUY":

                    if high >= entry:
                        entry_index = j
                        break

                else:

                    if low <= entry:
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

                    high = float(candle["High"])
                    low = float(candle["Low"])

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
                # BUY MANAGEMENT
                # =================================

                if signal == "BUY":

                    # Stop first
                    if low <= stoploss:

                        status = "LOSS"

                        exit_price = stoploss

                        exit_date = candle.name

                        target_hit = "NONE"

                        break

                    # Target 3
                    if high >= target3:

                        status = "WIN"

                        exit_price = target3

                        exit_date = candle.name

                        target_hit = "TARGET3"

                        break

                    # Target 2
                    if high >= target2:

                        status = "WIN"

                        exit_price = target2

                        exit_date = candle.name

                        target_hit = "TARGET2"

                        break

                    # Target 1
                    if high >= target1:

                        status = "WIN"

                        exit_price = target1

                        exit_date = candle.name

                        target_hit = "TARGET1"

                        break

                # =================================
                # SELL MANAGEMENT
                # =================================

                else:

                    # Stop first
                    if high >= stoploss:

                        status = "LOSS"

                        exit_price = stoploss

                        exit_date = candle.name

                        target_hit = "NONE"

                        break

                    # Target 3
                    if low <= target3:

                        status = "WIN"

                        exit_price = target3

                        exit_date = candle.name

                        target_hit = "TARGET3"

                        break

                    # Target 2
                    if low <= target2:

                        status = "WIN"

                        exit_price = target2

                        exit_date = candle.name

                        target_hit = "TARGET2"

                        break

                    # Target 1
                    if low <= target1:

                        status = "WIN"

                        exit_price = target1

                        exit_date = candle.name

                        target_hit = "TARGET1"

                        break

            # =================================
            # OPEN TRADE
            # =================================

            if status == "OPEN":

                try:

                    mark_price = float(
                        data.iloc[last_index]["Close"]
                    )

                except (TypeError, ValueError):

                    mark_price = close

                if signal == "BUY":

                    unrealized_per_share = (
                        mark_price - entry
                    )

                else:

                    unrealized_per_share = (
                        entry - mark_price
                    )

                unrealized_pnl = round(
                    unrealized_per_share * quantity,
                    2
                )

                current_price = mark_price

            else:

                unrealized_pnl = 0.0

                current_price = close

            # =================================
            # REALIZED P&L
            # =================================

            pnl = 0.0

            pnl_percent = 0.0

            r_multiple = 0.0

            if exit_price is not None:

                if signal == "BUY":

                    pnl_per_share = (
                        exit_price - entry
                    )

                else:

                    pnl_per_share = (
                        entry - exit_price
                    )

                pnl = round(
                    pnl_per_share * quantity,
                    2
                )

                pnl_percent = round(
                    (
                        pnl /
                        (entry * quantity)
                    ) * 100,
                    2
                )

                risk_amount = (
                    risk_per_share *
                    quantity
                )

                if risk_amount > 0:

                    r_multiple = round(
                        pnl /
                        risk_amount,
                        2
                    )

            else:

                risk_amount = (
                    risk_per_share *
                    quantity
                )

                if risk_amount > 0:

                    r_multiple = round(
                        unrealized_pnl /
                        risk_amount,
                        2
                    )

            # =================================
            # MFE / MAE
            # =================================

            if signal == "BUY":

                mfe = (
                    highest_price - entry
                )

                mae = (
                    lowest_price - entry
                )

            else:

                mfe = (
                    entry - lowest_price
                )

                mae = (
                    entry - highest_price
                )

            mfe = round(mfe, 2)
            mae = round(mae, 2)

            mfe_r = round(
                mfe / risk_per_share,
                2
            )

            mae_r = round(
                mae / risk_per_share,
                2
            )

            # =================================
            # SAVE TRADE
            # =================================

            results.append({

                "Signal": signal,

                "SignalDate": row.name,

                "Date": data.iloc[
                    entry_index
                ].name,

                "Entry": entry,

                "CurrentPrice": current_price,

                "StopLoss": stoploss,

                "Target1": target1,

                "Target2": target2,

                "Target3": target3,

                "RR": round(
                    self.target2_rr,
                    2
                ),

                "RiskPerTrade": self.risk_per_trade,

                "Quantity": quantity,

                "RiskAmount": round(
                    risk_amount,
                    2
                ),

                "ExitPrice": exit_price,

                "ExitDate": exit_date,

                "TargetHit": target_hit,

                "Status": status,

                "PnL": pnl,

                "UnrealizedPnL": unrealized_pnl,

                "TotalPnL": round(
                    pnl + unrealized_pnl,
                    2
                ),

                "PnLPercent": pnl_percent,

                "RMultiple": r_multiple,

                "MFE": mfe,

                "MAE": mae,

                "MFE_R": mfe_r,

                "MAE_R": mae_r

            })

            # Prevent overlapping trades

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

        win_rate = round(
            wins / closed * 100,
            2
        ) if closed > 0 else 0.0

        # =====================================
        # P&L
        # =====================================

        realized_pnl = round(
            sum(
                trade["PnL"]
                for trade in results
            ),
            2
        )

        unrealized_pnl = round(
            sum(
                trade["UnrealizedPnL"]
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
            trade["PnL"]
            for trade in results
            if trade["PnL"] > 0
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

        # =====================================
        # LOSSES
        # =====================================

        losses_list = [
            trade["PnL"]
            for trade in results
            if trade["PnL"] < 0
        ]

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

        gross_profit = sum(profits)

        gross_loss = abs(
            sum(losses_list)
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

        if closed > 0:

            expectancy = round(
                (
                    wins /
                    closed
                ) * average_profit
                +
                (
                    losses /
                    closed
                ) * average_loss,
                2
            )

        else:

            expectancy = 0.0

        # =====================================
        # AVERAGE R
        # =====================================

        closed_r = [
            trade["RMultiple"]
            for trade in results
            if trade["Status"]
            in ("WIN", "LOSS")
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

            equity += trade["PnL"]

            peak = max(
                peak,
                equity
            )

            drawdown = (
                equity - peak
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
            if trade["TargetHit"]
            == "TARGET1"
        )

        target2_wins = sum(
            1
            for trade in results
            if trade["TargetHit"]
            == "TARGET2"
        )
