"""Tests for tools/metrics_engine.py"""
from __future__ import annotations

import pandas as pd
import pytest

from tools.metrics_engine import (
    compute_beta,
    compute_cagr,
    compute_max_drawdown,
    compute_sharpe,
    compute_sortino,
)


def test_compute_cagr_basic():
    result = compute_cagr(nav_start=100.0, nav_end=200.0, years=5.0)
    assert result == pytest.approx(0.1487, rel=1e-3)


def test_compute_cagr_raises_on_zero_years():
    with pytest.raises(ValueError):
        compute_cagr(nav_start=100.0, nav_end=200.0, years=0)


def test_compute_sharpe_positive():
    returns = pd.Series([0.001] * 252)
    sharpe = compute_sharpe(returns, risk_free_rate=0.0)
    assert sharpe > 0


def test_compute_sharpe_zero_std():
    returns = pd.Series([0.0] * 252)
    assert compute_sharpe(returns) == 0.0


def test_compute_sortino_no_downside():
    returns = pd.Series([0.005] * 252)
    sortino = compute_sortino(returns, risk_free_rate=0.0)
    assert sortino == 0.0  # no downside deviation


def test_compute_beta():
    fund = pd.Series([0.01, -0.01, 0.02, -0.02])
    benchmark = pd.Series([0.01, -0.01, 0.02, -0.02])
    assert compute_beta(fund, benchmark) == pytest.approx(1.0)


def test_compute_max_drawdown():
    nav = pd.Series([100, 110, 90, 95, 80, 100])
    mdd = compute_max_drawdown(nav)
    assert mdd == pytest.approx(-80 / 110 + 1 - 1, rel=1e-3)  # (80-110)/110
    assert mdd < 0
