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
        
        print(f"Loaded {len(self.market_data)} Symbols")

    # ==========================================
    # Process One Stock
    # ==========================================

    def process_symbol(self, symbol, data):
    
        import streamlit as st

        if data.empty:
            return

        # Indicators
        data, indicator_score = self.indicator_engine.process(data)

        # Patterns
        data, pattern_score = self.pattern_engine.process(data)

        # Signal
        signal = self.signal_engine.generate_signal(data)

        # Risk
        trade = self.risk_engine.trade_plan(
            data,
            self.capital
        )

        last = data.iloc[-1]

        self.results.append({

            "Symbol": symbol,
            "Signal": signal["signal"],
            "Confidence": signal["strength"],
            "PatternScore": pattern_score,
            "SL": trade["StopLoss"],
            "Qty": trade["Quantity"],
            "CurrentPrice":    trade["CurrentPrice"],
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
                self.process_symbol(symbol, data)

            except Exception:
                st.write(f"Error in: {symbol}")
                st.code(traceback.format_exc())

        # Scanner Results
        self.results = pd.DataFrame(self.results)

        print(self.results)
        print(self.results.columns)
        print(self.results.shape)

        print("Rows:", len(self.results))
        print("Columns:", self.results.columns.tolist())
        print(self.results)

        # ==========================================
        # BACKTEST
        # ==========================================

        backtest_results = {}

        for symbol, data in self.market_data.items():

            if data.empty:
                continue

            try:

                bt_data, _ = self.indicator_engine.process(
                    data.copy()
                )

                raw_report = self.backtest.run(
                    bt_data
                )

                analysis = self.backtest_analyzer.analyze(
                    raw_report
                )

                backtest_results[symbol] = analysis

            except Exception:

                st.write(
                    f"Backtest Error: {symbol}"
                )

                st.code(
                    traceback.format_exc()
                )

        self.backtest_results = backtest_results

        return self.results


    # ==========================================
    # Dashboard
    # ==========================================

    def show_dashboard(self):

        if self.results.empty:
            print("No scan results generated.")
            return

        if "Signal" not in self.results.columns:
            print("Signal column missing.")
            print(self.results.columns.tolist())
            return

        print("\n========== TOP BUY ==========")
        print(
            self.dashboard.top_buy(
                self.results
            )
        )

        print("\n========== TOP SELL ==========")
        print(
            self.dashboard.top_sell(
                self.results
            )
        )

        print("\n========== SUMMARY ==========")
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
                target=row["Target"]
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
                target=row["Target"],
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

        print("\n========== PERFORMANCE ==========")

        print(self.performance.summary())

        print("\nAverage Profit")
        print(self.performance.average_profit())

        print("\nAverage Loss")
        print(self.performance.average_loss())


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":

    st.set_page_config(
        page_title="AI Stock Scanner",
        layout="wide"
    )

    st.title("AI Stock Scanner V1.1")

    st.success("App Running Successfully")

    scanner = StockScanner()

    results = scanner.run()

    st.subheader("Scanner Results")

    if not results.empty:

        st.dataframe(
            results,
            use_container_width=True
        )

    else:

        st.warning("No signals found.")

    # ==========================================
    # BACKTEST SUMMARY
    # ==========================================

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

            st.warning(
                f"{symbol}: Backtest report format incorrect."
            )