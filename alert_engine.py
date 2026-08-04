import logging
from typing import Optional, Union

import streamlit as st

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class AlertEngine:
    """
    Alert Engine for sending notifications via Streamlit, Telegram, and WhatsApp.
    """

    def __init__(self) -> None:
        pass

    # ============================
    # Buy Alert
    # ============================

    def buy_alert(self, symbol: str, price: float) -> None:
        try:
            st.success(f"🟢 BUY : {symbol} @ ₹{price}")
            logger.info(f"BUY alert displayed for {symbol} at ₹{price}")
        except Exception as e:
            logger.error(f"Failed to show BUY alert for {symbol}: {e}")

    # ============================
    # Sell Alert
    # ============================

    def sell_alert(self, symbol: str, price: float) -> None:
        try:
            st.error(f"🔴 SELL : {symbol} @ ₹{price}")
            logger.info(f"SELL alert displayed for {symbol} at ₹{price}")
        except Exception as e:
            logger.error(f"Failed to show SELL alert for {symbol}: {e}")

    # ============================
    # Watch Alert
    # ============================

    def watch_alert(self, symbol: str) -> None:
        try:
            st.warning(f"🟡 WATCH : {symbol}")
            logger.info(f"WATCH alert displayed for {symbol}")
        except Exception as e:
            logger.error(f"Failed to show WATCH alert for {symbol}: {e}")

    # ============================
    # Streamlit Notification
    # ============================

    def notify(self, signal: Union[str, None], symbol: str, price: Optional[float] = None) -> None:
        if signal is None:
            signal = ""
        signal = str(signal).strip().upper()

        try:
            if signal == "BUY":
                if price is None:
                    logger.warning(f"BUY alert for {symbol} called without price")
                    price = 0.0
                self.buy_alert(symbol, price)
            elif signal == "SELL":
                if price is None:
                    logger.warning(f"SELL alert for {symbol} called without price")
                    price = 0.0
                self.sell_alert(symbol, price)
            else:
                self.watch_alert(symbol)
            logger.debug(f"Notified signal {signal} for {symbol}")
        except Exception as e:
            logger.error(f"Error in notify for {symbol}: {e}")

    # ============================
    # Telegram (Future Ready)
    # ============================

    def telegram_alert(self, message: str) -> bool:
        logger.info(f"Telegram alert would be sent: {message}")
        return True

    # ============================
    # WhatsApp (Future Ready)
    # ============================

    def whatsapp_alert(self, message: str) -> bool:
        logger.info(f"WhatsApp alert would be sent: {message}")
        return True

    # ============================
    # Process Alert
    # ============================

    def process(self, signal: Union[str, None], symbol: str, price: Optional[float] = None) -> bool:
        self.notify(signal, symbol, price)

        if signal is None:
            signal = ""
        signal_str = str(signal).strip().upper()
        if price is not None:
            message = f"{signal_str} | {symbol} | ₹{price}"
        else:
            message = f"{signal_str} | {symbol}"

        self.telegram_alert(message)
        self.whatsapp_alert(message)

        logger.info(f"Processed alert: {message}")
        return True

    # ============================
    # Send Alert (Compatibility with App.py v1.3)
    # ============================

    def send_alert(
        self,
        symbol: str,
        signal: Union[str, None],
        confidence: Optional[float] = None,
        entry: Optional[float] = None,
        stoploss: Optional[float] = None,
        target: Optional[float] = None
    ) -> bool:
        price = entry if entry is not None else None
        return self.process(signal, symbol, price)