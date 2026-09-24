"""Metrics validated against hand-calculated values (§4.4)."""
import math

import numpy as np
import pandas as pd
import pytest

from src.evaluation.metrics import (
    annualized_return,
    annualized_volatility,
    cumulative_return,
    downside_deviation,
    max_drawdown,
    sharpe_ratio,
    summarize,
)


def test_cumulative_return_hand_calc():
    net = pd.Series([0.10, -0.05])
    assert math.isclose(cumulative_return(net), 1.10 * 0.95 - 1.0)  # 0.045


def test_annualized_return_hand_calc():
    net = pd.Series([0.10, -0.05])
    assert math.isclose(annualized_return(net), 1.045 ** (252 / 2) - 1.0)


def test_volatility_hand_calc():
    net = pd.Series([0.10, -0.05])
    # sample std of {0.10, -0.05}: mean 0.025, deviations +-0.075
    sd = math.sqrt((0.075**2 + 0.075**2) / (2 - 1))
    assert math.isclose(annualized_volatility(net), sd * math.sqrt(252))


def test_sharpe_hand_calc():
    net = pd.Series([0.10, -0.05])
    sd = math.sqrt(2 * 0.075**2)
    assert math.isclose(sharpe_ratio(net), 0.025 / sd * math.sqrt(252))
    # rf shifts the mean, not the std
    assert math.isclose(
        sharpe_ratio(net, rf_daily=0.01), (0.025 - 0.01) / sd * math.sqrt(252)
    )


def test_sharpe_undefined_cases():
    assert math.isnan(sharpe_ratio(pd.Series([0.01])))          # one observation
    assert math.isnan(sharpe_ratio(pd.Series([0.01, 0.01])))    # zero variance


def test_max_drawdown_hand_calc():
    net = pd.Series([0.10, -0.20, 0.05])
    # equity: 1.10, 0.88, 0.924; peak 1.10 -> trough 0.88 => -20%
    assert math.isclose(max_drawdown(net), 0.88 / 1.10 - 1.0)


def test_max_drawdown_monotonic_up_is_zero():
    assert max_drawdown(pd.Series([0.01, 0.02, 0.03])) == 0.0


def test_downside_deviation_hand_calc():
    net = pd.Series([0.10, -0.05, 0.02, -0.10])
    # sqrt(mean([0, 0.0025, 0, 0.01])) = sqrt(0.003125)
    assert math.isclose(
        downside_deviation(net), math.sqrt(0.003125) * math.sqrt(252)
    )


def test_downside_deviation_no_losses_is_zero():
    assert downside_deviation(pd.Series([0.01, 0.0, 0.02])) == 0.0


def test_summarize_keys_complete():
    keys = set(summarize(pd.Series([0.01, -0.01, 0.02])).keys())
    assert keys == {
        "cumulative_return",
        "annualized_return",
        "annualized_volatility",
        "sharpe_ratio",
        "max_drawdown",
        "downside_deviation",
    }
