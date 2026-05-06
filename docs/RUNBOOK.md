# 実行手順

## 1. ディレクトリへ移動

```powershell
cd E:\Users\User1st\Documents\3_Programming_study\codex\codex_tango
```

## 2. Codexに依頼

仕様・依頼文は `docs/` 配下に整理済み。

- README.md
- docs/CODEX_PROMPT.md
- docs/SPEC_TANGO_PROTOTYPE.md

依頼文:

```text
docs/CODEX_PROMPT.md と docs/SPEC_TANGO_PROTOTYPE.md を読んで、仕様通りに Python プロトタイプを実装してください。
実装後、pytest と CLI の動作確認まで行ってください。
```

## 3. 実装後の確認コマンド

```powershell
python -m tango.cli generate --count 5 --seed 42 --output generated/puzzles.json
python -m tango.cli validate --input generated/puzzles.json --index 0
python -m tango.cli solve --input generated/puzzles.json --index 0
pytest
```

## 4. 確認観点

最低限、以下を確認する。

```text
- generated/puzzles.json が生成される
- 各問題が count_solutions == 1 になる
- validate でエラーが出ない
- solve で解が表示される
- pytest が成功する
```

## 5. Android移植前に見るべき点

```text
- JSON形式がKotlinで読み込みやすいか
- 制約数が多すぎて簡単すぎないか
- 制約数が少なすぎて難しすぎないか
- 生成時間が許容範囲か
- 100問程度を安定生成できるか
```

## 6. 次フェーズ

Pythonで十分に検証できたら、次は以下に進む。

```text
1. JSONをAndroid assetsに配置
2. Kotlin側のデータクラスを作成
3. JSON読み込み
4. 盤面UI
5. プレイ状態管理
6. 完成判定
```
