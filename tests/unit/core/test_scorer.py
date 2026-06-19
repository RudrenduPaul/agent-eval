"""Tests for built-in scorer functions."""
from __future__ import annotations

import pytest

from agent_regress.core.scorer import exact_match_scorer, f1_scorer


class TestExactMatchScorer:
    def test_exact_match_returns_one(self) -> None:
        tc: dict[str, object] = {"expected": "hello world"}
        assert exact_match_scorer("hello world", tc) == 1.0

    def test_no_match_returns_zero(self) -> None:
        tc: dict[str, object] = {"expected": "hello world"}
        assert exact_match_scorer("goodbye", tc) == 0.0

    def test_strips_whitespace(self) -> None:
        tc: dict[str, object] = {"expected": "  answer  "}
        assert exact_match_scorer("answer", tc) == 1.0

    def test_missing_expected_raises(self) -> None:
        with pytest.raises(KeyError, match="'expected' key"):
            exact_match_scorer("answer", {})

    def test_numeric_output(self) -> None:
        tc: dict[str, object] = {"expected": "42"}
        assert exact_match_scorer(42, tc) == 1.0


class TestF1Scorer:
    def test_perfect_match(self) -> None:
        tc: dict[str, object] = {"expected": "the quick brown fox"}
        score = f1_scorer("the quick brown fox", tc)
        assert score == 1.0

    def test_no_overlap(self) -> None:
        tc: dict[str, object] = {"expected": "hello world"}
        score = f1_scorer("goodbye moon", tc)
        assert score == 0.0

    def test_partial_overlap(self) -> None:
        tc: dict[str, object] = {"expected": "the quick fox"}
        score = f1_scorer("the slow fox", tc)
        assert 0.0 < score < 1.0

    def test_empty_both(self) -> None:
        tc: dict[str, object] = {"expected": ""}
        score = f1_scorer("", tc)
        assert score == 1.0

    def test_missing_expected_raises(self) -> None:
        with pytest.raises(KeyError):
            f1_scorer("answer", {})
