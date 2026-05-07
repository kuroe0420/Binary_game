"""Difficulty presets for generated Tango puzzles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from tango.quality import PuzzleFilter

DifficultyName = Literal["easy", "normal", "hard"]


@dataclass(frozen=True)
class DifficultyPreset:
    """Named minimum quality thresholds for puzzle generation."""

    name: DifficultyName
    min_initial_cells: int
    min_total_hints: int
    min_constraints: int

    def to_filter(self) -> PuzzleFilter:
        """Convert this preset into a PuzzleFilter."""

        return PuzzleFilter(
            min_initial_cells=self.min_initial_cells,
            min_total_hints=self.min_total_hints,
            min_constraints=self.min_constraints,
        )


DIFFICULTY_PRESETS: dict[DifficultyName, DifficultyPreset] = {
    "easy": DifficultyPreset(
        name="easy",
        min_initial_cells=6,
        min_total_hints=13,
        min_constraints=5,
    ),
    "normal": DifficultyPreset(
        name="normal",
        min_initial_cells=4,
        min_total_hints=10,
        min_constraints=4,
    ),
    "hard": DifficultyPreset(
        name="hard",
        min_initial_cells=2,
        min_total_hints=7,
        min_constraints=3,
    ),
}

DIFFICULTY_ORDER: tuple[DifficultyName, ...] = ("easy", "normal", "hard")


def get_difficulty_preset(name: str) -> DifficultyPreset:
    """Return the preset for a supported difficulty name."""

    normalized = name.lower()
    if normalized not in DIFFICULTY_PRESETS:
        supported = ", ".join(DIFFICULTY_ORDER)
        raise ValueError(f"Unsupported difficulty '{name}'. Expected one of: {supported}.")
    return DIFFICULTY_PRESETS[normalized]  # type: ignore[index]


def make_puzzle_filter(
    difficulty: str | None = None,
    min_initial_cells: int | None = None,
    min_total_hints: int | None = None,
    min_constraints: int | None = None,
) -> PuzzleFilter:
    """Build a PuzzleFilter from an optional preset plus explicit overrides."""

    base = (
        get_difficulty_preset(difficulty).to_filter()
        if difficulty is not None
        else PuzzleFilter()
    )
    return PuzzleFilter(
        min_initial_cells=(
            base.min_initial_cells
            if min_initial_cells is None
            else min_initial_cells
        ),
        min_total_hints=(
            base.min_total_hints if min_total_hints is None else min_total_hints
        ),
        min_constraints=(
            base.min_constraints if min_constraints is None else min_constraints
        ),
    )
