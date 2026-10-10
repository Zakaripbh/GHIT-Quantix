"""Breakout strategy (Donchian channel + trend filter), long only.

Buy  : price closes ABOVE the highest high of the last `entry_n` candles
       AND price is above the long-term trend line (EMA `trend_n`).
Sell : price closes BELOW the lowest low of the last `exit_n` candles.

It trades rarely and tries to ride big moves, so fees hurt less.
Defaults are fixed on purpose. Do not tune them to the backtest (that is overfitting).
"""
import pandas as pd
from src.indicators.technical import ema, atr, rolling_high, rolling_low


def generate_signals(df: pd.DataFrame, entry_n=48, exit_n=24, trend_n=200) -> pd.DataFrame:
    out = df.copy()
    out["trend"] = ema(out["close"], trend_n)
    out["entry_level"] = rolling_high(out, entry_n)
    out["exit_level"] = rolling_low(out, exit_n)
    out["atr"] = atr(out, 14)

    enter = (out["close"] > out["entry_level"]) & (out["close"] > out["trend"])
    exit_ = out["close"] < out["exit_level"]

    signal, state = [], 0
    for e, x in zip(enter.values, exit_.values):
        if state == 0 and e:
            state = 1
        elif state == 1 and x:
            state = 0
        signal.append(state)
    out["signal"] = signal
    return out
