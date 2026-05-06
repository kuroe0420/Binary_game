"""JSON input and output for Tango puzzles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tango.model import Board, ConstraintGrid, Puzzle, clone_board, clone_constraints


def puzzle_to_dict(puzzle: Puzzle) -> dict[str, Any]:
    """Convert a puzzle to the JSON-compatible dictionary format."""

    return {
        "size": puzzle.size,
        "initialBoard": _board_to_ints(puzzle.initial_board),
        "horizontalConstraints": _constraints_to_ints(puzzle.horizontal_constraints),
        "verticalConstraints": _constraints_to_ints(puzzle.vertical_constraints),
        "solution": None
        if puzzle.solution is None
        else _board_to_ints(puzzle.solution),
    }


def puzzle_from_dict(data: dict[str, Any]) -> Puzzle:
    """Create a Puzzle from the JSON-compatible dictionary format."""

    solution_data = data.get("solution")
    solution = None if solution_data in (None, []) else clone_board(solution_data)
    return Puzzle(
        size=int(data["size"]),
        initial_board=clone_board(data["initialBoard"]),
        horizontal_constraints=clone_constraints(data["horizontalConstraints"]),
        vertical_constraints=clone_constraints(data["verticalConstraints"]),
        solution=solution,
    )


def save_puzzles(path: str | Path, puzzles: list[Puzzle]) -> None:
    """Save puzzles to a JSON file."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"puzzles": [puzzle_to_dict(puzzle) for puzzle in puzzles]}
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_puzzles(path: str | Path) -> list[Puzzle]:
    """Load puzzles from a JSON file."""

    input_path = Path(path)
    data = json.loads(input_path.read_text(encoding="utf-8"))
    if "puzzles" in data:
        return [puzzle_from_dict(item) for item in data["puzzles"]]
    return [puzzle_from_dict(data)]


def _board_to_ints(board: Board) -> list[list[int]]:
    return [[int(value) for value in row] for row in board]


def _constraints_to_ints(grid: ConstraintGrid) -> list[list[int]]:
    return [[int(value) for value in row] for row in grid]
