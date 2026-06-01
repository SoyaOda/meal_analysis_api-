# Lesson: Local OpenRouter credential failure

- Date: 2026-02-24
- Run context: local API (`http://localhost:8006`) on `apps/freeform_usda_meal_analysis_api`

## What happened
- local API runでOpenRouter呼び出しが `401 User not found`。
- Circuit Breaker がOPENになり、後続リクエストも連鎖失敗。
- その結果、ローカルPDCA runは `success_count=0` になった。

## Root cause (likely)
- ローカル環境の `OPENROUTER_API_KEY` が無効、または別プロジェクトのキー。

## Action taken
- 評価先をCloud Run本番APIへ切り替えてPDCAを継続。
- `run_pdca_batch_eval.py` に進捗ログを追加し、長時間runを監視可能にした。

## Next action
- ローカルでOpenRouter評価を行う場合は、有効キーを再設定して再検証する。
