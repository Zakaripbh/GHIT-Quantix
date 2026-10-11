"""Download candles from Binance public data (no API key needed).

Examples:
  python -m src.data.download_binance --symbol SOLUSDT --interval 5m --days 730
  python -m src.data.download_binance --symbol BTCUSDT --interval 4h --years 5
Saves to data/<SYMBOL>_<interval>.csv
"""
import argparse
import os
import time

import pandas as pd
import requests

BASE_URLS = [
    "https://api.binance.com",
    "https://data-api.binance.vision",  # backup address
]
INTERVAL_MS = {"5m": 5 * 60_000, "15m": 15 * 60_000, "1h": 60 * 60_000,
               "4h": 4 * 60 * 60_000, "1d": 24 * 60 * 60_000}
COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]


def fetch_batch(symbol, interval, start_ms, limit=1000):
    last_error = None
    for base in BASE_URLS:
        for _ in range(3):
            try:
                r = requests.get(
                    f"{base}/api/v3/klines",
                    params={"symbol": symbol, "interval": interval,
                            "startTime": start_ms, "limit": limit},
                    timeout=20,
                )
                if r.status_code == 200:
                    return r.json()
                last_error = f"{base} returned {r.status_code}: {r.text[:100]}"
            except requests.RequestException as e:
                last_error = str(e)
            time.sleep(1.5)
    raise RuntimeError(f"Could not download from Binance. Last error: {last_error}")


def download(symbol="SOLUSDT", interval="5m", days=180, out_path=None):
    if interval not in INTERVAL_MS:
        raise ValueError(f"interval must be one of {list(INTERVAL_MS)}")
    out_path = out_path or f"data/{symbol}_{interval}.csv"
    step = INTERVAL_MS[interval]
    end_ms = int(time.time() * 1000)
    start_ms = end_ms - int(days * 24 * 60 * 60 * 1000)
    rows = []
    print(f"Downloading {symbol} {interval} for the last {days:g} days...")

    while start_ms < end_ms:
        batch = fetch_batch(symbol, interval, start_ms)
        if not batch:
            break
        rows.extend(batch)
        start_ms = batch[-1][0] + step
        print(f"  {len(rows)} candles so far...", end="\r")
        time.sleep(0.2)  # be polite to the server

    if not rows:
        raise RuntimeError("No data came back.")

    df = pd.DataFrame(rows).iloc[:, :6]
    df.columns = COLUMNS
    df = df.astype(float)
    df["timestamp"] = df["timestamp"].astype("int64")
    df = df.drop_duplicates("timestamp").sort_values("timestamp")
    df = df.iloc[:-1]  # drop the last candle, it may still be forming

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df.to_csv(out_path, index=False)
    first = pd.to_datetime(df["timestamp"].iloc[0], unit="ms")
    last = pd.to_datetime(df["timestamp"].iloc[-1], unit="ms")
    print(f"\nSaved {len(df)} candles to {out_path}  ({first:%Y-%m-%d} to {last:%Y-%m-%d})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="SOLUSDT")
    ap.add_argument("--symbols", nargs="+", default=None, help="download several coins in one go")
    ap.add_argument("--interval", default="5m", choices=list(INTERVAL_MS))
    ap.add_argument("--days", type=float, default=None)
    ap.add_argument("--years", type=float, default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    days = args.days if args.days else (args.years * 365 if args.years else 180)
    for sym in (args.symbols or [args.symbol]):
        download(symbol=sym, interval=args.interval, days=days,
                 out_path=args.out if not args.symbols else None)
