"""Shared pytest fixtures for agentregress tests."""
from __future__ import annotations

import math
import random
from typing import Any

import pytest


def _deterministic_agent(
    base_score: float = 0.8,
    noise: float = 0.05,
    seed_offset: int = 0,
) -> Any:
    call_count = 0

    def _agent(test_case: dict[str, Any]) -> float:
        nonlocal call_count
        rng = random.Random(call_count + seed_offset + hash(str(test_case)) % 1000)
        call_count += 1
        return max(0.0, min(1.0, base_score + rng.gauss(0, noise)))

    return _agent


@pytest.fixture
def good_agent() -> Any:
    return _deterministic_agent(base_score=0.82, noise=0.04)


@pytest.fixture
def bad_agent() -> Any:
    return _deterministic_agent(base_score=0.62, noise=0.06, seed_offset=999)


@pytest.fixture
def basic_test_suite() -> list[dict[str, Any]]:
    return [
        {"query": f"question_{i}", "expected": f"answer_{i}"}
        for i in range(5)
    ]


@pytest.fixture
def large_test_suite() -> list[dict[str, Any]]:
    return [
        {"query": f"question_{i}", "expected": f"answer_{i}"}
        for i in range(20)
    ]


@pytest.fixture
def sample_scores_a() -> list[float]:
    rng = random.Random(42)
    return [max(0.0, min(1.0, rng.gauss(0.80, 0.05))) for _ in range(50)]


@pytest.fixture
def sample_scores_b() -> list[float]:
    rng = random.Random(123)
    return [max(0.0, min(1.0, rng.gauss(0.65, 0.07))) for _ in range(50)]


@pytest.fixture
def stable_scores() -> list[float]:
    rng = random.Random(42)
    return [max(0.0, min(1.0, rng.gauss(0.80, 0.05))) for _ in range(50)]
