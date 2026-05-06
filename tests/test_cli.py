from tango.cli import main
from tango.json_io import save_puzzles
from tango.model import Cell, Constraint, Puzzle, empty_board, empty_horizontal_constraints, empty_vertical_constraints


def test_show_command_prints_id_metadata_and_solution_count(tmp_path, capsys) -> None:
    board = empty_board(6)
    board[0][0] = Cell.A
    horizontal = empty_horizontal_constraints(6)
    horizontal[0][0] = Constraint.DIFFERENT
    vertical = empty_vertical_constraints(6)
    solution = [
        [Cell.A, Cell.B, Cell.A, Cell.B, Cell.A, Cell.B],
        [Cell.B, Cell.A, Cell.B, Cell.A, Cell.B, Cell.A],
        [Cell.B, Cell.A, Cell.A, Cell.B, Cell.A, Cell.B],
        [Cell.A, Cell.B, Cell.B, Cell.A, Cell.B, Cell.A],
        [Cell.B, Cell.A, Cell.B, Cell.A, Cell.A, Cell.B],
        [Cell.A, Cell.B, Cell.A, Cell.B, Cell.B, Cell.A],
    ]
    puzzle = Puzzle(
        size=6,
        initial_board=board,
        horizontal_constraints=horizontal,
        vertical_constraints=vertical,
        solution=solution,
    )
    path = tmp_path / "puzzles.json"
    save_puzzles(path, [puzzle])

    exit_code = main(["show", "--input", str(path), "--index", "0"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Puzzle id: duo_0001" in output
    assert "initialCellCount: 1" in output
    assert "horizontalConstraintCount: 1" in output
    assert "verticalConstraintCount: 0" in output
    assert "totalHintCount: 2" in output
    assert "solution count up to 2:" in output
