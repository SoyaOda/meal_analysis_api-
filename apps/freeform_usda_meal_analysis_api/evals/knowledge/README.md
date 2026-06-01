# Knowledge Store

PDCA実験の構造化ログを蓄積する場所。

- 生成コマンド:
  - `python -m apps.freeform_usda_meal_analysis_api.scripts.export_pdca_knowledge`
  - `python -m apps.freeform_usda_meal_analysis_api.scripts.pdca_session_bootstrap --api-url <api-url>`
- 出力:
  - `experiment_log.jsonl`（1 candidate/run = 1行）
  - `session_bootstrap_latest.md`（新規セッション開始時の要約）

用途:
- 「何が効いたか / 効かなかったか」をモデル横断・時系列で再集計する。
- promptや温度、reasoning設定と指標の相関を後から分析する。
- セッション開始時に baseline / latest lessons / remote config を同じ形式で確認する。
