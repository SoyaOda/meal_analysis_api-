# scripts/ — PDCA評価スクリプトのルール（path-scoped）

このディレクトリの評価スクリプト（`run_pdca_batch_eval.py` / `run_pdca_repeated_eval.py` / `merge_pdca_runs.py` / `pdca_session_bootstrap.py` / `export_pdca_knowledge.py` / `sync_openrouter_candidates.py`）を編集するときは次を厳守する。

- **CLI後方互換を壊さない**: 既存の引数（`--config` / `--api-url` / `--limit` / `--start-index` / `--end-index` / `--image-index-file` / `--required-image-count` / `--no-use-vlm-cache` 等）の意味・デフォルトを変えない。新機能は新しいオプトインのフラグで追加し、未指定時は従来挙動を維持する。
- **出力スキーマの後方互換**: `evals/runs/<timestamp>/summary.json` / `raw_results.json` の既存キーを削除・改名しない（過去runとの比較・`merge_pdca_runs` が依存する）。新指標は追加キーとして足す。
- **Fallback禁止**: 失敗は握りつぶさず明示的にエラーで止める（カバレッジ不足・config不一致・parse失敗を成功扱いにしない）。
- 変更後は `python -m py_compile <file>` で構文確認し、`apps/freeform_usda_meal_analysis_api/tests/` のテストを実行する。
- 評価ロジック（指標計算・ゲート判定）を変えたら `tests/test_pdca_eval_logic.py` にケースを追加する。

詳細は `apps/freeform_usda_meal_analysis_api/AGENTS.md` を参照。
