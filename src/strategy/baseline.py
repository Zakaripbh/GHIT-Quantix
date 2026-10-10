"""Baseline strategy: EMA trend + RSI pullback, long only.

Signal = 1 (be long) or 0 (be flat). Computed on closed candles only.
"""
import pandas as pd
from src.indicators.technical import ema, rsi, atr


def generate_signals(df: pd.DataFrame, fast=50, slow=200,
                     rsi_period=14, rsi_entry=40, rsi_exit=70) -> pd.DataFrame:
    out = df.copy()
    out["ema_fast"] = ema(out["close"], fast)
    out["ema_slow"] = ema(out["close"], slow)
    out["rsi"] = rsi(out["close"], rsi_period)
    out["atr"] = atr(out, 14)

    uptrend = out["ema_fast"] > out["ema_slow"]
    enter = uptrend & (out["rsi"] < rsi_entry)
    exit_ = (~uptrend) | (out["rsi"] > rsi_exit)

    signal, state = [], 0
    for e, x in zip(enter.values, exit_.values):
        if state == 0 and e:
            state = 1
        elif state == 1 and x:
            state = 0
        signal.append(state)
    out["signal"] = signal
    return out
