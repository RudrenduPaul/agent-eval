"""Report dataclass: p-value, effect size, CI, verdict."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Verdict(str, Enum):
    REGRESSED = "REGRESSED"
    STABLE = "STABLE"
    IMPROVED = "IMPROVED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


@dataclass(frozen=True)
class Report:
    metric: str
    verdict: Verdict
    p_value: float
    effect_size: float
    ci_lower: float
    ci_upper: float
    n_a: int
    n_b: int
    mean_a: float
    mean_b: float
    std_a: float
    std_b: float
    mean_delta: float
    warnings: list[str] = field(default_factory=list)

    def assert_stable(
        self,
        p_threshold: float = 0.05,
        min_effect: float = 0.2,
    ) -> None:
        if self.verdict == Verdict.INSUFFICIENT_DATA:
            return
        is_regression = self.p_value < p_threshold and self.effect_size < -min_effect
        if is_regression:
            pct = f"{abs(self.mean_delta) / max(self.mean_a, 1e-9):.1%}"
            raise AssertionError(
                f"REGRESSED: {self.metric} dropped {pct} "
                f"(p={self.p_value:.3f}, Cohen's d={self.effect_size:.2f}, "
                f"95% CI [{self.ci_lower:.3f}, {self.ci_upper:.3f}])\n"
                f"Version A: {self.mean_a:.3f} +/- {self.std_a:.3f} (n={self.n_a})\n"
                f"Version B: {self.mean_b:.3f} +/- {self.std_b:.3f} (n={self.n_b})"
            )

    def __str__(self) -> str:
        sep = "=" * 60
        lines = [
            "",
            sep,
            f"agentregress Report -- {self.metric}",
            sep,
            f"Verdict:    {self.verdict.value}",
            f"p-value:    {self.p_value:.4f}",
            f"Cohen's d:  {self.effect_size:.3f}",
            f"95% CI:     [{self.ci_lower:.3f}, {self.ci_upper:.3f}]",
            "",
            f"Version A:  {self.mean_a:.4f} +/- {self.std_a:.4f}  (n={self.n_a})",
            f"Version B:  {self.mean_b:.4f} +/- {self.std_b:.4f}  (n={self.n_b})",
            f"Delta:      {self.mean_delta:+.4f}",
        ]
        if self.warnings:
            lines += ["", "Warnings:"] + [f"  ! {w}" for w in self.warnings]
        lines.append(sep)
        return "\n".join(lines)
