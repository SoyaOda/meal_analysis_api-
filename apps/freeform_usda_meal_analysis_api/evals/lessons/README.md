# Lessons Log

失敗・成功の学習を時系列で残す。

必須ファイル名規約:
- `YYYYMMDD_<slug>.md`（`scripts/build_lessons_index.py` がこの規約に基づき `INDEX.md` を生成する。違反ファイルはビルドを失敗させる）
- 本文の先頭行は必ず `# ...` の H1 見出しにする（`INDEX.md` の finding 列にそのまま転記される）

テンプレート:
- `apps/freeform_usda_meal_analysis_api/evals/templates/lesson_template.md`

運用ルール:
- 「効いた要素」と「効かなかった要素」を分けて記録する。
- 過学習防止チェック（prompt leak / holdout / full50 / coverage）を必ず埋める。

## `INDEX.md`（自動生成・手編集禁止）
- `INDEX.md` はこのディレクトリの lesson 一覧（date / lesson リンク / finding=H1）を集約した索引で、**自動生成ファイル**。手で編集しない。
- 再生成: `PYTHONPATH=/Users/odasoya/meal_analysis_api_2 python -m apps.freeform_usda_meal_analysis_api.scripts.build_lessons_index`
- 鮮度検証のみ（再生成しない）: 上記コマンドに `--check` を付ける。
- `pdca_session_bootstrap.py` はセッション開始時にこの鮮度を検証し、古ければ自動で再生成する。

## `negative_results.json` との関係
- lesson = 個々の実験の詳細な evidence（設計・結果・過学習防止チェック・promoted prompt の有無）。
- `evals/knowledge/negative_results.json` = 棄却済み仮説（do-not-retry）の**結論だけをまとめた台帳**（`id` / `scope` / `claim` / `verdict` / `evidence`(lesson等へのパス) / `reopen_when`）。
- 新しい実験・調査を始める前は `scripts/check_prior_art.py --query "<keyword>"` で両方を横断照合し、ヒットした lesson を読んでから進めること（read-before-write）。
