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
        """Load market data for all symbols."""
        print("Loading Market Data...")
        self.market_data = self.data_engine.scan_ready_data()
        st.write(f"Loaded {len(self.market_data)} Symbols")
        return self.market_data

    def process_symbol(self, symbol: str, data: pd.DataFrame) -> None:
        """Process a single symbol through the entire pipeline."""
        if data.empty:
            return

        # Indicators
        data, indicator_score = self.indicator_engine.process(data)

        # Patterns
        data, pattern_score = self.pattern_engine.process(data)

        # Strategy
        strategy_result = self.strategy_engine.evaluate(data)

        # Confidence
        confidence = self.confidence_engine.calculate(
            strategy_score=strategy_result["strategy_score"],
            trend_score=data["TrendScore"].iloc[-1] if "TrendScore" in data.columns else 0,
            pattern_score=pattern_score,
            volume_spike=data["VOL_SPIKE"].iloc[-1] if "VOL_SPIKE" in data.columns else False,
            atr=data["ATR"].iloc[-1] if "ATR" in data.columns else 0
        )

        # Risk
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
        """Run the complete scanner pipeline."""
        self.load_market()

        for symbol, data in self.market_data.items():
            try:
                self.process_symbol(symbol, data)
            except Exception as e:
                st.write(f"Error in: {symbol}")
                st.code(traceback.format_exc())

        self.results = pd.DataFrame(self.results)
        print(f"Results shape: {self.results.shape}")
        print(self.results)

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
            except Exception as e:
                st.write(f"Backtest Error: {symbol}")
                st.code(traceback.format_exc())

        self.backtest_results = backtest_results
        return self.results

    def send_alerts(self):
        """Send alerts for BUY and SELL signals."""
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
        """Save all trades to log."""
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

    def show_dashboard(self):
        """Display dashboard statistics."""
        if self.results.empty:
            print("No scan results generated.")
            return
        if "Signal" not in self.results.columns:
            print("Signal column missing.")
            return
        print("\n========== TOP BUY ==========")
        print(self.dashboard.top_buy(self.results))
        print("\n========== TOP SELL ==========")
        print(self.dashboard.top_sell(self.results))
        print("\n========== SUMMARY ==========")
        print(self.dashboard.summary(self.results))

    def performance_report(self):
        """Generate performance report."""
        print("\n========== PERFORMANCE ==========")
        print(self.performance.summary())
        print("\nAverage Profit")
        print(self.performance.average_profit())
        print("\nAverage Loss")
        print(self.performance.average_loss())


def main():
    """Main Streamlit application."""
    st.set_page_config(page_title="AI Stock Scanner V1.4", layout="wide")
    st.title("AI Stock Scanner V1.4")
    st.success("App Running Successfully")

    scanner = StockScanner()
    results = scanner.run()

    # Display scanner results
    st.subheader("Scanner Results")
    if not results.empty:
        st.dataframe(results, use_container_width=True)
    else:
        st.warning("No signals found.")

    # Overall Backtest Dashboard
    st.subheader("📊 Overall Backtest Dashboard")

    # Calculate overall stats
    overall_stats = scanner.dashboard.overall_stats(scanner.backtest_results)

    if overall_stats["Total Trades"] > 0:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Trades", int(overall_stats["Total Trades"]))
        col2.metric("Wins", int(overall_stats["Wins"]))
        col3.metric("Losses", int(overall_stats["Losses"]))
        col4.metric("Overall Win Rate", f"{overall_stats['Win Rate']}%")

        col5, col6, col7 = st.columns(3)
        col5.metric("Total P&L", round(overall_stats["Total PnL"], 2))
        col6.metric("Profit Factor", round(overall_stats["Profit Factor"], 2))
        col7.metric("AI Score", int(overall_stats["AI Score"]))
    else:
        st.info("No backtest results available.")

    # Stock Ranking
    st.subheader("🏆 Stock Ranking")
    ranking_df = scanner.dashboard.ranking_table(scanner.backtest_results)

    if not ranking_df.empty:
        st.dataframe(ranking_df, use_container_width=True)
    else:
        st.info("No backtest results available.")

    # Backtest Summary
    st.subheader("Backtest Summary")
    for symbol, report in scanner.backtest_results.items():
        st.write(f"### {symbol}")
        if isinstance(report, dict):
            st.write({
                "Total Trades": report.get("Total Trades", 0),
                "Wins": report.get("Wins", 0),
                "Losses": report.get("Losses", 0),
                "BreakEven": report.get("BreakEven", 0),
                "Win Rate": report.get("Win Rate", 0),
                "Total PnL": report.get("Total PnL", 0),
                "Average Profit": report.get("Average Profit", 0),
                "Average Loss": report.get("Average Loss", 0),
                "Profit Factor": report.get("Profit Factor", 0),
                "Max Drawdown": report.get("Max Drawdown", 0),
                "AI Score": report.get("AI Score", 0),
                "Target1 Wins": report.get("Target1 Wins", 0),
                "Target2 Wins": report.get("Target2 Wins", 0),
                "Target3 Wins": report.get("Target3 Wins", 0)
            })
        else:
            st.warning(f"{symbol}: Backtest report format incorrect.")


if __name__ == "__main__":
    main()