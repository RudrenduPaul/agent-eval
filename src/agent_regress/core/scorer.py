"""Built-in scorer functions for common evaluation patterns."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Callable
from typing import Any


def _get_expected(test_case: dict[str, Any]) -> Any:
    if "expected" not in test_case:
        raise KeyError(
            "test_case missing 'expected' key. "
            "Add expected values or pass a custom scorer= function."
        )
    return test_case["expected"]


def exact_match_scorer(output: Any, test_case: dict[str, Any]) -> float:
    expected = _get_expected(test_case)
    return 1.0 if str(output).strip() == str(expected).strip() else 0.0


def f1_scorer(output: Any, test_case: dict[str, Any]) -> float:
    expected = _get_expected(test_case)

    pred_tokens = str(output).lower().split()
    gold_tokens = str(expected).lower().split()

    if not pred_tokens and not gold_tokens:
        return 1.0
    if not pred_tokens or not gold_tokens:
        return 0.0

    pred_counter = Counter(pred_tokens)
    gold_counter = Counter(gold_tokens)
    tp = sum((pred_counter & gold_counter).values())
    precision = tp / sum(pred_counter.values())
    recall = tp / sum(gold_counter.values())
    denom = precision + recall
    return 0.0 if denom == 0.0 else 2.0 * precision * recall / denom


def schema_conformance_scorer(output: Any, test_case: dict[str, Any]) -> float:
    """Validate `output` against `test_case["expected_schema"]`.

    `expected_schema` may be either a JSON Schema dict (validated via the
    `jsonschema` package) or a callable validator `Callable[[Any], bool]`.
    Returns 1.0 if `output` conforms, 0.0 otherwise.
    """
    if "expected_schema" not in test_case:
        raise KeyError(
            "test_case missing 'expected_schema' key. "
            "Add an expected_schema (JSON Schema dict or callable validator) "
            "or pass a custom scorer= function."
        )
    expected_schema = test_case["expected_schema"]

    if callable(expected_schema):
        return 1.0 if expected_schema(output) else 0.0

    try:
        # jsonschema ships as a hard dependency (see pyproject.toml), so this
        # except branch is a defensive fallback for a broken/incomplete
        # install rather than an expected code path.
        import jsonschema  # type: ignore[import-untyped]  # noqa: PLC0415
    except ImportError as exc:
        raise ImportError(
            "schema_conformance_scorer requires jsonschema for dict-based "
            "JSON Schema validation. Install with: pip install jsonschema"
        ) from exc

    try:
        jsonschema.validate(instance=output, schema=expected_schema)
    except jsonschema.exceptions.ValidationError:
        return 0.0
    return 1.0


def structured_content_scorer(
    result: Any,
    test_case: dict[str, Any],
    base_scorer: Callable[[Any, dict[str, Any]], float] | None = None,
) -> float:
    """Score structured (output + trace) results, not just a text output.

    `result` may be a plain output value, a `TracedResult`-shaped object
    exposing `.output`/`.trace` attributes, or a dict with "output"/"trace"
    keys (the shared contract used by e.g. openai_agents_runner's
    capture_trace=). All three shapes are accepted via duck typing.

    The output half is scored with `base_scorer(output, test_case)` (default
    `exact_match_scorer`). If `test_case["expected_trace"]` is present, every
    key/value pair in it must also be present and equal in the captured
    trace; the output score and trace-match fraction are then averaged
    (each weighted 0.5). Otherwise only the output score is returned.
    """
    if hasattr(result, "output"):
        output = result.output
        trace = getattr(result, "trace", None)
    elif isinstance(result, dict) and "output" in result:
        output = result["output"]
        trace = result.get("trace")
    else:
        output = result
        trace = None

    scorer = base_scorer if base_scorer is not None else exact_match_scorer
    output_score = scorer(output, test_case)

    expected_trace = test_case.get("expected_trace")
    if expected_trace is None:
        return output_score

    trace_dict = trace if isinstance(trace, dict) else {}
    if not expected_trace:
        trace_score = 1.0
    else:
        matches = sum(
            1
            for key, value in expected_trace.items()
            if key in trace_dict and trace_dict[key] == value
        )
        trace_score = matches / len(expected_trace)

    return 0.5 * output_score + 0.5 * trace_score


_POSIX_PATH_RE = re.compile(r"/(?:[\w.\-]+/)+[\w.\-]+")
_WINDOWS_PATH_RE = re.compile(r"[A-Za-z]:\\(?:[\w.\-]+\\)*[\w.\-]+")


def no_path_leak_scorer(output: Any, _test_case: dict[str, Any]) -> float:
    """Return 1.0 if `str(output)` contains no absolute filesystem paths.

    Detects both POSIX (`/foo/bar/baz`) and Windows (`C:\\foo\\bar`) absolute
    paths via regex. `_test_case` is accepted (unused) for interface
    consistency with other scorers.
    """
    text = str(output)
    if _POSIX_PATH_RE.search(text) or _WINDOWS_PATH_RE.search(text):
        return 0.0
    return 1.0


def _tool_call_id(message: Any) -> Any:
    if isinstance(message, dict):
        return message.get("tool_call_id")
    return getattr(message, "tool_call_id", None)


def tool_call_trace_scorer(output: Any, test_case: dict[str, Any]) -> float:
    """Score ToolNode-level invocation correctness from a messages trace.

    `output` is expected to be a dict with a "messages" list (LangGraph's
    typical `invoke()` return shape) containing message-like dicts/objects
    identified by a `tool_call_id` key/attribute. `test_case["expected_tool_call_ids"]`
    is the list of tool_call_ids that should each appear exactly once.
    Duplicates and missing ids are penalized equally.
    """
    if "expected_tool_call_ids" not in test_case:
        raise KeyError(
            "test_case missing 'expected_tool_call_ids' key. "
            "Add expected_tool_call_ids or pass a custom scorer= function."
        )
    expected_ids = test_case["expected_tool_call_ids"]
    if not expected_ids:
        return 1.0

    messages = output.get("messages", []) if isinstance(output, dict) else []

    counts: Counter[Any] = Counter()
    for message in messages:
        call_id = _tool_call_id(message)
        if call_id is not None:
            counts[call_id] += 1

    matched = sum(1 for call_id in expected_ids if counts.get(call_id, 0) == 1)
    return matched / len(expected_ids)


from agent_regress.core.state_diff import (  # noqa: E402
    state_diff_scorer as state_diff_scorer,  # noqa: PLC0414
)
