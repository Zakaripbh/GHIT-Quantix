# GHIT-Quantix

A research and backtesting engine for crypto trading strategies, built to test ideas **honestly** before any real money is used.

## Project structure

```
GHIT-Quantix/
├── .gitignore
├── README.md
├── requirements.txt              pandas, numpy, requests, scikit-learn
│
├── data/                         downloaded CSV files go here (kept off GitHub)
│   └── .gitkeep
│
├── results/                      test outputs go here (kept off GitHub)
│   └── .gitkeep
│
└── src/
    ├── __init__.py
    │
    ├── data/
    │   ├── __init__.py
    │   ├── quantix_data.py       loads and cleans candles, builds 15m/1h/4h candles
    │   └── download_binance.py   downloads any coin and candle size from Binance
    │
    ├── indicators/
    │   ├── __init__.py
    │   └── technical.py          EMA, RSI, ATR, rolling high and low
    │
    ├── strategy/
    │   ├── __init__.py
    │   ├── baseline.py           EMA + RSI rules
    │   ├── breakout.py           breakout with a trend filter
    │   └── ml_model.py           AI model with walk-forward training
    │
    ├── risk/
    │   ├── __init__.py
    │   └── position_sizing.py    risks 1% of the money per trade, ATR stop
    │
    ├── backtest/
    │   ├── __init__.py
    │   ├── engine.py             simulates trades with fees and slippage
    │   └── metrics.py            return, max drop, Sharpe, win rate, buy-and-hold
    │
    ├── run_backtest.py           test one strategy on one coin
    ├── run_compare.py            test one strategy on several coins
    ├── run_robustness.py         test 27 nearby settings of the breakout strategy
    ├── run_yearly.py             year-by-year breakdown
    └── run_ml.py                 walk-forward test of the AI strategy
```

## Setup

```
pip install -r requirements.txt
```

## Quick start

All commands run from the `GHIT-Quantix` folder.

```
# 1. download data (any coin, any candle size: 5m, 15m, 1h, 4h, 1d)
python -m src.data.download_binance --symbols SOLUSDT BTCUSDT ETHUSDT --interval 4h --years 5

# 2. test one strategy on one coin
python -m src.run_backtest --symbol SOLUSDT --strategy breakout --timeframe 4h

# 3. test the same strategy on several coins
python -m src.run_compare --strategy breakout --timeframe 4h --symbols SOLUSDT BTCUSDT ETHUSDT

# 4. does it survive slightly different settings?
python -m src.run_robustness --timeframe 4h --symbols SOLUSDT BTCUSDT ETHUSDT

# 5. was it steady, or lucky in one year?
python -m src.run_yearly --strategy breakout --timeframe 4h --symbols SOLUSDT BTCUSDT ETHUSDT

# 6. AI model, walk-forward
python -m src.run_ml --timeframe 4h --symbols SOLUSDT BTCUSDT ETHUSDT
```

Strategies: `baseline`, `breakout`, `ml`.
No data yet? Add `--synthetic` to run on fake data and check the pipeline.

## Data format

`data/<SYMBOL>_<interval>.csv` with columns `timestamp, open, high, low, close, volume`
(timestamp in milliseconds or a normal date string). The downloader creates these files.

## Rules of this project

1. Backtest first. No live trading until a strategy holds on data it never saw.
2. Fees and slippage are always included.
3. Signals use candle N, trades happen at the open of candle N+1 (no look-ahead).
4. Settings are fixed in advance. Tuning numbers until the backtest looks good is overfitting.
5. Every strategy is checked against buy-and-hold, with zero fees, on several coins, and year by year.
6. Never put passwords, API keys or tokens in this repository.

## Findings so far (2021-2026, Binance data, long-only, 4h candles)

| Strategy | Result |
|---|---|
| Baseline (EMA + RSI) | Lost money on 5m, 15m and 1h |
| Breakout | Small gains in 2023-2024 on SOL and BTC, faded in 2025-2026, weak on ETH, BNB, XRP, ADA. Not tradeable |
| AI model (gradient boosting and logistic), walk-forward | Lost money on every coin. Model skill (AUC) only 0.50 to 0.53 |

Conclusion: strategies built on price history alone did not make money after fees on these coins.
Not financial advice. Past results do not predict future results.
