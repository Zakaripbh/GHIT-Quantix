"""Run: python -m src.run_backtest [--symbol SOLUSDT] [--strategy baseline|breakout]
                                   [--timeframe 5m|15m|1h|4h] [--synthetic]

For each part of the data (in-sample / out-of-sample) it reports:
  strategy           -> with fees and slippage (the honest result)
  strategy_no_fees   -> same strategy with ZERO costs (tells us if fees are the problem)
  buy_and_hold       -> just buying and holding (the number we must beat)

Data: looks for data/<SYMBOL>_<timeframe>.csv first, otherwise it takes
data/<SYMBOL>_5m.csv and builds bigger candles from it.
"""
import argparse, json, os
from src.data.quantix_data import load_csv, make_synthetic, resample_ohlcv, TIMEFRAMES
from src.strategy import baseline, breakout
from src.backtest.engine import run
from src.backtest.metrics import compute, buy_and_hold

# name -> (signal function, ATR stop multiplier)
STRATEGIES = {"baseline": (baseline.generate_signals, 2.0),
              "breakout": (breakout.generate_signals, 3.0)}


def load_data(symbol, timeframe, synthetic=False):
    if synthetic:
        return resample_ohlcv(make_synthetic(seed=sum(map(ord, symbol))), timeframe)
    direct = f"data/{symbol}_{timeframe}.csv"
    base = f"data/{symbol}_5m.csv"
    if os.path.exists(direct):
        return load_csv(direct)
    if os.path.exists(base):
        return resample_ohlcv(load_csv(base), timeframe)
    raise FileNotFoundError(
        f"No data for {symbol}. Run: python -m src.data.download_binance "
        f"--symbol {symbol} --interval {timeframe} --years 5")


def evaluate(df, strategy, timeframe, train_frac=0.7, params=None, with_no_fees=True):
    signal_fn, atr_mult = STRATEGIES[strategy]
    df = signal_fn(df, **(params or {})).dropna()
    bars_per_year = 365 * 24 * 60 // TIMEFRAMES[timeframe][1]
    cut = int(len(df) * train_frac)
    report = {"strategy_name": strategy, "timeframe": timeframe, "candles": len(df),
              "from": str(df.index[0].date()), "to": str(df.index[-1].date())}
    raw = {}
    for name, part in [("in_sample", df.iloc[:cut]), ("out_of_sample", df.iloc[cut:])]:
        trades, equity = run(part, atr_mult=atr_mult)                                  # with fees
        report[name] = {
            "strategy": compute(equity, trades, bars_per_year),
            "buy_and_hold": buy_and_hold(part, equity, bars_per_year),
        }
        if with_no_fees:
            trades_free, equity_free = run(part, fee=0.0, slippage=0.0, atr_mult=atr_mult)  # no fees
            report[name]["strategy_no_fees"] = compute(equity_free, trades_free, bars_per_year)
        raw[name] = (trades, equity)
    return report, raw


def print_report(report, title):
    print(f"\n{title}   Candles: {report['candles']}   ({report['from']} to {report['to']})")
    for part in ("in_sample", "out_of_sample"):
        print(f"\n--- {part} ---")
        print(f"{'':20}{'return %':>10}{'max drop %':>12}{'trades':>8}")
        for key in ("strategy", "strategy_no_fees", "buy_and_hold"):
            if key not in report[part]:
                continue
            m = report[part][key]
            print(f"{key:20}{m['total_return_pct']:>10}{m['max_drawdown_pct']:>12}{m.get('n_trades', '-'):>8}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="SOLUSDT")
    ap.add_argument("--synthetic", action="store_true", help="use fake data to test the pipeline")
    ap.add_argument("--strategy", default="baseline", choices=list(STRATEGIES))
    ap.add_argument("--timeframe", default="5m", choices=list(TIMEFRAMES))
    ap.add_argument("--train-frac", type=float, default=0.7,
                    help="first part of data = in-sample, rest = out-of-sample")
    args = ap.parse_args()

    df = load_data(args.symbol, args.timeframe, args.synthetic)
    report, raw = evaluate(df, args.strategy, args.timeframe, args.train_frac)

    os.makedirs("results", exist_ok=True)
    tag = f"{args.symbol}_{args.strategy}_{args.timeframe}"
    for name, (trades, equity) in raw.items():
        trades.to_csv(f"results/trades_{tag}_{name}.csv", index=False)
        equity.to_csv(f"results/equity_{tag}_{name}.csv")
    with open(f"results/metrics_{tag}.json", "w") as f:
        json.dump(report, f, indent=2)

    print_report(report, f"{args.symbol}   Strategy: {args.strategy}   Timeframe: {args.timeframe}")


if __name__ == "__main__":
    main()
