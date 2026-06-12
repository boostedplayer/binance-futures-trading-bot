"""Binance Futures Testnet (USDT-M) ke liye simplified trading bot.

Bahar use hone wali cheezein:
    BinanceFuturesClient  - testnet API ke upar patla signed REST wrapper
    OrderManager          - client ke upar high-level order placement
    BinanceAPIError       - API error response aane pe raise hota hai
"""

from .client import BinanceFuturesClient, BinanceAPIError
from .orders import OrderManager

__all__ = ["BinanceFuturesClient", "BinanceAPIError", "OrderManager"]
__version__ = "1.0.0"
