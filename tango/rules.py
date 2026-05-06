"""Rule validation for Tango-style binary logic puzzles."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from tango.model import Cell, Constraint, Position, Puzzle, clone_board, validate_puzzle_shape


class ViolationType(str, Enum):
    """Known rule violation categories."""

    TOO_MANY_IN_ROW = "too_many_in_row"
    TOO_MANY_IN_COLUMN = "too_many_in_column"
    THREE_CONSECUTIVE_ROW = "three_consecutive_row"
    THREE_CONSECUTIVE_COLUMN = "three_consecutive_column"
    SAME_CONSTRAINT = "same_constraint"
    DIFFERENT_CONSTRAINT = "different_constraint"
    LOCKED_CELL_MODIFIED = "locked_cell_modified"


@dataclass(frozen=True)
class RuleViolation:
    """A single rule violation on the board."""

    type: ViolationType
    positions: tuple[Position, ...]
    message: str


def validate_board(puzzle: Puzzle, board: list[list[Cell | int]]) -> list[RuleViolation]:
    """Return all clear rule violations for a complete or partial board."""

    validate_puzzle_shape(puzzle)
    normalized = clone_board(board)
    if len(normalized) != puzzle.size or any(len(row) != puzzle.size for row in normalized):
        raise ValueError("board shape does not match puzzle size.")

    violations: list[RuleViolation] = []
    half = puzzle.size // 2

    _validate_locked_cells(puzzle, normalized, violations)
    _validate_row_counts(normalized, half, violations)
    _validate_column_counts(normalized, half, violations)
    _validate_row_runs(normalized, violations)
    _validate_column_runs(normalized, violations)
    _validate_constraints(puzzle, normalized, violations)

    return violations


def is_consistent_partial(puzzle: Puzzle, board: list[list[Cell | int]]) -> bool:
    """Return True when a partial board has no clear rule violations."""

    return not validate_board(puzzle, board)


def is_complete(puzzle: Puzzle, board: list[list[Cell | int]]) -> bool:
    """Return True when the board is filled and satisfies every rule."""

    normalized = clone_board(board)
    if any(cell == Cell.EMPTY for row in normalized for cell in row):
        return False
    if validate_board(puzzle, normalized):
        return False

    half = puzzle.size // 2
    for row in normalized:
        if row.count(Cell.A) != half or row.count(Cell.B) != half:
            return False

    for col in range(puzzle.size):
        values = [normalized[row][col] for row in range(puzzle.size)]
        if values.count(Cell.A) != half or values.count(Cell.B) != half:
            return False

    return True


def get_candidates(
    puzzle: Puzzle, board: list[list[Cell | int]], row: int, col: int
) -> list[Cell]:
    """Return legal candidate values for one cell in the current partial board."""

    normalized = clone_board(board)
    current = normalized[row][col]
    if current != Cell.EMPTY:
        return [current] if is_consistent_partial(puzzle, normalized) else []

    locked = Cell(puzzle.initial_board[row][col])
    choices = [locked] if locked != Cell.EMPTY else [Cell.A, Cell.B]
    candidates: list[Cell] = []
    for choice in choices:
        trial = [board_row.copy() for board_row in normalized]
        trial[row][col] = choice
        if is_consistent_partial(puzzle, trial):
            candidates.append(choice)
    return candidates


def _validate_locked_cells(
    puzzle: Puzzle, board: list[list[Cell]], violations: list[RuleViolation]
) -> None:
    for row in range(puzzle.size):
        for col in range(puzzle.size):
            locked = Cell(puzzle.initial_board[row][col])
            if locked != Cell.EMPTY and board[row][col] != locked:
                violations.append(
                    RuleViolation(
                        ViolationType.LOCKED_CELL_MODIFIED,
                        (Position(row, col),),
                        "Locked initial cell was modified.",
                    )
                )


def _validate_row_counts(
    board: list[list[Cell]], half: int, violations: list[RuleViolation]
) -> None:
    for row_index, row in enumerate(board):
        for cell in (Cell.A, Cell.B):
            if row.count(cell) > half:
                positions = tuple(
                    Position(row_index, col)
                    for col, value in enumerate(row)
                    if value == cell
                )
                violations.append(
                    RuleViolation(
                        ViolationType.TOO_MANY_IN_ROW,
                        positions,
                        f"Row {row_index} contains too many {cell.name} cells.",
                    )
                )


def _validate_column_counts(
    board: list[list[Cell]], half: int, violations: list[RuleViolation]
) -> None:
    size = len(board)
    for col in range(size):
        values = [board[row][col] for row in range(size)]
        for cell in (Cell.A, Cell.B):
            if values.count(cell) > half:
                positions = tuple(
                    Position(row, col) for row, value in enumerate(values) if value == cell
                )
                violations.append(
                    RuleViolation(
                        ViolationType.TOO_MANY_IN_COLUMN,
                        positions,
                        f"Column {col} contains too many {cell.name} cells.",
                    )
                )


def _validate_row_runs(board: list[list[Cell]], violations: list[RuleViolation]) -> None:
    for row_index, row in enumerate(board):
        for col in range(len(row) - 2):
            first, second, third = row[col : col + 3]
            if first != Cell.EMPTY and first == second == third:
                violations.append(
                    RuleViolation(
                        ViolationType.THREE_CONSECUTIVE_ROW,
                        (
                            Position(row_index, col),
                            Position(row_index, col + 1),
                            Position(row_index, col + 2),
                        ),
                        "Three equal cells are consecutive in a row.",
                    )
                )


def _validate_column_runs(
    board: list[list[Cell]], violations: list[RuleViolation]
) -> None:
    size = len(board)
    for row in range(size - 2):
        for col in range(size):
            first = board[row][col]
            second = board[row + 1][col]
            third = board[row + 2][col]
            if first != Cell.EMPTY and first == second == third:
                violations.append(
                    RuleViolation(
                        ViolationType.THREE_CONSECUTIVE_COLUMN,
                        (
                            Position(row, col),
                            Position(row + 1, col),
                            Position(row + 2, col),
                        ),
                        "Three equal cells are consecutive in a column.",
                    )
                )


def _validate_constraints(
    puzzle: Puzzle, board: list[list[Cell]], violations: list[RuleViolation]
) -> None:
    size = puzzle.size
    for row in range(size):
        for col in range(size - 1):
            constraint = Constraint(puzzle.horizontal_constraints[row][col])
            if constraint == Constraint.NONE:
                continue
            left = board[row][col]
            right = board[row][col + 1]
            _append_constraint_violation(
                constraint,
                left,
                right,
                (Position(row, col), Position(row, col + 1)),
                violations,
            )

    for row in range(size - 1):
        for col in range(size):
            constraint = Constraint(puzzle.vertical_constraints[row][col])
            if constraint == Constraint.NONE:
                continue
            top = board[row][col]
            bottom = board[row + 1][col]
            _append_constraint_violation(
                constraint,
                top,
                bottom,
                (Position(row, col), Position(row + 1, col)),
                violations,
            )


def _append_constraint_violation(
    constraint: Constraint,
    first: Cell,
    second: Cell,
    positions: tuple[Position, Position],
    violations: list[RuleViolation],
) -> None:
    if first == Cell.EMPTY or second == Cell.EMPTY:
        return
    if constraint == Constraint.SAME and first != second:
        violations.append(
            RuleViolation(
                ViolationType.SAME_CONSTRAINT,
                positions,
                "Adjacent cells must be the same.",
            )
        )
    elif constraint == Constraint.DIFFERENT and first == second:
        violations.append(
            RuleViolation(
                ViolationType.DIFFERENT_CONSTRAINT,
                positions,
                "Adjacent cells must be different.",
            )
        )
