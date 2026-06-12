# Trading Bot - Binance Futures Testnet (USDT-M)

Small Python CLI to place orders on the Binance Futures testnet
(https://testnet.binancefuture.com). Supports Market, Limit and Stop-Limit
orders, both BUY and SELL. Has input validation, file logging and proper error
handling.

Built with plain `requests` (no python-binance) so the signing and error
handling stay visible instead of being hidden inside a library.

## What it does

- Market and Limit orders, BUY/SELL
- Stop-Limit as a third type (the bonus)
- Validates CLI input before hitting the API
- Prints the order request, the response (orderId, status, executedQty,
  avgPrice) and a success/fail line
- Logs every request/response/error to `logs/trading_bot.log` (api key and
  signature are redacted)
- Different exit codes for input errors vs API/network errors

## Folder layout

```
trading_bot/
  bot/
    client.py          # signed REST client (signing + http)
    orders.py          # builds the order payload and places it
    validators.py      # input checks
    logging_config.py  # logging setup
  tests/               # pytest, runs offline (no keys needed)
  cli.py               # entry point
  requirements.txt
  requirements-dev.txt
  pytest.ini
  .env.example
```

## Setup

1. Make a testnet account at https://testnet.binancefuture.com and generate an
   API key + secret. The testnet gives you fake USDT, nothing real is at risk.

2. Install deps (Python 3.8+):

   ```bash
   python -m venv .venv
   .venv\Scripts\activate        # windows
   # source .venv/bin/activate   # mac/linux
   pip install -r requirements.txt
   ```

3. Put your keys in a `.env` file:

   ```bash
   cp .env.example .env
   # then open .env and paste your key + secret
   ```

   Or pass them directly with `--api-key` / `--api-secret` if you prefer.

## Running it

```bash
python cli.py --symbol <SYMBOL> --side <BUY|SELL> --type <MARKET|LIMIT|STOP> --quantity <QTY> [--price <PRICE>] [--stop-price <STOP>]
```

Market buy:

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

Limit sell (needs a price):

```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 95000
```

Stop-limit sell (needs both limit price and the trigger price):

```bash
python cli.py --symbol BTCUSDT --side SELL --type STOP --quantity 0.001 --price 90000 --stop-price 90500
```

Pass `--verbose` if you want debug output on the console.

Output looks like:

```
=== Order Request ===
  Symbol     : BTCUSDT
  Side       : BUY
  Type       : MARKET
  Quantity   : 0.001

=== Order Response ===
  Order ID    : 4012345678
  Status      : FILLED
  Executed Qty: 0.001
  Avg Price   : 94250.10

[SUCCESS] Order successfully place ho gaya.
```

## Logs

Everything goes to `logs/trading_bot.log` (rotating, 1MB x 3). Each order writes
the request params (signature hidden), the full response and any error. There
are sample logs from a market and a limit order in `logs/` as the task asked.

To regenerate them just run the two example commands above once your keys are
set, the log file gets appended automatically.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Tests run fully offline, no API keys needed. They cover the input validation,
the payload building for each order type, and the HMAC signing.

## Exit codes

- 0 = order placed
- 1 = exchange rejected it, or a network/unexpected error
- 2 = bad input or missing keys

Handled cases include bad symbol/side/type, quantity <= 0, missing price on a
LIMIT/STOP, missing keys, timeouts, connection drops, and whatever error Binance
sends back (insufficient margin etc).

## Assumptions / notes

- USDT-M futures only (`/fapi/v1/order`), one-way mode so no `positionSide` is
  sent.
- LIMIT and STOP use timeInForce GTC.
- The quantity/price in the examples are just placeholders, adjust them to the
  current price and the symbol's lot size or Binance will reject the order (with
  a clear message, which gets logged).
- Testnet only, fake money. Don't commit your real `.env`, it's gitignored.
