"""Solution and puzzle generation for Tango-style puzzles."""

from __future__ import annotations

import random
from functools import lru_cache
from itertools import product
from typing import Callable, Literal, TypeAlias

from tango.model import (
    Board,
    Cell,
    Constraint,
    Puzzle,
    clone_board,
    clone_constraints,
    empty_board,
    empty_horizontal_constraints,
    empty_vertical_constraints,
)
from tango.quality import PuzzleFilter, puzzle_matches_filter
from tango.solver import count_solutions

HintKind: TypeAlias = Literal["cell", "horizontal", "vertical"]
Hint: TypeAlias = tuple[HintKind, int, int]


def generate_solution(size: int = 6, rng: random.Random | None = None) -> Board:
    """Generate a complete valid board."""

    if size <= 0 or size % 2 != 0:
        raise ValueError("size must be a positive even number.")

    rng = rng or random.Random()
    patterns = list(_valid_row_patterns(size))
    half = size // 2

    for _ in range(1000):
        board: Board = []
        column_a_counts = [0 for _ in range(size)]
        column_b_counts = [0 for _ in range(size)]

        def can_add(pattern: tuple[Cell, ...]) -> bool:
            row_index = len(board)
            for col, value in enumerate(pattern):
                if value == Cell.A and column_a_counts[col] + 1 > half:
                    return False
                if value == Cell.B and column_b_counts[col] + 1 > half:
                    return False
                if row_index >= 2 and board[row_index - 1][col] == board[row_index - 2][col] == value:
                    return False
            return True

        def add(pattern: tuple[Cell, ...]) -> None:
            board.append(list(pattern))
            for col, value in enumerate(pattern):
                if value == Cell.A:
                    column_a_counts[col] += 1
                else:
                    column_b_counts[col] += 1

        def remove(pattern: tuple[Cell, ...]) -> None:
            board.pop()
            for col, value in enumerate(pattern):
                if value == Cell.A:
                    column_a_counts[col] -= 1
                else:
                    column_b_counts[col] -= 1

        def backtrack() -> bool:
            if len(board) == size:
                return all(count == half for count in column_a_counts) and all(
                    count == half for count in column_b_counts
                )

            shuffled = patterns[:]
            rng.shuffle(shuffled)
            for pattern in shuffled:
                if not can_add(pattern):
                    continue
                add(pattern)
                if backtrack():
                    return True
                remove(pattern)
            return False

        if backtrack():
            return clone_board(board)

    raise RuntimeError("Failed to generate a valid solution.")


def generate_puzzle(
    size: int = 6,
    rng: random.Random | None = None,
    max_attempts: int = 1000,
    puzzle_filter: PuzzleFilter | None = None,
) -> Puzzle:
    """Generate a puzzle with exactly one solution."""

    if max_attempts <= 0:
        raise ValueError("max_attempts must be positive.")

    rng = rng or random.Random()
    for _ in range(max_attempts):
        solution = generate_solution(size=size, rng=rng)
        initial_board = empty_board(size)
        horizontal_constraints = empty_horizontal_constraints(size)
        vertical_constraints = empty_vertical_constraints(size)
        hints = _all_hints(size)
        rng.shuffle(hints)

        active_hints: list[Hint] = []
        is_unique = False
        for hint in hints:
            _apply_hint(
                hint,
                solution,
                initial_board,
                horizontal_constraints,
                vertical_constraints,
            )
            active_hints.append(hint)
            puzzle = _make_puzzle(
                size,
                initial_board,
                horizontal_constraints,
                vertical_constraints,
                solution,
            )
            if not is_unique:
                is_unique = count_solutions(puzzle, limit=2) == 1
            if is_unique and _puzzle_is_ready_for_minimization(puzzle, puzzle_filter):
                _minimize_hints(
                    size,
                    solution,
                    initial_board,
                    horizontal_constraints,
                    vertical_constraints,
                    active_hints,
                    rng,
                    puzzle_filter=puzzle_filter,
                )
                final_puzzle = _make_puzzle(
                    size,
                    initial_board,
                    horizontal_constraints,
                    vertical_constraints,
                    solution,
                )
                if count_solutions(final_puzzle, limit=2) == 1 and puzzle_matches_filter(
                    final_puzzle,
                    puzzle_filter,
                ):
                    return final_puzzle
                break

    if puzzle_filter is None:
        raise RuntimeError("Failed to generate a unique puzzle.")
    raise RuntimeError(
        "Failed to generate a unique puzzle matching filter after "
        f"{max_attempts} attempts: {puzzle_filter.describe()}"
    )


def generate_puzzles(
    count: int,
    seed: int | None = None,
    size: int = 6,
    max_attempts: int = 1000,
    puzzle_filter: PuzzleFilter | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
) -> list[Puzzle]:
    """Generate multiple puzzles using an optional deterministic seed."""

    return generate_filtered_puzzles(
        count=count,
        seed=seed,
        size=size,
        max_attempts=max_attempts,
        puzzle_filter=puzzle_filter,
        progress_callback=progress_callback,
    )


def generate_filtered_puzzles(
    count: int,
    seed: int | None = None,
    size: int = 6,
    max_attempts: int = 1000,
    puzzle_filter: PuzzleFilter | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
) -> list[Puzzle]:
    """Generate multiple puzzles that satisfy optional quality thresholds."""

    if count < 0:
        raise ValueError("count must not be negative.")
    rng = random.Random(seed)
    puzzles: list[Puzzle] = []
    for index in range(count):
        puzzles.append(
            generate_puzzle_with_filter(
                size=size,
                rng=rng,
                max_attempts=max_attempts,
                puzzle_filter=puzzle_filter,
            )
        )
        if progress_callback is not None:
            progress_callback(index + 1, count)
    return puzzles


def generate_puzzle_with_filter(
    size: int = 6,
    rng: random.Random | None = None,
    max_attempts: int = 1000,
    puzzle_filter: PuzzleFilter | None = None,
) -> Puzzle:
    """Generate one unique puzzle that satisfies optional quality thresholds."""

    if max_attempts <= 0:
        raise ValueError("max_attempts must be positive.")

    rng = rng or random.Random()
    return generate_puzzle(
        size=size,
        rng=rng,
        max_attempts=max_attempts,
        puzzle_filter=puzzle_filter,
    )


@lru_cache(maxsize=None)
def _valid_row_patterns(size: int) -> tuple[tuple[Cell, ...], ...]:
    half = size // 2
    patterns: list[tuple[Cell, ...]] = []
    for raw_pattern in product((Cell.A, Cell.B), repeat=size):
        pattern = tuple(Cell(value) for value in raw_pattern)
        if pattern.count(Cell.A) != half or pattern.count(Cell.B) != half:
            continue
        if any(
            pattern[index] == pattern[index + 1] == pattern[index + 2]
            for index in range(size - 2)
        ):
            continue
        patterns.append(pattern)
    return tuple(patterns)


def _all_hints(size: int) -> list[Hint]:
    hints: list[Hint] = []
    hints.extend(("cell", row, col) for row in range(size) for col in range(size))
    hints.extend(
        ("horizontal", row, col) for row in range(size) for col in range(size - 1)
    )
    hints.extend(("vertical", row, col) for row in range(size - 1) for col in range(size))
    return hints


def _apply_hint(
    hint: Hint,
    solution: Board,
    initial_board: Board,
    horizontal_constraints: list[list[Constraint]],
    vertical_constraints: list[list[Constraint]],
) -> None:
    kind, row, col = hint
    if kind == "cell":
        initial_board[row][col] = solution[row][col]
    elif kind == "horizontal":
        horizontal_constraints[row][col] = _constraint_for(
            solution[row][col], solution[row][col + 1]
        )
    else:
        vertical_constraints[row][col] = _constraint_for(
            solution[row][col], solution[row + 1][col]
        )


def _remove_hint(
    hint: Hint,
    initial_board: Board,
    horizontal_constraints: list[list[Constraint]],
    vertical_constraints: list[list[Constraint]],
) -> None:
    kind, row, col = hint
    if kind == "cell":
        initial_board[row][col] = Cell.EMPTY
    elif kind == "horizontal":
        horizontal_constraints[row][col] = Constraint.NONE
    else:
        vertical_constraints[row][col] = Constraint.NONE


def _minimize_hints(
    size: int,
    solution: Board,
    initial_board: Board,
    horizontal_constraints: list[list[Constraint]],
    vertical_constraints: list[list[Constraint]],
    active_hints: list[Hint],
    rng: random.Random,
    puzzle_filter: PuzzleFilter | None = None,
) -> None:
    candidates = active_hints[:]
    rng.shuffle(candidates)
    for hint in candidates:
        _remove_hint(hint, initial_board, horizontal_constraints, vertical_constraints)
        trial = _make_puzzle(
            size,
            initial_board,
            horizontal_constraints,
            vertical_constraints,
            solution,
        )
        if not puzzle_matches_filter(trial, puzzle_filter):
            _apply_hint(
                hint,
                solution,
                initial_board,
                horizontal_constraints,
                vertical_constraints,
            )
            continue
        if count_solutions(trial, limit=2) == 1:
            active_hints.remove(hint)
        else:
            _apply_hint(
                hint,
                solution,
                initial_board,
                horizontal_constraints,
                vertical_constraints,
            )


def _puzzle_is_ready_for_minimization(
    puzzle: Puzzle,
    puzzle_filter: PuzzleFilter | None,
) -> bool:
    if puzzle_filter is None:
        return True
    return puzzle_matches_filter(puzzle, puzzle_filter)


def _constraint_for(first: Cell, second: Cell) -> Constraint:
    return Constraint.SAME if first == second else Constraint.DIFFERENT


def _make_puzzle(
    size: int,
    initial_board: Board,
    horizontal_constraints: list[list[Constraint]],
    vertical_constraints: list[list[Constraint]],
    solution: Board,
) -> Puzzle:
    return Puzzle(
        size=size,
        initial_board=clone_board(initial_board),
        horizontal_constraints=clone_constraints(horizontal_constraints),
        vertical_constraints=clone_constraints(vertical_constraints),
        solution=clone_board(solution),
    )
