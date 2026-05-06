# 引き継ぎメモ

## 現在の状態

- Tango 系二値ロジックパズルの Python プロトタイプは実装済み。
- コアモジュール、CLI、JSON 入出力、生成器、ソルバー、pytest テストが揃っている。
- 初期依頼文や仕様書などのドキュメントは `docs/` 配下に整理済み。
- 生成された問題 JSON は `.gitignore` により git 管理外。
- Python パッケージはリポジトリ直下の `.venv` で管理する方針。

## 実装済み範囲

- データモデル: `tango/model.py`
- ルール判定: `tango/rules.py`
- バックトラックソルバーと解数カウント: `tango/solver.py`
- 完成盤面生成と一意解問題生成: `tango/generator.py`
- 生成品質分析: `tango/analyze.py`
- JSON シリアライズと読み込み: `tango/json_io.py`
- CLI コマンド: `tango/cli.py`
- テスト: `tests/test_rules.py`, `tests/test_solver.py`, `tests/test_generator.py`, `tests/test_analyze.py`

## 確認済みコマンド

リポジトリルートから実行する。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
$env:PIP_CACHE_DIR = Join-Path (Get-Location) ".pip-cache"
python -m pip install -r requirements-dev.txt
python -m tango.cli generate --count 5 --seed 42 --output generated/puzzles.json
python -m tango.cli validate --input generated/puzzles.json --index 0
python -m tango.cli solve --input generated/puzzles.json --index 0
python -m tango.cli analyze --count 100 --seed 42
python -m pytest
```

直近の確認結果:

- CLI `generate` は成功し、`generated/puzzles.json` を作成した。
- CLI `validate` は `Solution count up to 2: 1` で成功した。
- CLI `solve` は有効な解を表示した。
- CLI `analyze --count 100 --seed 42` は `generated: 100`, `unique: 100`, `failed: 0` で成功した。
- `pytest` は `15 passed`。

## 既知の注意点

- Windows 環境で pytest キャッシュ書き込み警告を避けるため、`pyproject.toml` で pytest cache provider を無効化している。
- `generated/*.json` は git 管理外なので、生成済み問題ファイルは差分に出ない。
- `.venv/` と `.pip-cache/` は git 管理外なので、ローカルの依存パッケージ状態はコミットされない。
- 生成器は難易度調整や最適化よりも正確性を優先している。
- 現在の主対象は 6x6。盤面サイズは偶数を前提としている。

## 参照入口

- プロジェクト概要: `README.md`
- 元の実装依頼文: `docs/CODEX_PROMPT.md`
- 詳細仕様: `docs/SPEC_TANGO_PROTOTYPE.md`
- 手動確認手順: `docs/RUNBOOK.md`
- 実装後フォローアップ用プロンプト: `docs/FOLLOWUP_PROMPT_AFTER_IMPLEMENTATION.md`

## 次に検討する作業

- 生成問題の難易度とヒント数を確認する。
- 100 問を超える大きめのバッチ生成で安定性を確認する。
- Android assets 向けの JSON 形式をこのまま確定してよいか判断する。
- 共有ツールとして使う場合は、不正な JSON 入力に対するバリデーションを強化する。
