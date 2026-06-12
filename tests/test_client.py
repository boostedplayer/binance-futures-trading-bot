"""client.py ke tests - signing aur error handling (koi real network nahi)."""

import hashlib
import hmac

import pytest

from bot.client import BinanceAPIError, BinanceFuturesClient, _redact


def _make_client():
    return BinanceFuturesClient(api_key="testkey", api_secret="testsecret")


# ---------------------------------------------------------------- init guards

def test_bina_credentials_ke_error():
    with pytest.raises(ValueError):
        BinanceFuturesClient(api_key="", api_secret="")


# ---------------------------------------------------------------- signing

def test_signature_known_value_se_match_karta_hai():
    client = _make_client()
    params = {"symbol": "BTCUSDT", "timestamp": 1700000000000}
    expected = hmac.new(
        b"testsecret",
        b"symbol=BTCUSDT&timestamp=1700000000000",
        hashlib.sha256,
    ).hexdigest()
    assert client._sign(params) == expected


def test_alag_secret_alag_signature_deta_hai():
    c1 = BinanceFuturesClient(api_key="k", api_secret="secret1")
    c2 = BinanceFuturesClient(api_key="k", api_secret="secret2")
    params = {"a": "1"}
    assert c1._sign(params) != c2._sign(params)


# ---------------------------------------------------------------- redaction

def test_redact_sirf_aakhri_chars_dikhata_hai():
    out = _redact("supersecretkey", keep=4)
    assert out.endswith("tkey")
    assert out.startswith("*")
    assert "secret" not in out


def test_redact_empty_string():
    assert _redact("") == "<empty>"


# ---------------------------------------------------------------- error type

def test_api_error_str_me_status_aur_code():
    err = BinanceAPIError("API-key format invalid.", code=-2014, status=401)
    text = str(err)
    assert "401" in text
    assert "-2014" in text
    assert "API-key format invalid." in text
