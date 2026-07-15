"""Tests for the agent-regress CLI entry point."""

from __future__ import annotations

import json
import subprocess
import sys
import warnings
from pathlib import Path

import pytest

from agent_regress import __version__
from agent_regress.cli import main


def _write_scores(tmp_path: Path, name: str, scores: list[float]) -> str:
    path = tmp_path / name
    path.write_text(json.dumps(scores))
    return str(path)


class TestVersion:
    def test_version_flag_prints_version_and_exits_zero(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with pytest.raises(SystemExit) as exc:
            main(["--version"])
        assert exc.value.code == 0
        out = capsys.readouterr().out
        assert __version__ in out

    def test_no_command_prints_help_to_stderr_and_exits_two(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        exit_code = main([])
        assert exit_code == 2
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "usage" in captured.err.lower()


class TestCompareHumanReadable:
    def test_stable_verdict(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        a = _write_scores(tmp_path, "a.json", [0.8] * 50)
        b = _write_scores(tmp_path, "b.json", [0.8] * 50)
        exit_code = main(
            [
                "compare",
                "--version-a-results",
                a,
                "--version-b-results",
                b,
                "--metric",
                "accuracy",
            ]
        )
        assert exit_code == 0
        out = capsys.readouterr().out
        assert "STABLE" in out
        assert "agent-regress Report -- accuracy" in out

    def test_regressed_verdict_exits_zero_without_fail_flag(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        a = _write_scores(tmp_path, "a.json", [0.9] * 30)
        b = _write_scores(tmp_path, "b.json", [0.1] * 30)
        exit_code = main(
            [
                "compare",
                "--version-a-results",
                a,
                "--version-b-results",
                b,
            ]
        )
        assert exit_code == 0
        assert "REGRESSED" in capsys.readouterr().out

    def test_regressed_verdict_exits_one_with_fail_flag(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        a = _write_scores(tmp_path, "a.json", [0.9] * 30)
        b = _write_scores(tmp_path, "b.json", [0.1] * 30)
        exit_code = main(
            [
                "compare",
                "--version-a-results",
                a,
                "--version-b-results",
                b,
                "--fail-on-regression",
            ]
        )
        assert exit_code == 1


class TestCompareJson:
    def test_json_output_is_single_clean_object(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        a = _write_scores(tmp_path, "a.json", [0.8] * 50)
        b = _write_scores(tmp_path, "b.json", [0.81] * 50)
        exit_code = main(
            [
                "compare",
                "--version-a-results",
                a,
                "--version-b-results",
                b,
                "--metric",
                "tool_accuracy",
                "--json",
            ]
        )
        assert exit_code == 0
        captured = capsys.readouterr()
        payload = json.loads(captured.out)
        assert payload["metric"] == "tool_accuracy"
        assert payload["verdict"] in {"STABLE", "REGRESSED", "IMPROVED"}
        assert "p_value" in payload
        assert "effect_size" in payload
        assert "ci_lower" in payload and "ci_upper" in payload
        assert payload["n_a"] == 50
        assert payload["n_b"] == 50

    def test_json_stdout_has_no_extra_prose(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        a = _write_scores(tmp_path, "a.json", [0.8] * 50)
        b = _write_scores(tmp_path, "b.json", [0.8] * 50)
        main(
            [
                "compare",
                "--version-a-results",
                a,
                "--version-b-results",
                b,
                "--json",
            ]
        )
        out = capsys.readouterr().out
        # Exactly one line of output: the JSON object plus trailing newline.
        assert out.count("\n") == 1
        json.loads(out)  # must parse as a single JSON value

    def test_low_n_warning_goes_to_stderr_not_stdout(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        a = _write_scores(tmp_path, "a.json", [0.8] * 5)
        b = _write_scores(tmp_path, "b.json", [0.8] * 5)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            main(
                [
                    "compare",
                    "--version-a-results",
                    a,
                    "--version-b-results",
                    b,
                    "--json",
                ]
            )
        captured = capsys.readouterr()
        json.loads(captured.out)  # stdout is still clean JSON
        assert "insufficient" in captured.err.lower()


class TestCompareErrors:
    def test_missing_file_fails_with_exit_two(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        b = _write_scores(tmp_path, "b.json", [0.8] * 10)
        with pytest.raises(SystemExit) as exc:
            main(
                [
                    "compare",
                    "--version-a-results",
                    str(tmp_path / "does-not-exist.json"),
                    "--version-b-results",
                    b,
                ]
            )
        assert exc.value.code == 2
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "no such file" in captured.err.lower()

    def test_invalid_json_fails(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        bad = tmp_path / "bad.json"
        bad.write_text("{not valid json")
        b = _write_scores(tmp_path, "b.json", [0.8] * 10)
        with pytest.raises(SystemExit) as exc:
            main(
                [
                    "compare",
                    "--version-a-results",
                    str(bad),
                    "--version-b-results",
                    b,
                ]
            )
        assert exc.value.code == 2
        assert "not valid json" in capsys.readouterr().err.lower()

    def test_empty_array_fails(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        a = _write_scores(tmp_path, "a.json", [])
        b = _write_scores(tmp_path, "b.json", [0.8] * 10)
        with pytest.raises(SystemExit) as exc:
            main(
                [
                    "compare",
                    "--version-a-results",
                    a,
                    "--version-b-results",
                    b,
                ]
            )
        assert exc.value.code == 2
        assert "non-empty" in capsys.readouterr().err.lower()

    def test_non_numeric_array_fails(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        a = _write_scores(tmp_path, "a.json", [0.8] * 10)
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps(["not", "a", "number"]))
        with pytest.raises(SystemExit) as exc:
            main(
                [
                    "compare",
                    "--version-a-results",
                    a,
                    "--version-b-results",
                    str(bad),
                ]
            )
        assert exc.value.code == 2
        assert "only numbers" in capsys.readouterr().err.lower()

    def test_invalid_p_threshold_fails(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        a = _write_scores(tmp_path, "a.json", [0.8] * 10)
        b = _write_scores(tmp_path, "b.json", [0.8] * 10)
        with pytest.raises(SystemExit) as exc:
            main(
                [
                    "compare",
                    "--version-a-results",
                    a,
                    "--version-b-results",
                    b,
                    "--p-threshold",
                    "1.5",
                ]
            )
        assert exc.value.code == 2
        assert "p-threshold" in capsys.readouterr().err.lower()

    def test_invalid_min_effect_fails(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        a = _write_scores(tmp_path, "a.json", [0.8] * 10)
        b = _write_scores(tmp_path, "b.json", [0.8] * 10)
        with pytest.raises(SystemExit) as exc:
            main(
                [
                    "compare",
                    "--version-a-results",
                    a,
                    "--version-b-results",
                    b,
                    "--min-effect",
                    "-0.1",
                ]
            )
        assert exc.value.code == 2
        assert "min-effect" in capsys.readouterr().err.lower()

    def test_invalid_n_resamples_fails(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        a = _write_scores(tmp_path, "a.json", [0.8] * 10)
        b = _write_scores(tmp_path, "b.json", [0.8] * 10)
        with pytest.raises(SystemExit) as exc:
            main(
                [
                    "compare",
                    "--version-a-results",
                    a,
                    "--version-b-results",
                    b,
                    "--n-resamples",
                    "10",
                ]
            )
        assert exc.value.code == 2
        assert "n-resamples" in capsys.readouterr().err.lower()


class TestCliSubprocess:
    """One real end-to-end invocation through `python -m agent_regress.cli`,
    to prove argv parsing and process exit codes work outside of directly
    calling main() in-process."""

    def test_help_exits_zero(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "agent_regress.cli", "compare", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "--version-a-results" in result.stdout

    def test_end_to_end_json_compare(self, tmp_path: Path) -> None:
        a = _write_scores(tmp_path, "a.json", [0.8] * 50)
        b = _write_scores(tmp_path, "b.json", [0.8] * 50)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_regress.cli",
                "compare",
                "--version-a-results",
                a,
                "--version-b-results",
                b,
                "--json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        payload = json.loads(result.stdout)
        assert payload["verdict"] == "STABLE"
