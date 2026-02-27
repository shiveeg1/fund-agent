"""Tests for tools/tax_engine.py"""
from __future__ import annotations

from datetime import date

import pytest

from tools.tax_engine import (
    LTCG_EQUITY_THRESHOLD,
    classify_holding,
    compute_equity_tax,
)


def test_classify_holding_equity_ltcg():
    result = classify_holding(
        purchase_date=date(2023, 1, 1),
        redemption_date=date(2024, 2, 1),
        is_equity=True,
    )
    assert result == "LTCG"


def test_classify_holding_equity_stcg():
    result = classify_holding(
        purchase_date=date(2024, 1, 1),
        redemption_date=date(2024, 6, 1),
        is_equity=True,
    )
    assert result == "STCG"


def test_classify_holding_debt_always_stcg():
    result = classify_holding(
        purchase_date=date(2022, 1, 1),
        redemption_date=date(2025, 1, 1),
        is_equity=False,
    )
    assert result == "STCG"


def test_equity_tax_ltcg_exempt_under_threshold():
    result = compute_equity_tax(ltcg_total=100_000, stcg_total=0)
    assert result["ltcg_tax"] == 0.0  # under ₹1.25L exemption


def test_equity_tax_ltcg_above_threshold():
    result = compute_equity_tax(ltcg_total=225_000, stcg_total=0)
    taxable = 225_000 - LTCG_EQUITY_THRESHOLD  # 100_000
    assert result["ltcg_tax"] == pytest.approx(taxable * 0.125)


def test_equity_tax_stcg():
    result = compute_equity_tax(ltcg_total=0, stcg_total=50_000)
    assert result["stcg_tax"] == pytest.approx(50_000 * 0.20)
