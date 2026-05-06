"""Core data structures for Tango-style puzzles."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import TypeAlias


class Cell(IntEnum):
    """A board cell value."""

    EMPTY = -1
    A = 0
    B = 1


class Constraint(IntEnum):
    """A constraint between adjacent cells."""

    NONE = 0
    SAME = 1
    DIFFERENT = 2


@dataclass(frozen=True)
class Position:
    """A zero-based board position."""

    row: int
    col: int


Board: TypeAlias = list[list[Cell]]
ConstraintGrid: TypeAlias = list[list[Constraint]]


@dataclass(frozen=True)
class Puzzle:
    """A Tango puzzle definition."""

    size: int
    initial_board: Board
    horizontal_constraints: ConstraintGrid
    vertical_constraints: ConstraintGrid
    solution: Board | None = None


def empty_board(size: int) -> Board:
    """Create an empty square board."""

    return [[Cell.EMPTY for _ in range(size)] for _ in range(size)]


def empty_horizontal_constraints(size: int) -> ConstraintGrid:
    """Create an empty horizontal constraint grid."""

    return [[Constraint.NONE for _ in range(size - 1)] for _ in range(size)]


def empty_vertical_constraints(size: int) -> ConstraintGrid:
    """Create an empty vertical constraint grid."""

    return [[Constraint.NONE for _ in range(size)] for _ in range(size - 1)]


def clone_board(board: list[list[Cell | int]]) -> Board:
    """Copy a board and normalize values to Cell."""

    return [[Cell(value) for value in row] for row in board]


def clone_constraints(grid: list[list[Constraint | int]]) -> ConstraintGrid:
    """Copy a constraint grid and normalize values to Constraint."""

    return [[Constraint(value) for value in row] for row in grid]


def validate_puzzle_shape(puzzle: Puzzle) -> None:
    """Raise ValueError if a puzzle's grids do not match its declared size."""

    size = puzzle.size
    if size <= 0 or size % 2 != 0:
        raise ValueError("Puzzle size must be a positive even number.")
    _validate_board_shape(puzzle.initial_board, size, "initial_board")
    if puzzle.solution is not None:
        _validate_board_shape(puzzle.solution, size, "solution")
    _validate_grid_shape(
        puzzle.horizontal_constraints,
        size,
        size - 1,
        "horizontal_constraints",
    )
    _validate_grid_shape(
        puzzle.vertical_constraints,
        size - 1,
        size,
        "vertical_constraints",
    )


def _validate_board_shape(board: list[list[Cell | int]], size: int, name: str) -> None:
    _validate_grid_shape(board, size, size, name)


def _validate_grid_shape(
    grid: list[list[object]], rows: int, cols: int, name: str
) -> None:
    if len(grid) != rows:
        raise ValueError(f"{name} must have {rows} rows.")
    for row in grid:
        if len(row) != cols:
            raise ValueError(f"{name} rows must have {cols} columns.")
