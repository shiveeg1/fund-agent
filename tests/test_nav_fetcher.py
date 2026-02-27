"""Tests for tools/nav_fetcher.py"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tools.nav_fetcher import _parse_amfi_nav


SAMPLE_AMFI = """\
Scheme Code;ISIN Div Payout/ ISIN Growth;ISIN Div Reinvestment;Scheme Name;Net Asset Value;Date
119551;INF846K01DP8;INF846K01DQ6;Axis Bluechip Fund - Growth;52.3456;27-Feb-2026
120503;INF179K01BB0;-;HDFC Top 100 Fund - Growth;987.1234;27-Feb-2026
BadLine
"""


def test_parse_amfi_nav_extracts_valid_lines():
    records = _parse_amfi_nav(SAMPLE_AMFI)
    assert len(records) == 2
    assert records[0]["scheme_code"] == "119551"
    assert records[0]["nav"] == pytest.approx(52.3456)
    assert records[0]["nav_date"] == "27-Feb-2026"


def test_parse_amfi_nav_skips_malformed_lines():
    records = _parse_amfi_nav(SAMPLE_AMFI)
    scheme_codes = [r["scheme_code"] for r in records]
    assert "BadLine" not in scheme_codes


def test_parse_amfi_nav_empty_input():
    records = _parse_amfi_nav("")
    assert records == []
