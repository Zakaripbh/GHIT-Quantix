"""Year-by-year breakdown: how did the strategy do in each calendar year?

A strategy that earns most of its profit in ONE year (for example a crash year)
is less trustworthy than one that is steady. This shows which one we have.

Run: python -m src.run_yearly --strategy breakout --timeframe 4h --symbols SOLUSDT BTCUSDT ETHUSDT
A * after a year means the data covers only part of that year.
"""
import argparse
import pandas as pd
from src.data.quantix_data import TIMEFRAMES
from src.backtest.engine import run
from src.run_backtest import STRATEGIES, load_data


def yearly_table(df, strategy, signals_ready=False):
    signal_fn, atr_mult = STRATEGIES[strategy]
    df = (df if signals_ready else signal_fn(df)).dropna()
    trades, equity = run(df, atr_mult=atr_mult)
    close = df.loc[equity.index, "close"]
    hold = close / close.iloc[0] * equity.iloc[0]

    rows = []
    prev_s, prev_h = equity.iloc[0], hold.iloc[0]
    first_day, last_day = equity.index[0], equity.index[-1]
    for year, eq in equity.groupby(equity.index.year):
        h = hold.loc[eq.index]
        s_curve = pd.concat([pd.Series([prev_s]), eq.reset_index(drop=True)], ignore_index=True)
        h_curve = pd.concat([pd.Series([prev_h]), h.reset_index(drop=True)], ignore_index=True)
        n_trades = 0
        if len(trades):
            n_trades = int((pd.to_datetime(trades["exit_time"]).dt.year == year).sum())
        partial = (year == first_day.year and first_day > pd.Timestamp(f"{year}-01-15")) or \
                  (year == last_day.year and last_day < pd.Timestamp(f"{year}-12-15"))
        rows.append(dict(year=year, partial=partial,
                         strategy=round((eq.iloc[-1] / prev_s - 1) * 100, 1),
                         hold=round((h.iloc[-1] / prev_h - 1) * 100, 1),
                         strategy_drop=round((s_curve / s_curve.cummax() - 1).min() * 100, 1),
                         hold_drop=round((h_curve / h_curve.cummax() - 1).min() * 100, 1),
                         trades=n_trades))
        prev_s, prev_h = eq.iloc[-1], h.iloc[-1]
    return pd.DataFrame(rows)


def print_matrix(tables, col, title):
    years = sorted({y for t in tables.values() for y in t["year"]})
    print(f"\n{title}")
    print(f"{'year':8}" + "".join(f"{sym:>11}" for sym in tables))
    for y in years:
        line = f"{y:<8}"
        for t in tables.values():
            r = t[t["year"] == y]
            line += f"{'-':>11}" if r.empty else f"{str(r[col].iloc[0]) + ('*' if r['partial'].iloc[0] else ''):>11}"
        print(line)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategy", default="breakout", choices=list(STRATEGIES))
    ap.add_argument("--timeframe", default="4h", choices=list(TIMEFRAMES))
    ap.add_argument("--symbols", nargs="+", default=["SOLUSDT", "BTCUSDT", "ETHUSDT"])
    ap.add_argument("--synthetic", action="store_true")
    args = ap.parse_args()

    tables = {}
    for sym in args.symbols:
        try:
            tables[sym] = yearly_table(load_data(sym, args.timeframe, args.synthetic), args.strategy)
        except FileNotFoundError:
            print(f"{sym}: no data file")
    if not tables:
        return

    print(f"\nStrategy: {args.strategy}   Timeframe: {args.timeframe}   (* = partial year)")
    print_matrix(tables, "strategy", "STRATEGY return % per year")
    print_matrix(tables, "hold", "BUY-AND-HOLD return % per year")
    print_matrix(tables, "strategy_drop", "STRATEGY worst drop % inside the year")
    print_matrix(tables, "trades", "Number of trades closed in the year")

    print("\nYears with a positive strategy return:")
    for sym, t in tables.items():
        print(f"  {sym:10}{int((t['strategy'] > 0).sum())} of {len(t)}")


if __name__ == "__main__":
    main()
