"""validators.py ke tests - input validation sahi se kaam kar raha ya nahi."""

from decimal import Decimal

import pytest

from bot.validators import (
    ValidationError,
    validate_order,
    validate_order_type,
    validate_positive_decimal,
    validate_side,
    validate_symbol,
)


# ---------------------------------------------------------------- symbol

def test_symbol_lowercase_normalise_hota_hai():
    assert validate_symbol("btcusdt") == "BTCUSDT"


def test_symbol_extra_space_trim_hota_hai():
    assert validate_symbol("  ethusdt  ") == "ETHUSDT"


@pytest.mark.parametrize("bad", ["", "   ", "BTC-USDT", "BTC/USDT"])
def test_galat_symbol_pe_error(bad):
    with pytest.raises(ValidationError):
        validate_symbol(bad)


# ---------------------------------------------------------------- side

def test_side_case_insensitive():
    assert validate_side("buy") == "BUY"
    assert validate_side("Sell") == "SELL"


def test_galat_side_pe_error():
    with pytest.raises(ValidationError):
        validate_side("HODL")


# ---------------------------------------------------------------- order type

def test_order_type_normalise():
    assert validate_order_type("limit") == "LIMIT"


def test_galat_order_type_pe_error():
    with pytest.raises(ValidationError):
        validate_order_type("ICEBERG")


# ---------------------------------------------------------------- quantity / price

def test_positive_decimal_sahi():
    assert validate_positive_decimal("0.001", "Quantity") == Decimal("0.001")


@pytest.mark.parametrize("bad", ["0", "-5", "abc", None])
def test_non_positive_ya_garbage_pe_error(bad):
    with pytest.raises(ValidationError):
        validate_positive_decimal(bad, "Quantity")


# ---------------------------------------------------------------- poora order

def test_market_order_valid():
    out = validate_order("btcusdt", "buy", "market", "0.001")
    assert out["symbol"] == "BTCUSDT"
    assert out["side"] == "BUY"
    assert out["order_type"] == "MARKET"
    assert out["quantity"] == Decimal("0.001")
    assert out["price"] is None


def test_market_ke_saath_price_dene_pe_error():
    with pytest.raises(ValidationError):
        validate_order("BTCUSDT", "BUY", "MARKET", "0.001", price="95000")


def test_limit_bina_price_ke_error():
    with pytest.raises(ValidationError):
        validate_order("BTCUSDT", "SELL", "LIMIT", "0.001")


def test_limit_order_valid():
    out = validate_order("BTCUSDT", "SELL", "LIMIT", "0.001", price="95000")
    assert out["price"] == Decimal("95000")


def test_stop_bina_stop_price_ke_error():
    with pytest.raises(ValidationError):
        validate_order("BTCUSDT", "SELL", "STOP", "0.001", price="90000")


def test_stop_order_valid():
    out = validate_order(
        "BTCUSDT", "SELL", "STOP", "0.001", price="90000", stop_price="90500"
    )
    assert out["price"] == Decimal("90000")
    assert out["stop_price"] == Decimal("90500")
