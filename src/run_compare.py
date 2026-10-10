"""Run one strategy on several coins and print one short table.

Run: python -m src.run_compare --strategy breakout --timeframe 4h --symbols SOLUSDT BTCUSDT ETHUSDT
"""
import argparse
from src.data.quantix_data import TIMEFRAMES
from src.run_backtest import STRATEGIES, load_data, evaluate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategy", default="breakout", choices=list(STRATEGIES))
    ap.add_argument("--timeframe", default="4h", choices=list(TIMEFRAMES))
    ap.add_argument("--symbols", nargs="+", default=["SOLUSDT", "BTCUSDT", "ETHUSDT"])
    ap.add_argument("--synthetic", action="store_true")
    args = ap.parse_args()

    print(f"\nStrategy: {args.strategy}   Timeframe: {args.timeframe}")
    print(f"{'coin':10}{'part':15}{'strategy %':>11}{'no fees %':>11}{'hold %':>9}"
          f"{'drop %':>9}{'hold drop %':>13}{'trades':>8}")
    for sym in args.symbols:
        try:
            df = load_data(sym, args.timeframe, args.synthetic)
        except FileNotFoundError as e:
            print(f"{sym:10}{'(no data file)':15}")
            continue
        report, _ = evaluate(df, args.strategy, args.timeframe)
        for part in ("in_sample", "out_of_sample"):
            r = report[part]
            print(f"{sym:10}{part:15}{r['strategy']['total_return_pct']:>11}"
                  f"{r['strategy_no_fees']['total_return_pct']:>11}"
                  f"{r['buy_and_hold']['total_return_pct']:>9}"
                  f"{r['strategy']['max_drawdown_pct']:>9}"
                  f"{r['buy_and_hold']['max_drawdown_pct']:>13}"
                  f"{r['strategy'].get('n_trades', 0):>8}")
        print(f"{'':10}({report['from']} to {report['to']}, {report['candles']} candles)")


if __name__ == "__main__":
    main()
