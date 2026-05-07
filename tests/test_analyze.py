from tango.analyze import analyze_generation, count_hints, format_analysis_result
from tango.model import Cell, Constraint, Puzzle, empty_board, empty_horizontal_constraints, empty_vertical_constraints


def test_count_hints_counts_all_hint_types() -> None:
    board = empty_board(6)
    board[0][0] = Cell.A
    board[1][1] = Cell.B
    horizontal = empty_horizontal_constraints(6)
    horizontal[0][0] = Constraint.SAME
    vertical = empty_vertical_constraints(6)
    vertical[0][0] = Constraint.DIFFERENT
    vertical[1][2] = Constraint.SAME
    puzzle = Puzzle(
        size=6,
        initial_board=board,
        horizontal_constraints=horizontal,
        vertical_constraints=vertical,
    )

    counts = count_hints(puzzle)

    assert counts.initial_cells == 2
    assert counts.horizontal_constraints == 1
    assert counts.vertical_constraints == 2
    assert counts.total_hints == 5


def test_analyze_generation_summarizes_generated_puzzles(monkeypatch) -> None:
    puzzle = Puzzle(
        size=6,
        initial_board=empty_board(6),
        horizontal_constraints=empty_horizontal_constraints(6),
        vertical_constraints=empty_vertical_constraints(6),
    )

    def fake_generate_puzzle_with_filter(**kwargs):
        return puzzle

    monkeypatch.setattr(
        "tango.analyze.generate_puzzle_with_filter",
        fake_generate_puzzle_with_filter,
    )
    monkeypatch.setattr("tango.analyze.count_solutions", lambda puzzle, limit=2: 1)

    result = analyze_generation(count=3, seed=42)
    output = format_analysis_result(result)

    assert result.generated == 3
    assert result.unique == 3
    assert result.failed == 0
    assert "generated: 3" in output
    assert "total_hints min/avg/max: 0/0.00/0" in output


def test_format_analysis_result_includes_difficulty_when_provided(monkeypatch) -> None:
    puzzle = Puzzle(
        size=6,
        initial_board=empty_board(6),
        horizontal_constraints=empty_horizontal_constraints(6),
        vertical_constraints=empty_vertical_constraints(6),
    )

    def fake_generate_puzzle_with_filter(**kwargs):
        return puzzle

    monkeypatch.setattr(
        "tango.analyze.generate_puzzle_with_filter",
        fake_generate_puzzle_with_filter,
    )
    monkeypatch.setattr("tango.analyze.count_solutions", lambda puzzle, limit=2: 1)

    result = analyze_generation(count=1, seed=42)
    output = format_analysis_result(result, difficulty="easy")

    assert output.splitlines()[0] == "difficulty: easy"
