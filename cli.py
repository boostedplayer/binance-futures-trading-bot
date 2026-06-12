"""trading bot ka command-line entry point.

Examples
--------
Market buy:
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

Limit sell:
    python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 95000

Stop-limit (bonus order type):
    python cli.py --symbol BTCUSDT --side SELL --type STOP \
        --quantity 0.001 --price 90000 --stop-price 90500

Credentials BINANCE_API_KEY / BINANCE_API_SECRET env variables se aati hain
ya phir
--api-key / --api-secret se pass kar sakte ho.

"""

from __future__ import annotations

import argparse
import logging
import os
import sys

from bot.client import BinanceAPIError, BinanceFuturesClient, DEFAULT_BASE_URL
from bot.logging_config import setup_logging
from bot.orders import OrderManager
from bot.validators import ValidationError, validate_order

# Is project ki .env load karo agar python-dotenv mila. Sirf script wali directory
# tak limited rakha aur poora guard kiya - taaki system me kahin aur padi koi
# kharab/foreign .env bot ko crash na kar de.
try:
    from dotenv import load_dotenv

    _local_env = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(_local_env):
        load_dotenv(_local_env)
except Exception:  # noqa: BLE001 - dotenv bas convenience hai, kabhi fatal nahi
    pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Binance Futures Testnet (USDT-M) pe Market / Limit / Stop-Limit order place karo.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--symbol", required=True, help="Trading pair, jaise BTCUSDT")
    parser.add_argument(
        "--side", required=True, help="Order side: BUY ya SELL (case matter nahi karta)"
    )
    parser.add_argument(
        "--type",
        dest="order_type",
        required=True,
        help="Order type: MARKET, LIMIT ya STOP (stop-limit, bonus)",
    )
    parser.add_argument(
        "--quantity", required=True, help="Base asset me quantity, jaise 0.001"
    )
    parser.add_argument("--price", help="Limit price (LIMIT aur STOP ke liye zaroori)")
    parser.add_argument(
        "--stop-price", dest="stop_price", help="Trigger price (STOP ke liye zaroori)"
    )
    parser.add_argument(
        "--api-key", default=os.getenv("BINANCE_API_KEY"), help="API key (ya env BINANCE_API_KEY)"
    )
    parser.add_argument(
        "--api-secret",
        default=os.getenv("BINANCE_API_SECRET"),
        help="API secret (ya env BINANCE_API_SECRET)",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("BINANCE_BASE_URL", DEFAULT_BASE_URL),
        help="Testnet base URL",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="DEBUG level console output on karo"
    )
    return parser


def print_request_summary(order: dict) -> None:
    print("\n=== Order Request ===")
    print(f"  Symbol     : {order['symbol']}")
    print(f"  Side       : {order['side']}")
    print(f"  Type       : {order['order_type']}")
    print(f"  Quantity   : {order['quantity']}")
    if order.get("price") is not None:
        print(f"  Price      : {order['price']}")
    if order.get("stop_price") is not None:
        print(f"  Stop Price : {order['stop_price']}")


def print_response_summary(result: dict) -> None:
    print("\n=== Order Response ===")
    print(f"  Order ID    : {result.get('orderId')}")
    print(f"  Status      : {result.get('status')}")
    print(f"  Executed Qty: {result.get('executedQty')}")
    print(f"  Avg Price   : {result.get('avgPrice')}")


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logger = setup_logging(logging.DEBUG if args.verbose else logging.INFO)

    # 1. Kuch bhi mehnga karne se pehle input validate karo
    try:
        order = validate_order(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price,
        )
    except ValidationError as exc:
        logger.error("Input validation fail: %s", exc)
        print(f"\n[INPUT ERROR] {exc}", file=sys.stderr)
        return 2

    print_request_summary(order)

    # 2. Client banao (credentials missing ho to turant fail ho jaata hai)
    try:
        client = BinanceFuturesClient(
            api_key=args.api_key,
            api_secret=args.api_secret,
            base_url=args.base_url,
        )
    except ValueError as exc:
        logger.error("Client setup fail: %s", exc)
        print(f"\n[CONFIG ERROR] {exc}", file=sys.stderr)
        return 2

    # 3. Order place karo, API / network failure ko saaf se handle karo
    manager = OrderManager(client)
    try:
        result = manager.place(
            symbol=order["symbol"],
            side=order["side"],
            order_type=order["order_type"],
            quantity=order["quantity"],
            price=order["price"],
            stop_price=order["stop_price"],
        )
    except BinanceAPIError as exc:
        logger.error("Order place fail: %s", exc)
        print(f"\n[FAILED] Order exchange ne reject kar diya: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # last guard - taaki kabhi raw traceback na dikhe
        logger.exception("Order place karte waqt unexpected error")
        print(f"\n[FAILED] Unexpected error: {exc}", file=sys.stderr)
        return 1

    print_response_summary(result)
    print("\n[SUCCESS] Order successfully place ho gaya.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
