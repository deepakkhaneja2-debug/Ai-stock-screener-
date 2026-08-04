import streamlit as st
import pandas as pd
import traceback

from config import *

from data_engine import DataEngine
from indicator_engine import IndicatorEngine
from pattern_engine import PatternEngine
from strategy_engine import StrategyEngine
from confidence_engine import ConfidenceEngine
from risk_engine import RiskEngine
from alert_engine import AlertEngine
from dashboard import DashboardEngine
from trade_logger import TradeLogger
from performance_analyzer import PerformanceAnalyzer
from backtest_engine import BacktestEngine
from backtest_analyzer import BacktestAnalyzer


class StockScanner:

    def __init__(self):
        self.data_engine = DataEngine()
        self.indicator_engine = IndicatorEngine()
        self.pattern_engine = PatternEngine()
        self.strategy_engine = StrategyEngine()
        self.confidence_engine = ConfidenceEngine()
        self.risk_engine = RiskEngine()
        self.alert_engine = AlertEngine()
        self.dashboard = DashboardEngine()
        self.logger = TradeLogger()
        self.performance = PerformanceAnalyzer()
        self.backtest = BacktestEngine()
        self.backtest_analyzer = BacktestAnalyzer()
        self.capital = STARTING_CAPITAL
        self.results = []

    def load_market(self):
        print("Loading Market Data...")
        self.market_data = self.data_engine.scan_ready_data()
        st.write(self.market_data.keys())
        st.write(len(self.market_data))
        print(f"Loaded {len(self.market_data)} Symbols")

    def process_symbol(self, symbol, data):
        if data.empty:
            return

        data, indicator_score = self.indicator_engine.process(data)
        data, pattern_score = self.pattern_engine.process(data)

        strategy_result = self.strategy_engine.evaluate(data)

        confidence = self.confidence_engine.calculate(
            strategy_score=strategy_result["strategy_score"],
            trend_score=data["TrendScore"].iloc[-1] if "TrendScore" in data.columns else 0,
            pattern_score=pattern_score,
            volume_spike=data["VOL_SPIKE"].iloc[-1] if "VOL_SPIKE" in data.columns else False,
            atr=data["ATR"].iloc[-1] if "ATR" in data.columns else 0
        )

        trade = self.risk_engine.trade_plan(data, self.capital)
        if not trade:
            return

        self.results.append({
            "Symbol": symbol,
            "Signal": strategy_result["signal"],
            "Confidence": confidence,
            "StrategyScore": strategy_result["strategy_score"],
            "TriggeredStrategies": ", ".join(strategy_result["triggered_strategies"]),
            "PatternScore": pattern_score,
            "SL": trade["StopLoss"],
            "Qty": trade["Quantity"],
            "CurrentPrice": trade["CurrentPrice"],
            "Entry": trade["Entry"],
            "Target1": trade["Target1"],
            "Target2": trade["Target2"],
            "Target3": trade["Target3"],
            "RR": trade["RR"],
        })

    def run(self):
        self.load_market()

        for symbol, data in self.market_data.items():
            try:
                self.process_symbol(symbol, data)
            except Exception:
                st.write(f"Error in: {symbol}")
                st.code(traceback.format_exc())

        self.results = pd.DataFrame(self.results)
        print(self.results)
        print(self.results.columns)
        print(self.results.shape)

        # Backtest
        backtest_results = {}
        for symbol, data in self.market_data.items():
            if data.empty:
                continue
            try:
                bt_data, _ = self.indicator_engine.process(data.copy())
                raw_report = self.backtest.run(bt_data)
                analysis = self.backtest_analyzer.analyze(raw_report)
                backtest_results[symbol] = analysis
            except Exception:
                st.write(f"Backtest Error: {symbol}")
                st.code(traceback.format_exc())

        self.backtest_results = backtest_results
        return self.results

    def send_alerts(self):
        if self.results.empty:
            return
        for _, row in self.results.iterrows():
            if row["Signal"] == "WATCH":
                continue
            self.alert_engine.process(
                signal=row["Signal"],
                symbol=row["Symbol"],
                price=row["Entry"]
            )

    def save_logs(self):
        if self.results.empty:
            return
        for _, row in self.results.iterrows():
            self.logger.save_trade(
                symbol=row["Symbol"],
                signal=row["Signal"],
                entry=row["Entry"],
                exit_price=0,
                sl=row["SL"],
                target=row["Target1"],
                qty=row["Qty"],
                pnl=0,
                pnl_percent=0,
                reason="Signal Generated",
                confidence=row["Confidence"],
                ema=0,
                macd=0,
                rsi=0,
                pattern=row["PatternScore"],
                trend=0
            )

    def performance_report(self):
        print("\n========== PERFORMANCE ==========")
        print(self.performance.summary())
        print("\nAverage Profit")
        print(self.performance.average_profit())
        print("\nAverage Loss")
        print(self.performance.average_loss())

    def show_dashboard(self):
        if self.results.empty:
            print("No scan results generated.")
            return
        if "Signal" not in self.results.columns:
            print("Signal column missing.")
            print(self.results.columns.tolist())
            return
        print("\n========== TOP BUY ==========")
        print(self.dashboard.top_buy(self.results))
        print("\n========== TOP SELL ==========")
        print(self.dashboard.top_sell(self.results))
        print("\n========== SUMMARY ==========")
        print(self.dashboard.summary(self.results))


if __name__ == "__main__":
    st.set_page_config(page_title="AI Stock Scanner V1.4", layout="wide")
    st.title("AI Stock Scanner V1.4")
    st.success("App Running Successfully")

    scanner = StockScanner()
    results = scanner.run()

    st.subheader("Scanner Results")
    if not results.empty:
        st.dataframe(results, use_container_width=True)
    else:
        st.warning("No signals found.")

    st.subheader("📊 Overall Backtest Dashboard")
    all_reports = []
    for symbol, report in scanner.backtest_results.items():
        if isinstance(report, dict):
            all_reports.append({
                "Symbol": symbol,
                "Trades": report.get("Total Trades", 0),
                "Wins": report.get("Wins", 0),
                "Losses": report.get("Losses", 0),
                "Open": report.get("Open", 0),
                "Win Rate": report.get("Win Rate", 0),
                "PnL": report.get("Total PnL", 0),
                "Profit Factor": report.get("Profit Factor", 0),
                "Max Drawdown": report.get("Max Drawdown", 0),
                "Target1": report.get("Target1 Wins", 0),
                "Target2": report.get("Target2 Wins", 0),
                "Target3": report.get("Target3 Wins", 0)
            })

    overall_df = pd.DataFrame(all_reports)

    if not overall_df.empty:
        total_trades = overall_df["Trades"].sum()
        total_wins = overall_df["Wins"].sum()
        total_losses = overall_df["Losses"].sum()
        total_open = overall_df["Open"].sum()
        total_pnl = overall_df["PnL"].sum()
        closed_trades = total_wins + total_losses
        overall_win_rate = round((total_wins / closed_trades) * 100, 2) if closed_trades > 0 else 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Trades", int(total_trades))
        col2.metric("Wins", int(total_wins))
        col3.metric("Losses", int(total_losses))
        col4.metric("Overall Win Rate", f"{overall_win_rate}%")

        col5, col6, col7 = st.columns(3)
        col5.metric("Total P&L", round(total_pnl, 2))
        col6.metric("Open Trades", int(total_open))
        col7.metric("Best Stock", overall_df.loc[overall_df["PnL"].idxmax(), "Symbol"])

    st.subheader("🏆 Stock Ranking")
    if overall_df.empty or "PnL" not in overall_df.columns:
        st.info("No backtest results available.")
    else:
        ranking_df = overall_df.sort_values(by="PnL", ascending=False).reset_index(drop=True)
        st.dataframe(ranking_df, use_container_width=True)

    st.subheader("Backtest Summary")
    for symbol, report in scanner.backtest_results.items():
        st.write(f"### {symbol}")
        if isinstance(report, dict):
            st.write({
                "Total Trades": report.get("Total Trades", 0),
                "Wins": report.get("Wins", 0),
                "Losses": report.get("Losses", 0),
                "Open": report.get("Open", 0),
                "Win Rate": report.get("Win Rate", 0),
                "Total PnL": report.get("Total PnL", 0),
                "Average Profit": report.get("Average Profit", 0),
                "Average Loss": report.get("Average Loss", 0),
                "Profit Factor": report.get("Profit Factor", 0),
                "Max Drawdown": report.get("Max Drawdown", 0),
                "Target1 Wins": report.get("Target1 Wins", 0),
                "Target2 Wins": report.get("Target2 Wins", 0),
                "Target3 Wins": report.get("Target3 Wins", 0)
            })
        else:
            st.warning(f"{symbol}: Backtest report format incorrect.")