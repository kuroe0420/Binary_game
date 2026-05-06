"""Command line interface for the Tango prototype."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tango.analyze import AnalysisError, analyze_generation, format_analysis_result
from tango.generator import generate_puzzles
from tango.json_io import load_puzzles, save_puzzles
from tango.model import Board, Cell, Constraint, Puzzle
from tango.quality import PuzzleFilter, build_metadata
from tango.rules import RuleViolation, is_complete, validate_board
from tango.solver import count_solutions, solve


CELL_SYMBOLS = {
    Cell.EMPTY: ".",
    Cell.A: "A",
    Cell.B: "B",
}

CONSTRAINT_SYMBOLS = {
    Constraint.NONE: " ",
    Constraint.SAME: "=",
    Constraint.DIFFERENT: "x",
}


def main(argv: list[str] | None = None) -> int:
    """Run the CLI."""

    parser = argparse.ArgumentParser(prog="python -m tango.cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate", help="Generate puzzles.")
    generate_parser.add_argument("--count", type=int, required=True)
    generate_parser.add_argument("--seed", type=int)
    generate_parser.add_argument("--output", type=Path, required=True)
    _add_filter_args(generate_parser)

    solve_parser = subparsers.add_parser("solve", help="Solve a saved puzzle.")
    solve_parser.add_argument("--input", type=Path, required=True)
    solve_parser.add_argument("--index", type=int, default=0)

    show_parser = subparsers.add_parser("show", help="Show a saved puzzle.")
    show_parser.add_argument("--input", type=Path, required=True)
    show_parser.add_argument("--index", type=int, default=0)

    validate_parser = subparsers.add_parser("validate", help="Validate a saved puzzle.")
    validate_parser.add_argument("--input", type=Path, required=True)
    validate_parser.add_argument("--index", type=int, default=0)

    analyze_parser = subparsers.add_parser(
        "analyze", help="Generate puzzles and summarize generation quality."
    )
    analyze_parser.add_argument("--count", type=int, required=True)
    analyze_parser.add_argument("--seed", type=int)
    _add_filter_args(analyze_parser)

    args = parser.parse_args(argv)
    if args.command == "generate":
        return _cmd_generate(
            args.count,
            args.seed,
            args.output,
            _args_to_filter(args),
            args.max_attempts,
        )
    if args.command == "solve":
        return _cmd_solve(args.input, args.index)
    if args.command == "show":
        return _cmd_show(args.input, args.index)
    if args.command == "validate":
        return _cmd_validate(args.input, args.index)
    if args.command == "analyze":
        return _cmd_analyze(
            args.count,
            args.seed,
            _args_to_filter(args),
            args.max_attempts,
        )
    return 2


def format_board(board: Board) -> str:
    """Format only board cells."""

    return "\n".join(" ".join(CELL_SYMBOLS[Cell(value)] for value in row) for row in board)


def format_puzzle(puzzle: Puzzle, board: Board) -> str:
    """Format board cells with simple adjacent constraint markers."""

    lines: list[str] = []
    for row in range(puzzle.size):
        cell_line: list[str] = []
        for col in range(puzzle.size):
            cell_line.append(CELL_SYMBOLS[Cell(board[row][col])])
            if col < puzzle.size - 1:
                constraint = Constraint(puzzle.horizontal_constraints[row][col])
                cell_line.append(CONSTRAINT_SYMBOLS[constraint])
        lines.append(" ".join(cell_line).rstrip())

        if row < puzzle.size - 1:
            constraint_line: list[str] = []
            for col in range(puzzle.size):
                constraint = Constraint(puzzle.vertical_constraints[row][col])
                constraint_line.append(CONSTRAINT_SYMBOLS[constraint])
                if col < puzzle.size - 1:
                    constraint_line.append(" ")
            line = " ".join(constraint_line).rstrip()
            if line:
                lines.append(line)
    return "\n".join(lines)


def _cmd_generate(
    count: int,
    seed: int | None,
    output: Path,
    puzzle_filter: PuzzleFilter,
    max_attempts: int,
) -> int:
    try:
        puzzles = generate_puzzles(
            count=count,
            seed=seed,
            puzzle_filter=puzzle_filter,
            max_attempts=max_attempts,
        )
    except (RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    save_puzzles(output, puzzles)
    print(f"Generated {len(puzzles)} puzzle(s) to {output}")
    if puzzles:
        print()
        print("Puzzle 0:")
        print(format_puzzle(puzzles[0], puzzles[0].initial_board))
    return 0


def _cmd_solve(input_path: Path, index: int) -> int:
    puzzle = _load_one(input_path, index)
    solution = solve(puzzle)
    if solution is None:
        print("No solution.")
        return 1
    print("Solution:")
    print(format_board(solution))
    return 0


def _cmd_show(input_path: Path, index: int) -> int:
    puzzle = _load_one(input_path, index)
    metadata = build_metadata(puzzle)
    solution_count = count_solutions(puzzle, limit=2)

    print(f"Puzzle id: {_puzzle_display_id(puzzle, index)}")
    print()
    print("Initial board:")
    print(format_puzzle(puzzle, puzzle.initial_board))

    print()
    print("Solution board:")
    if puzzle.solution is not None:
        print(format_board(puzzle.solution))
    else:
        solution = solve(puzzle)
        print("No solution." if solution is None else format_board(solution))

    print()
    print(f"initialCellCount: {metadata['initialCellCount']}")
    print(f"horizontalConstraintCount: {metadata['horizontalConstraintCount']}")
    print(f"verticalConstraintCount: {metadata['verticalConstraintCount']}")
    print(f"totalHintCount: {metadata['totalHintCount']}")
    print(f"solution count up to 2: {solution_count}")
    return 0


def _cmd_validate(input_path: Path, index: int) -> int:
    puzzle = _load_one(input_path, index)
    initial_violations = validate_board(puzzle, puzzle.initial_board)
    solution_count = count_solutions(puzzle, limit=2)

    print("Initial board:")
    print(format_puzzle(puzzle, puzzle.initial_board))
    print()

    ok = True
    if initial_violations:
        ok = False
        print("Initial board violations:")
        print(_format_violations(initial_violations))
    else:
        print("Initial board is consistent.")

    if puzzle.solution is not None:
        print()
        print("Stored solution:")
        print(format_board(puzzle.solution))
        if is_complete(puzzle, puzzle.solution):
            print("Stored solution is complete.")
        else:
            ok = False
            print("Stored solution is not complete.")

    print()
    print(f"Solution count up to 2: {solution_count}")
    if solution_count != 1:
        ok = False
    return 0 if ok else 1


def _cmd_analyze(
    count: int,
    seed: int | None,
    puzzle_filter: PuzzleFilter,
    max_attempts: int,
) -> int:
    try:
        result = analyze_generation(
            count=count,
            seed=seed,
            puzzle_filter=puzzle_filter,
            max_attempts=max_attempts,
        )
    except (AnalysisError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(format_analysis_result(result))
    return 0


def _load_one(input_path: Path, index: int) -> Puzzle:
    puzzles = load_puzzles(input_path)
    if index < 0 or index >= len(puzzles):
        raise SystemExit(f"Puzzle index {index} is out of range.")
    return puzzles[index]


def _format_violations(violations: list[RuleViolation]) -> str:
    return "\n".join(
        f"- {violation.type.value}: {violation.message} "
        f"at {[(position.row, position.col) for position in violation.positions]}"
        for violation in violations
    )


def _puzzle_display_id(puzzle: Puzzle, index: int) -> str:
    return puzzle.id or f"duo_{index + 1:04d}"


def _add_filter_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--min-initial-cells", type=int, default=0)
    parser.add_argument("--min-total-hints", type=int, default=0)
    parser.add_argument("--min-constraints", type=int, default=0)
    parser.add_argument("--max-attempts", type=int, default=1000)


def _args_to_filter(args: argparse.Namespace) -> PuzzleFilter:
    return PuzzleFilter(
        min_initial_cells=args.min_initial_cells,
        min_total_hints=args.min_total_hints,
        min_constraints=args.min_constraints,
    )


if __name__ == "__main__":
    sys.exit(main())
