"""Command line interface for the Tango prototype."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tango.analyze import AnalysisError, analyze_generation, format_analysis_result
from tango.generator import generate_puzzles
from tango.json_io import load_puzzles, save_puzzles
from tango.model import Board, Cell, Constraint, Puzzle
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

    solve_parser = subparsers.add_parser("solve", help="Solve a saved puzzle.")
    solve_parser.add_argument("--input", type=Path, required=True)
    solve_parser.add_argument("--index", type=int, default=0)

    validate_parser = subparsers.add_parser("validate", help="Validate a saved puzzle.")
    validate_parser.add_argument("--input", type=Path, required=True)
    validate_parser.add_argument("--index", type=int, default=0)

    analyze_parser = subparsers.add_parser(
        "analyze", help="Generate puzzles and summarize generation quality."
    )
    analyze_parser.add_argument("--count", type=int, required=True)
    analyze_parser.add_argument("--seed", type=int)

    args = parser.parse_args(argv)
    if args.command == "generate":
        return _cmd_generate(args.count, args.seed, args.output)
    if args.command == "solve":
        return _cmd_solve(args.input, args.index)
    if args.command == "validate":
        return _cmd_validate(args.input, args.index)
    if args.command == "analyze":
        return _cmd_analyze(args.count, args.seed)
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


def _cmd_generate(count: int, seed: int | None, output: Path) -> int:
    puzzles = generate_puzzles(count=count, seed=seed)
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


def _cmd_analyze(count: int, seed: int | None) -> int:
    try:
        result = analyze_generation(count=count, seed=seed)
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


if __name__ == "__main__":
    sys.exit(main())
