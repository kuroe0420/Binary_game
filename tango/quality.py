"""Shared quality metrics and filters for Tango puzzles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tango.model import Cell, Constraint, Puzzle

GENERATOR_VERSION = "0.2.0"


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

    @property
    def total_constraints(self) -> int:
        """Return the total number of adjacent constraints."""

        return self.horizontal_constraints + self.vertical_constraints


@dataclass(frozen=True)
class PuzzleFilter:
    """Minimum quality thresholds used while generating puzzles."""

    min_initial_cells: int = 0
    min_total_hints: int = 0
    min_constraints: int = 0

    def __post_init__(self) -> None:
        if self.min_initial_cells < 0:
            raise ValueError("min_initial_cells must not be negative.")
        if self.min_total_hints < 0:
            raise ValueError("min_total_hints must not be negative.")
        if self.min_constraints < 0:
            raise ValueError("min_constraints must not be negative.")

    def describe(self) -> str:
        """Return a concise text description for error messages."""

        return (
            f"min_initial_cells={self.min_initial_cells}, "
            f"min_total_hints={self.min_total_hints}, "
            f"min_constraints={self.min_constraints}"
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


def build_metadata(puzzle: Puzzle, difficulty: str | None = None) -> dict[str, Any]:
    """Build JSON metadata for a puzzle from its current hints."""

    counts = count_hints(puzzle)
    metadata_difficulty = difficulty
    if metadata_difficulty is None:
        metadata_difficulty = puzzle.metadata.get("difficulty", "custom")
    return {
        "initialCellCount": counts.initial_cells,
        "horizontalConstraintCount": counts.horizontal_constraints,
        "verticalConstraintCount": counts.vertical_constraints,
        "totalHintCount": counts.total_hints,
        "difficulty": metadata_difficulty,
        "generatorVersion": GENERATOR_VERSION,
    }


def puzzle_matches_filter(
    puzzle: Puzzle,
    puzzle_filter: PuzzleFilter | None = None,
) -> bool:
    """Return True if a puzzle satisfies the requested minimum thresholds."""

    if puzzle_filter is None:
        puzzle_filter = PuzzleFilter()
    counts = count_hints(puzzle)
    return (
        counts.initial_cells >= puzzle_filter.min_initial_cells
        and counts.total_hints >= puzzle_filter.min_total_hints
        and counts.total_constraints >= puzzle_filter.min_constraints
    )
