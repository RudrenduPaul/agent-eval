"""Command-line entry point for agent-regress.

The public Python API (`agent_regress.compare()`) takes two *callables* --
`version_a` and `version_b` -- and runs them itself via `run_suite()`. That
shape has no clean shell equivalent: a CLI can't accept "a callable" as a
flag value. So this CLI exposes a different, file-based contract that fits
what a shell/agent workflow can realistically produce: two JSON files, each
holding a flat array of per-run scores already computed by whatever harness
ran that agent version (`[0.82, 0.79, 0.91, ...]`). Those two score arrays
are fed through the exact same Mann-Whitney U / bootstrap CI / Cohen's d /
Verdict pipeline `compare()` uses internally, so the statistical output is
identical for the same underlying scores -- only how the scores get here
differs.
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path
from typing import Any, NoReturn

import numpy as np

from agent_regress import __version__
from agent_regress.core.report import Report, Verdict
from agent_regress.stats.bootstrap import bootstrap_mean_ci
from agent_regress.stats.effect_size import cohens_d
from agent_regress.stats.mann_whitney import mann_whitney_u

_MIN_N_WARN = 50
_PROG = "agent-regress"


def _fail(message: str) -> NoReturn:
    """Print a usage/data error to stderr and exit non-zero.

    Never writes to stdout, so `--json` invocations keep stdout clean even
    on failure -- callers only need to check the exit code and stderr.
    """
    print(f"{_PROG}: error: {message}", file=sys.stderr)
    raise SystemExit(2)


def _load_scores(path: str, flag: str) -> list[float]:
    """Load a JSON array of per-run scores from `path`.

    Args:
        path: Filesystem path to a JSON file containing a flat, non-empty
            array of numbers, e.g. `[0.8, 0.9, 0.75]`.
        flag: The CLI flag this path came from (e.g. "--version-a-results"),
            used to make error messages actionable.

    Returns:
        The parsed scores as a list of floats.
    """
    file_path = Path(path)
    if not file_path.is_file():
        _fail(f"{flag}: no such file: {path}")
    try:
        raw = json.loads(file_path.read_text())
    except json.JSONDecodeError as exc:
        _fail(f"{flag}: {path} is not valid JSON ({exc})")
    if not isinstance(raw, list) or not raw:
        _fail(f"{flag}: {path} must contain a non-empty JSON array of scores")
    try:
        return [float(x) for x in raw]
    except (TypeError, ValueError):
        _fail(f"{flag}: {path} must contain only numbers, got: {raw!r}")


def _report_from_scores(  # noqa: PLR0913
    metric: str,
    scores_a: list[float],
    scores_b: list[float],
    p_threshold: float,
    min_effect: float,
    n_resamples: int,
) -> Report:
    """Build a `Report` from two pre-computed score lists.

    Mirrors the pipeline in `agent_regress.core.compare.compare()`
    (Mann-Whitney U -> bootstrap CI -> Cohen's d -> Verdict thresholding),
    minus the `run_suite()` step, since the CLI receives scores an external
    harness already computed rather than callables it needs to invoke.
    """
    n_a, n_b = len(scores_a), len(scores_b)
    warn_msgs: list[str] = []
    if n_a < _MIN_N_WARN or n_b < _MIN_N_WARN:
        msg = (
            f"n_a={n_a}, n_b={n_b}: insufficient for 80% power at small effect "
            f"(d=0.2). Run at least {_MIN_N_WARN} per version for reliable results."
        )
        warn_msgs.append(msg)
        warnings.warn(msg, UserWarning, stacklevel=2)

    mw = mann_whitney_u(scores_a, scores_b, _warn=False)
    ci = bootstrap_mean_ci(scores_a, scores_b, n_resamples=n_resamples)
    d = cohens_d(scores_a, scores_b)

    arr_a = np.asarray(scores_a, dtype=np.float64)
    arr_b = np.asarray(scores_b, dtype=np.float64)
    std_a = float(arr_a.std(ddof=1)) if n_a > 1 else 0.0
    std_b = float(arr_b.std(ddof=1)) if n_b > 1 else 0.0

    if n_a < 10 or n_b < 10:
        verdict = Verdict.INSUFFICIENT_DATA
    elif mw.p_value < p_threshold and abs(d) >= min_effect:
        verdict = Verdict.REGRESSED if d < 0.0 else Verdict.IMPROVED
    else:
        verdict = Verdict.STABLE

    return Report(
        metric=metric,
        verdict=verdict,
        p_value=mw.p_value,
        effect_size=d,
        ci_lower=ci.lower,
        ci_upper=ci.upper,
        n_a=n_a,
        n_b=n_b,
        mean_a=float(arr_a.mean()),
        mean_b=float(arr_b.mean()),
        std_a=std_a,
        std_b=std_b,
        mean_delta=ci.mean_delta,
        p_threshold=p_threshold,
        min_effect=min_effect,
        warnings=warn_msgs,
    )


def _report_to_json(report: Report) -> dict[str, Any]:
    """Flatten a `Report` into the same fields `str(report)` shows, as a
    JSON-serializable dict -- the "agent-native" machine-readable surface.
    """
    return {
        "metric": report.metric,
        "verdict": report.verdict.value,
        "p_value": report.p_value,
        "effect_size": report.effect_size,
        "ci_lower": report.ci_lower,
        "ci_upper": report.ci_upper,
        "n_a": report.n_a,
        "n_b": report.n_b,
        "mean_a": report.mean_a,
        "mean_b": report.mean_b,
        "std_a": report.std_a,
        "std_b": report.std_b,
        "mean_delta": report.mean_delta,
        "p_threshold": report.p_threshold,
        "min_effect": report.min_effect,
        "warnings": report.warnings,
    }


def _cmd_compare(args: argparse.Namespace) -> int:
    scores_a = _load_scores(args.version_a_results, "--version-a-results")
    scores_b = _load_scores(args.version_b_results, "--version-b-results")

    if args.n_resamples < 100:
        _fail(f"--n-resamples must be >= 100, got {args.n_resamples}")
    if not (0.0 < args.p_threshold < 1.0):
        _fail(f"--p-threshold must be in (0, 1), got {args.p_threshold}")
    if args.min_effect < 0.0:
        _fail(f"--min-effect must be >= 0, got {args.min_effect}")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        report = _report_from_scores(
            metric=args.metric,
            scores_a=scores_a,
            scores_b=scores_b,
            p_threshold=args.p_threshold,
            min_effect=args.min_effect,
            n_resamples=args.n_resamples,
        )
    # Warnings go to stderr only -- stdout stays clean JSON in --json mode.
    for w in caught:
        print(f"{_PROG}: warning: {w.message}", file=sys.stderr)

    if args.json:
        sys.stdout.write(json.dumps(_report_to_json(report)) + "\n")
    else:
        print(str(report))

    if args.fail_on_regression and report.verdict == Verdict.REGRESSED:
        return 1
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=_PROG,
        description=(
            "Statistical regression testing for LLM agents: compare two "
            "sets of per-run scores and get a verdict (REGRESSED / STABLE / "
            "IMPROVED / INSUFFICIENT_DATA) backed by a Mann-Whitney U test, "
            "a bootstrap confidence interval, and Cohen's d effect size."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"{_PROG} {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command")

    compare_parser = subparsers.add_parser(
        "compare",
        help="Compare two versions' pre-computed per-run scores.",
        description=(
            "Compare two agent versions from pre-computed per-run scores. "
            "Each --version-*-results file must be a JSON array of numbers, "
            "one score per run, e.g. [0.82, 0.79, 0.91]. Produce these with "
            "whatever harness ran each agent version -- the Python API's "
            "compare() runs the harness for you via callables, but a CLI "
            "invocation can't accept a callable, so this command starts "
            "one step later, from the resulting scores."
        ),
    )
    compare_parser.add_argument(
        "--version-a-results",
        required=True,
        metavar="PATH",
        help="Path to a JSON array of per-run scores for version A (baseline).",
    )
    compare_parser.add_argument(
        "--version-b-results",
        required=True,
        metavar="PATH",
        help="Path to a JSON array of per-run scores for version B (candidate).",
    )
    compare_parser.add_argument(
        "--metric",
        default="accuracy",
        metavar="NAME",
        help="Name of the metric being compared, shown in the report "
        "(default: accuracy).",
    )
    compare_parser.add_argument(
        "--p-threshold",
        type=float,
        default=0.05,
        metavar="P",
        help="Significance threshold for the Mann-Whitney U p-value (default: 0.05).",
    )
    compare_parser.add_argument(
        "--min-effect",
        type=float,
        default=0.2,
        metavar="D",
        help="Minimum |Cohen's d| to call a statistically significant "
        "difference a REGRESSED/IMPROVED verdict rather than STABLE "
        "(default: 0.2).",
    )
    compare_parser.add_argument(
        "--n-resamples",
        type=int,
        default=1000,
        metavar="N",
        help="Number of bootstrap resamples used for the confidence "
        "interval (default: 1000, minimum: 100).",
    )
    compare_parser.add_argument(
        "--json",
        action="store_true",
        help="Print the report as a single JSON object to stdout instead "
        "of the human-readable format. Warnings go to stderr, so stdout "
        "is clean, parseable JSON.",
    )
    compare_parser.add_argument(
        "--fail-on-regression",
        action="store_true",
        help="Exit with status 1 if the verdict is REGRESSED (useful for "
        "CI). Without this flag, the command exits 0 regardless of verdict, "
        "matching how the Python compare() function never raises on its "
        "own -- only Report.assert_stable() / the ci.gate module do.",
    )
    compare_parser.set_defaults(func=_cmd_compare)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help(sys.stderr)
        return 2
    result: int = args.func(args)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
