"""Tests for the state-diff / checkpoint round-trip scorer."""

from __future__ import annotations

from typing import Any

import pytest

from agent_regress.core.state_diff import state_diff_scorer


class TestStateDiffScorer:
    def test_all_top_level_keys_match(self) -> None:
        tc: dict[str, Any] = {"expected_state": {"a": 1, "b": "two"}}
        assert state_diff_scorer({"a": 1, "b": "two"}, tc) == 1.0

    def test_half_top_level_keys_match(self) -> None:
        tc: dict[str, Any] = {"expected_state": {"a": 1, "b": 2, "c": 3, "d": 4}}
        output = {"a": 1, "b": 2, "c": 999, "d": 999}
        assert state_diff_scorer(output, tc) == 0.5

    def test_missing_key_is_non_match_not_error(self) -> None:
        tc: dict[str, Any] = {"expected_state": {"a": 1, "b": 2}}
        output: dict[str, Any] = {"a": 1}
        assert state_diff_scorer(output, tc) == 0.5

    def test_extra_keys_in_output_ignored(self) -> None:
        tc: dict[str, Any] = {"expected_state": {"a": 1}}
        output = {"a": 1, "unexpected": "value"}
        assert state_diff_scorer(output, tc) == 1.0

    def test_empty_expected_state_returns_one(self) -> None:
        tc: dict[str, Any] = {"expected_state": {}}
        assert state_diff_scorer({"anything": "here"}, tc) == 1.0

    def test_nested_dict_compared_recursively(self) -> None:
        tc: dict[str, Any] = {
            "expected_state": {
                "checkpoint": {"thread_id": "t1", "step": 3},
                "status": "done",
            }
        }
        output = {
            "checkpoint": {"thread_id": "t1", "step": 3},
            "status": "done",
        }
        assert state_diff_scorer(output, tc) == 1.0

    def test_nested_dict_mismatch_counts_whole_key_as_non_match(self) -> None:
        tc: dict[str, Any] = {
            "expected_state": {
                "checkpoint": {"thread_id": "t1", "step": 3},
                "status": "done",
            }
        }
        output = {
            "checkpoint": {"thread_id": "t1", "step": 4},
            "status": "done",
        }
        assert state_diff_scorer(output, tc) == 0.5

    def test_non_dict_output_falls_back_to_equality(self) -> None:
        tc: dict[str, Any] = {"expected_state": {"a": 1}}
        assert state_diff_scorer("not-a-dict", tc) == 0.0

    def test_missing_expected_state_raises_key_error(self) -> None:
        with pytest.raises(KeyError, match="expected_state"):
            state_diff_scorer({"a": 1}, {})
