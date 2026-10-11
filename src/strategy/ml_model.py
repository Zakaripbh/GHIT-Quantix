"""AI strategy: a model that predicts if price will be higher in `horizon` candles.

HOW IT STAYS HONEST (walk-forward):
  * The model only ever sees the PAST. It is trained on old data, then used to
    predict the next block of candles it has never seen.
  * Every `retrain_every` candles it is retrained with the newest data, and so on.
  * Training labels that would peek into the prediction block are removed (purged).
  * Settings are fixed in advance. They are NOT tuned to the results.

Buy  : predicted chance of going up > enter_p
Sell : predicted chance of going up < exit_p
Output starts at the first predicted candle, so every candle returned is out-of-sample.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.indicators.technical import ema, rsi, atr


def make_features(df: pd.DataFrame) -> pd.DataFrame:
    """Every feature uses only the current and PAST candles (no look-ahead)."""
    c, r = df["close"], df["close"].pct_change()
    hi, lo = df["high"].rolling(48).max(), df["low"].rolling(48).min()
    return pd.DataFrame({
        "ret_1": r,
        "ret_6": c.pct_change(6),
        "ret_18": c.pct_change(18),
        "ret_42": c.pct_change(42),
        "ret_120": c.pct_change(120),
        "vol_20": r.rolling(20).std(),
        "vol_60": r.rolling(60).std(),
        "rsi": rsi(c, 14),
        "dist_ema50": c / ema(c, 50) - 1,
        "dist_ema200": c / ema(c, 200) - 1,
        "atr_pct": atr(df, 14) / c,
        "vol_ratio": df["volume"] / df["volume"].rolling(50).mean(),
        "range_pos": (c - lo) / (hi - lo),
    }, index=df.index)


def make_model(kind: str):
    if kind == "logistic":
        return make_pipeline(StandardScaler(), LogisticRegression(C=0.1, max_iter=500))
    return HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=150,
                                          min_samples_leaf=100, l2_regularization=1.0,
                                          random_state=0)


def generate_signals(df: pd.DataFrame, horizon=6, min_train=3000, retrain_every=500,
                     enter_p=0.55, exit_p=0.50, model="gbm") -> pd.DataFrame:
    feats = make_features(df)
    X = feats.values
    fwd = df["close"].shift(-horizon) / df["close"] - 1
    y = (fwd > 0).astype(float).where(fwd.notna())          # NaN where the future is unknown
    y = y.values
    n = len(df)

    ok = ~np.isnan(X).any(axis=1)
    first_valid = max(int(np.argmax(ok)), 200)               # EMA200 needs time to settle
    first_pred = first_valid + min_train
    if first_pred >= n:
        raise ValueError(f"Not enough data: need more than {first_pred} candles, have {n}.")

    prob = np.full(n, np.nan)
    for start in range(first_pred, n, retrain_every):
        end = min(start + retrain_every, n)
        # purge: only rows whose label is fully known BEFORE this block starts
        train = np.arange(first_valid, start - horizon)
        train = train[ok[train] & ~np.isnan(y[train])]
        if len(np.unique(y[train])) < 2:
            continue
        m = make_model(model).fit(X[train], y[train])
        block = np.arange(start, end)
        block = block[ok[block]]
        prob[block] = m.predict_proba(X[block])[:, 1]

    signal, state = np.zeros(n, dtype=int), 0
    for i in range(first_pred, n):
        p = prob[i]
        if not np.isnan(p):
            if state == 0 and p > enter_p:
                state = 1
            elif state == 1 and p < exit_p:
                state = 0
        signal[i] = state

    out = df.copy()
    out["atr"] = atr(df, 14)
    out["prob"] = prob
    out["fwd_up"] = y
    out["signal"] = signal
    return out.iloc[first_pred:]
