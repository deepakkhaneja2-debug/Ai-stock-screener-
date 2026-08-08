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


def main():
    """Main Streamlit application."""

    st.set_page_config(
        page_title="AI Stock Scanner V1.4",
        layout="wide"
    )

    st.title("🤖 AI Stock Scanner V1.4")
    st.success("App Running Successfully")

    # Create scanner only once per Streamlit session
    if "scanner" not in st.session_state:
        st.session_state.scanner = StockScanner()

    scanner = st.session_state.scanner

    # --------------------------------------------------
    # CONTROL PANEL
    # --------------------------------------------------

    st.subheader("⚙️ Scanner Control")

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

    if clear_results:
        st.session_state.scanner = StockScanner()
        st.session_state.pop("scanner_results", None)
        st.session_state.pop("backtest_results", None)
        st.rerun()

    # --------------------------------------------------
    # RUN ONLY WHEN BUTTON IS PRESSED
    # --------------------------------------------------

    if run_scanner:

        with st.spinner("Loading market data..."):
            try:
                results = scanner.run()

                st.session_state.scanner_results = results
                st.session_state.backtest_results = (
                    scanner.backtest_results
                )

                st.success("✅ Scanner Completed Successfully")

            except Exception as e:
                st.error("❌ Scanner failed")
                st.code(traceback.format_exc())

    # --------------------------------------------------
    # GET STORED RESULTS
    # --------------------------------------------------

    results = st.session_state.get(
        "scanner_results",
        pd.DataFrame()
    )

    backtest_results = st.session_state.get(
        "backtest_results",
        {}
    )

    # --------------------------------------------------
    # SCANNER RESULTS
    # --------------------------------------------------

    st.subheader("📋 Scanner Results")

    if not results.empty:

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
    # BACKTEST DASHBOARD
    # --------------------------------------------------

    st.subheader("📊 Overall Backtest Dashboard")

    if not backtest_results:

        st.info(
            "No backtest results available. "
            "Run the scanner first."
        )

    else:

        try:

            overall_stats = scanner.dashboard.overall_stats(
                backtest_results
            )

            if overall_stats.get("Total Trades", 0) > 0:

                col1, col2, col3, col4 = st.columns(4)

                col1.metric(
                    "Total Trades",
                    int(
                        overall_stats.get(
                            "Total Trades",
                            0
                        )
                    )
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

                col5, col6, col7 = st.columns(3)

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
                    "Backtest completed but no closed trades were generated."
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

    st.subheader("🏆 Stock Ranking")

    try:

        ranking_df = scanner.dashboard.ranking_table(
            backtest_results
        )

        if ranking_df is not None and not ranking_df.empty:

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

    st.subheader("📈 Backtest Summary")

    if backtest_results:

        for symbol, report in backtest_results.items():

            with st.expander(
                f"📊 {symbol}"
            ):

                if not isinstance(report, dict):

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

                st.json(summary)


if __name__ == "__main__":
    main()