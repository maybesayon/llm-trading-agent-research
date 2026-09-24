"""Performance metrics (§4.4). Single source of truth: the engine and all
reporting import from here so no two definitions can drift apart."""
from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 252


def equity_curve(net: pd.Series) -> pd.Series:
    return (1.0 + net).cumprod()


def cumulative_return(net: pd.Series) -> float:
    return float(equity_curve(net).iloc[-1] - 1.0)


def annualized_return(net: pd.Series) -> float:
    final = float(equity_curve(net).iloc[-1])
    return float(final ** (TRADING_DAYS_PER_YEAR / len(net)) - 1.0)


def annualized_volatility(net: pd.Series) -> float:
    if len(net) < 2:
        return float("nan")
    return float(net.std(ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR))


def sharpe_ratio(net: pd.Series, rf_daily: float = 0.0) -> float:
    """Daily Sharpe annualized by sqrt(252) (Sharpe, 1966 convention).
    NaN when undefined (constant returns or a single observation)."""
    if len(net) < 2:
        return float("nan")
    excess = net - rf_daily
    sd = float(excess.std(ddof=1))
    if sd == 0.0:
        return float("nan")
    return float(excess.mean() / sd * np.sqrt(TRADING_DAYS_PER_YEAR))


def max_drawdown(net: pd.Series) -> float:
    eq = equity_curve(net)
    return float((eq / eq.cummax() - 1.0).min())


def downside_deviation(net: pd.Series, target: float = 0.0) -> float:
    """Annualized target-0 downside deviation: sqrt(mean(min(r - target, 0)^2))
    over ALL observations (standard Sortino denominator).

    NOTE (protocol decision D-METRICS-1): manuscript §4.4 says 'standard
    deviation of negative daily returns', which is ambiguous between this
    standard definition and the std of the negative subset. This module
    implements the standard definition; the manuscript wording should be
    aligned at merge. Flagged, not silently chosen.
    """
    shortfall = np.minimum(np.asarray(net, dtype=float) - target, 0.0)
    return float(np.sqrt(np.mean(shortfall**2)) * np.sqrt(TRADING_DAYS_PER_YEAR))


def summarize(net: pd.Series, rf_daily: float = 0.0) -> dict:
    return {
        "cumulative_return": cumulative_return(net),
        "annualized_return": annualized_return(net),
        "annualized_volatility": annualized_volatility(net),
        "sharpe_ratio": sharpe_ratio(net, rf_daily),
        "max_drawdown": max_drawdown(net),
        "downside_deviation": downside_deviation(net),
    }
