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
