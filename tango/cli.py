"""Command line interface for the Tango prototype."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tango.analyze import AnalysisError, analyze_generation, format_analysis_result
from tango.difficulty import (
    DIFFICULTY_ORDER,
    DIFFICULTY_PRESETS,
    get_difficulty_preset,
    make_puzzle_filter,
)
from tango.generator import generate_puzzles
from tango.json_io import load_puzzles, save_puzzles
from tango.model import Board, Cell, Constraint, Puzzle
from tango.quality import HintCounts, PuzzleFilter, build_metadata, count_hints
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

    bundle_parser = subparsers.add_parser(
        "generate-bundle",
        help="Generate easy, normal, and hard puzzle JSON files.",
    )
    bundle_parser.add_argument("--count-per-difficulty", type=int, required=True)
    bundle_parser.add_argument("--seed", type=int)
    bundle_parser.add_argument("--output-dir", type=Path, required=True)
    bundle_parser.add_argument("--max-attempts", type=int, default=1000)

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
            _args_to_difficulty_label(args),
            args.max_attempts,
        )
    if args.command == "generate-bundle":
        return _cmd_generate_bundle(
            args.count_per_difficulty,
            args.seed,
            args.output_dir,
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
            args.difficulty,
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
    difficulty: str,
    max_attempts: int,
) -> int:
    try:
        puzzles = generate_puzzles(
            count=count,
            seed=seed,
            puzzle_filter=puzzle_filter,
            max_attempts=max_attempts,
            progress_callback=_print_progress,
        )
    except (RuntimeError, ValueError) as exc:
        context = _format_failure_context(difficulty, puzzle_filter)
        print(f"ERROR: {context}: {exc}", file=sys.stderr)
        return 1
    save_puzzles(output, puzzles, difficulty=difficulty)
    print(f"Generated {len(puzzles)} puzzle(s) to {output}")
    if puzzles:
        print()
        print("Puzzle 0:")
        print(format_puzzle(puzzles[0], puzzles[0].initial_board))
    return 0


def _cmd_generate_bundle(
    count_per_difficulty: int,
    seed: int | None,
    output_dir: Path,
    max_attempts: int,
) -> int:
    if count_per_difficulty < 0:
        print("ERROR: count-per-difficulty must not be negative.", file=sys.stderr)
        return 1

    for offset, difficulty in enumerate(DIFFICULTY_ORDER):
        current_seed = None if seed is None else seed + offset
        output = output_dir / f"duo_logic_{difficulty}_{count_per_difficulty}.json"
        puzzle_filter = get_difficulty_preset(difficulty).to_filter()
        try:
            puzzles = generate_puzzles(
                count=count_per_difficulty,
                seed=current_seed,
                puzzle_filter=puzzle_filter,
                max_attempts=max_attempts,
                progress_callback=(
                    lambda current, total, name=difficulty: _print_progress(
                        current,
                        total,
                        prefix=f"{name} ",
                    )
                ),
            )
        except (RuntimeError, ValueError) as exc:
            context = _format_failure_context(difficulty, puzzle_filter)
            print(f"ERROR: failed to generate {context}: {exc}", file=sys.stderr)
            return 1

        save_puzzles(output, puzzles, difficulty=difficulty)
        print(
            f"{difficulty}: generated {len(puzzles)} puzzle(s) to {output} "
            f"(seed={current_seed})"
        )
        if puzzles:
            print(_format_hint_summary(puzzles))
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
    print(f"difficulty: {metadata['difficulty']}")
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
    difficulty: str | None,
    max_attempts: int,
) -> int:
    try:
        result = analyze_generation(
            count=count,
            seed=seed,
            puzzle_filter=puzzle_filter,
            max_attempts=max_attempts,
            progress_callback=_print_progress,
        )
    except (AnalysisError, ValueError) as exc:
        context = _format_failure_context(difficulty, puzzle_filter)
        print(f"ERROR: {context}: {exc}", file=sys.stderr)
        return 1
    print(format_analysis_result(result, difficulty=difficulty))
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
    parser.add_argument("--difficulty", choices=DIFFICULTY_PRESETS.keys())
    parser.add_argument("--min-initial-cells", type=int)
    parser.add_argument("--min-total-hints", type=int)
    parser.add_argument("--min-constraints", type=int)
    parser.add_argument("--max-attempts", type=int, default=1000)


def _args_to_filter(args: argparse.Namespace) -> PuzzleFilter:
    return make_puzzle_filter(
        difficulty=args.difficulty,
        min_initial_cells=args.min_initial_cells,
        min_total_hints=args.min_total_hints,
        min_constraints=args.min_constraints,
    )


def _args_to_difficulty_label(args: argparse.Namespace) -> str:
    return args.difficulty if args.difficulty is not None else "custom"


def _print_progress(current: int, total: int, prefix: str = "") -> None:
    print(f"{prefix}generated {current}/{total}", flush=True)


def _format_failure_context(
    difficulty: str | None,
    puzzle_filter: PuzzleFilter,
) -> str:
    difficulty_label = difficulty if difficulty is not None else "custom"
    return f"difficulty={difficulty_label}, filter=({puzzle_filter.describe()})"


def _format_hint_summary(puzzles: list[Puzzle]) -> str:
    counts = [count_hints(puzzle) for puzzle in puzzles]
    return "\n".join(
        [
            f"  initial_cells min/avg/max: {_format_count_summary(counts, 'initial_cells')}",
            "  horizontal_constraints min/avg/max: "
            f"{_format_count_summary(counts, 'horizontal_constraints')}",
            "  vertical_constraints min/avg/max: "
            f"{_format_count_summary(counts, 'vertical_constraints')}",
            f"  total_hints min/avg/max: {_format_count_summary(counts, 'total_hints')}",
        ]
    )


def _format_count_summary(counts: list[HintCounts], name: str) -> str:
    values = [getattr(count, name) for count in counts]
    return f"{min(values)}/{sum(values) / len(values):.2f}/{max(values)}"


if __name__ == "__main__":
    sys.exit(main())
