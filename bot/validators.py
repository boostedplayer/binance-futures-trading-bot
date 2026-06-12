"""Order parameters ka input validation.

Validation jaan boojh ke provider-agnostic rakha hai aur har network call se
*pehle* chalta hai. Isse galat input turant clear message ke saath fail ho jaata
hai, baad me koi cryptic API error nahi aata.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP"}


class ValidationError(ValueError):
    """Jab user ke diye order parameters galat ho to ye raise hota hai."""


def validate_symbol(symbol: str) -> str:
    """Trading symbol (jaise BTCUSDT) ko normalise aur check karo."""
    if not symbol or not symbol.strip():
        raise ValidationError("Symbol zaroori hai (jaise BTCUSDT).")
    cleaned = symbol.strip().upper()
    if not cleaned.isalnum():
        raise ValidationError(
            f"Symbol '{symbol}' galat lag raha hai - sirf letters/digits chahiye, jaise BTCUSDT."
        )
    return cleaned


def validate_side(side: str) -> str:
    """Order side validate karo, normalised value return karta hai."""
    if not side:
        raise ValidationError("Side zaroori hai (BUY ya SELL).")
    cleaned = side.strip().upper()
    if cleaned not in VALID_SIDES:
        raise ValidationError(
            f"Side '{side}' galat hai. In me se ek choose karo: {', '.join(sorted(VALID_SIDES))}."
        )
    return cleaned


def validate_order_type(order_type: str) -> str:
    """Order type validate karo, normalised value return karta hai."""
    if not order_type:
        raise ValidationError("Order type zaroori hai (MARKET, LIMIT ya STOP).")
    cleaned = order_type.strip().upper()
    if cleaned not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Order type '{order_type}' galat hai. "
            f"In me se ek choose karo: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    return cleaned


def validate_positive_decimal(value, field_name: str) -> Decimal:
    """Check karo ki value ek positive number hai (0 se bada)."""
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise ValidationError(f"{field_name} number hona chahiye, mila '{value}'.")
    if amount <= 0:
        raise ValidationError(f"{field_name} 0 se bada hona chahiye, mila {value}.")
    return amount


def validate_order(
    symbol: str,
    side: str,
    order_type: str,
    quantity,
    price: Optional[str] = None,
    stop_price: Optional[str] = None,
) -> dict:
    """Poora order request validate karke normalised, typed params return karta hai.

    Jaise hi pehli galti milti hai, clear message ke saath ValidationError raise
    hota hai.
    """
    symbol = validate_symbol(symbol)
    side = validate_side(side)
    order_type = validate_order_type(order_type)
    quantity = validate_positive_decimal(quantity, "Quantity")

    result = {
        "symbol": symbol,
        "side": side,
        "order_type": order_type,
        "quantity": quantity,
        "price": None,
        "stop_price": None,
    }

    # LIMIT aur STOP dono ke liye limit price chahiye
    if order_type in {"LIMIT", "STOP"}:
        if price is None:
            raise ValidationError(f"{order_type} order ke liye price zaroori hai.")
        result["price"] = validate_positive_decimal(price, "Price")

    # STOP (stop-limit) ko upar se ek trigger/stop price bhi chahiye
    if order_type == "STOP":
        if stop_price is None:
            raise ValidationError("STOP order ke liye stop price (--stop-price) zaroori hai.")
        result["stop_price"] = validate_positive_decimal(stop_price, "Stop price")

    # MARKET order ke saath price nahi hona chahiye
    if order_type == "MARKET" and price is not None:
        raise ValidationError("MARKET order ke saath price nahi dena chahiye.")

    return result
