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
        self.market_data = {}
        self.backtest_results = {}

    def load_market(self):
        """Load market data for all symbols."""

        self.market_data = self.data_engine.scan_ready_data()

        st.write(
            f"📥 Loaded {len(self.market_data)} symbols"
        )

        return self.market_data

    def process_symbol(
        self,
        symbol: str,
        data: pd.DataFrame
    ) -> None:
        """Process one symbol through the complete pipeline."""

        if data is None or data.empty:
            return

        # --------------------------------------------------
        # INDICATORS
        # --------------------------------------------------

        data, indicator_score = self.indicator_engine.process(
            data
        )

        # --------------------------------------------------
        # PATTERNS
        # --------------------------------------------------

        data, pattern_score = self.pattern_engine.process(
            data
        )

        # --------------------------------------------------
        # STRATEGY
        # --------------------------------------------------

        strategy_result = self.strategy_engine.evaluate(
            data
        )

        # --------------------------------------------------
        # CONFIDENCE
        # --------------------------------------------------

        confidence = self.confidence_engine.calculate(
            strategy_score=strategy_result.get(
                "strategy_score",
                0
            ),

            trend_score=(
                data["TrendScore"].iloc[-1]
                if "TrendScore" in data.columns
                else 0
            ),

            pattern_score=pattern_score,

            volume_spike=(
                data["VOL_SPIKE"].iloc[-1]
                if "VOL_SPIKE" in data.columns
                else False
            ),

            atr=(
                data["ATR"].iloc[-1]
                if "ATR" in data.columns
                else 0
            )
        )

        # --------------------------------------------------
        # RISK / TRADE PLAN
        # --------------------------------------------------

        trade = self.risk_engine.trade_plan(
            data,
            self.capital
        )

        if not trade:
            return

        # --------------------------------------------------
        # RESULT
        # --------------------------------------------------

        self.results.append({

            "Symbol": symbol,

            "Signal": strategy_result.get(
                "signal",
                "WATCH"
            ),

            "Confidence": confidence,

            "StrategyScore": strategy_result.get(
                "strategy_score",
                0
            ),

            "TriggeredStrategies": ", ".join(
                strategy_result.get(
                    "triggered_strategies",
                    []
                )
            ),

            "PatternScore": pattern_score,

            "SL": trade.get(
                "StopLoss",
                0
            ),

            "Qty": trade.get(
                "Quantity",
                0
            ),

            "CurrentPrice": trade.get(
                "CurrentPrice",
                0
            ),

            "Entry": trade.get(
                "Entry",
                0
            ),

            "Target1": trade.get(
                "Target1",
                0
            ),

            "Target2": trade.get(
                "Target2",
                0
            ),

            "Target3": trade.get(
                "Target3",
                0
            ),

            "RR": trade.get(
                "RR",
                0
            )
        ])

    def run(self):
        """Run scanner and backtest."""

        # --------------------------------------------------
        # LOAD MARKET DATA
        # --------------------------------------------------

        self.load_market()

        if not self.market_data:
            self.results = pd.DataFrame()
            self.backtest_results = {}

            return self.results

        # --------------------------------------------------
        # LIVE SCANNER
        # --------------------------------------------------

        progress = st.progress(
            0,
            text="Scanning stocks..."
        )

        total_symbols = len(
            self.market_data
        )

        for count, (
            symbol,
            data
        ) in enumerate(
            self.market_data.items(),
            start=1
        ):

            try:

                self.process_symbol(
                    symbol,
                    data
                )

            except Exception:

                st.warning(
                    f"⚠️ Error processing {symbol}"
                )

                st.code(
                    traceback.format_exc()
                )

            progress.progress(
                count / total_symbols,
                text=(
                    f"Scanning {symbol} "
                    f"({count}/{total_symbols})"
                )
            )

        progress.empty()

        # --------------------------------------------------
        # CONVERT RESULTS TO DATAFRAME
        # --------------------------------------------------

        self.results = pd.DataFrame(
            self.results
        )

        # --------------------------------------------------
        # BACKTEST
        # --------------------------------------------------

        self.backtest_results = {}

        bt_progress = st.progress(
            0,
            text="Running backtests..."
        )

        for count, (
            symbol,
            data
        ) in enumerate(
            self.market_data.items(),
            start=1
        ):

            if data is None or data.empty:
                continue

            try:

                bt_data, _ = (
                    self.indicator_engine.process(
                        data.copy()
                    )
                )

                raw_report = (
                    self.backtest.run(
                        bt_data
                    )
                )

                analysis = (
                    self.backtest_analyzer.analyze(
                        raw_report
                    )
                )

                self.backtest_results[
                    symbol
                ] = analysis

            except Exception:

                st.warning(
                    f"⚠️ Backtest error: {symbol}"
                )

                st.code(
                    traceback.format_exc()
                )

            bt_progress.progress(
                count / total_symbols,
                text=(
                    f"Backtesting {symbol} "
                    f"({count}/{total_symbols})"
                )
            )

        bt_progress.empty()

        return self.results

    def send_alerts(self):

        if self.results.empty:
            return

        for _, row in self.results.iterrows():

            if row.get(
                "Signal",
                "WATCH"
            ) == "WATCH":

                continue

            try:

                self.alert_engine.process(
                    signal=row["Signal"],
                    symbol=row["Symbol"],
                    price=row["Entry"]
                )

            except Exception:

                st.warning(
                    f"Alert error: {row['Symbol']}"
                )

    def save_logs(self):

        if self.results.empty:
            return

        for _, row in self.results.iterrows():

            try:

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

            except Exception:

                st.warning(
                    f"Log error: {row['Symbol']}"
                )

    def show_dashboard(self):

        if self.results.empty:
            return

        try:

            st.subheader(
                "📊 Live Dashboard"
            )

            st.write(
                self.dashboard.summary(
                    self.results
                )
            )

        except Exception:

            st.warning(
                "Dashboard could not be generated."
            )

    def performance_report(self):

        try:

            return {
                "Summary":
                    self.performance.summary(),

                "Average Profit":
                    self.performance.average_profit(),

                "Average Loss":
                    self.performance.average_loss()
            }

        except Exception:

            return {}


def main():
    """Main Streamlit application."""

    # --------------------------------------------------
    # PAGE CONFIG
    # --------------------------------------------------

    st.set_page_config(
        page_title="AI Stock Scanner V1.4",
        page_icon="🤖",
        layout="wide"
    )

    # --------------------------------------------------
    # HEADER
    # --------------------------------------------------

    st.title(
        "🤖 AI Stock Scanner V1.4"
    )

    st.success(
        "App Running Successfully"
    )

    # --------------------------------------------------
    # CREATE SCANNER ONCE
    # --------------------------------------------------

    if "scanner" not in st.session_state:

        st.session_state.scanner = (
            StockScanner()
        )

    scanner = (
        st.session_state.scanner
    )

    # --------------------------------------------------
    # CONTROL PANEL
    # --------------------------------------------------

    st.subheader(
        "⚙️ Scanner Control"
    )

    col1, col2 = st.columns(2)

    with col1:

        run_scanner = st.button(
            "🚀 Run Scanner",
            type="primary",
            use_container_width=True
        )

    with col2:

        clear_results = st.button(
            "🗑️ Clear Results",
            use_container_width=True
        )

    # --------------------------------------------------
    # CLEAR
    # --------------------------------------------------

    if clear_results:

        st.session_state.pop(
            "scanner_results",
            None
        )

        st.session_state.pop(
            "backtest_results",
            None
        )

        st.session_state.scanner = (
            StockScanner()
        )

        st.rerun()

    # --------------------------------------------------
    # RUN SCANNER
    # --------------------------------------------------

    if run_scanner:

        try:

            with st.spinner(
                "🔄 Loading market data..."
            ):

                results = scanner.run()

            # Save results in session

            st.session_state.scanner_results = (
                results
            )

            st.session_state.backtest_results = (
                scanner.backtest_results
            )

            st.success(
                "✅ Scanner Completed Successfully"
            )

        except Exception:

            st.error(
                "❌ Scanner failed"
            )

            st.code(
                traceback.format_exc()
            )

    # --------------------------------------------------
    # GET STORED RESULTS
    # --------------------------------------------------

    results = st.session_state.get(
        "scanner_results",
        pd.DataFrame()
    )

    backtest_results = (
        st.session_state.get(
            "backtest_results",
            {}
        )
    )

    # --------------------------------------------------
    # SCANNER RESULTS
    # --------------------------------------------------

    st.subheader(
        "📋 Scanner Results"
    )

    if (
        isinstance(results, pd.DataFrame)
        and not results.empty
    ):

        st.dataframe(
            results,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No scanner results yet. "
            "Click 'Run Scanner' to start."
        )

    # --------------------------------------------------
    # OVERALL BACKTEST DASHBOARD
    # --------------------------------------------------

    st.subheader(
        "📊 Overall Backtest Dashboard"
    )

    if not backtest_results:

        st.info(
            "No backtest results available. "
            "Run the scanner first."
        )

    else:

        try:

            overall_stats = (
                scanner.dashboard.overall_stats(
                    backtest_results
                )
            )

            total_trades = int(
                overall_stats.get(
                    "Total Trades",
                    0
                )
            )

            if total_trades > 0:

                col1, col2, col3, col4 = (
                    st.columns(4)
                )

                col1.metric(
                    "Total Trades",
                    total_trades
                )

                col2.metric(
                    "Wins",
                    int(
                        overall_stats.get(
                            "Wins",
                            0
                        )
                    )
                )

                col3.metric(
                    "Losses",
                    int(
                        overall_stats.get(
                            "Losses",
                            0
                        )
                    )
                )

                col4.metric(
                    "Win Rate",
                    f"{overall_stats.get('Win Rate', 0)}%"
                )

                col5, col6, col7 = (
                    st.columns(3)
                )

                col5.metric(
                    "Total P&L",
                    round(
                        overall_stats.get(
                            "Total PnL",
                            0
                        ),
                        2
                    )
                )

                col6.metric(
                    "Profit Factor",
                    round(
                        overall_stats.get(
                            "Profit Factor",
                            0
                        ),
                        2
                    )
                )

                col7.metric(
                    "AI Score",
                    int(
                        overall_stats.get(
                            "AI Score",
                            0
                        )
                    )
                )

            else:

                st.info(
                    "Backtest completed but "
                    "no closed trades were generated."
                )

        except Exception:

            st.warning(
                "Overall dashboard could not be generated."
            )

            st.code(
                traceback.format_exc()
            )

    # --------------------------------------------------
    # STOCK RANKING
    # --------------------------------------------------

    st.subheader(
        "🏆 Stock Ranking"
    )

    try:

        ranking_df = (
            scanner.dashboard.ranking_table(
                backtest_results
            )
        )

        if (
            ranking_df is not None
            and not ranking_df.empty
        ):

            st.dataframe(
                ranking_df,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "No stock ranking available."
            )

    except Exception:

        st.warning(
            "Stock ranking could not be generated."
        )

        st.code(
            traceback.format_exc()
        )

    # --------------------------------------------------
    # BACKTEST SUMMARY
    # --------------------------------------------------

    st.subheader(
        "📈 Backtest Summary"
    )

    if backtest_results:

        for symbol, report in (
            backtest_results.items()
        ):

            with st.expander(
                f"📊 {symbol}"
            ):

                if not isinstance(
                    report,
                    dict
                ):

                    st.warning(
                        "Backtest report format incorrect."
                    )

                    continue

                summary = {

                    "Total Trades":
                        report.get(
                            "Total Trades",
                            0
                        ),

                    "Wins":
                        report.get(
                            "Wins",
                            0
                        ),

                    "Losses":
                        report.get(
                            "Losses",
                            0
                        ),

                    "BreakEven":
                        report.get(
                            "BreakEven",
                            0
                        ),

                    "Win Rate":
                        report.get(
                            "Win Rate",
                            0
                        ),

                    "Total PnL":
                        report.get(
                            "Total PnL",
                            0
                        ),

                    "Average Profit":
                        report.get(
                            "Average Profit",
                            0
                        ),

                    "Average Loss":
                        report.get(
                            "Average Loss",
                            0
                        ),

                    "Profit Factor":
                        report.get(
                            "Profit Factor",
                            0
                        ),

                    "Max Drawdown":
                        report.get(
                            "Max Drawdown",
                            0
                        ),

                    "AI Score":
                        report.get(
                            "AI Score",
                            0
                        ),

                    "Target1 Wins":
                        report.get(
                            "Target1 Wins",
                            0
                        ),

                    "Target2 Wins":
                        report.get(
                            "Target2 Wins",
                            0
                        ),

                    "Target3 Wins":
                        report.get(
                            "Target3 Wins",
                            0
                        )
                }

                st.json(
                    summary
                )

    else:

        st.info(
            "Run the scanner to generate "
            "individual backtest summaries."
        )


if __name__ == "__main__":
    main()