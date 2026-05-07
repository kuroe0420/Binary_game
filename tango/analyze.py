"""Generation quality analysis for Tango puzzles."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Callable

from tango.generator import generate_puzzle_with_filter
from tango.quality import HintCounts, PuzzleFilter, count_hints
from tango.solver import count_solutions


@dataclass(frozen=True)
class MetricSummary:
    """Minimum, average, and maximum for one numeric metric."""

    minimum: int
    average: float
    maximum: int


@dataclass(frozen=True)
class AnalysisResult:
    """Summary of a generation quality run."""

    generated: int
    unique: int
    failed: int
    elapsed_sec: float
    initial_cells: MetricSummary
    horizontal_constraints: MetricSummary
    vertical_constraints: MetricSummary
    total_hints: MetricSummary


class AnalysisError(RuntimeError):
    """Raised when generation quality analysis detects a failed puzzle."""


def analyze_generation(
    count: int,
    seed: int | None = None,
    size: int = 6,
    max_attempts: int = 1000,
    puzzle_filter: PuzzleFilter | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
) -> AnalysisResult:
    """Generate puzzles, verify uniqueness, and summarize hint counts."""

    if count <= 0:
        raise ValueError("count must be positive.")

    rng = random.Random(seed)
    started = time.perf_counter()
    hint_counts: list[HintCounts] = []
    unique = 0
    failed = 0

    for index in range(count):
        try:
            puzzle = generate_puzzle_with_filter(
                size=size,
                rng=rng,
                max_attempts=max_attempts,
                puzzle_filter=puzzle_filter,
            )
        except Exception as exc:
            failed += 1
            elapsed_sec = time.perf_counter() - started
            raise AnalysisError(
                f"Puzzle generation failed at index {index}: {exc}. "
                f"generated={len(hint_counts)}, unique={unique}, "
                f"failed={failed}, elapsed_sec={elapsed_sec:.2f}"
            ) from exc

        solution_count = count_solutions(puzzle, limit=2)
        if solution_count != 1:
            failed += 1
            elapsed_sec = time.perf_counter() - started
            raise AnalysisError(
                f"Puzzle at index {index} is not unique: "
                f"count_solutions={solution_count}. "
                f"generated={len(hint_counts) + 1}, unique={unique}, "
                f"failed={failed}, elapsed_sec={elapsed_sec:.2f}"
            )

        unique += 1
        hint_counts.append(count_hints(puzzle))
        if progress_callback is not None:
            progress_callback(index + 1, count)

    elapsed_sec = time.perf_counter() - started
    return AnalysisResult(
        generated=len(hint_counts),
        unique=unique,
        failed=failed,
        elapsed_sec=elapsed_sec,
        initial_cells=_summarize([counts.initial_cells for counts in hint_counts]),
        horizontal_constraints=_summarize(
            [counts.horizontal_constraints for counts in hint_counts]
        ),
        vertical_constraints=_summarize(
            [counts.vertical_constraints for counts in hint_counts]
        ),
        total_hints=_summarize([counts.total_hints for counts in hint_counts]),
    )


def format_analysis_result(
    result: AnalysisResult,
    difficulty: str | None = None,
) -> str:
    """Format an analysis result for CLI output."""

    lines = []
    if difficulty is not None:
        lines.append(f"difficulty: {difficulty}")
    lines.extend(
        [
            f"generated: {result.generated}",
            f"unique: {result.unique}",
            f"failed: {result.failed}",
            f"elapsed_sec: {result.elapsed_sec:.2f}",
            f"initial_cells min/avg/max: {_format_metric(result.initial_cells)}",
            "horizontal_constraints min/avg/max: "
            f"{_format_metric(result.horizontal_constraints)}",
            "vertical_constraints min/avg/max: "
            f"{_format_metric(result.vertical_constraints)}",
            f"total_hints min/avg/max: {_format_metric(result.total_hints)}",
        ]
    )
    return "\n".join(lines)


def _summarize(values: list[int]) -> MetricSummary:
    if not values:
        raise ValueError("values must not be empty.")
    return MetricSummary(
        minimum=min(values),
        average=sum(values) / len(values),
        maximum=max(values),
    )


def _format_metric(metric: MetricSummary) -> str:
    return f"{metric.minimum}/{metric.average:.2f}/{metric.maximum}"
