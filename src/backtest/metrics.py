"""Performance metrics."""
import numpy as np
import pandas as pd

BARS_PER_YEAR_5M = 365 * 24 * 12


def compute(equity: pd.Series, trades: pd.DataFrame, bars_per_year=BARS_PER_YEAR_5M) -> dict:
    ret = equity.pct_change().dropna()
    total_return = equity.iloc[-1] / equity.iloc[0] - 1
    peak = equity.cummax()
    max_dd = ((equity - peak) / peak).min()
    sharpe = (ret.mean() / ret.std() * np.sqrt(bars_per_year)) if ret.std() > 0 else 0.0

    m = dict(total_return_pct=round(total_return * 100, 2),
             max_drawdown_pct=round(max_dd * 100, 2),
             sharpe=round(float(sharpe), 2),
             n_trades=int(len(trades)))
    if len(trades):
        wins = trades[trades["pnl"] > 0]["pnl"].sum()
        losses = -trades[trades["pnl"] <= 0]["pnl"].sum()
        m["win_rate_pct"] = round((trades["pnl"] > 0).mean() * 100, 2)
        m["profit_factor"] = round(float(wins / losses), 2) if losses > 0 else None
    return m
