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
# download data (any coin, any candle size)
python -m src.data.download_binance --symbol SOLUSDT --interval 4h --years 5
python -m src.data.download_binance --symbol BTCUSDT --interval 4h --years 5
python -m src.data.download_binance --symbol ETHUSDT --interval 4h --years 5

# test one coin
python -m src.run_backtest --symbol SOLUSDT --strategy breakout --timeframe 4h

# test the same strategy on several coins
python -m src.run_compare --strategy breakout --timeframe 4h --symbols SOLUSDT BTCUSDT ETHUSDT

# does it survive slightly different settings? (robustness)
python -m src.run_robustness --timeframe 4h --symbols SOLUSDT BTCUSDT ETHUSDT

# download many coins at once
python -m src.data.download_binance --symbols BNBUSDT XRPUSDT ADAUSDT --interval 4h --years 5
```
Each run compares the strategy (with fees), the strategy with zero fees, and buy-and-hold.
Results (trades + equity curve + metrics) go to `results/`.

## Rules of this project
1. Backtest first. No live trading until results hold on data the strategy never saw.
2. Fees and slippage are always included.
3. Signals use candle N, trades happen at the open of candle N+1 (no look-ahead).
