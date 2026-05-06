# Tango系二値ロジックパズル Pythonプロトタイプ仕様書 v0.1

## 1. 目的

Androidアプリへ実装する前に、Tango系の二値ロジックパズルの以下を Python で検証する。

- ルール判定
- ソルバー
- 一意解チェック
- 問題生成
- JSON出力

この段階では Android / Kotlin / Jetpack Compose は扱わない。

---

## 2. パズル概要

6x6 の盤面に2種類の記号を配置する一人用ロジックパズル。

各マスは以下のいずれか。

| 値 | 意味 |
|---:|---|
| -1 | Empty |
| 0 | A |
| 1 | B |

完成盤面では、各行・各列に A と B が同数入る。  
6x6の場合は各行・各列に A が3個、B が3個となる。

---

## 3. ルール

### 3.1 行の個数制約

6x6の場合、各行には A と B がそれぞれ3個ずつ入る。

未完成盤面では、A または B が4個以上になった時点で違反。

### 3.2 列の個数制約

6x6の場合、各列には A と B がそれぞれ3個ずつ入る。

未完成盤面では、A または B が4個以上になった時点で違反。

### 3.3 横3連続禁止

横方向に同じ記号が3つ連続してはいけない。

```text
A A A  NG
B B B  NG
A A B  OK
A B A  OK
```

空白を含む場合は、その時点では違反にしない。

```text
A A .  OK as partial
```

### 3.4 縦3連続禁止

縦方向に同じ記号が3つ連続してはいけない。

### 3.5 隣接制約

隣接する2マスの間に以下の制約を置ける。

| 値 | 意味 | 表示 |
|---:|---|---|
| 0 | None | 空 |
| 1 | Same | = |
| 2 | Different | x |

#### Same

隣接2マスが同じ記号でなければならない。

```text
A = A  OK
B = B  OK
A = B  NG
```

#### Different

隣接2マスが異なる記号でなければならない。

```text
A x B  OK
B x A  OK
A x A  NG
```

空白を含む場合は、その時点では違反にしない。

---

## 4. データ構造

### 4.1 Puzzle

```python
@dataclass(frozen=True)
class Puzzle:
    size: int
    initial_board: list[list[Cell]]
    horizontal_constraints: list[list[Constraint]]
    vertical_constraints: list[list[Constraint]]
    solution: list[list[Cell]] | None = None
```

### 4.2 サイズ

6x6の場合:

```text
initial_board          : 6 x 6
solution               : 6 x 6
horizontal_constraints : 6 x 5
vertical_constraints   : 5 x 6
```

`horizontal_constraints[row][col]` は、以下の2マスの間の制約。

```text
board[row][col] と board[row][col + 1]
```

`vertical_constraints[row][col]` は、以下の2マスの間の制約。

```text
board[row][col] と board[row + 1][col]
```

---

## 5. バリデーション仕様

### 5.1 validate_board

```python
def validate_board(puzzle: Puzzle, board: list[list[Cell]]) -> list[RuleViolation]:
    ...
```

現在の盤面に対するルール違反を返す。

### 5.2 違反種別

最低限、以下を区別する。

```python
class ViolationType(Enum):
    TOO_MANY_IN_ROW = "too_many_in_row"
    TOO_MANY_IN_COLUMN = "too_many_in_column"
    THREE_CONSECUTIVE_ROW = "three_consecutive_row"
    THREE_CONSECUTIVE_COLUMN = "three_consecutive_column"
    SAME_CONSTRAINT = "same_constraint"
    DIFFERENT_CONSTRAINT = "different_constraint"
    LOCKED_CELL_MODIFIED = "locked_cell_modified"
```

### 5.3 RuleViolation

```python
@dataclass(frozen=True)
class RuleViolation:
    type: ViolationType
    positions: tuple[Position, ...]
    message: str
```

### 5.4 部分盤面の扱い

空白を含む箇所は、明確な違反でない限り違反にしない。

例:

```text
A A .  はまだ違反ではない
A A A  は違反
```

---

## 6. 完成判定

```python
def is_complete(puzzle: Puzzle, board: list[list[Cell]]) -> bool:
    ...
```

以下をすべて満たす場合に true。

1. 空白セルがない
2. ルール違反がない
3. 各行に A と B が同数
4. 各列に A と B が同数
5. すべての隣接制約を満たす

---

## 7. ソルバー仕様

### 7.1 solve

```python
def solve(puzzle: Puzzle) -> list[list[Cell]] | None:
    ...
```

1つの解を返す。解がなければ `None`。

### 7.2 count_solutions

```python
def count_solutions(puzzle: Puzzle, limit: int = 2) -> int:
    ...
```

解の個数を返す。

ただし、`limit` 個見つかったら探索を打ち切る。  
生成器では `limit=2` を使う。

意味:

| 返り値 | 意味 |
|---:|---|
| 0 | 解なし |
| 1 | 一意解 |
| 2以上 | 複数解 |

### 7.3 探索方針

- バックトラック
- 初期配置セルは変更しない
- 空セルの中から候補数が少ないセルを優先する
- 候補が0個のセルがある場合は即バックトラック
- 各手ごとに部分盤面の整合性を確認する

---

## 8. 完成盤面生成仕様

```python
def generate_solution(size: int = 6, rng: random.Random | None = None) -> list[list[Cell]]:
    ...
```

### 要件

- size は偶数
- 6x6を主対象
- 各行・各列で A/B が同数
- 横・縦に3連続なし
- 生成失敗時はリトライ

### 推奨アルゴリズム

1. 有効な行パターンを全列挙する
2. 行をランダム順に選ぶ
3. 行を追加するたびに列方向の個数制約と3連続禁止を確認する
4. 6行そろったら列も A/B 同数か確認する

---

## 9. 問題生成仕様

```python
def generate_puzzle(size: int = 6, rng: random.Random | None = None, max_attempts: int = 1000) -> Puzzle:
    ...
```

### 9.1 生成手順

1. 完成盤面を生成する
2. 完成盤面から初期セル候補を作る
3. 完成盤面から隣接制約候補を作る
4. ヒントをランダムに追加する
5. ソルバーで一意解か確認する
6. 一意解でなければヒントを増やす
7. 一意解になったら、削れるヒントを削る
8. 最終的に `count_solutions(puzzle, limit=2) == 1` なら採用

### 9.2 ヒント

ヒントは以下の2種類。

- 初期セル
- 隣接制約

### 9.3 初期セル

`initial_board[row][col]` に A または B が入っている場合、プレイヤーは変更できない。

空白は -1。

### 9.4 隣接制約

完成盤面をもとに生成する。

隣接2セルが同じなら `SAME` 候補。  
隣接2セルが異なるなら `DIFFERENT` 候補。

---

## 10. JSON仕様

### 10.1 単一問題

```json
{
  "size": 6,
  "initialBoard": [
    [-1, -1, 0, -1, -1, 1],
    [-1, -1, -1, -1, -1, -1],
    [1, -1, -1, -1, -1, -1],
    [-1, -1, -1, 0, -1, -1],
    [-1, -1, -1, -1, -1, -1],
    [0, -1, -1, -1, 1, -1]
  ],
  "horizontalConstraints": [
    [0, 1, 0, 2, 0],
    [0, 0, 0, 0, 0],
    [2, 0, 0, 1, 0],
    [0, 0, 1, 0, 0],
    [0, 2, 0, 0, 0],
    [0, 0, 0, 0, 1]
  ],
  "verticalConstraints": [
    [0, 0, 2, 0, 0, 0],
    [1, 0, 0, 0, 2, 0],
    [0, 0, 0, 1, 0, 0],
    [0, 2, 0, 0, 0, 0],
    [0, 0, 1, 0, 0, 0]
  ],
  "solution": [
    [0, 1, 0, 1, 0, 1],
    [1, 0, 1, 0, 1, 0],
    [1, 0, 0, 1, 0, 1],
    [0, 1, 1, 0, 1, 0],
    [1, 0, 1, 0, 0, 1],
    [0, 1, 0, 1, 1, 0]
  ]
}
```

### 10.2 複数問題

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

### 10.3 Android移植時の対応

Python側の値は Kotlin 側で以下に対応させる予定。

| JSON値 | Kotlin側 |
|---:|---|
| -1 | TangoCell.Empty |
| 0 | TangoCell.A |
| 1 | TangoCell.B |
| 0 | TangoConstraint.None |
| 1 | TangoConstraint.Same |
| 2 | TangoConstraint.Different |

---

## 11. CLI仕様

### 11.1 generate

```bash
python -m tango.cli generate --count 10 --seed 42 --output generated/puzzles.json
```

指定個数の問題を生成して保存する。

### 11.2 solve

```bash
python -m tango.cli solve --input generated/puzzles.json --index 0
```

指定問題を解いて表示する。

### 11.3 validate

```bash
python -m tango.cli validate --input generated/puzzles.json --index 0
```

指定問題の初期盤面・制約・解の整合性を検証する。

---

## 12. 非対象

v0.1では以下を対象外とする。

- Android実装
- Kotlin実装
- GUI
- 難易度の厳密評価
- ヒント機能
- プレイ履歴保存
- アニメーション
- 太陽/月アイコン
- 既存 Android アプリへのマージ
