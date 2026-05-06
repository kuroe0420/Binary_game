# codex_tango

Tango系の二値ロジックパズルを、Androidアプリへ移植する前に Python で検証するためのプロトタイプ用ディレクトリです。

この段階では Android / Kotlin / Jetpack Compose への統合は行いません。

## 目的

1. 6x6 二値ロジックパズルのルール判定を実装する
2. バックトラックソルバーを実装する
3. 解の個数を数え、一意解を判定できるようにする
4. 完成盤面を生成する
5. 初期セルと `=` / `x` 制約を持つ問題を生成する
6. 生成した問題を JSON に出力する
7. 後続フェーズで Android アプリに移植しやすい形にする

## 想定環境

- Python 3.11 以上
- 標準ライブラリ中心
- テストは pytest 推奨

## ドキュメント

初期依頼文や詳細仕様は `docs/` にまとめています。

- `docs/CODEX_PROMPT.md`
- `docs/SPEC_TANGO_PROTOTYPE.md`
- `docs/RUNBOOK.md`
- `docs/FOLLOWUP_PROMPT_AFTER_IMPLEMENTATION.md`

## 想定する最終構成

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

## 実行例

```bash
python -m tango.cli generate --count 10 --output generated/puzzles.json
python -m tango.cli validate --input generated/puzzles.json --index 0
python -m tango.cli solve --input generated/puzzles.json --index 0
pytest
```
