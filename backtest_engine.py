# ============================================
# AI STOCK SCANNER V1.3
# ROBUST BACKTEST ENGINE
# ============================================

class BacktestEngine:

    def __init__(self):

        self.lookahead_days = 15
        self.risk_per_trade = 0.01
        self.min_trades_for_ranking = 3

        # Entry / risk settings
        self.entry_atr = 0.25
        self.stop_atr = 1.5

        # BUY RSI range
        self.buy_rsi_min = 50
        self.buy_rsi_max = 72

        # SELL RSI range
        self.sell_rsi_min = 28
        self.sell_rsi_max = 50

        # Debug information
        self.diagnostics = {}

    # =========================================
    # SAFE FLOAT
    # =========================================

    def safe_float(self, value):

        try:
            if value is None:
                return None

            value = float(value)

            if value != value:       # NaN
                return None

            return value

        except (TypeError, ValueError):
            return None

    # =========================================
    # CHECK REQUIRED COLUMNS
    # =========================================

    def validate_columns(self, data):

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

        missing = [
            col
            for col in required
            if col not in data.columns
        ]

        return missing

    # =========================================
    # CREATE DIAGNOSTICS
    # =========================================

    def create_diagnostics(self):

        return {

            "Rows": 0,

            "ValidRows": 0,

            "TrendBuy": 0,

            "MomentumBuy": 0,

            "RSIBuy": 0,

            "VWAPBuy": 0,

            "FinalBuySetup": 0,

            "BuyEntryTriggered": 0,

            "TrendSell": 0,

            "MomentumSell": 0,

            "RSISell": 0,

            "VWAPSell": 0,

            "FinalSellSetup": 0,

            "SellEntryTriggered": 0,

            "TotalSetups": 0,

            "TotalEntries": 0
        }

    # =========================================
    # PROCESS ONE TRADE
    # =========================================

    def simulate_trade(
        self,
        data,
        signal_index,
        direction
    ):

        row = data.iloc[signal_index]

        close = self.safe_float(row["Close"])
        atr = self.safe_float(row["ATR"])

        if close is None or atr is None:
            return None

        if close <= 0 or atr <= 0:
            return None

        # =====================================
        # ENTRY
        # =====================================

        if direction == "BUY":

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

        risk = abs(
            entry - stoploss
        )

        if risk <= 0:
            return None

        # =====================================
        # TARGETS
        # =====================================

        if direction == "BUY":

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

        else:

            target1 = round(
                entry - risk * 1.5,
                2
            )

            target2 = round(
                entry - risk * 2.5,
                2
            )

            target3 = round(
                entry - risk * 4.0,
                2
            )

        # =====================================
        # FIND ENTRY
        # =====================================

        entry_index = None

        for j in range(
            signal_index + 1,
            len(data)
        ):

            candle = data.iloc[j]

            high = self.safe_float(
                candle["High"]
            )

            low = self.safe_float(
                candle["Low"]
            )

            if high is None or low is None:
                continue

            if direction == "BUY":

                if high >= entry:

                    entry_index = j
                    break

            else:

                if low <= entry:

                    entry_index = j
                    break

        if entry_index is None:
            return None

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

        if end_index <= entry_index:
            return None

        last_index = end_index - 1

        for j in range(
            entry_index,
            end_index
        ):

            candle = data.iloc[j]

            high = self.safe_float(
                candle["High"]
            )

            low = self.safe_float(
                candle["Low"]
            )

            if high is None or low is None:
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
            # BUY TRADE
            # =================================

            if direction == "BUY":

                # Conservative rule:
                # SL checked before targets

                if low <= stoploss:

                    status = "LOSS"
                    exit_price = stoploss
                    exit_date = candle.name
                    target_hit = "NONE"

                    break

                if high >= target3:

                    status = "WIN"
                    exit_price = target3
                    exit_date = candle.name
                    target_hit = "TARGET3"

                    break

                if high >= target2:

                    status = "WIN"
                    exit_price = target2
                    exit_date = candle.name
                    target_hit = "TARGET2"

                    break

                if high >= target1:

                    status = "WIN"
                    exit_price = target1
                    exit_date = candle.name
                    target_hit = "TARGET1"

                    break

            # =================================
            # SELL TRADE
            # =================================

            else:

                # Conservative:
                # SL checked before targets

                if high >= stoploss:

                    status = "LOSS"
                    exit_price = stoploss
                    exit_date = candle.name
                    target_hit = "NONE"

                    break

                if low <= target3:

                    status = "WIN"
                    exit_price = target3
                    exit_date = candle.name
                    target_hit = "TARGET3"

                    break

                if low <= target2:

                    status = "WIN"
                    exit_price = target2
                    exit_date = candle.name
                    target_hit = "TARGET2"

                    break

                if low <= target1:

                    status = "WIN"
                    exit_price = target1
                    exit_date = candle.name
                    target_hit = "TARGET1"

                    break

        # =====================================
        # OPEN TRADE
        # =====================================

        if status == "OPEN":

            mark_price = self.safe_float(
                data.iloc[last_index]["Close"]
            )

            if mark_price is None:
                mark_price = close

            current_price = mark_price

            if direction == "BUY":

                unrealized_pnl = (
                    current_price - entry
                )

            else:

                unrealized_pnl = (
                    entry - current_price
                )

            unrealized_pnl = round(
                unrealized_pnl,
                2
            )

        else:

            unrealized_pnl = 0.0
            current_price = exit_price

        # =====================================
        # REALIZED PNL
        # =====================================

        pnl = 0.0

        pnl_percent = 0.0

        r_multiple = 0.0

        if exit_price is not None:

            if direction == "BUY":

                pnl = (
                    exit_price - entry
                )

            else:

                pnl = (
                    entry - exit_price
                )

            pnl = round(
                pnl,
                2
            )

            pnl_percent = round(
                (
                    pnl / entry
                ) * 100,
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

        if direction == "BUY":

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

        mfe = round(
            mfe,
            2
        )

        mae = round(
            mae,
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
        # RESULT
        # =====================================

        return {

            "Date":
                data.iloc[entry_index].name,

            "SignalDate":
                row.name,

            "Direction":
                direction,

            "Entry":
                entry,

            "CurrentPrice":
                round(
                    current_price,
                    2
                ),

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
                    2.5,
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
        }

    # =========================================
    # BACKTEST
    # =========================================

    def run(self, data):

        results = []

        self.diagnostics = (
            self.create_diagnostics()
        )

        if data is None or data.empty:

            return self.summary(
                results
            )

        data = data.copy()

        self.diagnostics["Rows"] = len(
            data
        )

        # =====================================
        # NORMALIZE COLUMNS
        # =====================================

        if hasattr(
            data.columns,
            "levels"
        ):

            try:

                data.columns = [
                    str(col[0])
                    if isinstance(
                        col,
                        tuple
                    )
                    else str(col)
                    for col in data.columns
                ]

            except Exception:
                pass

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

        missing = self.validate_columns(
            data
        )

        if missing:

            self.diagnostics[
                "MissingColumns"
            ] = missing

            return self.summary(
                results
            )

        # =====================================
        # CLEAN
        # =====================================

        data = data.dropna(
            subset=required
        ).copy()

        self.diagnostics[
            "ValidRows"
        ] = len(data)

        if len(data) < 61:

            return self.summary(
                results
            )

        # =====================================
        # HISTORICAL SCAN
        # =====================================

        next_available_index = 60

        for i in range(
            60,
            len(data) - 1
        ):

            if i < next_available_index:
                continue

            row = data.iloc[i]

            close = self.safe_float(
                row["Close"]
            )

            ema20 = self.safe_float(
                row["EMA20"]
            )

            ema50 = self.safe_float(
                row["EMA50"]
            )

            rsi = self.safe_float(
                row["RSI"]
            )

            macd = self.safe_float(
                row["MACD"]
            )

            macd_signal = self.safe_float(
                row["MACD_SIGNAL"]
            )

            atr = self.safe_float(
                row["ATR"]
            )

            vwap = self.safe_float(
                row["VWAP"]
            )

            if any(
                x is None
                for x in [
                    close,
                    ema20,
                    ema50,
                    rsi,
                    macd,
                    macd_signal,
                    atr,
                    vwap
                ]
            ):

                continue

            if (
                close <= 0
                or atr <= 0
            ):

                continue

            # =================================
            # BUY CONDITIONS
            # =================================

            trend_buy = (
                ema20 > ema50
            )

            momentum_buy = (
                macd > macd_signal
            )

            rsi_buy = (
                self.buy_rsi_min
                <= rsi
                <= self.buy_rsi_max
            )

            vwap_buy = (
                close > vwap
            )

            if trend_buy:
                self.diagnostics[
                    "TrendBuy"
                ] += 1

            if momentum_buy:
                self.diagnostics[
                    "MomentumBuy"
                ] += 1

            if rsi_buy:
                self.diagnostics[
                    "RSIBuy"
                ] += 1

            if vwap_buy:
                self.diagnostics[
                    "VWAPBuy"
                ] += 1

            buy_setup = (
                trend_buy
                and momentum_buy
                and rsi_buy
                and vwap_buy
            )

            if buy_setup:

                self.diagnostics[
                    "FinalBuySetup"
                ] += 1

                trade = self.simulate_trade(
                    data,
                    i,
                    "BUY"
                )

                if trade is not None:

                    results.append(
                        trade
                    )

                    self.diagnostics[
                        "BuyEntryTriggered"
                    ] += 1

                    next_available_index = (
                        min(
                            i + self.lookahead_days,
                            len(data)
                        )
                    )

                    continue

            # =================================
            # SELL CONDITIONS
            # =================================

            trend_sell = (
                ema20 < ema50
            )

            momentum_sell = (
                macd < macd_signal
            )

            rsi_sell = (
                self.sell_rsi_min
                <= rsi
                <= self.sell_rsi_max
            )

            vwap_sell = (
                close < vwap
            )

            if trend_sell:
                self.diagnostics[
                    "TrendSell"
                ] += 1

            if momentum_sell:
                self.diagnostics[
                    "MomentumSell"
                ] += 1

            if rsi_sell:
                self.diagnostics[
                    "RSISell"
                ] += 1

            if vwap_sell:
                self.diagnostics[
                    "VWAPSell"
                ] += 1

            sell_setup = (
                trend_sell
                and momentum_sell
                and rsi_sell
                and vwap_sell
            )

            if sell_setup:

                self.diagnostics[
                    "FinalSellSetup"
                ] += 1

                trade = self.simulate_trade(
                    data,
                    i,
                    "SELL"
                )

                if trade is not None:

                    results.append(
                        trade
                    )

                    self.diagnostics[
                        "SellEntryTriggered"
                    ] += 1

                    next_available_index = (
                        min(
                            i + self.lookahead_days,
                            len(data)
                        )
                    )

                    continue

        # =====================================
        # TOTALS
        # =====================================

        self.diagnostics[
            "TotalSetups"
        ] = (
            self.diagnostics[
                "FinalBuySetup"
            ]
            +
            self.diagnostics[
                "FinalSellSetup"
            ]
        )

        self.diagnostics[
            "TotalEntries"
        ] = (
            self.diagnostics[
                "BuyEntryTriggered"
            ]
            +
            self.diagnostics[
                "SellEntryTriggered"
            ]
        )

        return self.summary(
            results
        )

    # =========================================
    # SUMMARY
    # =========================================

    def summary(self, results):

        total = len(results)

        wins = sum(
            1 for trade in results
            if trade.get("Status") == "WIN"
        )

        losses = sum(
            1 for trade in results
            if trade.get("Status") == "LOSS"
        )

        opens = sum(
            1 for trade in results
            if trade.get("Status") == "OPEN"
        )

        closed = wins + losses

        win_rate = (
            round((wins / closed) * 100, 2)
            if closed > 0 else 0.0
        )

        realized_pnl = round(
            sum(float(trade.get("PnL", 0)) for trade in results),
            2
        )

        unrealized_pnl = round(
            sum(float(trade.get("UnrealizedPnL", 0)) for trade in results),
            2
        )

        total_pnl = round(
            realized_pnl + unrealized_pnl,
            2
        )

        profits = [
            float(trade.get("PnL", 0))
            for trade in results
            if float(trade.get("PnL", 0)) > 0
        ]

        losses_list = [
            float(trade.get("PnL", 0))
            for trade in results
            if float(trade.get("PnL", 0)) < 0
        ]

        average_profit = (
            round(sum(profits) / len(profits), 2)
            if profits else 0.0
        )

        average_loss = (
            round(sum(losses_list) / len(losses_list), 2)
            if losses_list else 0.0
        )

        gross_profit = sum(profits)
        gross_loss = abs(sum(losses_list))

        profit_factor = (
            round(gross_profit / gross_loss, 2)
            if gross_loss > 0
            else (999.0 if gross_profit > 0 else 0.0)
        )

        expectancy = (
            round(total_pnl / closed, 2)
            if closed > 0 else 0.0
        )

        closed_r = [
            float(trade.get("RMultiple", 0))
            for trade in results
            if trade.get("Status") in ("WIN", "LOSS")
        ]

        average_r = (
            round(sum(closed_r) / len(closed_r), 2)
            if closed_r else 0.0
        )

        # =========================================
        # MAX DRAWDOWN
        # =========================================

        equity = 0.0
        peak = 0.0
        max_drawdown = 0.0

        for trade in results:

            equity += float(trade.get("PnL", 0))

            peak = max(peak, equity)

            drawdown = equity - peak

            max_drawdown = min(
                max_drawdown,
                drawdown
            )

        max_drawdown = round(
            max_drawdown,
            2
        )

        # =========================================
        # TARGETS
        # =========================================

        target1_wins = sum(
            1 for trade in results
            if trade.get("TargetHit") == "TARGET1"
        )

        target2_wins = sum(
            1 for trade in results
            if trade.get("TargetHit") == "TARGET2"
        )

        target3_wins = sum(
            1 for trade in results
            if trade.get("TargetHit") == "TARGET3"
        )

        # =========================================
        # RISK ADJUSTED SCORE
        # =========================================

        if total > 0:

            pf_component = min(
                profit_factor,
                5.0
            ) * 15.0

            win_component = win_rate * 0.35

            pnl_component = (
                max(
                    min(total_pnl, 500.0),
                    -500.0
                ) * 0.05
            )

            drawdown_penalty = (
                abs(max_drawdown) * 0.05
            )

            expectancy_component = (
                expectancy * 2.0
            )

            sample_factor = min(
                total /
                max(self.min_trades_for_ranking, 1),
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
                raw_score * sample_factor,
                2
            )

        else:

            risk_adjusted_score = 0.0

        return {

            "Total Trades": total,
            "Wins": wins,
            "Losses": losses,
            "Open": opens,
            "Closed Trades": closed,

            "Win Rate": win_rate,

            "Realized PnL": realized_pnl,
            "Unrealized PnL": unrealized_pnl,
            "Total PnL": total_pnl,

            "Average Profit": average_profit,
            "Average Loss": average_loss,

            "Profit Factor": profit_factor,
            "Expectancy": expectancy,
            "Average R": average_r,

            "Max Drawdown": max_drawdown,

            "Target1 Wins": target1_wins,
            "Target2 Wins": target2_wins,
            "Target3 Wins": target3_wins,

            "Risk Adjusted Score": risk_adjusted_score,

            "Trades": results
        }