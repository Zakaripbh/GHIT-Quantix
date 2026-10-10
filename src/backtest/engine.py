"""Event-by-event backtest. Long only, one position at a time.

Signal on candle N -> fill at OPEN of candle N+1 (no look-ahead).
Stop loss = entry - atr_mult * ATR (checked intrabar using the low).
"""
import pandas as pd
from src.risk.position_sizing import position_size


def run(df: pd.DataFrame, initial_equity=1000.0, fee=0.0004,
        slippage=0.0002, risk_pct=0.01, atr_mult=2.0):
    cash = initial_equity
    units = 0.0
    entry_price = stop = entry_time = None
    trades, equity_curve = [], []

    idx, o, h, l, c = df.index, df["open"].values, df["high"].values, df["low"].values, df["close"].values
    sig, atr_v = df["signal"].values, df["atr"].values

    for i in range(1, len(df)):
        # 1) stop loss check on current candle
        if units > 0 and l[i] <= stop:
            px = min(stop, o[i]) * (1 - slippage)
            cash += units * px * (1 - fee)
            trades.append(dict(entry_time=entry_time, exit_time=idx[i], entry=entry_price,
                               exit=px, units=units, reason="stop",
                               pnl=units * (px - entry_price)))
            units = 0.0

        # 2) act on previous candle's signal at this candle's open
        if sig[i - 1] == 1 and units == 0 and atr_v[i - 1] > 0:
            px = o[i] * (1 + slippage)
            u = position_size(cash, px, atr_v[i - 1], risk_pct, atr_mult)
            if u > 0:
                cash -= u * px * (1 + fee)
                units, entry_price, entry_time = u, px, idx[i]
                stop = px - atr_mult * atr_v[i - 1]
        elif sig[i - 1] == 0 and units > 0:
            px = o[i] * (1 - slippage)
            cash += units * px * (1 - fee)
            trades.append(dict(entry_time=entry_time, exit_time=idx[i], entry=entry_price,
                               exit=px, units=units, reason="signal",
                               pnl=units * (px - entry_price)))
            units = 0.0

        equity_curve.append(cash + units * c[i])

    equity = pd.Series(equity_curve, index=idx[1:], name="equity")
    return pd.DataFrame(trades), equity
