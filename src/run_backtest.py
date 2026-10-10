"""Run: python -m src.run_backtest [--synthetic]"""
import argparse, json, os
from src.data.quantix_data import load_csv, make_synthetic
from src.strategy.baseline import generate_signals
from src.backtest.engine import run
from src.backtest.metrics import compute

DATA_PATH = "data/SOLUSDT_5m.csv"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--synthetic", action="store_true", help="use fake data to test the pipeline")
    ap.add_argument("--train-frac", type=float, default=0.7,
                    help="first part of data = in-sample, rest = out-of-sample")
    args = ap.parse_args()

    df = make_synthetic() if args.synthetic else load_csv(DATA_PATH)
    df = generate_signals(df).dropna()
    os.makedirs("results", exist_ok=True)

    cut = int(len(df) * args.train_frac)
    report = {}
    for name, part in [("in_sample", df.iloc[:cut]), ("out_of_sample", df.iloc[cut:])]:
        trades, equity = run(part)
        report[name] = compute(equity, trades)
        trades.to_csv(f"results/trades_{name}.csv", index=False)
        equity.to_csv(f"results/equity_{name}.csv")

    with open("results/metrics.json", "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
