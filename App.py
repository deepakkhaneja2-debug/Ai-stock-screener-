import traceback

import pandas as pd
import streamlit as st

from stock_scanner import StockScanner


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI Stock Scanner V1.4",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# MAIN APP
# ============================================================

def main():
    """Main Streamlit application."""

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    st.title("🤖 AI Stock Scanner V1.4")
    st.success("✅ App Running Successfully")

    st.caption(
        "AI-powered stock scanning, signal analysis and backtesting dashboard"
    )

    # --------------------------------------------------------
    # CREATE SCANNER ONCE PER SESSION
    # --------------------------------------------------------

    if "scanner" not in st.session_state:

        try:
            st.session_state.scanner = StockScanner()

        except Exception:

            st.error("❌ StockScanner initialization failed")

            st.code(
                traceback.format_exc()
            )

            st.stop()

    scanner = st.session_state.scanner

    # --------------------------------------------------------
    # CONTROL PANEL
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # CLEAR RESULTS
    # --------------------------------------------------------

    if clear_results:

        st.session_state.pop(
            "scanner_results",
            None
        )

        st.session_state.pop(
            "backtest_results",
            None
        )

        try:
            st.session_state.scanner = StockScanner()

        except Exception:

            st.error(
                "❌ Scanner could not be reset"
            )

            st.code(
                traceback.format_exc()
            )

            st.stop()

        st.rerun()

    # --------------------------------------------------------
    # RUN SCANNER
    # --------------------------------------------------------

    if run_scanner:

        with st.spinner(
            "📡 Loading market data and running scanner..."
        ):

            try:

                results = scanner.run()

                # --------------------------------------------
                # NORMALIZE SCANNER RESULTS
                # --------------------------------------------

                if results is None:

                    results = pd.DataFrame()

                elif not isinstance(
                    results,
                    pd.DataFrame
                ):

                    try:

                        results = pd.DataFrame(
                            results
                        )

                    except Exception:

                        results = pd.DataFrame()

                # --------------------------------------------
                # STORE RESULTS
                # --------------------------------------------

                st.session_state.scanner_results = (
                    results
                )

                st.session_state.backtest_results = (
                    getattr(
                        scanner,
                        "backtest_results",
                        {}
                    )
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

    # --------------------------------------------------------
    # GET STORED RESULTS
    # --------------------------------------------------------

    results = st.session_state.get(
        "scanner_results",
        pd.DataFrame()
    )

    backtest_results = st.session_state.get(
        "backtest_results",
        {}
    )

    # ========================================================
    # SCANNER RESULTS
    # ========================================================

    st.subheader("📋 Scanner Results")

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

    # ========================================================
    # BACKTEST DASHBOARD
    # ========================================================

    st.subheader(
        "📊 Overall Backtest Dashboard"
    )

    if not backtest_results:

        st.info(
            "No backtest results available. "
            "Run the scanner first."
        )

    else:

        dashboard = getattr(
            scanner,
            "dashboard",
            None
        )

        if dashboard is None:

            st.warning(
                "⚠️ Dashboard module is not available."
            )

        else:

            try:

                overall_stats = (
                    dashboard.overall_stats(
                        backtest_results
                    )
                )

                if not isinstance(
                    overall_stats,
                    dict
                ):

                    overall_stats = {}

                total_trades = int(
                    overall_stats.get(
                        "Total Trades",
                        0
                    )
                )

                if total_trades > 0:

                    # ----------------------------------------
                    # ROW 1
                    # ----------------------------------------

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

                    # ----------------------------------------
                    # ROW 2
                    # ----------------------------------------

                    col5, col6, col7 = (
                        st.columns(3)
                    )

                    col5.metric(
                        "Total P&L",
                        round(
                            float(
                                overall_stats.get(
                                    "Total PnL",
                                    0
                                )
                            ),
                            2
                        )
                    )

                    col6.metric(
                        "Profit Factor",
                        round(
                            float(
                                overall_stats.get(
                                    "Profit Factor",
                                    0
                                )
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
                        "Backtest completed but no "
                        "closed trades were generated."
                    )

            except Exception:

                st.warning(
                    "⚠️ Overall dashboard could not be generated."
                )

                st.code(
                    traceback.format_exc()
                )

    # ========================================================
    # STOCK RANKING
    # ========================================================

    st.subheader("🏆 Stock Ranking")

    dashboard = getattr(
        scanner,
        "dashboard",
        None
    )

    if dashboard is None:

        st.info(
            "Stock ranking dashboard is not available."
        )

    else:

        try:

            ranking_df = (
                dashboard.ranking_table(
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
                "⚠️ Stock ranking could not be generated."
            )

            st.code(
                traceback.format_exc()
            )

    # ========================================================
    # BACKTEST SUMMARY
    # ========================================================

    st.subheader("📈 Backtest Summary")

    if not backtest_results:

        st.info(
            "No individual backtest reports available."
        )

    else:

        for symbol, report in backtest_results.items():

            with st.expander(
                f"📊 {symbol}"
            ):

                # --------------------------------------------
                # VALIDATE REPORT
                # --------------------------------------------

                if not isinstance(
                    report,
                    dict
                ):

                    st.warning(
                        "Backtest report format incorrect."
                    )

                    continue

                # --------------------------------------------
                # SUMMARY
                # --------------------------------------------

                summary = {

                    "Total Trades": report.get(
                        "Total Trades",
                        0
                    ),

                    "Wins": report.get(
                        "Wins",
                        0
                    ),

                    "Losses": report.get(
                        "Losses",
                        0
                    ),

                    "BreakEven": report.get(
                        "BreakEven",
                        0
                    ),

                    "Win Rate": report.get(
                        "Win Rate",
                        0
                    ),

                    "Total PnL": report.get(
                        "Total PnL",
                        0
                    ),

                    "Total Return %": report.get(
                        "Total Return %",
                        0
                    ),

                    "Average Profit": report.get(
                        "Average Profit",
                        0
                    ),

                    "Average Loss": report.get(
                        "Average Loss",
                        0
                    ),

                    "Avg Win R": report.get(
                        "Avg Win R",
                        0
                    ),

                    "Avg Loss R": report.get(
                        "Avg Loss R",
                        0
                    ),

                    "Profit Factor": report.get(
                        "Profit Factor",
                        0
                    ),

                    "Expectancy": report.get(
                        "Expectancy",
                        0
                    ),

                    "Expectancy R": report.get(
                        "Expectancy R",
                        0
                    ),

                    "Average R": report.get(
                        "Average R",
                        0
                    ),

                    "Average Holding Days": report.get(
                        "Average Holding Days",
                        0
                    ),

                    "Max Drawdown": report.get(
                        "Max Drawdown",
                        0
                    ),

                    "Consecutive Wins": report.get(
                        "Consecutive Wins",
                        0
                    ),

                    "Consecutive Losses": report.get(
                        "Consecutive Losses",
                        0
                    ),

                    "Target1 Wins": report.get(
                        "Target1 Wins",
                        0
                    ),

                    "Target2 Wins": report.get(
                        "Target2 Wins",
                        0
                    ),

                    "Target3 Wins": report.get(
                        "Target3 Wins",
                        0
                    ),

                    "Data Quality": report.get(
                        "Data Quality",
                        "UNKNOWN"
                    ),

                    "Final Equity": report.get(
                        "FinalEquity",
                        0
                    )
                }

                # --------------------------------------------
                # METRICS
                # --------------------------------------------

                c1, c2, c3, c4 = (
                    st.columns(4)
                )

                c1.metric(
                    "Trades",
                    int(
                        summary["Total Trades"]
                    )
                )

                c2.metric(
                    "Win Rate",
                    f"{summary['Win Rate']}%"
                )

                c3.metric(
                    "P&L",
                    round(
                        float(
                            summary["Total PnL"]
                        ),
                        2
                    )
                )

                c4.metric(
                    "AI Score",
                    int(
                        report.get(
                            "AI Score",
                            0
                        )
                    )
                )

                # --------------------------------------------
                # DETAILED JSON
                # --------------------------------------------

                st.json(summary)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()