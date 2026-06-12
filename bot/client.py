"""Binance Futures Testnet (USDT-M) ke liye patla signed REST client.

Is layer ko CLI ke baare me kuch nahi pata. Iska bas itna kaam hai:
  * request ko sign karna (HMAC SHA256, query string ke upar, Binance spec ke hisaab se)
  * usse testnet pe bhejna
  * har request/response/error log karna
  * API ya network fail hone pe ek typed exception raise karna

Yaha jaan boojh ke plain ``requests`` use kiya hai, koi heavy SDK nahi - taaki
signing aur error-handling ka logic saaf dikhe aur review me easy rahe.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

from .logging_config import get_logger

DEFAULT_BASE_URL = "https://testnet.binancefuture.com"
ORDER_PATH = "/fapi/v1/order"
TIME_PATH = "/fapi/v1/time"
ACCOUNT_PATH = "/fapi/v2/account"

logger = get_logger()


class BinanceAPIError(Exception):
    """Jab Binance error response deta hai tab ye raise hota hai.

    Attributes:
        code:    Binance error code (jaise -2019), ya None agar HTTP/transport error ho.
        message: API ya transport layer se aaya human-readable message.
        status:  HTTP status code, jab available ho.
    """

    def __init__(self, message: str, code: Optional[int] = None, status: Optional[int] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status

    def __str__(self) -> str:
        parts = []
        if self.status is not None:
            parts.append(f"HTTP {self.status}")
        if self.code is not None:
            parts.append(f"code={self.code}")
        prefix = f"[{', '.join(parts)}] " if parts else ""
        return f"{prefix}{self.message}"


def _redact(value: str, keep: int = 4) -> str:
    """Secret ko chhupao, bas aakhri kuch characters rakho taaki correlate kar sake."""
    if not value:
        return "<empty>"
    if len(value) <= keep:
        return "*" * len(value)
    return "*" * (len(value) - keep) + value[-keep:]


class BinanceFuturesClient:
    """Binance Futures Testnet API ke upar signed REST wrapper."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = DEFAULT_BASE_URL,
        recv_window: int = 5000,
        timeout: int = 10,
    ):
        if not api_key or not api_secret:
            raise ValueError(
                "API key aur secret dono chahiye. BINANCE_API_KEY / "
                "BINANCE_API_SECRET set karo ya seedha pass karo."
            )
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self.recv_window = recv_window
        self.timeout = timeout

        # Session reuse karte hain taaki har call pe API key header dubara na lagana pade
        self._session = requests.Session()
        self._session.headers.update({"X-MBX-APIKEY": api_key})
        logger.debug(
            "Client ready | base_url=%s | api_key=%s",
            self.base_url,
            _redact(api_key),
        )

    # ------------------------------------------------------------------ signing

    def _sign(self, params: Dict[str, Any]) -> str:
        """Params ki query-string ka HMAC SHA256 signature banata hai."""
        query = urlencode(params)
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    # ---------------------------------------------------------------- transport

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False,
    ) -> Any:
        """Request bhejta hai aur parsed JSON return karta hai, fail pe BinanceAPIError."""
        params = dict(params or {})
        url = f"{self.base_url}{path}"

        # Signed call me timestamp + recvWindow + signature add karna padta hai
        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params["recvWindow"] = self.recv_window
            params["signature"] = self._sign(params)

        # Outgoing request log karo, par signature redact karke
        safe_params = dict(params)
        if "signature" in safe_params:
            safe_params["signature"] = _redact(safe_params["signature"])
        logger.info("REQUEST  %s %s | params=%s", method, path, safe_params)

        try:
            response = self._session.request(
                method, url, params=params, timeout=self.timeout
            )
        except requests.exceptions.Timeout as exc:
            logger.error("Network timeout %s %s pe: %s", method, path, exc)
            raise BinanceAPIError(f"Request {self.timeout}s me timeout ho gaya") from exc
        except requests.exceptions.ConnectionError as exc:
            logger.error("Network connection error %s %s pe: %s", method, path, exc)
            raise BinanceAPIError(f"Network connection fail: {exc}") from exc
        except requests.exceptions.RequestException as exc:
            logger.error("Unexpected request error %s %s pe: %s", method, path, exc)
            raise BinanceAPIError(f"Request fail: {exc}") from exc

        return self._handle_response(response, method, path)

    def _handle_response(self, response: requests.Response, method: str, path: str) -> Any:
        """Response parse karo, log karo aur API/HTTP error pe raise karo."""
        try:
            payload = response.json()
        except ValueError:
            payload = response.text

        logger.info(
            "RESPONSE %s %s | status=%s | body=%s",
            method,
            path,
            response.status_code,
            payload,
        )

        if response.status_code >= 400:
            # Binance ka error body aise dikhta hai: {"code": -2019, "msg": "..."}
            if isinstance(payload, dict) and "msg" in payload:
                err = BinanceAPIError(
                    payload.get("msg", "Unknown API error"),
                    code=payload.get("code"),
                    status=response.status_code,
                )
            else:
                err = BinanceAPIError(str(payload), status=response.status_code)
            logger.error("API error %s %s pe: %s", method, path, err)
            raise err

        return payload

    # ----------------------------------------------------------------- requests

    def ping_time(self) -> int:
        """Testnet server time (ms) return karta hai - unsigned, connectivity check ke liye sahi."""
        data = self._request("GET", TIME_PATH)
        return data["serverTime"]

    def get_account(self) -> Dict[str, Any]:
        """Account ki info return karta hai (signed call)."""
        return self._request("GET", ACCOUNT_PATH, signed=True)

    def place_order(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Order place karta hai. ``params`` already Binance-shape aur valid hone chahiye."""
        return self._request("POST", ORDER_PATH, params=params, signed=True)
