from tango.generator import generate_puzzle, generate_solution
from tango.json_io import load_puzzles, save_puzzles
from tango.model import Puzzle, empty_board, empty_horizontal_constraints, empty_vertical_constraints
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
