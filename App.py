import streamlit as st
import pandas as pd
import traceback

from config import *

from data_engine import DataEngine
from indicator_engine import IndicatorEngine
from pattern_engine import PatternEngine
from signal_engine import SignalEngine
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
        self.signal_engine = SignalEngine()
        self.risk_engine = RiskEngine()
        self.alert_engine = AlertEngine()
        self.dashboard = DashboardEngine()
        self.logger = TradeLogger()
        self.performance = PerformanceAnalyzer()
        self.backtest = BacktestEngine()
        self.backtest_analyzer = BacktestAnalyzer()

        self.capital = STARTING_CAPITAL

        self.results = []


    # ==========================================
    # Load Market Data
    # ==========================================

    def load_market(self):

        print("Loading Market Data...")

        self.market_data = self.data_engine.scan_ready_data()

        st.write(self.market_data.keys())
        st.write(len(self.market_data))

        print(
            f"Loaded {len(self.market_data)} Symbols"
        )


    # ==========================================
    # Process One Stock
    # ==========================================

    def process_symbol(self, symbol, data):

        if data.empty:
            return

        # Indicators
        data, indicator_score = (
            self.indicator_engine.process(data)
        )

        # Patterns
        data, pattern_score = (
            self.pattern_engine.process(data)
        )

        # Signal
        signal = (
            self.signal_engine.generate_signal(data)
        )

        # Risk
        trade = (
            self.risk_engine.trade_plan(
                data,
                self.capital
            )
        )

        self.results.append({

            "Symbol": symbol,

            "Signal": signal["signal"],

            "Confidence": signal["strength"],

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


    # ==========================================
    # Run Scanner
    # ==========================================

    def run(self):

        self.load_market()

        for symbol, data in self.market_data.items():

            try:

                self.process_symbol(
                    symbol,
                    data
                )

            except Exception:

                st.write(
                    f"Error in: {symbol}"
                )

                st.code(
                    traceback.format_exc()
                )


        # ======================================
        # Scanner Results
        # ======================================

        self.results = pd.DataFrame(
            self.results
        )

        print(self.results)

        if not self.results.empty:

            print(
                self.results.columns
            )

            print(
                self.results.shape
            )

        print(
            "Rows:",
            len(self.results)
        )


        # ======================================
        # BACKTEST
        # ======================================

        backtest_results = {}

        for symbol, data in self.market_data.items():

            if data.empty:
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

                backtest_results[
                    symbol
                ] = analysis

            except Exception:

                st.write(
                    f"Backtest Error: {symbol}"
                )

                st.code(
                    traceback.format_exc()
                )


        self.backtest_results = (
            backtest_results
        )

        return self.results


    # ==========================================
    # Dashboard
    # ==========================================

    def show_dashboard(self):

        if self.results.empty:

            print(
                "No scan results generated."
            )

            return


        if "Signal" not in self.results.columns:

            print(
                "Signal column missing."
            )

            print(
                self.results.columns.tolist()
            )

            return


        print(
            "\n========== TOP BUY =========="
        )

        print(
            self.dashboard.top_buy(
                self.results
            )
        )


        print(
            "\n========== TOP SELL =========="
        )

        print(
            self.dashboard.top_sell(
                self.results
            )
        )


        print(
            "\n========== SUMMARY =========="
        )

        print(
            self.dashboard.summary(
                self.results
            )
        )


    # ==========================================
    # Send Alerts
    # ==========================================

    def send_alerts(self):

        for _, row in self.results.iterrows():

            if row["Signal"] == "WATCH":
                continue

            self.alert_engine.send_alert(

                symbol=row["Symbol"],

                signal=row["Signal"],

                confidence=row["Confidence"],

                entry=row["Entry"],

                stoploss=row["SL"],

                target=row["Target1"]
            )


    # ==========================================
    # Save Trade Log
    # ==========================================

    def save_logs(self):

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


    # ==========================================
    # Performance Report
    # ==========================================

    def performance_report(self):

        print(
            "\n========== PERFORMANCE =========="
        )

        print(
            self.performance.summary()
        )

        print(
            "\nAverage Profit"
        )

        print(
            self.performance.average_profit()
        )

        print(
            "\nAverage Loss"
        )

        print(
            self.performance.average_loss()
        )


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":

    st.set_page_config(

        page_title="AI Stock Scanner V1.3",

        page_icon="📊",

        layout="wide"
    )


    st.title(
        "AI Stock Scanner V1.3"
    )


    st.success(
        "App Running Successfully"
    )


    scanner = StockScanner()


    results = scanner.run()


    # ==========================================
    # SCANNER RESULTS
    # ==========================================

    st.subheader(
        "Scanner Results"
    )


    if not results.empty:

        st.dataframe(

            results,

            use_container_width=True
        )

    else:

        st.warning(
            "No signals found."
        )


    # ==========================================
    # OVERALL BACKTEST DASHBOARD
    # ==========================================

    st.subheader(
        "📊 Overall Backtest Dashboard"
    )


    all_reports = []


    for symbol, report in (
        scanner.backtest_results.items()
    ):

        if isinstance(report, dict):

            all_reports.append({

                "Symbol": symbol,

                "Trades": report.get(
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

                "Open": report.get(
                    "Open",
                    0
                ),

                "Win Rate": report.get(
                    "Win Rate",
                    0
                ),

                "PnL": report.get(
                    "Total PnL",
                    0
                ),

                "Profit Factor": report.get(
                    "Profit Factor",
                    0
                ),

                "Max Drawdown": report.get(
                    "Max Drawdown",
                    0
                ),

                "Target1": report.get(
                    "Target1 Wins",
                    0
                ),

                "Target2": report.get(
                    "Target2 Wins",
                    0
                ),

                "Target3": report.get(
                    "Target3 Wins",
                    0
                )
            })


    overall_df = pd.DataFrame(
        all_reports
    )


    if not overall_df.empty:

        # ======================================
        # TOTAL METRICS
        # ======================================

        total_trades = int(
            overall_df["Trades"].sum()
        )

        total_wins = int(
            overall_df["Wins"].sum()
        )

        total_losses = int(
            overall_df["Losses"].sum()
        )

        total_open = int(
            overall_df["Open"].sum()
        )

        total_pnl = round(
            overall_df["PnL"].sum(),
            2
        )


        closed_trades = (
            total_wins +
            total_losses
        )


        overall_win_rate = (

            round(
                (
                    total_wins /
                    closed_trades
                ) * 100,
                2
            )

            if closed_trades > 0

            else 0
        )


        # ======================================
        # DASHBOARD CARDS
        # ======================================

        col1, col2, col3, col4 = (
            st.columns(4)
        )


        col1.metric(
            "Total Trades",
            total_trades
        )


        col2.metric(
            "Wins",
            total_wins
        )


        col3.metric(
            "Losses",
            total_losses
        )


        col4.metric(
            "Overall Win Rate",
            f"{overall_win_rate}%"
        )


        col5, col6, col7 = (
            st.columns(3)
        )


        col5.metric(
            "Total P&L",
            total_pnl
        )


        col6.metric(
            "Open Trades",
            total_open
        )


        best_stock = (
            overall_df.loc[
                overall_df["PnL"].idxmax(),
                "Symbol"
            ]
        )


        col7.metric(
            "Best Stock",
            best_stock
        )


        # ======================================
        # V1.3 RISK ADJUSTED RANKING
        # ======================================

        ranking_df = (
            overall_df.copy()
        )


        # Closed trades
        ranking_df["Closed"] = (
            ranking_df["Wins"] +
            ranking_df["Losses"]
        )


        # ======================================
        # Adjusted Win Rate
        # ======================================

        ranking_df["Adjusted Win Rate"] = (

            ranking_df.apply(

                lambda row:

                round(
                    (
                        row["Wins"] /
                        row["Closed"]
                    ) * 100,
                    2
                )

                if row["Closed"] > 0

                else 0,

                axis=1
            )
        )


        # ======================================
        # Drawdown Penalty
        # ======================================

        ranking_df["Drawdown Penalty"] = (
            ranking_df["Max Drawdown"].abs()
        )


        # ======================================
        # SCORE
        #
        # PnL        = 40%
        # Win Rate   = 25%
        # PF         = 20%
        # Drawdown   = 15%
        # ======================================

        pnl_max = (
            ranking_df["PnL"].abs().max()
        )

        if pnl_max == 0:
            pnl_max = 1


        ranking_df["PnL Score"] = (

            ranking_df["PnL"] /
            pnl_max
        ) * 40


        ranking_df["Win Score"] = (

            ranking_df[
                "Adjusted Win Rate"
            ] / 100
        ) * 25


        ranking_df["PF Score"] = (

            ranking_df[
                "Profit Factor"
            ].clip(
                lower=0,
                upper=5
            ) / 5
        ) * 20


        dd_max = (
            ranking_df[
                "Drawdown Penalty"
            ].max()
        )


        if dd_max == 0:
            dd_max = 1


        ranking_df["DD Score"] = (

            1 -

            (
                ranking_df[
                    "Drawdown Penalty"
                ] / dd_max
            )

        ) * 15


        ranking_df["Overall Score"] = (

            ranking_df["PnL Score"] +

            ranking_df["Win Score"] +

            ranking_df["PF Score"] +

            ranking_df["DD Score"]
        )


        ranking_df["Overall Score"] = (
            ranking_df[
                "Overall Score"
            ].round(2)
        )


        # ======================================
        # RATING
        # ======================================

        def get_rating(score):

            if score >= 60:
                return "🟢 BEST"

            elif score >= 35:
                return "🟡 WATCH"

            else:
                return "🔴 AVOID"


        ranking_df["Rating"] = (
            ranking_df[
                "Overall Score"
            ].apply(get_rating)
        )


        # ======================================
        # FINAL RANKING
        # ======================================

        ranking_df = (

            ranking_df.sort_values(

                by="Overall Score",

                ascending=False
            )

            .reset_index(drop=True)
        )


        ranking_df.insert(

            0,

            "Rank",

            range(
                1,
                len(ranking_df) + 1
            )
        )


        st.subheader(
            "🏆 V1.3 Risk-Adjusted Stock Ranking"
        )


        display_columns = [

            "Rank",

            "Symbol",

            "Rating",

            "Overall Score",

            "Trades",

            "Wins",

            "Losses",

            "Open",

            "Adjusted Win Rate",

            "PnL",

            "Profit Factor",

            "Max Drawdown",

            "Target1",

            "Target2",

            "Target3"
        ]


        st.dataframe(

            ranking_df[
                display_columns
            ],

            use_container_width=True,

            hide_index=True
        )


    else:

        st.warning(
            "No backtest data available."
        )


    # ==========================================
    # BACKTEST SUMMARY
    # ==========================================

    st.subheader(
        "Backtest Summary"
    )


    for symbol, report in (
        scanner.backtest_results.items()
    ):

        st.write(
            f"### {symbol}"
        )


        if isinstance(report, dict):

            st.write({

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

                "Open": report.get(
                    "Open",
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

                "Average Profit": report.get(
                    "Average Profit",
                    0
                ),

                "Average Loss": report.get(
                    "Average Loss",
                    0
                ),

                "Profit Factor": report.get(
                    "Profit Factor",
                    0
                ),

                "Max Drawdown": report.get(
                    "Max Drawdown",
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
                )
            })


        else:

            st.warning(
                f"{symbol}: "
                "Backtest report format incorrect."
            )