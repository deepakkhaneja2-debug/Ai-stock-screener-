```python
import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Any

from config import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class BacktestEngine:
    """
    Enhanced backtest engine with proper trade management.
    Closes trades correctly on target hits, stop losses, and break-even.
    Uses consistent dictionary keys for analyzer compatibility.
    """

    def __init__(self):
        self.lookahead_days = BACKTEST_LOOKAHEAD
        self.entry_atr_buffer = ENTRY_ATR_BUFFER
        self.stop_atr_multiplier = STOP_ATR_MULTIPLIER
        self.target1_r = TARGET1_R
        self.target2_r = TARGET2_R
        self.target3_r = TARGET3_R
        self.use_break_even = BREAK_EVEN_AT_TARGET1
        self.trailing_stop_atr = TRAILING_STOP_ATR
        self.min_trades_for_ranking = MIN_TRADES_FOR_RANKING
        self.risk_per_trade = RISK_PER_TRADE
        self.initial_capital = STARTING_CAPITAL
        self.slippage = SLIPPAGE
        self.brokerage = BROKERAGE_PER_TRADE
        self.enable_transaction_cost = ENABLE_TRANSACTION_COST
        self.brokerage_type = BROKERAGE_TYPE if 'BROKERAGE_TYPE' in globals() else "fixed"

    def run(self, data: pd.DataFrame) -> dict:
        """Run backtest with full trade management."""
        if data is None or data.empty:
            logger.warning("No data provided for backtest")
            return self._summary([])

        data = data.copy()
        
        # Required columns (VWAP is optional)
        required = [
            "Close", "High", "Low",
            "EMA20", "EMA50",
            "RSI", "MACD", "MACD_SIGNAL",
            "ATR"
        ]

        if not all(col in data.columns for col in required):
            logger.warning("Missing required columns for backtest")
            return self._summary([])

        # Drop rows with NaN in required columns
        data = data.dropna(subset=required)
        
        # If VWAP column exists, also drop rows where VWAP is NaN
        if "VWAP" in data.columns:
            data = data.dropna(subset=["VWAP"])
        
        if len(data) < 61:
            logger.warning("Insufficient data for backtest")
            return self._summary([])

        data = data.sort_index()
        next_available_index = 60
        results = []
        equity_curve = []
        cumulative_pnl = 0
        trade_counter = 0

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
                vwap = float(row["VWAP"]) if "VWAP" in data.columns else close
            except (TypeError, ValueError) as e:
                logger.debug(f"Error reading indicators at {i}: {e}")
                continue

            if atr <= 0 or close <= 0:
                continue

            # Enhanced buy setup with confirmation
            buy_setup = (
                ema20 > ema50 and
                macd > macd_signal and
                macd > 0 and
                55 < rsi < 70 and
                close > vwap and
                close > ema20
            )

            if not buy_setup:
                continue

            # Calculate theoretical entry and stop loss
            theoretical_entry = round(close + atr * self.entry_atr_buffer, 2)
            theoretical_stoploss = round(theoretical_entry - atr * self.stop_atr_multiplier, 2)
            theoretical_risk = round(theoretical_entry - theoretical_stoploss, 2)

            if theoretical_risk <= 0:
                continue

            theoretical_target1 = round(theoretical_entry + theoretical_risk * self.target1_r, 2)
            theoretical_target2 = round(theoretical_entry + theoretical_risk * self.target2_r, 2)
            theoretical_target3 = round(theoretical_entry + theoretical_risk * self.target3_r, 2)

            # Find entry trigger with realistic gap handling
            entry_index = None
            actual_entry_price = None
            
            for j in range(i + 1, min(i + 10, len(data))):
                try:
                    candle_open = float(data.iloc[j]["Open"])
                    candle_high = float(data.iloc[j]["High"])
                    
                    # Check if entry price is reached
                    if candle_high >= theoretical_entry:
                        # If candle gaps above entry, fill at open
                        if candle_open > theoretical_entry:
                            actual_entry_price = candle_open
                        else:
                            actual_entry_price = theoretical_entry
                        entry_index = j
                        break
                except (TypeError, ValueError):
                    continue

            if entry_index is None or actual_entry_price is None:
                continue

            # Recalculate stop loss based on actual entry price
            stoploss = round(actual_entry_price - atr * self.stop_atr_multiplier, 2)
            actual_risk = round(actual_entry_price - stoploss, 2)
            
            if actual_risk <= 0:
                continue

            # Recalculate targets based on actual entry and risk
            actual_target1 = round(actual_entry_price + actual_risk * self.target1_r, 2)
            actual_target2 = round(actual_entry_price + actual_risk * self.target2_r, 2)
            actual_target3 = round(actual_entry_price + actual_risk * self.target3_r, 2)

            # Calculate position size based on risk
            capital = self.initial_capital + cumulative_pnl
            risk_amount = capital * (self.risk_per_trade / 100)
            quantity = max(
                int(risk_amount / max(actual_risk, 0.01)),
                1
            )
            
            # Increment trade counter
            trade_counter += 1
            
            logger.info(f"Entry signal at {data.iloc[entry_index].name} - Entry: {actual_entry_price}, Stop: {stoploss}, Risk: {actual_risk}, Qty: {quantity}")

            # Initialize trade
            trade = {
                "TradeID": trade_counter,
                "Date": data.iloc[entry_index].name,
                "SignalDate": row.name,
                "Entry": round(actual_entry_price, 2),  # Use actual entry as main Entry
                "StopLoss": stoploss,
                "Risk": actual_risk,
                "Target1": actual_target1,
                "Target2": actual_target2,
                "Target3": actual_target3,
                "Expiry": min(entry_index + self.lookahead_days, len(data)),
                "Status": "OPEN",
                "EntryIndex": entry_index,
                "CurrentStop": stoploss,
                "HighestPrice": actual_entry_price,
                "LowestPrice": actual_entry_price,
                "TargetHit": None,
                "ExitPrice": None,
                "ExitDate": None,
                "ExitReason": None,
                "HoldingDays": 0,
                "PnL": 0.0,
                "PnLPercent": 0.0,
                "RMultiple": 0.0,
                "TradeReason": "EMA50 + MACD + RSI Setup",
                "RR": round((actual_target2 - actual_entry_price) / actual_risk, 2) if actual_risk > 0 else 0,
                "Quantity": quantity,
                "CapitalUsed": capital,
                "RiskAmount": risk_amount,
                "EntrySlippage": 0.0,
                "ExitSlippage": 0.0,
                "Brokerage": 0.0,
                "GrossPnL": 0.0,
                "NetPnL": 0.0,
                "RunningEquity": 0.0
            }

            # --- TRADE MANAGEMENT LOOP ---
            trade_closed = False
            break_even_triggered = False
            trade_ended_at = None
            
            for j in range(entry_index, trade["Expiry"]):
                candle = data.iloc[j]
                try:
                    low = float(candle["Low"])
                    high = float(candle["High"])
                    candle_open = float(candle["Open"])
                    candle_close = float(candle["Close"])
                    atr = float(candle["ATR"]) if "ATR" in data.columns else trade["Risk"] / 1.5
                except (TypeError, ValueError):
                    continue

                trade["HoldingDays"] = j - trade["EntryIndex"] + 1
                trade["HighestPrice"] = max(trade["HighestPrice"], high)
                trade["LowestPrice"] = min(trade["LowestPrice"], low)

                # Update trailing stop - ensure it never moves backwards and never exceeds Target3
                if not break_even_triggered:
                    profit = high - trade["Entry"]
                    if profit >= trade["Risk"] * 1.5:
                        new_stop = high - atr * self.trailing_stop_atr
                        # Cap trailing stop at Target3 to ensure Target3 can still be hit
                        new_stop = min(new_stop, trade["Target3"])
                        # Only update if new stop is higher than current stop
                        if new_stop > trade["CurrentStop"]:
                            trade["CurrentStop"] = new_stop
                            logger.debug(f"Trailing stop updated to {trade['CurrentStop']} at {candle.name}")

                # Check targets (priority: T3 > T2 > T1)
                if high >= trade["Target3"]:
                    logger.info(f"TARGET3 hit at {candle.name} - Price: {high}")
                    self._close_trade(trade, j, "TARGET3", data)
                    trade_closed = True
                    trade_ended_at = j
                    break
                elif high >= trade["Target2"]:
                    logger.info(f"TARGET2 hit at {candle.name} - Price: {high}")
                    self._close_trade(trade, j, "TARGET2", data)
                    trade_closed = True
                    trade_ended_at = j
                    break
                elif high >= trade["Target1"]:
                    if self.use_break_even:
                        # Move stop to entry (break-even) but keep trade open
                        trade["CurrentStop"] = trade["Entry"]
                        break_even_triggered = True
                        logger.info(f"Break-even triggered at {trade['Entry']} for {trade['Date']}")
                    else:
                        logger.info(f"TARGET1 hit at {candle.name} - Price: {high}")
                        self._close_trade(trade, j, "TARGET1", data)
                        trade_closed = True
                        trade_ended_at = j
                        break

                # Check stop loss with realistic gap handling
                if low <= trade["CurrentStop"]:
                    # Check if candle gapped below stop loss
                    if candle_open < trade["CurrentStop"]:
                        # Exit at open if gap below stop
                        exit_price = candle_open
                    else:
                        exit_price = trade["CurrentStop"]
                    
                    if break_even_triggered and trade["CurrentStop"] == trade["Entry"]:
                        logger.info(f"Break-even stop hit at {candle.name} - Price: {exit_price}")
                        trade["ExitPrice"] = exit_price
                        self._close_trade(trade, j, "BREAK_EVEN", data)
                    else:
                        logger.info(f"Stop loss hit at {candle.name} - Price: {exit_price}")
                        trade["ExitPrice"] = exit_price
                        self._close_trade(trade, j, "STOP_LOSS", data)
                    trade_closed = True
                    trade_ended_at = j
                    break

            # If still open after expiry
            if not trade_closed and trade["Status"] == "OPEN":
                last_idx = min(trade["Expiry"] - 1, len(data) - 1)
                trade["ExitPrice"] = float(data.iloc[last_idx]["Close"])
                logger.info(f"Time exit at {data.iloc[last_idx].name} - Price: {trade['ExitPrice']}")
                self._close_trade(trade, last_idx, "TIME_EXIT", data)
                trade_ended_at = last_idx

            # Append closed trade
            if trade["Status"] != "OPEN":
                # Update running equity
                cumulative_pnl += trade["NetPnL"]
                trade["RunningEquity"] = self.initial_capital + cumulative_pnl
                
                results.append(trade)
                equity_curve.append({
                    "Date": trade["ExitDate"],
                    "Equity": trade["RunningEquity"],
                    "CumulativePnL": cumulative_pnl
                })
                logger.info(
                    f"Trade {trade['TradeID']} - {trade['ExitReason']} | Entry={trade['Entry']} Exit={trade['ExitPrice']:.2f} "
                    f"Qty={trade['Quantity']} NetPnL={trade['NetPnL']:.2f} R={trade['RMultiple']} "
                    f"Equity={trade['RunningEquity']:.2f}"
                )

            # Prevent overlapping trades using expiry
            next_available_index = max(entry_index + 1, trade["Expiry"] + 1)

        return self._summary(results, equity_curve)

    def _close_trade(self, trade: dict, exit_idx: int, reason: str, data: pd.DataFrame) -> None:
        """Close a trade and calculate P&L."""
        if trade["Status"] != "OPEN":
            return

        # Determine exit price based on reason
        if reason == "TARGET3":
            exit_price = trade["Target3"]
        elif reason == "TARGET2":
            exit_price = trade["Target2"]
        elif reason == "TARGET1":
            exit_price = trade["Target1"]
        elif reason in ["STOP_LOSS", "BREAK_EVEN"]:
            exit_price = trade.get("ExitPrice", trade["CurrentStop"])
        else:  # TIME_EXIT
            exit_price = trade.get("ExitPrice", trade["Entry"])

        # Use entry price from trade dict
        entry_price_raw = trade["Entry"]

        # Apply slippage and brokerage if enabled
        if self.enable_transaction_cost:
            entry_slippage = entry_price_raw * self.slippage
            exit_slippage = exit_price * self.slippage
            entry_price = entry_price_raw + entry_slippage  # Buy at ask
            exit_price = exit_price - exit_slippage  # Sell at bid
            
            # Calculate brokerage based on type
            if self.brokerage_type == 'percentage':
                brokerage = (entry_price * trade["Quantity"] * self.brokerage / 100) + \
                           (exit_price * trade["Quantity"] * self.brokerage / 100)
            else:  # fixed
                brokerage = self.brokerage * 2  # Entry and exit
        else:
            entry_slippage = 0.0
            exit_slippage = 0.0
            entry_price = entry_price_raw
            brokerage = 0.0

        # Calculate P&L with position sizing
        quantity = trade["Quantity"]
        gross_pnl = (exit_price - entry_price) * quantity
        net_pnl = gross_pnl - brokerage
        
        pnl = round(net_pnl, 2)
        pnl_percent = round((pnl / (entry_price_raw * quantity)) * 100, 2) if entry_price_raw > 0 else 0
        r_multiple = round((exit_price - entry_price) / trade["Risk"], 2) if trade["Risk"] > 0 else 0

        # Determine status
        if pnl > 0:
            status = "WIN"
        elif pnl < 0:
            status = "LOSS"
        else:
            status = "BREAK_EVEN"

        # Update trade record
        trade["Status"] = status
        trade["ExitPrice"] = round(exit_price, 2)
        trade["ExitDate"] = data.iloc[exit_idx].name
        trade["ExitReason"] = reason
        trade["PnL"] = pnl
        trade["PnLPercent"] = pnl_percent
        trade["RMultiple"] = r_multiple
        trade["EntrySlippage"] = round(entry_slippage, 2)
        trade["ExitSlippage"] = round(exit_slippage, 2)
        trade["Brokerage"] = round(brokerage, 2)
        trade["GrossPnL"] = round(gross_pnl, 2)
        trade["NetPnL"] = pnl

        # Update target hit
        if reason in ["TARGET1", "TARGET2", "TARGET3"]:
            trade["TargetHit"] = reason

        logger.debug(f"Trade closed: {status} | Gross: {gross_pnl:.2f} | Net: {pnl:.2f} | Brokerage: {brokerage:.2f}")

    def _summary(self, trades: list, equity_curve: list = None) -> dict:
        """Generate comprehensive backtest summary."""
        if equity_curve is None:
            equity_curve = []
            
        if not trades:
            return self._empty_summary()

        # Basic stats
        wins = sum(1 for t in trades if t["Status"] == "WIN")
        losses = sum(1 for t in trades if t["Status"] == "LOSS")
        break_even = sum(1 for t in trades if t["Status"] == "BREAK_EVEN")
        closed = wins + losses + break_even

        # Win rate
        win_rate = round((wins / closed) * 100, 2) if closed > 0 else 0

        # P&L
        total_pnl = round(sum(t["NetPnL"] for t in trades), 2)
        total_return = round((total_pnl / self.initial_capital) * 100, 2)

        # Average profit/loss
        profits = [t["NetPnL"] for t in trades if t["Status"] == "WIN"]
        losses_list = [t["NetPnL"] for t in trades if t["Status"] == "LOSS"]

        avg_profit = round(sum(profits) / len(profits), 2) if profits else 0
        avg_loss = round(sum(losses_list) / len(losses_list), 2) if losses_list else 0

        # Average R for wins and losses
        win_r = [t["RMultiple"] for t in trades if t["Status"] == "WIN"]
        loss_r = [t["RMultiple"] for t in trades if t["Status"] == "LOSS"]
        avg_win_r = round(sum(win_r) / len(win_r), 2) if win_r else 0
        avg_loss_r = round(sum(loss_r) / len(loss_r), 2) if loss_r else 0

        # Profit factor - use 999 instead of inf for dashboard compatibility
        # Change to float('inf') if your dashboard supports it
        gross_profit = sum(profits)
        gross_loss = abs(sum(losses_list))
        profit_factor = (
            round(gross_profit / gross_loss, 2)
            if gross_loss > 0
            else 999
        )

        # Expectancy in dollars and R
        expectancy_dollar = round((wins/closed * avg_profit) + (losses/closed * avg_loss), 2) if closed > 0 else 0
        expectancy_r = round((wins/closed * avg_win_r) + (losses/closed * avg_loss_r), 2) if closed > 0 else 0

        # Average R
        r_values = [t["RMultiple"] for t in trades if t["Status"] in ["WIN", "LOSS"]]
        avg_r = round(sum(r_values) / len(r_values), 2) if r_values else 0

        # Average holding days
        hold_days = [t["HoldingDays"] for t in trades]
        avg_hold_days = round(sum(hold_days) / len(hold_days), 1) if hold_days else 0

        # Consecutive wins/losses
        max_win_streak = 0
        max_loss_streak = 0
        current_win_streak = 0
        current_loss_streak = 0
        
        for t in trades:
            if t["Status"] == "WIN":
                current_win_streak += 1
                current_loss_streak = 0
                max_win_streak = max(max_win_streak, current_win_streak)
            elif t["Status"] == "LOSS":
                current_loss_streak += 1
                current_win_streak = 0
                max_loss_streak = max(max_loss_streak, current_loss_streak)
            else:
                current_win_streak = 0
                current_loss_streak = 0

        # Max drawdown using equity curve
        max_drawdown = 0
        if equity_curve:
            equity_values = [ec["Equity"] for ec in equity_curve]
            peak = equity_values[0] if equity_values else self.initial_capital
            for value in equity_values:
                if value > peak:
                    peak = value
                drawdown = peak - value
                max_drawdown = max(max_drawdown, drawdown)
        else:
            # Fallback to cumulative PnL if equity curve not available
            equity = self.initial_capital
            peak = equity
            for t in trades:
                equity += t["NetPnL"]
                peak = max(peak, equity)
                drawdown = peak - equity
                max_drawdown = max(max_drawdown, drawdown)

        max_drawdown = round(max_drawdown, 2)

        # Target hits
        target1_wins = sum(1 for t in trades if t.get("TargetHit") == "TARGET1")
        target2_wins = sum(1 for t in trades if t.get("TargetHit") == "TARGET2")
        target3_wins = sum(1 for t in trades if t.get("TargetHit") == "TARGET3")

        # Data quality
        data_quality = "NO CLOSED TRADES" if closed == 0 else \
                      "LOW SAMPLE" if closed < self.min_trades_for_ranking else "SUFFICIENT SAMPLE"

        return {
            "Total Trades": len(trades),
            "Wins": wins,
            "Losses": losses,
            "BreakEven": break_even,
            "Open": 0,
            "Closed Trades": closed,
            "Win Rate": win_rate,
            "Total PnL": total_pnl,
            "Total Return %": total_return,
            "Average Profit": avg_profit,
            "Average Loss": avg_loss,
            "Avg Win R": avg_win_r,
            "Avg Loss R": avg_loss_r,
            "Profit Factor": profit_factor,
            "Expectancy": expectancy_dollar,
            "Expectancy R": expectancy_r,
            "Average R": avg_r,
            "Average Holding Days": avg_hold_days,
            "Max Drawdown": max_drawdown,
            "Consecutive Wins": max_win_streak,
            "Consecutive Losses": max_loss_streak,
            "Target1 Wins": target1_wins,
            "Target2 Wins": target2_wins,
            "Target3 Wins": target3_wins,
            "Data Quality": data_quality,
            "Equity Curve": equity_curve,
            "Trades": trades,
            "FinalEquity": self.initial_capital + total_pnl
        }

    def _empty_summary(self) -> dict:
        return {
            "Total Trades": 0,
            "Wins": 0,
            "Losses": 0,
            "BreakEven": 0,
            "Open": 0,
            "Closed Trades": 0,
            "Win Rate": 0,
            "Total PnL": 0,
            "Total Return %": 0,
            "Average Profit": 0,
            "Average Loss": 0,
            "Avg Win R": 0,
            "Avg Loss R": 0,
            "Profit Factor": 0,
            "Expectancy": 0,
            "Expectancy R": 0,
            "Average R": 0,
            "Average Holding Days": 0,
            "Max Drawdown": 0,
            "Consecutive Wins": 0,
            "Consecutive Losses": 0,
            "Target1 Wins": 0,
            "Target2 Wins": 0,
            "Target3 Wins": 0,
            "Data Quality": "NO TRADES",
            "Equity Curve": [],
            "Trades": [],
            "FinalEquity": self.initial_capital
        }
