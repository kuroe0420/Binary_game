import json

from tango.analyze import AnalysisResult, MetricSummary
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
    save_puzzles(path, [puzzle], difficulty="easy")

    exit_code = main(["show", "--input", str(path), "--index", "0"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Puzzle id: duo_0001" in output
    assert "difficulty: easy" in output
    assert "initialCellCount: 1" in output
    assert "horizontalConstraintCount: 1" in output
    assert "verticalConstraintCount: 0" in output
    assert "totalHintCount: 2" in output
    assert "solution count up to 2:" in output


def test_generate_command_accepts_easy_difficulty(tmp_path, monkeypatch, capsys) -> None:
    puzzle = _empty_test_puzzle()
    captured = {}

    def fake_generate_puzzles(**kwargs):
        captured.update(kwargs)
        kwargs["progress_callback"](1, 1)
        return [puzzle]

    monkeypatch.setattr("tango.cli.generate_puzzles", fake_generate_puzzles)
    output_path = tmp_path / "easy.json"

    exit_code = main(
        [
            "generate",
            "--count",
            "1",
            "--seed",
            "42",
            "--difficulty",
            "easy",
            "--output",
            str(output_path),
        ]
    )
    data = json.loads(output_path.read_text(encoding="utf-8"))
    puzzle_filter = captured["puzzle_filter"]

    assert exit_code == 0
    assert "generated 1/1" in capsys.readouterr().out
    assert puzzle_filter.min_initial_cells == 6
    assert puzzle_filter.min_total_hints == 13
    assert puzzle_filter.min_constraints == 5
    assert data["puzzles"][0]["metadata"]["difficulty"] == "easy"


def test_analyze_command_accepts_easy_difficulty(monkeypatch, capsys) -> None:
    captured = {}

    def fake_analyze_generation(**kwargs):
        captured.update(kwargs)
        kwargs["progress_callback"](1, 1)
        metric = MetricSummary(minimum=1, average=1.0, maximum=1)
        return AnalysisResult(
            generated=1,
            unique=1,
            failed=0,
            elapsed_sec=0.0,
            initial_cells=metric,
            horizontal_constraints=metric,
            vertical_constraints=metric,
            total_hints=metric,
        )

    monkeypatch.setattr("tango.cli.analyze_generation", fake_analyze_generation)

    exit_code = main(
        [
            "analyze",
            "--count",
            "1",
            "--seed",
            "42",
            "--difficulty",
            "easy",
        ]
    )
    output = capsys.readouterr().out
    puzzle_filter = captured["puzzle_filter"]

    assert exit_code == 0
    assert "generated 1/1" in output
    assert "difficulty: easy" in output
    assert puzzle_filter.min_initial_cells == 6
    assert puzzle_filter.min_total_hints == 13
    assert puzzle_filter.min_constraints == 5


def _empty_test_puzzle() -> Puzzle:
    return Puzzle(
        size=6,
        initial_board=empty_board(6),
        horizontal_constraints=empty_horizontal_constraints(6),
        vertical_constraints=empty_vertical_constraints(6),
    )
