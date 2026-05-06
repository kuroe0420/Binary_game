"""Generation quality analysis for Tango puzzles."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass

from tango.generator import generate_puzzle
from tango.model import Cell, Constraint, Puzzle
from tango.solver import count_solutions


@dataclass(frozen=True)
class HintCounts:
    """Hint counts for a single puzzle."""

    initial_cells: int
    horizontal_constraints: int
    vertical_constraints: int

    @property
    def total_hints(self) -> int:
        """Return the total number of visible hints."""

        return (
            self.initial_cells
            + self.horizontal_constraints
            + self.vertical_constraints
        )


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
            puzzle = generate_puzzle(size=size, rng=rng, max_attempts=max_attempts)
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


def count_hints(puzzle: Puzzle) -> HintCounts:
    """Count initial cells and adjacent constraints in a puzzle."""

    initial_cells = sum(
        1
        for row in puzzle.initial_board
        for value in row
        if Cell(value) != Cell.EMPTY
    )
    horizontal_constraints = sum(
        1
        for row in puzzle.horizontal_constraints
        for value in row
        if Constraint(value) != Constraint.NONE
    )
    vertical_constraints = sum(
        1
        for row in puzzle.vertical_constraints
        for value in row
        if Constraint(value) != Constraint.NONE
    )
    return HintCounts(
        initial_cells=initial_cells,
        horizontal_constraints=horizontal_constraints,
        vertical_constraints=vertical_constraints,
    )


def format_analysis_result(result: AnalysisResult) -> str:
    """Format an analysis result for CLI output."""

    return "\n".join(
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
