"""Position sizing: risk a fixed % of equity per trade, using ATR stop distance."""


def position_size(equity: float, price: float, atr_value: float,
                  risk_pct: float = 0.01, atr_mult: float = 2.0,
                  max_leverage: float = 1.0) -> float:
    """Return units of the asset to buy."""
    if atr_value <= 0 or price <= 0:
        return 0.0
    stop_distance = atr_mult * atr_value
    units = (equity * risk_pct) / stop_distance
    max_units = (equity * max_leverage) / price
    return max(0.0, min(units, max_units))
