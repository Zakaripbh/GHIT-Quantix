"""Load and clean OHLCV candle data."""
import numpy as np
import pandas as pd

COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]


def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    missing = [c for c in COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing columns: {missing}")
    df = df[COLUMNS].copy()

    ts = df["timestamp"]
    if np.issubdtype(ts.dtype, np.number):
        unit = "ms" if ts.iloc[0] > 1e11 else "s"
        df["timestamp"] = pd.to_datetime(ts, unit=unit)
    else:
        df["timestamp"] = pd.to_datetime(ts)

    df = (df.drop_duplicates("timestamp")
            .sort_values("timestamp")
            .set_index("timestamp"))
    df = df.astype(float).dropna()
    return df


def make_synthetic(n: int = 20000, seed: int = 42) -> pd.DataFrame:
    """Fake random-walk 5m candles, only for testing the pipeline."""
    rng = np.random.default_rng(seed)
    ret = rng.normal(0, 0.002, n)
    close = 100 * np.exp(np.cumsum(ret))
    open_ = np.concatenate([[100], close[:-1]])
    high = np.maximum(open_, close) * (1 + rng.uniform(0, 0.001, n))
    low = np.minimum(open_, close) * (1 - rng.uniform(0, 0.001, n))
    vol = rng.uniform(100, 1000, n)
    idx = pd.date_range("2024-01-01", periods=n, freq="5min")
    return pd.DataFrame({"open": open_, "high": high, "low": low,
                         "close": close, "volume": vol}, index=idx)


TIMEFRAMES = {"5m": (None, 5), "15m": ("15min", 15), "1h": ("1h", 60), "4h": ("4h", 240)}


def resample_ohlcv(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """Turn 5-minute candles into bigger candles (15m, 1h, 4h)."""
    if timeframe not in TIMEFRAMES:
        raise ValueError(f"timeframe must be one of {list(TIMEFRAMES)}")
    rule, _ = TIMEFRAMES[timeframe]
    if rule is None:
        return df
    out = df.resample(rule).agg({"open": "first", "high": "max", "low": "min",
                                 "close": "last", "volume": "sum"})
    return out.dropna()
