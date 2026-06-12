"""orders.py ke tests - payload sahi ban raha aur response sahi parse ho raha."""

from decimal import Decimal

from bot.orders import OrderManager


class _FakeClient:
    """Ek nakli client jo network call ki jagah fixed response laut deta hai."""

    def __init__(self, response=None):
        self.response = response or {}
        self.last_payload = None

    def place_order(self, params):
        self.last_payload = params
        return self.response


def test_market_payload_me_price_nahi_hota():
    mgr = OrderManager(_FakeClient())
    payload = mgr.build_payload("BTCUSDT", "BUY", "MARKET", Decimal("0.001"))
    assert payload == {
        "symbol": "BTCUSDT",
        "side": "BUY",
        "type": "MARKET",
        "quantity": "0.001",
    }


def test_limit_payload_me_price_aur_tif_hota_hai():
    mgr = OrderManager(_FakeClient())
    payload = mgr.build_payload(
        "BTCUSDT", "SELL", "LIMIT", Decimal("0.001"), price=Decimal("95000")
    )
    assert payload["price"] == "95000"
    assert payload["timeInForce"] == "GTC"


def test_stop_payload_me_stop_price_hota_hai():
    mgr = OrderManager(_FakeClient())
    payload = mgr.build_payload(
        "BTCUSDT",
        "SELL",
        "STOP",
        Decimal("0.001"),
        price=Decimal("90000"),
        stop_price=Decimal("90500"),
    )
    assert payload["stopPrice"] == "90500"
    assert payload["price"] == "90000"
    assert payload["timeInForce"] == "GTC"


def test_quantity_me_sci_notation_nahi_aata():
    # Decimal("0.00010") jaisi value plain string banni chahiye, "1E-4" nahi
    mgr = OrderManager(_FakeClient())
    payload = mgr.build_payload("BTCUSDT", "BUY", "MARKET", Decimal("0.00010"))
    assert "E" not in payload["quantity"].upper()


def test_place_response_ko_summary_me_badalta_hai():
    fake = _FakeClient(
        {
            "orderId": 123456,
            "status": "FILLED",
            "executedQty": "0.001",
            "avgPrice": "94250.10",
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "MARKET",
        }
    )
    mgr = OrderManager(fake)
    summary = mgr.place("BTCUSDT", "BUY", "MARKET", Decimal("0.001"))
    assert summary["orderId"] == 123456
    assert summary["status"] == "FILLED"
    assert summary["executedQty"] == "0.001"
    assert summary["avgPrice"] == "94250.10"
    # raw response bhi pass hona chahiye
    assert summary["raw"]["symbol"] == "BTCUSDT"
