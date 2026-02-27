"""Tests for tools/cams_parser.py"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tools.cams_parser import (
    _normalise_txn_type,
    _parse_cams_json,
    _parse_trade_date,
    run,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_RECORDS = [
    # Financial: Purchase
    {
        "MF_NAME": "ABSL Mutual Fund",
        "FOLIO_NUMBER": "1038369310",
        "SCHEME_NAME": "ABSL ELSS Tax Saver Fund - Direct-Growth",
        "TRADE_DATE": "14-JAN-2019",
        "TRANSACTION_TYPE": "Purchase",
        "AMOUNT": 15000.0,
        "UNITS": 468.897,
        "PRICE": 31.99,
        "BROKER": None,
        "DIVIDEND_RATE": None,
    },
    # Financial: Purchase Systematic → SIP
    {
        "MF_NAME": "HDFC Mutual Fund",
        "FOLIO_NUMBER": "9876543210",
        "SCHEME_NAME": "HDFC Flexi Cap Fund - Direct Growth",
        "TRADE_DATE": "10-MAR-2022",
        "TRANSACTION_TYPE": "Purchase Systematic",
        "AMOUNT": 5000.0,
        "UNITS": 12.345,
        "PRICE": 405.12,
        "BROKER": None,
        "DIVIDEND_RATE": None,
    },
    # Financial: Redemption
    {
        "MF_NAME": "ABSL Mutual Fund",
        "FOLIO_NUMBER": "1038369310",
        "SCHEME_NAME": "ABSL ELSS Tax Saver Fund - Direct-Growth",
        "TRADE_DATE": "17-JAN-2022",
        "TRANSACTION_TYPE": "Redemption",
        "AMOUNT": -22173.92,
        "UNITS": -468.897,
        "PRICE": 47.29,
        "BROKER": None,
        "DIVIDEND_RATE": None,
    },
    # Financial: Systematic Switch In → Switch-In
    {
        "MF_NAME": "Axis Mutual Fund",
        "FOLIO_NUMBER": "1111111111",
        "SCHEME_NAME": "Axis Small Cap Fund - Direct Growth",
        "TRADE_DATE": "05-JUN-2023",
        "TRANSACTION_TYPE": "Systematic Switch In",
        "AMOUNT": 10000.0,
        "UNITS": 100.0,
        "PRICE": 100.0,
        "BROKER": None,
        "DIVIDEND_RATE": None,
    },
    # Non-financial: null AMOUNT + UNITS
    {
        "MF_NAME": "ABSL Mutual Fund",
        "FOLIO_NUMBER": "1038369310",
        "SCHEME_NAME": "ABSL ELSS Tax Saver Fund - Direct-Growth",
        "TRADE_DATE": "15-JAN-2019",
        "TRANSACTION_TYPE": "Registration of Nominee",
        "AMOUNT": None,
        "UNITS": None,
        "PRICE": None,
        "BROKER": None,
        "DIVIDEND_RATE": None,
    },
    # Non-financial: administrative type even with amount present
    {
        "MF_NAME": "HDFC Mutual Fund",
        "FOLIO_NUMBER": "9876543210",
        "SCHEME_NAME": "HDFC Flexi Cap Fund - Direct Growth",
        "TRADE_DATE": "01-APR-2021",
        "TRANSACTION_TYPE": "CAN Data Updation",
        "AMOUNT": 0.0,
        "UNITS": 0.0,
        "PRICE": 0.0,
        "BROKER": None,
        "DIVIDEND_RATE": None,
    },
]

DUPLICATE_RECORD = {
    "MF_NAME": "ABSL Mutual Fund",
    "FOLIO_NUMBER": "1038369310",
    "SCHEME_NAME": "ABSL ELSS Tax Saver Fund - Direct-Growth",
    "TRADE_DATE": "14-JAN-2019",
    "TRANSACTION_TYPE": "Purchase",
    "AMOUNT": 15000.0,
    "UNITS": 468.897,  # same as SAMPLE_RECORDS[0] → duplicate key
    "PRICE": 31.99,
    "BROKER": None,
    "DIVIDEND_RATE": None,
}


@pytest.fixture
def sample_json_file(tmp_path: Path) -> Path:
    """Write SAMPLE_RECORDS as a CAMS JSON file and return its path."""
    data = {"dtTrxnResult": SAMPLE_RECORDS}
    p = tmp_path / "cams_export.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# _parse_trade_date
# ---------------------------------------------------------------------------

class TestParseTradeDate:
    def test_valid_date(self):
        assert _parse_trade_date("14-JAN-2019") == "2019-01-14"

    def test_valid_date_lowercase_month(self):
        assert _parse_trade_date("10-mar-2022") == "2022-03-10"

    def test_valid_date_with_whitespace(self):
        assert _parse_trade_date("  05-JUN-2023  ") == "2023-06-05"

    def test_invalid_date_returns_raw(self):
        assert _parse_trade_date("not-a-date") == "not-a-date"

    def test_empty_string_returns_empty(self):
        assert _parse_trade_date("") == ""


# ---------------------------------------------------------------------------
# _normalise_txn_type
# ---------------------------------------------------------------------------

class TestNormaliseTxnType:
    @pytest.mark.parametrize("raw,expected", [
        ("Purchase Systematic", "SIP"),
        ("Systematic Switch In", "Switch-In"),  # contains "switch" + "in" → Switch-In takes precedence
        ("Purchase", "Purchase"),
        ("PURCHASE", "Purchase"),
        ("Purchase (Continuous Offer)", "Purchase"),
        ("Redemption", "Redemption"),
        ("Redemption Of Units", "Redemption"),
        ("Redemption ", "Redemption"),
        ("Switch-In", "Switch-In"),
        ("Switch Out", "Switch-Out"),
    ])
    def test_normalisation(self, raw: str, expected: str):
        assert _normalise_txn_type(raw) == expected

    def test_unknown_type_returned_as_is(self):
        assert _normalise_txn_type("  Some Unknown Type  ") == "Some Unknown Type"


# ---------------------------------------------------------------------------
# _parse_cams_json
# ---------------------------------------------------------------------------

class TestParseCamsJson:
    def test_extracts_only_financial_transactions(self, sample_json_file: Path):
        txns = _parse_cams_json(sample_json_file, logger)
        # 4 financial records out of 6
        assert len(txns) == 4

    def test_field_mapping_purchase(self, sample_json_file: Path):
        txns = _parse_cams_json(sample_json_file, logger)
        purchase = next(t for t in txns if t["txn_type"] == "Purchase")
        assert purchase["folio"] == "1038369310"
        assert purchase["scheme_name"] == "ABSL ELSS Tax Saver Fund - Direct-Growth"
        assert purchase["transaction_date"] == "2019-01-14"
        assert purchase["amount"] == pytest.approx(15000.0)
        assert purchase["units"] == pytest.approx(468.897)
        assert purchase["nav"] == pytest.approx(31.99)

    def test_purchase_systematic_normalised_to_sip(self, sample_json_file: Path):
        txns = _parse_cams_json(sample_json_file, logger)
        sip = next(t for t in txns if t["txn_type"] == "SIP")
        assert sip["folio"] == "9876543210"
        assert sip["transaction_date"] == "2022-03-10"

    def test_redemption_extracted(self, sample_json_file: Path):
        txns = _parse_cams_json(sample_json_file, logger)
        redemptions = [t for t in txns if t["txn_type"] == "Redemption"]
        assert len(redemptions) == 1
        assert redemptions[0]["units"] == pytest.approx(-468.897)

    def test_null_amount_records_skipped(self, sample_json_file: Path):
        txns = _parse_cams_json(sample_json_file, logger)
        folios_and_types = [(t["folio"], t["txn_type"]) for t in txns]
        # "Registration of Nominee" has null AMOUNT → must not appear
        assert all(t["txn_type"] != "Registration of Nominee" for t in txns)

    def test_administrative_txn_types_skipped(self, sample_json_file: Path):
        txns = _parse_cams_json(sample_json_file, logger)
        assert all(t["txn_type"] != "CAN Data Updation" for t in txns)

    def test_nav_is_none_when_price_null(self, tmp_path: Path):
        data = {"dtTrxnResult": [{
            "FOLIO_NUMBER": "111",
            "SCHEME_NAME": "Some Fund",
            "TRADE_DATE": "01-JAN-2023",
            "TRANSACTION_TYPE": "Purchase",
            "AMOUNT": 1000.0,
            "UNITS": 10.0,
            "PRICE": None,
        }]}
        p = tmp_path / "no_price.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        txns = _parse_cams_json(p, logger)
        assert txns[0]["nav"] is None

    def test_invalid_structure_raises(self, tmp_path: Path):
        p = tmp_path / "bad.json"
        p.write_text(json.dumps({"dtTrxnResult": "not-a-list"}), encoding="utf-8")
        with pytest.raises(ValueError, match="Expected dtTrxnResult to be a list"):
            _parse_cams_json(p, logger)

    def test_empty_result_list(self, tmp_path: Path):
        p = tmp_path / "empty.json"
        p.write_text(json.dumps({"dtTrxnResult": []}), encoding="utf-8")
        assert _parse_cams_json(p, logger) == []

    def test_missing_dtTrxnResult_key(self, tmp_path: Path):
        p = tmp_path / "missing_key.json"
        p.write_text(json.dumps({"other_key": []}), encoding="utf-8")
        # missing key → empty list (raw.get returns [])
        assert _parse_cams_json(p, logger) == []


# ---------------------------------------------------------------------------
# run() — integration (sheets_writer mocked)
# ---------------------------------------------------------------------------

class TestRun:
    def _make_config(self):
        cfg = MagicMock()
        return cfg

    def test_skipped_when_no_files(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)  # empty dir — no data/cams/
        result = run(self._make_config(), logger, context={})
        assert result["status"] == "skipped"
        assert result["rows_written"] == 0
        assert result["errors"] == []

    def test_skipped_when_dir_empty(self, tmp_path: Path, monkeypatch):
        (tmp_path / "data" / "cams").mkdir(parents=True)
        monkeypatch.chdir(tmp_path)
        result = run(self._make_config(), logger, context={})
        assert result["status"] == "skipped"

    def test_success_with_json(self, tmp_path: Path, monkeypatch):
        cams_dir = tmp_path / "data" / "cams"
        cams_dir.mkdir(parents=True)
        (cams_dir / "export.json").write_text(
            json.dumps({"dtTrxnResult": SAMPLE_RECORDS}), encoding="utf-8"
        )
        monkeypatch.chdir(tmp_path)

        mock_writer = MagicMock(return_value=4)
        with patch("tools.sheets_writer.append_timeseries", mock_writer):
            ctx: dict = {}
            result = run(self._make_config(), logger, context=ctx)

        assert result["status"] == "success"
        assert result["rows_written"] == 4
        assert result["errors"] == []
        assert "transactions" in ctx
        assert len(ctx["transactions"]) == 4

    def test_deduplication_applied(self, tmp_path: Path, monkeypatch):
        records_with_dup = SAMPLE_RECORDS + [DUPLICATE_RECORD]
        cams_dir = tmp_path / "data" / "cams"
        cams_dir.mkdir(parents=True)
        (cams_dir / "export.json").write_text(
            json.dumps({"dtTrxnResult": records_with_dup}), encoding="utf-8"
        )
        monkeypatch.chdir(tmp_path)

        mock_writer = MagicMock(return_value=4)
        with patch("tools.sheets_writer.append_timeseries", mock_writer):
            ctx: dict = {}
            run(self._make_config(), logger, context=ctx)

        # 5 raw financial records (4 + 1 dup), deduped to 4
        assert len(ctx["transactions"]) == 4

    def test_sheets_writer_called_with_correct_tab(self, tmp_path: Path, monkeypatch):
        cams_dir = tmp_path / "data" / "cams"
        cams_dir.mkdir(parents=True)
        (cams_dir / "export.json").write_text(
            json.dumps({"dtTrxnResult": SAMPLE_RECORDS}), encoding="utf-8"
        )
        monkeypatch.chdir(tmp_path)

        mock_writer = MagicMock(return_value=4)
        with patch("tools.sheets_writer.append_timeseries", mock_writer):
            run(self._make_config(), logger, context={})

        call_kwargs = mock_writer.call_args.kwargs
        assert call_kwargs["tab"] == "Transactions"

    def test_result_has_required_keys(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = run(self._make_config(), logger, context={})
        assert set(result.keys()) == {"status", "rows_written", "errors", "duration_s"}

    def test_duration_is_non_negative_float(self, tmp_path: Path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = run(self._make_config(), logger, context={})
        assert isinstance(result["duration_s"], float)
        assert result["duration_s"] >= 0
