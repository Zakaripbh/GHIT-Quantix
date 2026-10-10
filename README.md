# GHIT-Quantix

Backtesting engine for crypto strategies. First version = SOL/USDT, 5-minute candles, one baseline strategy.

## Setup
```
pip install -r requirements.txt
```

## Data
Put a CSV in `data/SOLUSDT_5m.csv` with columns:
`timestamp, open, high, low, close, volume`
(timestamp = milliseconds or a normal date string).

No data yet? Run `python -m src.run_backtest --synthetic` to test the pipeline on fake data.

## Run
```
python -m src.run_backtest
```
Results (trades + equity curve + metrics) go to `results/`.

## Rules of this project
1. Backtest first. No live trading until results hold on data the strategy never saw.
2. Fees and slippage are always included.
3. Signals use candle N, trades happen at the open of candle N+1 (no look-ahead).
