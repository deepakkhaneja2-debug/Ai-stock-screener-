import math
import pandas as pd

from config import *


class RiskEngine:

    def __init__(self):
        self.risk_percent = 1.0
        self.reward_ratio = 2.0
        self.max_open_trades = 5
        self.max_daily_loss = 3.0

    # =========================================
    # ATR STOP LOSS
    # =========================================

    def atr_stoploss(self, data):

        last = data.iloc[-1]

        return last["Close"] - (last["ATR"] * 2)

    # =========================================
    # SWING STOP LOSS
    # =========================================

    def swing_stoploss(self, data):

        return data["Low"].rolling(10).min().iloc[-1]

    # =========================================
    # FINAL STOP LOSS
    # =========================================

    def stoploss(self, data):

        atr = self.atr_stoploss(data)

        swing = self.swing_stoploss(data)

        return min(atr, swing)

    # =========================================
    # TARGET
    # =========================================

    def target(self, entry, sl):

        risk = entry - sl

        return entry + (risk * self.reward_ratio)

    # =========================================
    # POSITION SIZE
    # =========================================

    def quantity(self,
                 capital,
                 entry,
                 sl):

        risk_amount = capital * self.risk_percent / 100

        risk_per_share = abs(entry - sl)

        if risk_per_share <= 0:

            return 0

        qty = math.floor(risk_amount / risk_per_share)

        return max(qty, 0)

    # =========================================
    # TRAILING STOP
    # =========================================

    def trailing_sl(self,
                    current_price,
                    old_sl,
                    atr):

        tsl = current_price - (atr * 2)

        return max(old_sl, tsl)

    # =========================================
    # RISK SCORE
    # =========================================

    def risk_score(self,
                   entry,
                   sl):

        risk = abs(entry - sl)

        if risk <= 1:
            return 100

        elif risk <= 2:
            return 80

        elif risk <= 3:
            return 60

        return 40

    # =========================================
    # REWARD SCORE
    # =========================================

    def reward_score(self,
                     entry,
                     target):

        reward = abs(target - entry)

        if reward >= 6:
            return 100

        elif reward >= 4:
            return 80

        elif reward >= 2:
            return 60

        return 40

    # =========================================
    # FINAL TRADE PLAN
    # =========================================

    def trade_plan(self, data, capital):

    last = data.iloc[-1]

    current_price = float(last["Close"])
    atr = float(last["ATR"])

    entry = round(current_price + atr * 0.25, 2)

    stoploss = round(entry - atr * 1.5, 2)

    target1 = round(entry + (entry - stoploss) * 1.5, 2)
    target2 = round(entry + (entry - stoploss) * 2.5, 2)
    target3 = round(entry + (entry - stoploss) * 4.0, 2)

    qty = self.quantity(
        capital,
        entry,
        stoploss
    )

    risk = entry - stoploss
    reward = target2 - entry

    rr = round(reward / risk, 2) if risk > 0 else 0

    return {
        "CurrentPrice": round(current_price, 2),
        "Entry": entry,
        "StopLoss": stoploss,
        "Target1": target1,
        "Target2": target2,
        "Target3": target3,
        "RR": rr,
        "Quantity": qty,
        "RiskScore": self.risk_score(entry, stoploss),
        "RewardScore": self.reward_score(entry, target2)
    }