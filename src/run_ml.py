"""Walk-forward test of the AI strategy.

Run: python -m src.run_ml --timeframe 4h --symbols SOLUSDT BTCUSDT ETHUSDT BNBUSDT XRPUSDT ADAUSDT
     python -m src.run_ml --model logistic ...      (a simpler model)

Reports, per coin:
  AUC            -> does the model rank up-moves above down-moves? 0.50 = no skill (coin flip)
  in market %    -> share of candles where the strategy held a position
  strategy / buy-and-hold results, then a year-by-year table.
Every candle tested is out-of-sample (the model had never seen it when predicting).
"""
import argparse
import numpy as np
from sklearn.metrics import roc_auc_score

from src.data.quantix_data import TIMEFRAMES
from src.strategy.ml_model import generate_signals
from src.run_backtest import load_data, evaluate
from src.run_yearly import yearly_table, print_matrix
from src.run_compare import ratio


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeframe", default="4h", choices=list(TIMEFRAMES))
    ap.add_argument("--symbols", nargs="+", default=["SOLUSDT", "BTCUSDT", "ETHUSDT"])
    ap.add_argument("--model", default="gbm", choices=["gbm", "logistic"])
    ap.add_argument("--synthetic", action="store_true")
    args = ap.parse_args()

    tables = {}
    print(f"\nAI strategy ({args.model}), walk-forward, timeframe {args.timeframe}")
    print(f"{'coin':10}{'tested period':26}{'AUC':>7}{'in market %':>13}")
    detail = []
    for sym in args.symbols:
        try:
            raw = load_data(sym, args.timeframe, args.synthetic)
        except FileNotFoundError:
            print(f"{sym:10}(no data file)")
            continue
        try:
            sig = generate_signals(raw, model=args.model)
        except ValueError as e:
            print(f"{sym:10}{e}")
            continue
        known = sig["fwd_up"].notna() & sig["prob"].notna()
        auc = roc_auc_score(sig.loc[known, "fwd_up"], sig.loc[known, "prob"])
        period = f"{sig.index[0].date()} to {sig.index[-1].date()}"
        print(f"{sym:10}{period:26}{auc:>7.3f}{sig['signal'].mean() * 100:>13.1f}")

        rep, _ = evaluate(sig, "ml", args.timeframe, with_no_fees=False, signals_ready=True)
        detail.append((sym, rep))
        tables[sym] = yearly_table(sig, "ml", signals_ready=True)

    print(f"\n{'coin':10}{'part':15}{'strategy %':>11}{'hold %':>9}{'drop %':>9}"
          f"{'hold drop %':>13}{'ret/drop':>10}{'trades':>8}")
    positive = total = 0
    for sym, rep in detail:
        for part in ("in_sample", "out_of_sample"):
            r = rep[part]
            ret, drop = r["strategy"]["total_return_pct"], r["strategy"]["max_drawdown_pct"]
            total += 1
            positive += ret > 0
            print(f"{sym:10}{part:15}{ret:>11}{r['buy_and_hold']['total_return_pct']:>9}"
                  f"{drop:>9}{r['buy_and_hold']['max_drawdown_pct']:>13}"
                  f"{ratio(ret, drop):>10}{r['strategy'].get('n_trades', 0):>8}")
    print(f"\nPositive parts: {positive} of {total}")
    print("(in_sample / out_of_sample here = first 70% / last 30% of the walk-forward period."
          " Both are truly out-of-sample.)")

    if tables:
        print_matrix(tables, "strategy", "AI STRATEGY return % per year")
        print_matrix(tables, "hold", "BUY-AND-HOLD return % per year")
        print_matrix(tables, "trades", "Number of trades closed in the year")


if __name__ == "__main__":
    main()
