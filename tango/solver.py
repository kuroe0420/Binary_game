"""Backtracking solver for Tango-style puzzles."""

from __future__ import annotations

from tango.model import Board, Cell, Puzzle, clone_board
from tango.rules import get_candidates, is_complete, is_consistent_partial


def solve(puzzle: Puzzle) -> Board | None:
    """Return one solution for a puzzle, or None if no solution exists."""

    solutions = find_solutions(puzzle, limit=1)
    return solutions[0] if solutions else None


def count_solutions(puzzle: Puzzle, limit: int = 2) -> int:
    """Return the number of solutions, stopping once limit is reached."""

    return len(find_solutions(puzzle, limit=limit))


def find_solutions(puzzle: Puzzle, limit: int = 2) -> list[Board]:
    """Find solutions using MRV-guided backtracking."""

    if limit <= 0:
        return []

    board = clone_board(puzzle.initial_board)
    if not is_consistent_partial(puzzle, board):
        return []

    solutions: list[Board] = []

    def choose_cell() -> tuple[int, int, list[Cell]] | None:
        best: tuple[int, int, list[Cell]] | None = None
        for row in range(puzzle.size):
            for col in range(puzzle.size):
                if board[row][col] != Cell.EMPTY:
                    continue
                candidates = get_candidates(puzzle, board, row, col)
                if not candidates:
                    return (row, col, [])
                if best is None or len(candidates) < len(best[2]):
                    best = (row, col, candidates)
                    if len(candidates) == 1:
                        return best
        return best

    def backtrack() -> None:
        if len(solutions) >= limit:
            return
        if is_complete(puzzle, board):
            solutions.append(clone_board(board))
            return

        choice = choose_cell()
        if choice is None:
            return

        row, col, candidates = choice
        for candidate in candidates:
            board[row][col] = candidate
            if is_consistent_partial(puzzle, board):
                backtrack()
            board[row][col] = Cell.EMPTY
            if len(solutions) >= limit:
                return

    backtrack()
    return solutions
