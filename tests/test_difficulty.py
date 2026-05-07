from tango.difficulty import get_difficulty_preset, make_puzzle_filter


def test_difficulty_preset_builds_puzzle_filter() -> None:
    puzzle_filter = get_difficulty_preset("easy").to_filter()

    assert puzzle_filter.min_initial_cells == 6
    assert puzzle_filter.min_total_hints == 13
    assert puzzle_filter.min_constraints == 5


def test_difficulty_filter_accepts_explicit_overrides() -> None:
    puzzle_filter = make_puzzle_filter("easy", min_total_hints=14)

    assert puzzle_filter.min_initial_cells == 6
    assert puzzle_filter.min_total_hints == 14
    assert puzzle_filter.min_constraints == 5


def test_filter_without_difficulty_keeps_legacy_zero_thresholds() -> None:
    puzzle_filter = make_puzzle_filter()

    assert puzzle_filter.min_initial_cells == 0
    assert puzzle_filter.min_total_hints == 0
    assert puzzle_filter.min_constraints == 0
