# Codex実装依頼プロンプト

以下の仕様に従って、Tango系の二値ロジックパズルを Python で検証するためのプロトタイプを実装してください。

## 重要な前提

- このディレクトリは空の新規プロジェクトとして扱ってください。
- Android / Kotlin / Jetpack Compose への実装は行わないでください。
- 目的は、後で Android アプリへ移植する前に、パズルロジック・ソルバー・問題生成を検証することです。
- まず正確性を優先し、過度な最適化は不要です。
- 外部依存は最小限にしてください。
- テストは pytest を使用してください。
- Python 3.11 以上を想定してください。

## 実装対象

以下の構成で実装してください。

```text
codex_tango/
├ README.md
├ docs/
│ ├ CODEX_PROMPT.md
│ ├ SPEC_TANGO_PROTOTYPE.md
│ ├ RUNBOOK.md
│ └ FOLLOWUP_PROMPT_AFTER_IMPLEMENTATION.md
├ tango/
│ ├ __init__.py
│ ├ model.py
│ ├ rules.py
│ ├ solver.py
│ ├ generator.py
│ ├ json_io.py
│ └ cli.py
├ tests/
│ ├ test_rules.py
│ ├ test_solver.py
│ └ test_generator.py
├ generated/
│ └ .gitkeep
├ .gitignore
└ pyproject.toml
```

## 作るもの

### 1. データモデル

`model.py` に以下を実装してください。

- `Cell`
  - `EMPTY = -1`
  - `A = 0`
  - `B = 1`
- `Constraint`
  - `NONE = 0`
  - `SAME = 1`
  - `DIFFERENT = 2`
- `Position`
  - `row: int`
  - `col: int`
- `Puzzle`
  - `size: int`
  - ` initial_board: list[list[Cell]]`
  - `horizontal_constraints: list[list[Constraint]]`
  - `vertical_constraints: list[list[Constraint]]`
  - `solution: list[list[Cell]] | None = None`

注: PythonのEnumを使ってもよいですが、JSONとの相互変換が簡単になるように、int値への変換が明確な設計にしてください。

### 2. ルール判定

`rules.py` に以下を実装してください。

- `validate_board(puzzle: Puzzle, board: list[list[Cell]]) -> list[RuleViolation]`
- `is_complete(puzzle: Puzzle, board: list[list[Cell]]) -> bool`
- `is_consistent_partial(puzzle: Puzzle, board: list[list[Cell]]) -> bool`
- `get_candidates(puzzle: Puzzle, board: list[list[Cell]], row: int, col: int) -> list[Cell]`

違反種別は最低限以下を区別してください。

- `too_many_in_row`
- `too_many_in_column`
- `three_consecutive_row`
- `three_consecutive_column`
- `same_constraint`
- `different_constraint`
- `locked_cell_modified`

### 3. ソルバー

`solver.py` に以下を実装してください。

- `solve(puzzle: Puzzle) -> list[list[Cell]] | None`
- `count_solutions(puzzle: Puzzle, limit: int = 2) -> int`
- `find_solutions(puzzle: Puzzle, limit: int = 2) -> list[list[list[Cell]]]`

要件:

- バックトラックでよい
- `limit=2` の場合は2解見つかった時点で打ち切る
- 空セルのうち候補数が少ないセルを優先して探索する
- 初期配置セルは固定する
- 6x6で実用的な速度で動くこと

### 4. 完成盤面生成

`generator.py` に以下を実装してください。

- `generate_solution(size: int = 6, rng: random.Random | None = None) -> list[list[Cell]]`

要件:

- 各行・各列に A と B が同数
- 横・縦に3連続なし
- 6x6を主対象にする
- sizeは偶数のみサポートでよい
- 失敗した場合はリトライする

### 5. 問題生成

`generator.py` に以下も実装してください。

- `generate_puzzle(size: int = 6, rng: random.Random | None = None, max_attempts: int = 1000) -> Puzzle`
- `generate_puzzles(count: int, seed: int | None = None) -> list[Puzzle]`

要件:

- 完成盤面から初期セルと制約を選ぶ
- horizontal_constraints / vertical_constraints を生成する
- `count_solutions(puzzle, limit=2) == 1` になる問題のみ採用する
- 生成後に、不要なヒントを削れるだけ削る処理を入れる
- 最初は難易度評価は簡易でよい
- 生成失敗時は別の完成盤面でリトライする

### 6. JSON入出力

`json_io.py` に以下を実装してください。

- `puzzle_to_dict(puzzle: Puzzle) -> dict`
- `puzzle_from_dict(data: dict) -> Puzzle`
- `save_puzzles(path: str | Path, puzzles: list[Puzzle]) -> None`
- `load_puzzles(path: str | Path) -> list[Puzzle]`

JSON形式は以下にしてください。

```json
{
  "size": 6,
  "initialBoard": [[-1, -1, 0, -1, -1, 1]],
  "horizontalConstraints": [[0, 1, 0, 2, 0]],
  "verticalConstraints": [[0, 0, 2, 0, 0, 0]],
  "solution": [[0, 1, 0, 1, 0, 1]]
}
```

複数問題保存時は以下。

```json
{
  "puzzles": [
    {
      "size": 6,
      "initialBoard": [],
      "horizontalConstraints": [],
      "verticalConstraints": [],
      "solution": []
    }
  ]
}
```

### 7. CLI

`cli.py` に最低限以下を実装してください。

```bash
python -m tango.cli generate --count 10 --seed 1 --output generated/puzzles.json
python -m tango.cli solve --input generated/puzzles.json --index 0
python -m tango.cli validate --input generated/puzzles.json --index 0
```

出力では、盤面を人間が読めるように表示してください。

表示例:

```text
. . A . . B
. . . . . .
B . . . . .
. . . A . .
. . . . . .
A . . . B .
```

制約も簡易表示できると望ましいです。

### 8. テスト

pytestで以下をテストしてください。

#### test_rules.py

- 行にAが4個あると違反
- 列にBが4個あると違反
- 横3連続を検出
- 縦3連続を検出
- SAME制約違反を検出
- DIFFERENT制約違反を検出
- 完成盤面を complete と判定

#### test_solver.py

- 解ける固定問題で `count_solutions == 1`
- 複数解になり得る空問題で `count_solutions >= 2`
- 解なし問題で `count_solutions == 0`

#### test_generator.py

- `generate_solution()` がルールを満たす
- `generate_puzzle()` が一意解を持つ
- JSON保存・読み込み後も `count_solutions == 1`

## 実装上の注意

- 6x6を最優先で動かしてください。
- 盤面サイズは偶数のみサポートで構いません。
- ソルバー・生成器はまず正確性優先です。
- ログやprintはCLI以外では最小限にしてください。
- 型ヒントを付けてください。
- docstringを主要関数に付けてください。
- テストが通る状態で完了してください。

## 完了条件

以下が成功すること。

```bash
python -m tango.cli generate --count 5 --seed 42 --output generated/puzzles.json
python -m tango.cli validate --input generated/puzzles.json --index 0
python -m tango.cli solve --input generated/puzzles.json --index 0
pytest
```

## 非対象

以下は実装しないでください。

- Android実装
- Kotlin実装
- GUI
- Webアプリ
- 画像・アイコン作成
- ストア配布
- LinkedIn TangoのUI再現
- LinkedIn Tangoの問題データコピー
