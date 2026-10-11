"""Robustness test: do slightly different settings give similar results?

If the strategy only works with ONE exact set of numbers, it is probably luck.
If most nearby settings also work, it is stronger.

Run: python -m src.run_robustness --symbols SOLUSDT BTCUSDT ETHUSDT --timeframe 4h
Saves every result to results/robustness_<COIN>_<timeframe>.csv
"""
import argparse, itertools, os, statistics
import pandas as pd
from src.data.quantix_data import TIMEFRAMES
from src.run_backtest import load_data, evaluate

GRID = dict(entry_n=[36, 48, 60], exit_n=[18, 24, 30], trend_n=[150, 200, 250])
DEFAULT = dict(entry_n=48, exit_n=24, trend_n=200)


def summarize(rows, col):
    vals = [r[col] for r in rows]
    pos = sum(v > 0 for v in vals)
    return (f"{pos} of {len(vals)} positive   median {statistics.median(vals):.1f}%   "
            f"worst {min(vals):.1f}%   best {max(vals):.1f}%")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeframe", default="4h", choices=list(TIMEFRAMES))
    ap.add_argument("--symbols", nargs="+", default=["SOLUSDT", "BTCUSDT", "ETHUSDT"])
    ap.add_argument("--synthetic", action="store_true")
    args = ap.parse_args()
    os.makedirs("results", exist_ok=True)

    for sym in args.symbols:
        try:
            df = load_data(sym, args.timeframe, args.synthetic)
        except FileNotFoundError:
            print(f"\n{sym}: no data file")
            continue
        rows = []
        for e, x, t in itertools.product(GRID["entry_n"], GRID["exit_n"], GRID["trend_n"]):
            rep, _ = evaluate(df, "breakout", args.timeframe,
                              params=dict(entry_n=e, exit_n=x, trend_n=t), with_no_fees=False)
            rows.append(dict(entry_n=e, exit_n=x, trend_n=t,
                             in_ret=rep["in_sample"]["strategy"]["total_return_pct"],
                             out_ret=rep["out_of_sample"]["strategy"]["total_return_pct"],
                             in_drop=rep["in_sample"]["strategy"]["max_drawdown_pct"],
                             out_drop=rep["out_of_sample"]["strategy"]["max_drawdown_pct"],
                             trades=rep["in_sample"]["strategy"]["n_trades"]
                                    + rep["out_of_sample"]["strategy"]["n_trades"]))
        pd.DataFrame(rows).to_csv(f"results/robustness_{sym}_{args.timeframe}.csv", index=False)

        print(f"\n===== {sym}  ({args.timeframe}, {len(rows)} setting combinations) =====")
        print("first 70% :", summarize(rows, "in_ret"))
        print("last 30%  :", summarize(rows, "out_ret"))
        both = sum(r["in_ret"] > 0 and r["out_ret"] > 0 for r in rows)
        print(f"positive in BOTH parts: {both} of {len(rows)}")
        print(f"\nReturn % (first 70% / last 30%), trend line = {DEFAULT['trend_n']}")
        print(f"{'entry \\ exit':>14}" + "".join(f"{x:>16}" for x in GRID["exit_n"]))
        for e in GRID["entry_n"]:
            cells = []
            for x in GRID["exit_n"]:
                r = next(r for r in rows if (r["entry_n"], r["exit_n"], r["trend_n"]) == (e, x, DEFAULT["trend_n"]))
                cells.append(f"{r['in_ret']:.1f} / {r['out_ret']:.1f}")
            print(f"{e:>14}" + "".join(f"{c:>16}" for c in cells))


if __name__ == "__main__":
    main()
