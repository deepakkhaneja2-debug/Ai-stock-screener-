import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class BacktestEngine:
    """Runs historical backtests with trade management."""

    def __init__(self):
        self.lookahead_days = 15
        self.risk_per_trade = 0.01
        self.entry_atr_buffer = 0.25
        self.stop_atr_multiplier = 1.5
        self.target1_r = 1.5
        self.target2_r = 2.5
        self.target3_r = 4.0
        self.use_break_even = True
        self.min_trades_for_ranking = 5

    def run(self, data: pd.DataFrame) -> dict:
        if data is None or data.empty:
            return self._summary([])

        data = data.copy()
        required = ["Close", "High", "Low", "EMA20", "EMA50", "RSI", "MACD", "MACD_SIGNAL", "ATR", "VWAP"]
        if not all(col in data.columns for col in required):
            return self._summary([])

        data = data.dropna(subset=required)
        if len(data) < 61:
            return self._summary([])

        data = data.sort_index()
        next_available_index = 60
        results = []

        for i in range(60, len(data) - 1):
            if i < next_available_index:
                continue

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

            if atr <= 0 or close <= 0:
                continue

            # Buy setup
            if not (ema20 > ema50 and macd > macd_signal and 55 < rsi < 70 and close > vwap):
                continue

            entry = round(close + atr * self.entry_atr_buffer, 2)
            stoploss = round(entry - atr * self.stop_atr_multiplier, 2)
            risk = round(entry - stoploss, 2)
            if risk <= 0:
                continue

            target1 = round(entry + risk * self.target1_r, 2)
            target2 = round(entry + risk * self.target2_r, 2)
            target3 = round(entry + risk * self.target3_r, 2)

            # Find entry trigger
            entry_index = None
            for j in range(i + 1, len(data)):
                try:
                    if float(data.iloc[j]["High"]) >= entry:
                        entry_index = j
                        break
                except (TypeError, ValueError):
                    continue
            if entry_index is None:
                continue

            # Trade management
            status = "OPEN"
            exit_price = None
            exit_date = None
            target_hit = "NONE"
            current_stop = stoploss
            target1_reached = False
            highest_price = entry
            lowest_price = entry

            end_index = min(entry_index + self.lookahead_days, len(data))
            last_index = end_index - 1

            for j in range(entry_index, end_index):
                candle = data.iloc[j]
                try:
                    low = float(candle["Low"])
                    high = float(candle["High"])
                except (TypeError, ValueError):
                    continue

                highest_price = max(highest_price, high)
                lowest_price = min(lowest_price, low)

                # Break-even
                if self.use_break_even and high >= target1 and not target1_reached:
                    target1_reached = True
                    current_stop = entry

                # Stop loss
                if low <= current_stop:
                    status = "WIN" if target1_reached else "LOSS"
                    exit_price = entry if target1_reached else current_stop
                    exit_date = candle.name
                    target_hit = "TARGET1" if target1_reached else "NONE"
                    break

                # Targets
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
                    target1_reached = True
                    current_stop = entry

            # Open trade handling
            unrealized_pnl = 0.0
            if status == "OPEN":
                try:
                    mark_price = float(data.iloc[last_index]["Close"])
                except (TypeError, ValueError):
                    mark_price = close
                unrealized_pnl = round(mark_price - entry, 2)
                if unrealized_pnl > 0:
                    status = "OPEN_PROFIT"
                elif unrealized_pnl < 0:
                    status = "OPEN_LOSS"
                else:
                    status = "OPEN"

            # P&L
            pnl = 0.0
            pnl_percent = 0.0
            r_multiple = 0.0
            if exit_price is not None:
                pnl = round(exit_price - entry, 2)
                pnl_percent = round((pnl / entry) * 100, 2)
                r_multiple = round(pnl / risk, 2)
            else:
                r_multiple = round(unrealized_pnl / risk, 2)

            mfe = round(highest_price - entry, 2)
            mae = round(lowest_price - entry, 2)
            mfe_r = round(mfe / risk, 2)
            mae_r = round(mae / risk, 2)

            results.append({
                "Date": data.iloc[entry_index].name,
                "SignalDate": row.name,
                "Entry": entry,
                "StopLoss": stoploss,
                "CurrentStop": current_stop,
                "Target1": target1,
                "Target2": target2,
                "Target3": target3,
                "RR": round((target2 - entry) / risk, 2) if risk > 0 else 0,
                "ExitPrice": exit_price,
                "ExitDate": exit_date,
                "HoldingDays": entry_index - i if exit_date is None else (exit_date - entry_index).days if hasattr(exit_date, 'days') else 0,
                "TargetHit": target_hit,
                "Status": status,
                "PnL": pnl,
                "UnrealizedPnL": unrealized_pnl,
                "TotalPnL": round(pnl + unrealized_pnl, 2),
                "PnLPercent": pnl_percent,
                "RMultiple": r_multiple,
                "MFE": mfe,
                "MAE": mae,
                "MFE_R": mfe_r,
                "MAE_R": mae_r
            })

            next_available_index = max(entry_index + 1, end_index)

        return self._summary(results)

    def _summary(self, results: list) -> dict:
        total = len(results)
        wins = sum(1 for t in results if t.get("Status") == "WIN")
        losses = sum(1 for t in results if t.get("Status") == "LOSS")
        open_trades = sum(1 for t in results if t.get("Status") in ("OPEN", "OPEN_PROFIT", "OPEN_LOSS"))
        closed = wins + losses

        win_rate = round((wins / closed) * 100, 2) if closed > 0 else 0.0

        realized_pnl = round(sum(float(t.get("PnL", 0)) for t in results), 2)
        unrealized_pnl = round(sum(float(t.get("UnrealizedPnL", 0)) for t in results), 2)
        total_pnl = round(realized_pnl + unrealized_pnl, 2)

        profits = [t.get("PnL", 0) for t in results if t.get("Status") == "WIN" and t.get("PnL", 0) > 0]
        losses_list = [t.get("PnL", 0) for t in results if t.get("Status") == "LOSS" and t.get("PnL", 0) < 0]

        avg_profit = round(sum(profits) / len(profits), 2) if profits else 0.0
        avg_loss = round(sum(losses_list) / len(losses_list), 2) if losses_list else 0.0

        gross_profit = sum(profits)
        gross_loss = abs(sum(losses_list))
        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else (10.0 if gross_profit > 0 and closed >= self.min_trades_for_ranking else 0.0)

        expectancy = round((wins / closed) * avg_profit + (losses / closed) * avg_loss, 2) if closed > 0 else 0.0

        r_values = [t.get("RMultiple", 0) for t in results if t.get("Status") in ("WIN", "LOSS")]
        avg_r = round(sum(r_values) / len(r_values), 2) if r_values else 0.0

        equity = 0.0
        peak = 0.0
        max_dd = 0.0
        for t in results:
            equity += float(t.get("PnL", 0))
            peak = max(peak, equity)
            max_dd = min(max_dd, equity - peak)
        max_drawdown = round(max_dd, 2)

        target1_wins = sum(1 for t in results if t.get("TargetHit") == "TARGET1")
        target2_wins = sum(1 for t in results if t.get("TargetHit") == "TARGET2")
        target3_wins = sum(1 for t in results if t.get("TargetHit") == "TARGET3")

        data_quality = "NO CLOSED TRADES" if closed == 0 else ("LOW SAMPLE" if closed < self.min_trades_for_ranking else "SUFFICIENT SAMPLE")

        return {
            "Total Trades": total,
            "Wins": wins,
            "Losses": losses,
            "Open": open_trades,
            "Closed Trades": closed,
            "Win Rate": win_rate,
            "Realized PnL": realized_pnl,
            "Unrealized PnL": unrealized_pnl,
            "Total PnL": total_pnl,
            "Average Profit": avg_profit,
            "Average Loss": avg_loss,
            "Profit Factor": profit_factor,
            "Expectancy": expectancy,
            "Average R": avg_r,
            "Max Drawdown": max_drawdown,
            "Target1 Wins": target1_wins,
            "Target2 Wins": target2_wins,
            "Target3 Wins": target3_wins,
            "Data Quality": data_quality,
            "Trades": results
        }