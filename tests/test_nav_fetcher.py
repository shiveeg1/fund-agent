"""Tests for tools/nav_fetcher.py"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tools.nav_fetcher import _parse_amfi_nav, run


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


# ---------------------------------------------------------------------------
# Filtering behaviour
# ---------------------------------------------------------------------------

def _make_config(scheme_codes: set[str]) -> MagicMock:
    cfg = MagicMock()
    cfg.amfi_base_url = "https://example.com/NAVAll.txt"
    cfg.portfolio_scheme_codes = scheme_codes
    return cfg


def _mock_response(text: str) -> MagicMock:
    resp = MagicMock()
    resp.text = text
    resp.raise_for_status = MagicMock()
    return resp


def test_run_filters_to_portfolio_scheme_codes(mocker):
    """Only records whose scheme_code is in portfolio_scheme_codes are written."""
    mocker.patch("requests.get", return_value=_mock_response(SAMPLE_AMFI))
    mock_append = mocker.patch("tools.sheets_writer.append_timeseries", return_value=1)

    config = _make_config({"119551"})
    context: dict = {}
    result = run(config=config, logger=MagicMock(), context=context)

    written_records = mock_append.call_args.kwargs["records"]
    assert len(written_records) == 1
    assert written_records[0]["scheme_code"] == "119551"
    assert result["status"] == "success"
    assert result["rows_written"] == 1


def test_run_writes_all_records_when_scheme_codes_unset(mocker):
    """When portfolio_scheme_codes is empty, all parsed records are written."""
    mocker.patch("requests.get", return_value=_mock_response(SAMPLE_AMFI))
    mock_append = mocker.patch("tools.sheets_writer.append_timeseries", return_value=2)

    config = _make_config(set())
    context: dict = {}
    result = run(config=config, logger=MagicMock(), context=context)

    written_records = mock_append.call_args.kwargs["records"]
    assert len(written_records) == 2  # both valid lines, no filter applied
    assert result["rows_written"] == 2


def test_run_stores_filtered_records_in_context(mocker):
    """context['nav_records'] should contain only the filtered records."""
    mocker.patch("requests.get", return_value=_mock_response(SAMPLE_AMFI))
    mocker.patch("tools.sheets_writer.append_timeseries", return_value=1)

    config = _make_config({"120503"})
    context: dict = {}
    run(config=config, logger=MagicMock(), context=context)

    assert len(context["nav_records"]) == 1
    assert context["nav_records"][0]["scheme_code"] == "120503"
