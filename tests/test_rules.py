from tango.model import Cell, Constraint, Puzzle, empty_board, empty_horizontal_constraints, empty_vertical_constraints
from tango.rules import ViolationType, is_complete, validate_board


SOLUTION = [
    [Cell.A, Cell.B, Cell.A, Cell.B, Cell.A, Cell.B],
    [Cell.B, Cell.A, Cell.B, Cell.A, Cell.B, Cell.A],
    [Cell.B, Cell.A, Cell.A, Cell.B, Cell.A, Cell.B],
    [Cell.A, Cell.B, Cell.B, Cell.A, Cell.B, Cell.A],
    [Cell.B, Cell.A, Cell.B, Cell.A, Cell.A, Cell.B],
    [Cell.A, Cell.B, Cell.A, Cell.B, Cell.B, Cell.A],
]


def empty_puzzle() -> Puzzle:
    return Puzzle(
        size=6,
        initial_board=empty_board(6),
        horizontal_constraints=empty_horizontal_constraints(6),
        vertical_constraints=empty_vertical_constraints(6),
    )


def violation_types(puzzle: Puzzle, board: list[list[Cell]]) -> set[ViolationType]:
    return {violation.type for violation in validate_board(puzzle, board)}


def test_row_with_four_a_is_violation() -> None:
    puzzle = empty_puzzle()
    board = empty_board(6)
    board[0][:4] = [Cell.A, Cell.A, Cell.A, Cell.A]

    assert ViolationType.TOO_MANY_IN_ROW in violation_types(puzzle, board)


def test_column_with_four_b_is_violation() -> None:
    puzzle = empty_puzzle()
    board = empty_board(6)
    for row in range(4):
        board[row][0] = Cell.B

    assert ViolationType.TOO_MANY_IN_COLUMN in violation_types(puzzle, board)


def test_three_consecutive_row_is_violation() -> None:
    puzzle = empty_puzzle()
    board = empty_board(6)
    board[2][1:4] = [Cell.A, Cell.A, Cell.A]

    assert ViolationType.THREE_CONSECUTIVE_ROW in violation_types(puzzle, board)


def test_three_consecutive_column_is_violation() -> None:
    puzzle = empty_puzzle()
    board = empty_board(6)
    for row in range(1, 4):
        board[row][3] = Cell.B

    assert ViolationType.THREE_CONSECUTIVE_COLUMN in violation_types(puzzle, board)


def test_same_constraint_violation() -> None:
    puzzle = empty_puzzle()
    puzzle.horizontal_constraints[0][0] = Constraint.SAME
    board = empty_board(6)
    board[0][0] = Cell.A
    board[0][1] = Cell.B

    assert ViolationType.SAME_CONSTRAINT in violation_types(puzzle, board)


def test_different_constraint_violation() -> None:
    puzzle = empty_puzzle()
    puzzle.horizontal_constraints[0][0] = Constraint.DIFFERENT
    board = empty_board(6)
    board[0][0] = Cell.B
    board[0][1] = Cell.B

    assert ViolationType.DIFFERENT_CONSTRAINT in violation_types(puzzle, board)


def test_complete_solution_is_complete() -> None:
    puzzle = empty_puzzle()

    assert is_complete(puzzle, SOLUTION)
