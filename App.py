import streamlit as st
import pandas as pd
import traceback

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

try:
    from config import STARTING_CAPITAL
except ImportError:
    STARTING_CAPITAL = 100000


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
        self.market_data = {}
        self.backtest_results = {}

    def load_market(self):
        self.market_data = self.data_engine.scan_ready_data() or {}
        st.write(f"Loaded {len(self.market_data)} symbols")
        return self.market_data

    def process_symbol(self, symbol, data):
        if data is None or data.empty:
            return

        data, _ = self.indicator_engine.process(data)
        data, pattern_score = self.pattern_engine.process(data)
        strategy = self.strategy_engine.evaluate(data)

        strategy_score = strategy.get("strategy_score", 0)
        trend_score = data["TrendScore"].iloc[-1] if "TrendScore" in data.columns else 0
        volume_spike = data["VOL_SPIKE"].iloc[-1] if "VOL_SPIKE" in data.columns else False
        atr = data["ATR"].iloc[-1] if "ATR" in data.columns else 0

        confidence = self.confidence_engine.calculate(
            strategy_score=strategy_score,
            trend_score=trend_score,
            pattern_score=pattern_score,
            volume_spike=volume_spike,
            atr=atr,
        )

        trade = self.risk_engine.trade_plan(data, self.capital)
        if not trade:
            return

        self.results.append({
            "Symbol": symbol,
            "Signal": strategy.get("signal", "WATCH"),
            "Confidence": confidence,
            "StrategyScore": strategy_score,
            "TriggeredStrategies": ", ".join(map(str, strategy.get("triggered_strategies", []))),
            "PatternScore": pattern_score,
            "SL": trade.get("StopLoss", 0),
            "Qty": trade.get("Quantity", 0),
            "CurrentPrice": trade.get("CurrentPrice", 0),
            "Entry": trade.get("Entry", 0),
            "Target1": trade.get("Target1", 0),
            "Target2": trade.get("Target2", 0),
            "Target3": trade.get("Target3", 0),
            "RR": trade.get("RR", 0),
        })

    def run(self):
        self.results = []
        self.load_market()

        for symbol, data in self.market_data.items():
            try:
                self.process_symbol(symbol, data)
            except Exception:
                st.warning(f"Scanner error: {symbol}")
                st.code(traceback.format_exc())

        self.results = pd.DataFrame(self.results)
        self.backtest_results = {}

        for symbol, data in self.market_data.items():
            if data is None or data.empty:
                continue
            try:
                bt_data, _ = self.indicator_engine.process(data.copy())
                raw_report = self.backtest.run(bt_data)
                self.backtest_results[symbol] = self.backtest_analyzer.analyze(raw_report)
            except Exception:
                st.warning(f"Backtest error: {symbol}")
                st.code(traceback.format_exc())

        return self.results


def show_dashboard(scanner, backtest_results):
    st.subheader("📊 Overall Backtest Dashboard")

    if not backtest_results:
        st.info("No backtest results available. Run the scanner first.")
        return

    try:
        stats = scanner.dashboard.overall_stats(backtest_results)
        if not isinstance(stats, dict):
            st.warning("Overall statistics format is invalid.")
            return

        if stats.get("Total Trades", 0) > 0:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Trades", int(stats.get("Total Trades", 0)))
            c2.metric("Wins", int(stats.get("Wins", 0)))
            c3.metric("Losses", int(stats.get("Losses", 0)))
            c4.metric("Win Rate", f"{stats.get('Win Rate', 0)}%")

            c5, c6, c7 = st.columns(3)
            c5.metric("Total P&L", round(float(stats.get("Total PnL", 0)), 2))
            c6.metric("Profit Factor", round(float(stats.get("Profit Factor", 0)), 2))
            c7.metric("AI Score", int(stats.get("AI Score", 0)))
        else:
            st.info("Backtest completed but no closed trades were generated.")
    except Exception:
        st.warning("Overall dashboard could not be generated.")
        st.code(traceback.format_exc())


def show_ranking(scanner, backtest_results):
    st.subheader("🏆 Stock Ranking")
    if not backtest_results:
        st.info("Run the scanner first to generate ranking.")
        return
    try:
        ranking = scanner.dashboard.ranking_table(backtest_results)
        if ranking is not None and not ranking.empty:
            st.dataframe(ranking, use_container_width=True, hide_index=True)
        else:
            st.info("No stock ranking available.")
    except Exception:
        st.warning("Stock ranking could not be generated.")
        st.code(traceback.format_exc())


def show_summary(backtest_results):
    st.subheader("📈 Backtest Summary")
    if not backtest_results:
        st.info("No backtest summary available.")
        return

    keys = [
        "Total Trades", "Wins", "Losses", "BreakEven", "Win Rate",
        "Total PnL", "Average Profit", "Average Loss", "Profit Factor",
        "Max Drawdown", "AI Score", "Target1 Wins", "Target2 Wins", "Target3 Wins"
    ]

    for symbol, report in backtest_results.items():
        with st.expander(f"📊 {symbol}"):
            if not isinstance(report, dict):
                st.warning("Backtest report format incorrect.")
                continue
            st.json({key: report.get(key, 0) for key in keys})


def main():
    st.set_page_config(page_title="AI Stock Scanner V1.4", layout="wide")
    st.title("🤖 AI Stock Scanner V1.4")
    st.success("App Running Successfully")

    if "scanner" not in st.session_state:
        st.session_state.scanner = StockScanner()

    scanner = st.session_state.scanner

    st.subheader("⚙️ Scanner Control")
    c1, c2 = st.columns(2)

    with c1:
        run_scanner = st.button("🚀 Run Scanner", type="primary", use_container_width=True)
    with c2:
        clear_results = st.button("🗑️ Clear Results", use_container_width=True)

    if clear_results:
        st.session_state.scanner = StockScanner()
        st.session_state.pop("scanner_results", None)
        st.session_state.pop("backtest_results", None)
        st.rerun()

    if run_scanner:
        with st.spinner("🔄 Loading market data and running scanner..."):
            try:
                results = scanner.run()
                st.session_state.scanner_results = results
                st.session_state.backtest_results = scanner.backtest_results
                st.success("✅ Scanner Completed Successfully")
            except Exception:
                st.error("❌ Scanner failed")
                st.code(traceback.format_exc())

    results = st.session_state.get("scanner_results", pd.DataFrame())
    backtest_results = st.session_state.get("backtest_results", {})

    st.subheader("📋 Scanner Results")
    if results is not None and not results.empty:
        st.dataframe(results, use_container_width=True, hide_index=True)
    else:
        st.info("No scanner results yet. Click '🚀 Run Scanner' to start.")

    show_dashboard(scanner, backtest_results)
    show_ranking(scanner, backtest_results)
    show_summary(backtest_results)


if __name__ == "__main__":
    main()
