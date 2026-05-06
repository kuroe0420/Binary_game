from tango.model import Cell, Puzzle, empty_board, empty_horizontal_constraints, empty_vertical_constraints
from tango.solver import count_solutions, solve


SOLUTION = [
    [Cell.A, Cell.B, Cell.A, Cell.B, Cell.A, Cell.B],
    [Cell.B, Cell.A, Cell.B, Cell.A, Cell.B, Cell.A],
    [Cell.B, Cell.A, Cell.A, Cell.B, Cell.A, Cell.B],
    [Cell.A, Cell.B, Cell.B, Cell.A, Cell.B, Cell.A],
    [Cell.B, Cell.A, Cell.B, Cell.A, Cell.A, Cell.B],
    [Cell.A, Cell.B, Cell.A, Cell.B, Cell.B, Cell.A],
]


def empty_puzzle(initial_board: list[list[Cell]] | None = None) -> Puzzle:
    return Puzzle(
        size=6,
        initial_board=initial_board if initial_board is not None else empty_board(6),
        horizontal_constraints=empty_horizontal_constraints(6),
        vertical_constraints=empty_vertical_constraints(6),
    )


def test_fixed_solvable_puzzle_has_one_solution() -> None:
    puzzle = empty_puzzle(initial_board=[row.copy() for row in SOLUTION])

    assert count_solutions(puzzle) == 1
    assert solve(puzzle) == SOLUTION


def test_empty_puzzle_has_multiple_solutions() -> None:
    puzzle = empty_puzzle()

    assert count_solutions(puzzle, limit=2) >= 2


def test_unsolvable_puzzle_has_zero_solutions() -> None:
    board = empty_board(6)
    board[0][:4] = [Cell.A, Cell.A, Cell.A, Cell.A]
    puzzle = empty_puzzle(initial_board=board)

    assert count_solutions(puzzle) == 0
