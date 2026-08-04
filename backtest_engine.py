import pandas as pd
import numpy as np
from datetime import datetime
import logging

from config import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class BacktestEngine:
    """
    Enhanced backtest engine with:
    - Improved trade management
    - Proper target hit detection
    - Open trade handling
    - Trade reason tracking
    - Performance metrics
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

    def run(self, data: pd.DataFrame) -> dict:
        """Run enhanced backtest with full trade tracking."""
        if data is None or data.empty:
            return self._summary([])

        data = data.copy()
        required = ["Close", "High", "Low", "EMA20", "EMA50", 
                   "RSI", "MACD", "MACD_SIGNAL", "ATR", "VWAP"]
        
        if not all(col in data.columns for col in required):
            logger.warning("Missing required columns for backtest")
            return self._summary([])

        data = data.dropna(subset=required)
        if len(data) < 61:
            logger.warning("Insufficient data for backtest")
            return self._summary([])

        data = data.sort_index()
        next_available_index = 60
        results = []
        equity = 0.0
        equity_curve = []

        # Track open trades properly
        open_trades = []
        all_trades = []

        for i in range(60, len(data) - 1):
            if i < next_available_index:
                continue

            row = data.iloc[i]
            
            # Check and close any open trades that have expired
            current_date = row.name
            open_trades = [t for t in open_trades if t["expiry"] > i]
            
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

            # Calculate entry with better precision
            entry = round(close + atr * self.entry_atr_buffer, 2)
            stoploss = round(entry - atr * self.stop_atr_multiplier, 2)
            risk = round(entry - stoploss, 2)
            
            if risk <= 0:
                continue

            target1 = round(entry + risk * self.target1_r, 2)
            target2 = round(entry + risk * self.target2_r, 2)
            target3 = round(entry + risk * self.target3_r, 2)

            # Find entry trigger with confirmation
            entry_index = None
            for j in range(i + 1, min(i + 5, len(data))):
                try:
                    if float(data.iloc[j]["High"]) >= entry:
                        entry_index = j
                        break
                except (TypeError, ValueError):
                    continue

            if entry_index is None:
                continue

            # Create trade record
            trade = {
                "entry_date": data.iloc[entry_index].name,
                "signal_date": row.name,
                "entry_price": entry,
                "stop_loss": stoploss,
                "target1": target1,
                "target2": target2,
                "target3": target3,
                "risk": risk,
                "expiry": min(entry_index + self.lookahead_days, len(data)),
                "status": "OPEN",
                "entry_index": entry_index,
                "current_stop": stoploss,
                "highest_price": entry,
                "lowest_price": entry,
                "target_hit": None,
                "exit_price": None,
                "exit_date": None,
                "exit_reason": None,
                "holding_days": 0,
                "pnl": 0,
                "unrealized_pnl": 0,
                "r_multiple": 0,
                "trade_reason": "EMA50 + MACD + RSI Setup"
            }
            
            open_trades.append(trade)

            # Process open trades
            for t in open_trades:
                self._update_trade(data, t, entry_index, i)

        # Close remaining open trades
        for t in open_trades:
            if t["status"] == "OPEN":
                self._close_trade(data, t, len(data) - 1, "EXPIRED")

        # Collect all closed trades
        all_trades = [t for t in open_trades if t["status"] != "OPEN"]
        
        return self._summary(all_trades)

    def _update_trade(self, data: pd.DataFrame, trade: dict, 
                     entry_index: int, current_idx: int) -> None:
        """Update trade status and check exits."""
        if trade["status"] != "OPEN":
            return

        # Check each candle for exit conditions
        for j in range(trade["entry_index"], trade["expiry"]):
            candle = data.iloc[j]
            try:
                low = float(candle["Low"])
                high = float(candle["High"])
                close = float(candle["Close"])
                atr = float(candle["ATR"]) if "ATR" in data.columns else trade["risk"] / 1.5
            except (TypeError, ValueError):
                continue

            trade["holding_days"] = j - trade["entry_index"] + 1
            trade["highest_price"] = max(trade["highest_price"], high)
            trade["lowest_price"] = min(trade["lowest_price"], low)

            # Update trailing stop
            profit = high - trade["entry_price"]
            if profit >= trade["risk"] * 1.5:
                trade["current_stop"] = max(
                    trade["current_stop"],
                    high - atr * self.trailing_stop_atr
                )

            # Check targets
            if high >= trade["target3"]:
                self._close_trade(data, trade, j, "TARGET3")
                return
            elif high >= trade["target2"]:
                self._close_trade(data, trade, j, "TARGET2")
                return
            elif high >= trade["target1"]:
                if self.use_break_even:
                    trade["current_stop"] = trade["entry_price"]
                    # Continue tracking for higher targets
                else:
                    self._close_trade(data, trade, j, "TARGET1")
                    return

            # Check stop loss
            if low <= trade["current_stop"]:
                self._close_trade(data, trade, j, "STOP_LOSS")
                return

        # If still open after expiry
        if trade["holding_days"] >= self.lookahead_days:
            self._close_trade(data, trade, trade["expiry"] - 1, "TIME_EXIT")

    def _close_trade(self, data: pd.DataFrame, trade: dict, 
                    exit_idx: int, reason: str) -> None:
        """Close a trade and calculate P&L."""
        try:
            exit_candle = data.iloc[exit_idx]
            exit_price = float(exit_candle["Close"])
        except (IndexError, TypeError, ValueError):
            exit_price = trade["entry_price"]

        # Determine exit price based on reason
        if reason == "TARGET3":
            exit_price = trade["target3"]
        elif reason == "TARGET2":
            exit_price = trade["target2"]
        elif reason == "TARGET1":
            exit_price = trade["target1"]
        elif reason == "STOP_LOSS":
            exit_price = trade["current_stop"]
        elif reason == "BREAK_EVEN":
            exit_price = trade["entry_price"]
        
        # Calculate P&L
        pnl = round(exit_price - trade["entry_price"], 2)
        pnl_percent = round((pnl / trade["entry_price"]) * 100, 2)
        r_multiple = round(pnl / trade["risk"], 2)

        # Determine status
        if pnl > 0:
            status = "WIN"
        elif pnl < 0:
            status = "LOSS"
        else:
            status = "BREAK_EVEN"

        # Update trade record
        trade["status"] = status
        trade["exit_price"] = exit_price
        trade["exit_date"] = data.index[exit_idx] if exit_idx < len(data.index) else None
        trade["exit_reason"] = reason
        trade["pnl"] = pnl
        trade["pnl_percent"] = pnl_percent
        trade["r_multiple"] = r_multiple
        trade["holding_days"] = exit_idx - trade["entry_index"] + 1

        # Update target hit
        if reason in ["TARGET1", "TARGET2", "TARGET3"]:
            trade["target_hit"] = reason

    def _summary(self, trades: list) -> dict:
        """Generate comprehensive backtest summary."""
        total = len(trades)
        if total == 0:
            return self._empty_summary()

        # Basic stats
        wins = sum(1 for t in trades if t["status"] == "WIN")
        losses = sum(1 for t in trades if t["status"] == "LOSS")
        break_even = sum(1 for t in trades if t["status"] == "BREAK_EVEN")
        open_trades = sum(1 for t in trades if t["status"] == "OPEN")
        closed = wins + losses + break_even

        # Win rate
        win_rate = round((wins / closed) * 100, 2) if closed > 0 else 0

        # P&L
        total_pnl = round(sum(t["pnl"] for t in trades if t["status"] != "OPEN"), 2)
        unrealized_pnl = round(sum(t.get("unrealized_pnl", 0) for t in trades if t["status"] == "OPEN"), 2)

        # Average profit/loss
        profits = [t["pnl"] for t in trades if t["status"] == "WIN"]
        losses_list = [t["pnl"] for t in trades if t["status"] == "LOSS"]
        
        avg_profit = round(sum(profits) / len(profits), 2) if profits else 0
        avg_loss = round(sum(losses_list) / len(losses_list), 2) if losses_list else 0

        # Profit factor
        gross_profit = sum(profits)
        gross_loss = abs(sum(losses_list))
        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else 0

        # Expectancy
        expectancy = round((wins/closed * avg_profit) + (losses/closed * avg_loss), 2) if closed > 0 else 0

        # Average R
        r_values = [t["r_multiple"] for t in trades if t["status"] in ["WIN", "LOSS"]]
        avg_r = round(sum(r_values) / len(r_values), 2) if r_values else 0

        # Average holding days
        hold_days = [t["holding_days"] for t in trades if t["status"] != "OPEN"]
        avg_hold_days = round(sum(hold_days) / len(hold_days), 1) if hold_days else 0

        # Max drawdown
        equity = 0
        peak = 0
        max_dd = 0
        for t in trades:
            if t["status"] != "OPEN":
                equity += t["pnl"]
                peak = max(peak, equity)
                max_dd = min(max_dd, equity - peak)
        max_drawdown = round(max_dd, 2)

        # Target hits
        target1_wins = sum(1 for t in trades if t.get("target_hit") == "TARGET1")
        target2_wins = sum(1 for t in trades if t.get("target_hit") == "TARGET2")
        target3_wins = sum(1 for t in trades if t.get("target_hit") == "TARGET3")

        # Trade reasons
        trade_reasons = {}
        for t in trades:
            reason = t.get("trade_reason", "Unknown")
            trade_reasons[reason] = trade_reasons.get(reason, 0) + 1

        # Data quality
        data_quality = "NO CLOSED TRADES" if closed == 0 else \
                      "LOW SAMPLE" if closed < self.min_trades_for_ranking else "SUFFICIENT SAMPLE"

        # Monthly P&L
        monthly_pnl = {}
        for t in trades:
            if t["status"] != "OPEN" and t.get("exit_date"):
                try:
                    month = t["exit_date"].strftime("%Y-%m")
                    monthly_pnl[month] = monthly_pnl.get(month, 0) + t["pnl"]
                except AttributeError:
                    pass

        return {
            "Total Trades": total,
            "Wins": wins,
            "Losses": losses,
            "BreakEven": break_even,
            "Open": open_trades,
            "Closed Trades": closed,
            "Win Rate": win_rate,
            "Total PnL": total_pnl,
            "Unrealized PnL": unrealized_pnl,
            "Average Profit": avg_profit,
            "Average Loss": avg_loss,
            "Profit Factor": profit_factor,
            "Expectancy": expectancy,
            "Average R": avg_r,
            "Average Holding Days": avg_hold_days,
            "Max Drawdown": max_drawdown,
            "Target1 Wins": target1_wins,
            "Target2 Wins": target2_wins,
            "Target3 Wins": target3_wins,
            "Trade Reasons": trade_reasons,
            "Monthly PnL": monthly_pnl,
            "Data Quality": data_quality,
            "Trades": trades
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
            "Unrealized PnL": 0,
            "Average Profit": 0,
            "Average Loss": 0,
            "Profit Factor": 0,
            "Expectancy": 0,
            "Average R": 0,
            "Average Holding Days": 0,
            "Max Drawdown": 0,
            "Target1 Wins": 0,
            "Target2 Wins": 0,
            "Target3 Wins": 0,
            "Trade Reasons": {},
            "Monthly PnL": {},
            "Data Quality": "NO TRADES",
            "Trades": []
        }