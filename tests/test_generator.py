import json

from tango.generator import generate_puzzle, generate_puzzle_with_filter, generate_solution
from tango.json_io import load_puzzles, save_puzzles
from tango.model import Puzzle, empty_board, empty_horizontal_constraints, empty_vertical_constraints
from tango.quality import PuzzleFilter, count_hints
from tango.rules import is_complete
from tango.solver import count_solutions


def test_generate_solution_satisfies_rules() -> None:
    solution = generate_solution()
    puzzle = Puzzle(
        size=6,
        initial_board=empty_board(6),
        horizontal_constraints=empty_horizontal_constraints(6),
        vertical_constraints=empty_vertical_constraints(6),
    )

    assert is_complete(puzzle, solution)


def test_generate_puzzle_has_unique_solution() -> None:
    puzzle = generate_puzzle()

    assert count_solutions(puzzle, limit=2) == 1


def test_json_roundtrip_keeps_unique_solution(tmp_path) -> None:
    puzzle = generate_puzzle()
    path = tmp_path / "puzzles.json"

    save_puzzles(path, [puzzle])
    loaded = load_puzzles(path)

    assert len(loaded) == 1
    assert count_solutions(loaded[0], limit=2) == 1


def test_save_puzzles_adds_id_and_metadata(tmp_path) -> None:
    puzzle = generate_puzzle()
    counts = count_hints(puzzle)
    path = tmp_path / "puzzles.json"

    save_puzzles(path, [puzzle])
    data = json.loads(path.read_text(encoding="utf-8"))
    saved = data["puzzles"][0]

    assert saved["id"] == "duo_0001"
    assert saved["metadata"]["initialCellCount"] == counts.initial_cells
    assert saved["metadata"]["horizontalConstraintCount"] == counts.horizontal_constraints
    assert saved["metadata"]["verticalConstraintCount"] == counts.vertical_constraints
    assert saved["metadata"]["totalHintCount"] == counts.total_hints
    assert saved["metadata"]["generatorVersion"] == "0.1.0"


def test_load_puzzles_accepts_old_format_without_id_or_metadata(tmp_path) -> None:
    path = tmp_path / "old_puzzle.json"
    path.write_text(
        json.dumps(
            {
                "size": 6,
                "initialBoard": [[-1 for _ in range(6)] for _ in range(6)],
                "horizontalConstraints": [[0 for _ in range(5)] for _ in range(6)],
                "verticalConstraints": [[0 for _ in range(6)] for _ in range(5)],
                "solution": [],
            }
        ),
        encoding="utf-8",
    )

    loaded = load_puzzles(path)

    assert len(loaded) == 1
    assert loaded[0].id is None


def test_generate_puzzle_with_filter_rejects_impossible_filter() -> None:
    impossible_filter = PuzzleFilter(min_total_hints=999)

    try:
        generate_puzzle_with_filter(puzzle_filter=impossible_filter, max_attempts=1)
    except RuntimeError as exc:
        assert "matching filter" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError for impossible filter.")
