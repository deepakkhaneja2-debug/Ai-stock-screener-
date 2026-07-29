import pandas as pd


class BacktestEngine:

    def __init__(self):
        pass

    def run(self, data):

        trades = []
        capital = 100000

        return {
            "Total Trades": 0,
            "Wins": 0,
            "Losses": 0,
            "Win Rate": 0,
            "Net Profit": 0,
            "Capital": capital,
            "Trades": trades
        }