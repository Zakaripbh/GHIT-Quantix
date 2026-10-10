"""Download SOL/USDT 5-minute candles from Binance public data (no API key needed).

Run:  python -m src.data.download_binance --days 180
Saves to data/SOLUSDT_5m.csv
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
FIVE_MIN_MS = 5 * 60 * 1000
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


def download(symbol="SOLUSDT", interval="5m", days=180, out_path="data/SOLUSDT_5m.csv"):
    end_ms = int(time.time() * 1000)
    start_ms = end_ms - days * 24 * 60 * 60 * 1000
    rows = []
    print(f"Downloading {symbol} {interval} for the last {days} days...")

    while start_ms < end_ms:
        batch = fetch_batch(symbol, interval, start_ms)
        if not batch:
            break
        rows.extend(batch)
        start_ms = batch[-1][0] + FIVE_MIN_MS
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
    print(f"\nSaved {len(df)} candles to {out_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=180)
    ap.add_argument("--symbol", default="SOLUSDT")
    ap.add_argument("--out", default="data/SOLUSDT_5m.csv")
    args = ap.parse_args()
    download(symbol=args.symbol, days=args.days, out_path=args.out)
