"""Tests for tools/overlap_engine.py"""
from __future__ import annotations

import logging

import pytest

from tools.overlap_engine import compute_pairwise_overlap

logger = logging.getLogger(__name__)

HOLDINGS = [
    # Fund A: stocks 1,2,3
    {"scheme_code": "A", "isin": "ISIN001", "weight_pct": 30.0},
    {"scheme_code": "A", "isin": "ISIN002", "weight_pct": 40.0},
    {"scheme_code": "A", "isin": "ISIN003", "weight_pct": 30.0},
    # Fund B: stocks 2,3,4 — overlap on 2,3
    {"scheme_code": "B", "isin": "ISIN002", "weight_pct": 20.0},
    {"scheme_code": "B", "isin": "ISIN003", "weight_pct": 50.0},
    {"scheme_code": "B", "isin": "ISIN004", "weight_pct": 30.0},
]


def test_jaccard_overlap_computed():
    results = compute_pairwise_overlap(HOLDINGS, logger)
    assert len(results) == 1
    pair = results[0]
    # intersection = {ISIN002, ISIN003} = 2, union = {ISIN001..004} = 4
    assert pair["jaccard_overlap"] == pytest.approx(2 / 4)
    assert pair["common_stocks"] == 2


def test_weighted_overlap_computed():
    results = compute_pairwise_overlap(HOLDINGS, logger)
    pair = results[0]
    # min(40,20) + min(30,50) = 20 + 30 = 50
    assert pair["weighted_overlap_pct"] == pytest.approx(50.0)


def test_empty_composition_returns_empty():
    results = compute_pairwise_overlap([], logger)
    assert results == []
