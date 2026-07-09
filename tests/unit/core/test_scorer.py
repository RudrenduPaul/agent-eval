"""Tests for built-in scorer functions."""

from __future__ import annotations

from typing import Any

import pytest

from agent_regress.core.scorer import (
    exact_match_scorer,
    f1_scorer,
    no_path_leak_scorer,
    schema_conformance_scorer,
    state_diff_scorer,
    structured_content_scorer,
    tool_call_trace_scorer,
)


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


class TestSchemaConformanceScorer:
    def test_valid_dict_schema_returns_one(self) -> None:
        tc: dict[str, Any] = {
            "expected_schema": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            }
        }
        assert schema_conformance_scorer({"name": "alice"}, tc) == 1.0

    def test_invalid_dict_schema_returns_zero(self) -> None:
        tc: dict[str, Any] = {
            "expected_schema": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            }
        }
        assert schema_conformance_scorer({"age": 5}, tc) == 0.0

    def test_callable_validator_true(self) -> None:
        tc: dict[str, Any] = {"expected_schema": lambda output: isinstance(output, int)}
        assert schema_conformance_scorer(42, tc) == 1.0

    def test_callable_validator_false(self) -> None:
        tc: dict[str, Any] = {"expected_schema": lambda output: isinstance(output, int)}
        assert schema_conformance_scorer("nope", tc) == 0.0

    def test_missing_expected_schema_raises(self) -> None:
        with pytest.raises(KeyError, match="expected_schema"):
            schema_conformance_scorer({"name": "alice"}, {})


class TestStateDiffScorer:
    def test_all_fields_match(self) -> None:
        tc: dict[str, Any] = {"expected_state": {"a": 1, "b": 2}}
        assert state_diff_scorer({"a": 1, "b": 2}, tc) == 1.0

    def test_partial_match(self) -> None:
        tc: dict[str, Any] = {"expected_state": {"a": 1, "b": 2}}
        assert state_diff_scorer({"a": 1, "b": 99}, tc) == 0.5

    def test_missing_key_counts_as_non_match(self) -> None:
        tc: dict[str, Any] = {"expected_state": {"a": 1, "b": 2}}
        assert state_diff_scorer({"a": 1}, tc) == 0.5

    def test_no_match(self) -> None:
        tc: dict[str, Any] = {"expected_state": {"a": 1}}
        assert state_diff_scorer({"a": 2}, tc) == 0.0

    def test_nested_dict_recursion(self) -> None:
        tc: dict[str, Any] = {
            "expected_state": {"a": 1, "nested": {"x": 1, "y": 2}}
        }
        output = {"a": 1, "nested": {"x": 1, "y": 2}}
        assert state_diff_scorer(output, tc) == 1.0

    def test_nested_dict_partial_mismatch_fails_that_key(self) -> None:
        tc: dict[str, Any] = {
            "expected_state": {"a": 1, "nested": {"x": 1, "y": 2}}
        }
        output = {"a": 1, "nested": {"x": 1, "y": 999}}
        assert state_diff_scorer(output, tc) == 0.5

    def test_missing_expected_state_raises(self) -> None:
        with pytest.raises(KeyError, match="expected_state"):
            state_diff_scorer({"a": 1}, {})

    def test_reexported_from_scorer_module(self) -> None:
        from agent_regress.core.state_diff import (
            state_diff_scorer as direct_import,
        )

        assert state_diff_scorer is direct_import


class TestStructuredContentScorer:
    def test_plain_output_uses_exact_match(self) -> None:
        tc: dict[str, Any] = {"expected": "hello"}
        assert structured_content_scorer("hello", tc) == 1.0
        assert structured_content_scorer("goodbye", tc) == 0.0

    def test_dict_shaped_result_extracts_output(self) -> None:
        tc: dict[str, Any] = {"expected": "hello"}
        result = {"output": "hello", "trace": {"model": "gpt-5"}}
        assert structured_content_scorer(result, tc) == 1.0

    def test_traced_result_shaped_object_extracts_output(self) -> None:
        class TracedResult:
            def __init__(self, output: Any, trace: Any) -> None:
                self.output = output
                self.trace = trace

        tc: dict[str, Any] = {"expected": "hello"}
        result = TracedResult(output="hello", trace={"model": "gpt-5"})
        assert structured_content_scorer(result, tc) == 1.0

    def test_custom_base_scorer_used(self) -> None:
        tc: dict[str, Any] = {"expected": "the quick fox"}
        result = {"output": "the slow fox"}
        score = structured_content_scorer(result, tc, base_scorer=f1_scorer)
        assert 0.0 < score < 1.0

    def test_expected_trace_matches_averages_with_output_score(self) -> None:
        tc: dict[str, Any] = {
            "expected": "hello",
            "expected_trace": {"model": "gpt-5"},
        }
        result = {"output": "hello", "trace": {"model": "gpt-5", "extra": True}}
        assert structured_content_scorer(result, tc) == 1.0

    def test_expected_trace_mismatch_lowers_score(self) -> None:
        tc: dict[str, Any] = {
            "expected": "hello",
            "expected_trace": {"model": "gpt-5"},
        }
        result = {"output": "hello", "trace": {"model": "gpt-4"}}
        score = structured_content_scorer(result, tc)
        assert score == 0.5

    def test_expected_trace_missing_from_captured_trace(self) -> None:
        tc: dict[str, Any] = {
            "expected": "hello",
            "expected_trace": {"model": "gpt-5"},
        }
        result = {"output": "hello", "trace": None}
        score = structured_content_scorer(result, tc)
        assert score == 0.5

    def test_no_expected_trace_returns_output_score_only(self) -> None:
        tc: dict[str, Any] = {"expected": "hello"}
        result = {"output": "wrong"}
        assert structured_content_scorer(result, tc) == 0.0

    def test_expected_converted_tool_output_types_all_present(self) -> None:
        tc: dict[str, Any] = {
            "expected": "hello",
            "expected_converted_tool_output_types": {"call_1": ["text", "image_url"]},
        }
        result = {
            "output": "hello",
            "trace": {
                "converted_tool_outputs": [
                    {
                        "pre_conversion_outputs": [{"call_id": "call_1", "output": "..."}],
                        "post_conversion_tool_messages": [
                            {
                                "role": "tool",
                                "tool_call_id": "call_1",
                                "content": [
                                    {"type": "text", "text": "here"},
                                    {"type": "image_url", "image_url": {"url": "x"}},
                                ],
                            }
                        ],
                    }
                ]
            },
        }
        assert structured_content_scorer(result, tc) == 1.0

    def test_expected_converted_tool_output_types_missing_lowers_score(self) -> None:
        """The converter stripped the image (e.g. no preserve_tool_output_all_content),
        so only "text" survived -> the expected "image_url" type is missing.
        """
        tc: dict[str, Any] = {
            "expected": "hello",
            "expected_converted_tool_output_types": {"call_1": ["text", "image_url"]},
        }
        result = {
            "output": "hello",
            "trace": {
                "converted_tool_outputs": [
                    {
                        "pre_conversion_outputs": [{"call_id": "call_1", "output": "..."}],
                        "post_conversion_tool_messages": [
                            {
                                "role": "tool",
                                "tool_call_id": "call_1",
                                "content": [{"type": "text", "text": "here"}],
                            }
                        ],
                    }
                ]
            },
        }
        score = structured_content_scorer(result, tc)
        assert score == 0.5  # output_score=1.0 averaged with conv_score=0.0

    def test_expected_converted_tool_output_types_missing_trace_scores_zero_component(
        self,
    ) -> None:
        tc: dict[str, Any] = {
            "expected": "hello",
            "expected_converted_tool_output_types": {"call_1": ["image_url"]},
        }
        result = {"output": "hello", "trace": None}
        score = structured_content_scorer(result, tc)
        assert score == 0.5

    def test_expected_converted_tool_output_types_and_expected_trace_average_three_ways(
        self,
    ) -> None:
        tc: dict[str, Any] = {
            "expected": "hello",
            "expected_trace": {"model": "gpt-5"},
            "expected_converted_tool_output_types": {"call_1": ["text"]},
        }
        result = {
            "output": "hello",
            "trace": {
                "model": "gpt-5",
                "converted_tool_outputs": [
                    {
                        "pre_conversion_outputs": [{"call_id": "call_1", "output": "..."}],
                        "post_conversion_tool_messages": [
                            {
                                "role": "tool",
                                "tool_call_id": "call_1",
                                "content": [{"type": "text", "text": "here"}],
                            }
                        ],
                    }
                ],
            },
        }
        # output_score=1.0, trace_score=1.0, conv_score=1.0 -> average is still 1.0
        assert structured_content_scorer(result, tc) == 1.0

    def test_no_expected_converted_tool_output_types_unaffected(self) -> None:
        """Backward compatibility: omitting the new key changes nothing."""
        tc: dict[str, Any] = {"expected": "hello", "expected_trace": {"model": "gpt-5"}}
        result = {"output": "hello", "trace": {"model": "gpt-5"}}
        assert structured_content_scorer(result, tc) == 1.0


class TestNoPathLeakScorer:
    def test_no_path_returns_one(self) -> None:
        assert no_path_leak_scorer("The answer is 42.", {}) == 1.0

    def test_posix_path_detected(self) -> None:
        assert no_path_leak_scorer("Wrote to /Users/alice/secrets/keys.txt", {}) == 0.0

    def test_windows_path_detected(self) -> None:
        text = r"Saved at C:\Users\alice\secrets\keys.txt"
        assert no_path_leak_scorer(text, {}) == 0.0

    def test_relative_path_not_flagged(self) -> None:
        assert no_path_leak_scorer("see docs/readme.md for details", {}) == 1.0

    def test_test_case_argument_unused(self) -> None:
        # Interface consistency: test_case is accepted but ignored.
        assert no_path_leak_scorer("ok", {"anything": "goes"}) == 1.0


class TestToolCallTraceScorer:
    def test_all_expected_ids_present_exactly_once(self) -> None:
        output = {
            "messages": [
                {"tool_call_id": "call_1", "role": "tool"},
                {"tool_call_id": "call_2", "role": "tool"},
            ]
        }
        tc: dict[str, Any] = {"expected_tool_call_ids": ["call_1", "call_2"]}
        assert tool_call_trace_scorer(output, tc) == 1.0

    def test_missing_id_penalized(self) -> None:
        output = {"messages": [{"tool_call_id": "call_1"}]}
        tc: dict[str, Any] = {"expected_tool_call_ids": ["call_1", "call_2"]}
        assert tool_call_trace_scorer(output, tc) == 0.5

    def test_duplicate_id_penalized(self) -> None:
        output = {
            "messages": [
                {"tool_call_id": "call_1"},
                {"tool_call_id": "call_1"},
                {"tool_call_id": "call_2"},
            ]
        }
        tc: dict[str, Any] = {"expected_tool_call_ids": ["call_1", "call_2"]}
        assert tool_call_trace_scorer(output, tc) == 0.5

    def test_duck_typed_object_messages(self) -> None:
        class ToolMessage:
            def __init__(self, tool_call_id: str) -> None:
                self.tool_call_id = tool_call_id

        output = {"messages": [ToolMessage("call_1")]}
        tc: dict[str, Any] = {"expected_tool_call_ids": ["call_1"]}
        assert tool_call_trace_scorer(output, tc) == 1.0

    def test_empty_expected_ids_returns_one(self) -> None:
        output = {"messages": []}
        tc: dict[str, Any] = {"expected_tool_call_ids": []}
        assert tool_call_trace_scorer(output, tc) == 1.0

    def test_missing_expected_tool_call_ids_raises(self) -> None:
        with pytest.raises(KeyError, match="expected_tool_call_ids"):
            tool_call_trace_scorer({"messages": []}, {})
