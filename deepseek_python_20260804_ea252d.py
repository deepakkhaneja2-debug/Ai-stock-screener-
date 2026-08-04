import pandas as pd
from brokerage_engine import BrokerageEngine   # Single import
import numpy as np


class BacktestEngine:

    def __init__(self):

        # ==================================
        # PROFESSIONAL SETTINGS
        # ==================================

        self.enable_brokerage = True
        self.enable_slippage = True
        self.enable_partial_exit = True
        self.enable_trailing = True

        self.partial_qty_1 = 0.25
        self.partial_qty_2 = 0.25
        self.partial_qty_3 = 0.50

        self.trailing_atr = 2

        self.initial_capital = 100000
        self.current_equity = self.initial_capital
        self.equity_curve = []

        self.brokerage = BrokerageEngine()

        # ==============================
        # BACKTEST SETTINGS
        # ==============================

        self.lookahead_days = 15
        self.risk_per_trade = 0.01
        self.min_trades_for_ranking = 5

        # Entry trigger
        self.entry_atr_buffer = 0.25

        # Stop loss
        self.stop_atr_multiplier = 1.5

        # Targets
        self.target1_r = 1.5
        self.target2_r = 2.5
        self.target3_r = 4.0

        # Break-even after T1
        self.use_break_even = True

        # ==============================
        # RANKING SETTINGS
        # ==============================

        self.max_profit_factor = 5.0

    # ==========================================================
    # MAIN BACKTEST
    # ==========================================================

    def run(self, data):

        results = []

        # ------------------------------------------
        # EMPTY DATA
        # ------------------------------------------

        if data is None or data.empty:

            return self.summary(results)

        data = data.copy()

        # ------------------------------------------
        # REQUIRED COLUMNS
        # ------------------------------------------

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

        # ------------------------------------------
        # CLEAN DATA
        # ------------------------------------------

        data = data.dropna(
            subset=required
        ).copy()

        if len(data) < 61:

            return self.summary(results)

        # ------------------------------------------
        # SORT DATA
        # ------------------------------------------

        try:

            data = data.sort_index()

        except Exception:

            pass

        # ------------------------------------------
        # PREVENT OVERLAPPING TRADES
        # ------------------------------------------

        next_available_index = 60

        # ======================================================
        # HISTORICAL SCAN
        # ======================================================

        for i in range(
            60,
            len(data) - 1
        ):

            if i < next_available_index:

                continue

            row = data.iloc[i]

            # ------------------------------------------
            # READ INDICATORS
            # ------------------------------------------

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

            except (
                TypeError,
                ValueError
            ):

                continue

            if atr <= 0:

                continue

            if close <= 0:

                continue

            # ==================================================
            # BUY SETUP
            # ==================================================

            trend_ok = (
                ema20 > ema50
            )

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

            # ==================================================
            # ENTRY
            # ==================================================

            entry = round(
                close +
                (atr * self.entry_atr_buffer),
                2
            )

            if self.enable_slippage:

                entry += self.brokerage.slippage_price(entry)

            stoploss = round(
                entry -
                (
                    atr *
                    self.stop_atr_multiplier
                ),
                2
            )

            risk = round(
                entry - stoploss,
                2
            )

            if risk <= 0:

                continue

            # ==================================================
            # TARGETS
            # ==================================================

            target1 = round(
                entry +
                (
                    risk *
                    self.target1_r
                ),
                2
            )

            target2 = round(
                entry +
                (
                    risk *
                    self.target2_r
                ),
                2
            )

            target3 = round(
                entry +
                (
                    risk *
                    self.target3_r
                ),
                2
            )

            # ==================================================
            # FIND ENTRY TRIGGER
            # ==================================================

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

                except (
                    TypeError,
                    ValueError
                ):

                    continue

                if high >= entry:

                    entry_index = j

                    break

            if entry_index is None:

                continue

            # ==================================================
            # TRADE MANAGEMENT
            # ==================================================

            status = "OPEN"

            remaining_qty = 1.0

            realized_pnl = 0

            charges_paid = 0

            partial_exit_done = False

            partial2_exit_done = False

            exit_price = None

            exit_date = None

            exit_reason = "OPEN"

            target_hit = "NONE"

            highest_price = entry

            lowest_price = entry

            current_stop = stoploss

            target1_reached = False

            end_index = min(
                entry_index +
                self.lookahead_days,
                len(data)
            )

            last_index = (
                end_index - 1
            )

            holding_days = 0

            # ==================================================
            # CANDLE LOOP
            # ==================================================

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

                    candle_close = float(
                        candle["Close"]
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    continue

                holding_days = (
                    j -
                    entry_index +
                    1
                )

                highest_price = max(
                    highest_price,
                    high
                )

                lowest_price = min(
                    lowest_price,
                    low
                )

                # ==================================================
                # BREAK-EVEN LOGIC
                # ==================================================

                if (
                    self.use_break_even
                    and high >= target1
                    and not target1_reached
                ):

                    target1_reached = True

                    current_stop = entry

                # ==================================================
                # STOP LOSS
                #
                # Conservative rule:
                # If SL and target are both touched
                # on same candle, SL is considered first.
                # ==================================================

                if low <= current_stop:

                    status = (
                        "WIN"
                        if target1_reached
                        else "LOSS"
                    )

                    exit_price = (
                        entry
                        if target1_reached
                        else current_stop
                    )

                    exit_date = candle.name

                    if target1_reached:

                        target_hit = (
                            "TARGET1"
                        )

                        exit_reason = (
                            "BREAK_EVEN"
                        )

                    else:

                        target_hit = (
                            "NONE"
                        )

                        exit_reason = (
                            "STOP_LOSS"
                        )

                    break

                # ==================================================
                # TARGET 3
                # ==================================================

                if high >= target3:

                    status = "WIN"

                    exit_price = target3

                    exit_date = candle.name

                    target_hit = (
                        "TARGET3"
                    )

                    exit_reason = (
                        "TARGET3"
                    )

                    break

                # ==================================================
                # TARGET 2
                # ==================================================

                if high >= target2:

                    status = "WIN"

                    exit_price = target2

                    exit_date = candle.name

                    target_hit = (
                        "TARGET2"
                    )

                    exit_reason = (
                        "TARGET2"
                    )

                    break

                # ==================================================
                # TARGET 1
                # ==================================================

                if high >= target1:

                    target1_reached = True

                    # ------------------------------------------
                    # Do NOT immediately close.
                    # Move SL to break-even and allow
                    # the trade to continue toward T2/T3.
                    # ------------------------------------------

                    current_stop = entry

            # ==================================================
            # OPEN TRADE
            # ==================================================

            if status == "OPEN":

                try:

                    mark_price = float(
                        data.iloc[
                            last_index
                        ]["Close"]
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    mark_price = close

                current_price = mark_price

                unrealized_pnl = round(
                    mark_price -
                    entry,
                    2
                )

                exit_reason = (
                    "TIME_EXIT"
                )

                # ------------------------------------------
                # Optional time-based classification
                # ------------------------------------------

                if unrealized_pnl > 0:

                    status = "OPEN_PROFIT"

                elif unrealized_pnl < 0:

                    status = "OPEN_LOSS"

                else:

                    status = "OPEN"

            else:

                current_price = (
                    exit_price
                    if exit_price is not None
                    else close
                )

                unrealized_pnl = 0.0

            # ==================================================
            # REALIZED P&L
            # ==================================================

            pnl = 0.0

            pnl_percent = 0.0

            r_multiple = 0.0

            if exit_price is not None:

                pnl = round(
                    exit_price -
                    entry,
                    2
                )

                pnl_percent = round(
                    (
                        pnl /
                        entry
                    ) *
                    100,
                    2
                )

                r_multiple = round(
                    pnl /
                    risk,
                    2
                )

            else:

                r_multiple = round(
                    unrealized_pnl /
                    risk,
                    2
                )

            # ==========================================
            # BROKERAGE CALCULATION
            # ==========================================

            gross_pnl = pnl
            net_pnl = pnl

            charges = {
                "Brokerage": 0,
                "STT": 0,
                "Exchange": 0,
                "GST": 0,
                "SEBI": 0,
                "Stamp": 0,
                "TotalCharges": 0
            }

            if self.enable_brokerage and exit_price is not None:

                calc = self.brokerage.net_pnl(
                    buy_price=entry,
                    sell_price=exit_price,
                    qty=1
                )

                gross_pnl = calc["GrossPnL"]
                net_pnl = calc["NetPnL"]
                charges = calc["Charges"]

            # ==================================================
            # MFE / MAE
            # ==================================================

            mfe = round(
                highest_price -
                entry,
                2
            )

            mae = round(
                lowest_price -
                entry,
                2
            )

            mfe_r = round(
                mfe /
                risk,
                2
            )

            mae_r = round(
                mae /
                risk,
                2
            )

            # ==================================================
            # SAVE TRADE
            # ==================================================

            results.append({

                "GrossPnL": gross_pnl,
                "NetPnL": net_pnl,
                "Brokerage": charges["Brokerage"],
                "Charges": charges["TotalCharges"],
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

                "CurrentStop":
                    current_stop,

                "Target1":
                    target1,

                "Target2":
                    target2,

                "Target3":
                    target3,

                "RR":
                    round(
                        (
                            target2 -
                            entry
                        ) /
                        risk,
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

                "HoldingDays":
                    holding_days,

                "TargetHit":
                    target_hit,

                "ExitReason":
                    exit_reason,

                "Status":
                    status,

                "PnL": net_pnl,

                "UnrealizedPnL":
                    unrealized_pnl,

                "TotalPnL":
                    round(
                        net_pnl +
                        unrealized_pnl,
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

            # ==================================================
            # PREVENT OVERLAPPING TRADES
            # ==================================================

            next_available_index = max(
                entry_index + 1,
                end_index
            )

        return self.summary(
            results
        )

    # ==========================================================
    # SUMMARY
    # ==========================================================

    def summary(self, results):

        total = len(results)

        # ======================================================
        # CLOSED TRADE COUNTS
        # ======================================================

        wins = sum(
            1
            for trade in results
            if trade.get(
                "Status"
            ) == "WIN"
        )

        losses = sum(
            1
            for trade in results
            if trade.get(
                "Status"
            ) == "LOSS"
        )

        open_trades = sum(
            1
            for trade in results
            if trade.get(
                "Status"
            ) in (
                "OPEN",
                "OPEN_PROFIT",
                "OPEN_LOSS"
            )
        )

        closed = (
            wins +
            losses
        )

        # ======================================================
        # WIN RATE
        # ======================================================

        win_rate = (

            round(
                (
                    wins /
                    closed
                ) *
                100,
                2
            )

            if closed > 0

            else 0.0
        )

        # ======================================================
        # REALIZED NET P&L
        # ======================================================

        realized_pnl = round(

            sum(
                float(
                    trade.get(
                        "NetPnL",
                        0
                    )
                )

                for trade in results
            ),

            2
        )

        # ======================================================
        # UNREALIZED P&L
        # ======================================================

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

        # ======================================================
        # TOTAL P&L
        # ======================================================

        total_pnl = round(

            realized_pnl +
            unrealized_pnl,

            2
        )

        # ======================================================
        # CLOSED PROFITS
        # ======================================================

        profits = [

            float(
                trade.get(
                    "PnL",
                    0
                )
            )

            for trade in results

            if (
                trade.get(
                    "Status"
                ) == "WIN"
                and
                float(
                    trade.get(
                        "PnL",
                        0
                    )
                ) > 0
            )
        ]

        # ======================================================
        # CLOSED LOSSES
        # ======================================================

        losses_list = [

            float(
                trade.get(
                    "PnL",
                    0
                )
            )

            for trade in results

            if (
                trade.get(
                    "Status"
                ) == "LOSS"
                and
                float(
                    trade.get(
                        "PnL",
                        0
                    )
                ) < 0
            )
        ]

        # ======================================================
        # AVERAGE PROFIT
        # ======================================================

        average_profit = (

            round(
                sum(profits) /
                len(profits),
                2
            )

            if profits

            else 0.0
        )

        # ======================================================
        # AVERAGE LOSS
        # ======================================================

        average_loss = (

            round(
                sum(losses_list) /
                len(losses_list),
                2
            )

            if losses_list

            else 0.0
        )

        # ======================================================
        # GROSS PROFIT / LOSS
        # ======================================================

        gross_profit = sum(
            profits
        )

        gross_loss = abs(
            sum(
                losses_list
            )
        )

        # ======================================================
        # PROFIT FACTOR
        # ======================================================

        if gross_loss > 0:

            profit_factor = round(
                gross_profit /
                gross_loss,
                2
            )

        elif gross_profit > 0:

            # Avoid artificially giving 999
            # for very small samples.

            if closed >= self.min_trades_for_ranking:

                profit_factor = 10.0

            else:

                profit_factor = 0.0

        else:

            profit_factor = 0.0

        # ======================================================
        # EXPECTANCY
        # ======================================================

        if closed > 0:

            expectancy = round(

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

        else:

            expectancy = 0.0

        # ======================================================
        # AVERAGE R
        # ======================================================

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

        # ======================================================
        # MAX DRAWDOWN
        # ======================================================

        equity = 0.0

        peak = 0.0

        max_drawdown = 0.0

        for trade in results:

            # Only realized P&L is used
            # for historical drawdown.

            equity += float(
                trade.get(
                    "PnL",
                    0
                )
            )

            if equity > peak:

                peak = equity

            drawdown = (
                equity -
                peak
            )

            if drawdown < max_drawdown:

                max_drawdown = drawdown

        max_drawdown = round(
            max_drawdown,
            2
        )

        # ======================================================
        # TARGET PERFORMANCE
        # ======================================================

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

        # ======================================================
        # BREAK-EVEN TRADES
        # ======================================================

        break_even_trades = sum(

            1

            for trade in results

            if trade.get(
                "ExitReason"
            ) == "BREAK_EVEN"
        )

        # ======================================================
        # RISK ADJUSTED SCORE
        # ======================================================

        if closed > 0:

            # ----------------------------------------------
            # Profit Factor Component
            # ----------------------------------------------

            pf_component = (

                min(
                    profit_factor,
                    self.max_profit_factor
                )
                /
                self.max_profit_factor
            ) * 30.0

            # ----------------------------------------------
            # Win Rate Component
            # ----------------------------------------------

            win_component = (
                win_rate *
                0.30
            )

            # ----------------------------------------------
            # Expectancy Component
            # ----------------------------------------------

            expectancy_component = (

                max(
                    min(
                        expectancy,
                        100.0
                    ),
                    -100.0
                )
                *
                0.15
            )

            # ----------------------------------------------
            # Average R Component
            # ----------------------------------------------

            r_component = (

                max(
                    min(
                        average_r,
                        3.0
                    ),
                    -3.0
                )
                *
                5.0
            )

            # ----------------------------------------------
            # Drawdown Penalty
            # ----------------------------------------------

            drawdown_penalty = (

                abs(
                    max_drawdown
                )
                *
                0.05
            )

            raw_score = (

                pf_component

                +
                win_component

                +
                expectancy_component

                +
                r_component

                -
                drawdown_penalty
            )

            # ----------------------------------------------
            # SAMPLE SIZE PENALTY
            # ----------------------------------------------

            sample_factor = min(

                closed /
                max(
                    self.min_trades_for_ranking,
                    1
                ),

                1.0
            )

            risk_adjusted_score = round(

                raw_score *
                sample_factor,

                2
            )

        else:

            risk_adjusted_score = 0.0

        # ======================================================
        # DATA QUALITY
        # ======================================================

        if closed == 0:

            data_quality = (
                "NO CLOSED TRADES"
            )

        elif closed < self.min_trades_for_ranking:

            data_quality = (
                "LOW SAMPLE"
            )

        else:

            data_quality = (
                "SUFFICIENT SAMPLE"
            )

        # ======================================================
        # FINAL REPORT
        # ======================================================

        return {

            "Total Trades":
                total,

            "Wins":
                wins,

            "Losses":
                losses,

            "Open":
                open_trades,

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

            "BreakEven Trades":
                break_even_trades,

            "Risk Adjusted Score":
                risk_adjusted_score,

            "Data Quality":
                data_quality,

            "Trades":
                results
        }