"""Technical indicators (pure functions, pandas in -> pandas out)."""
import pandas as pd


def ema(s: pd.Series, period: int) -> pd.Series:
    return s.ewm(span=period, adjust=False).mean()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    rs = gain / loss.replace(0, float("nan"))
    return 100 - 100 / (1 + rs)


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    prev_close = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"],
                    (df["high"] - prev_close).abs(),
                    (df["low"] - prev_close).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def rolling_high(df: pd.DataFrame, period: int) -> pd.Series:
    """Highest high of the PREVIOUS `period` candles (the current candle is not included)."""
    return df["high"].rolling(period).max().shift(1)


def rolling_low(df: pd.DataFrame, period: int) -> pd.Series:
    """Lowest low of the PREVIOUS `period` candles (the current candle is not included)."""
    return df["low"].rolling(period).min().shift(1)
