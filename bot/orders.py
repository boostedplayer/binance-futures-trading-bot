"""Order place karne ka high-level logic.

Ye CLI aur raw client ke beech me baithta hai: validated, normalised params leta
hai, unhe exactly waise payload me badalta hai jaisa Binance maangta hai, client
ko call karta hai, aur display ke liye ek saaf summary dict return karta hai.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Optional

from .client import BinanceFuturesClient
from .logging_config import get_logger

logger = get_logger()

# Resting order ke liye default time-in-force. GTC = good 'til cancelled.
DEFAULT_TIF = "GTC"


class OrderManager:
    """BinanceFuturesClient ke upar order banata aur bhejta hai."""

    def __init__(self, client: BinanceFuturesClient):
        self.client = client

    @staticmethod
    def _fmt(value: Decimal) -> str:
        """Decimal ko plain string banata hai jo Binance accept kare (sci-notation nahi)."""
        return format(value.normalize(), "f")

    def build_payload(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None,
    ) -> Dict[str, Any]:
        """Normalised params ko Binance order payload me badalta hai."""
        payload: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": self._fmt(quantity),
        }

        if order_type == "LIMIT":
            payload["price"] = self._fmt(price)
            payload["timeInForce"] = DEFAULT_TIF
        elif order_type == "STOP":
            # Binance Futures pe STOP matlab stop-limit: price + stopPrice dono chahiye
            payload["price"] = self._fmt(price)
            payload["stopPrice"] = self._fmt(stop_price)
            payload["timeInForce"] = DEFAULT_TIF

        return payload

    def place(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None,
    ) -> Dict[str, Any]:
        """Order place karke ek normalised result summary return karta hai.

        Dict me ye keys hoti hain: orderId, status, executedQty, avgPrice,
        aur raw API response ``raw`` ke andar.
        """
        payload = self.build_payload(
            symbol, side, order_type, quantity, price, stop_price
        )
        logger.info("%s %s order place kar rahe %s pe | payload=%s", order_type, side, symbol, payload)

        response = self.client.place_order(payload)

        # API response me se sirf kaam ki fields nikaal ke ek clean summary banate hain
        summary = {
            "orderId": response.get("orderId"),
            "status": response.get("status"),
            "executedQty": response.get("executedQty"),
            "avgPrice": response.get("avgPrice"),
            "symbol": response.get("symbol", symbol),
            "side": response.get("side", side),
            "type": response.get("type", order_type),
            "raw": response,
        }
        logger.info(
            "Order accept hua | orderId=%s | status=%s | executedQty=%s | avgPrice=%s",
            summary["orderId"],
            summary["status"],
            summary["executedQty"],
            summary["avgPrice"],
        )
        return summary
