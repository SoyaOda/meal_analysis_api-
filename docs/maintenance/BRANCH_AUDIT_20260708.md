# ブランチ棚卸しレポート（2026-07-08）

> **⚠️ 削除はユーザー明示指示があるまで実行しない（report-only）。**
> 本レポートは現況の可視化のみを目的とし、削除コマンドはすべてコメントアウトで提示する。

## 1. 現状サマリ

- ローカルブランチ総数: **59**（`git for-each-ref --format='%(refname:short)' refs/heads | wc -l`）
- `main` の最終コミット日: **2025-12-07**（`feat: Add debug logging for hybrid search pipeline`）
- 実トランクは `docs/mozu-dataset-inventory-e13-uiux-handoff`（現行チェックアウト中のブランチ）で、`main` から **122 コミット先行**（`git rev-list --count main..docs/mozu-dataset-inventory-e13-uiux-handoff`）。
- `main` は開発OS再設計（mozu 期以降）の実運用トランクとしては事実上凍結されており、実質的な最新状態は現行ブランチが保持している。

採取コマンド:
```
git for-each-ref --sort=-committerdate --format='%(committerdate:short) %(refname:short)' refs/heads
git branch --no-merged main
git branch --merged main
```

## 2. KEEP（削除禁止）

| ブランチ | 最終コミット | 理由 |
|---|---|---|
| `docs/mozu-dataset-inventory-e13-uiux-handoff` | 2026-07-07 | 現行チェックアウト中の実トランク（main に対し122コミット先行） |
| `main` | 2025-12-07 | リポジトリの正式トランク（デフォルトブランチ） |
| `feature/mozu-api` | 2026-06-06 | mozu 期の API 開発ブランチ |
| `feature/deep-review-improvements` | 2026-06-03 | mozu 期の DEEP_REVIEW 改善ブランチ |
| `feature/config-manager-refactoring` | 2026-06-01 | mozu 期の ConfigManager リファクタリングブランチ |

## 3. 削除候補カテゴリ

`--no-merged main` / `--merged main` の判定結果と、コミットメッセージ・作成時期から下記6カテゴリに分類。KEEP の5本を除く**54本**全てが対象。

### A. 旧 deploy 系（9本）

| ブランチ | 最終コミット | 判定理由 |
|---|---|---|
| `v3_deploy` | 2025-12-06 | Cloud Run v3/v2 URL をデモHTMLに追加した旧デプロイ検証ブランチ。未マージ |
| `freeform_usda_meal_analysis_deploy` | 2025-11-12 | `.env` 運用整理のみの旧デプロイ作業ブランチ。マージ済み |
| `feature/cloud-run-phase1-implementation` | 2025-11-12 | Cloud Run Phase1 実装の作業ブランチ（テストスクリプト追加のみ）。未マージ |
| `query_api_deploy` | 2025-09-21 | Word Query API v2.1 のデプロイ検証ブランチ。未マージ |
| `meal_analysis_api_deploy2` | 2025-09-14 | Meal Analysis API v2.0 Clean Release デプロイブランチ。マージ済み |
| `meal_analysis_api_deploy` | 2025-09-14 | Meal Analysis API v2.0 デプロイ README 追加ブランチ。マージ済み |
| `api_deploy3` | 2025-09-12 | Model ID外部指定機能のデプロイ検証ブランチ。未マージ |
| `api_deploy2` | 2025-08-31 | 本番デプロイドキュメント更新ブランチ。未マージ |
| `api_deploy` | 2025-08-29 | Cloud Run API デプロイ初期検証ブランチ。未マージ |

### B. elasticsearch 期（2025-06〜09、11本）

| ブランチ | 最終コミット | 判定理由 |
|---|---|---|
| `qwen2.5-vl-32b-integration` | 2025-09-05 | Qwen2.5-VL-32B モデル統合検証（elasticsearch期の一時実験）。未マージ |
| `elasticsearch2-mynetdiary-tier-gemma-clean` | 2025-09-05 | elasticsearch2 系 tier-gemma のクリーンアップ版。マージ済み |
| `mynetdiary_conversion_final` | 2025-06-27 | MyNetDiary→EatThisMuch形式変換の最終版。マージ済み（現行は Elasticsearch 自体を使わない構成に移行済み） |
| `elasticsearch2-mynetdiary-tier-gemma` | 2025-06-15 | elasticsearch2-mynetdiary の tier+gemma 版。未マージ |
| `elasticsearch2-mynetdiary-tier` | 2025-06-15 | elasticsearch2-mynetdiary の tier 版。未マージ |
| `elasticsearch2-mynetdiary` | 2025-06-15 | elasticsearch2 の MyNetDiary 統合版。マージ済み |
| `elasticsearch_exact_match-recursive` | 2025-06-13 | Phase1.5統合による再帰的exact match実験。未マージ |
| `elasticsearch_exact_match` | 2025-06-13 | niche food mapping 自動更新の実験実装。マージ済み |
| `elasticsearch2` | 2025-06-12 | プロンプト最適化・ドレッシング識別改善の実験。マージ済み |
| `local_db` | 2025-06-10 | YAZIO/MyNetDiary/EatThisMuch マルチDB検索の実験実装。マージ済み |
| `elasticsearch` | 2025-06-08 | Elasticsearch検索アルゴリズム改善の初期実験。マージ済み |

### C. query/demo 実験（9本）

| ブランチ | 最終コミット | 判定理由 |
|---|---|---|
| `barcode` | 2025-09-25 | Open Food Facts フォールバック付きバーコード実験（正式版は `apps/barcode_api`）。未マージ |
| `word_query_demo` | 2025-09-23 | Word Query API デモUI/UX実装。未マージ |
| `unified_api_management` | 2025-09-22 | ログ統合・分析結果クリーンアップの実験。未マージ |
| `voice_input1` | 2025-09-22 | 音声画像分析パラメータ調整の実験実装。未マージ |
| `simple_query_phase` | 2025-09-14 | Meal analysisパイプラインをWord Query APIのみに簡略化する実験。マージ済み |
| `query_system_demo` | 2025-08-13 | MyNetDiary食品検索最適化デモ。マージ済み |
| `usda_dynamic_query` | 2025-06-01 | tiered USDA検索戦略・FNDDS廃止実験。未マージ |
| `recursive-query-generation` | 2025-06-01 | tiered検索フォールバック・厳格FDC ID選定実験。未マージ |
| `usda_dynamic_query2` | 2025-05-28 | 動的栄養計算システム実装の重複ブランチ（下記Dの複数ブランチと同一コミット内容）。マージ済み |

### D. 2025年前半 アーキテクチャ実験（13本）

| ブランチ | 最終コミット | 判定理由 |
|---|---|---|
| `develop` | 2025-05-27 | Meal Analysis API の初期実装ブランチ（プロジェクト最初期）。未マージ |
| `feature/vertex-ai-integration` | 2025-05-27 | Vertex AI / Gemini 2.5 Flash統合の初期実験。未マージ |
| `feature/phase2-usda-integration` | 2025-05-28 | アーキテクチャ分析ツール追加の実験。マージ済み |
| `feature/usda-specification-implementation` | 2025-05-28 | 動的栄養計算システム実装（`usda_dynamic_query2`等と同一コミット内容の重複ブランチ）。未マージ |
| `feature/nutrition-calculation-dynamic-strategy` | 2025-05-28 | 同上、重複ブランチ。未マージ |
| `feature/modular-refactor-v2` | 2025-05-28 | 同上、重複ブランチ。未マージ |
| `feature/local-nutrition-db-migration` | 2025-06-02 | 栄養データ分析スクリプト追加の実験。未マージ |
| `feature/local-db-migration` | 2025-06-04 | モジュラーアーキテクチャ実装完了版（DataInterpreter/WorkflowManager等）。未マージ |
| `feature/phase1-preparation-method-enhancement` | 2025-06-02 | Phase1/Phase2実行結果ファイル追加のみの実験。マージ済み |
| `enhanced-cooking-state-validation` | 2025-06-02 | バッチ分析スクリプト追加の実験。マージ済み |
| `feature/modular-architecture` | 2025-06-04 | モジュラーアーキテクチャ対応README更新。マージ済み |
| `feature/modular-component-architecture` | 2025-06-05 | 栄養計算パイプライン完成版。マージ済み |
| `feature/module-architecture` | 2025-06-05 | 信頼度表示削除等の細部調整。未マージ |

### E. misc・backup（5本）

| ブランチ | 最終コミット | 判定理由 |
|---|---|---|
| `dev` | 2026-01-16 | ConfigManager部分移行の作業ブランチ。main以降（2025-12-07後）に進んだが、現行トランク（mozu期ブランチ）には未統合の孤立した部分作業。要精査のうえアーカイブ候補 |
| `apps/usda_meal_analysis_api_backup` | 2025-10-28 | FAISSインデックスの.gitignore化のみのバックアップ用ブランチ。未マージ |
| `apps/usda_meal_analysis_api` | 2025-10-28 | USDAベースmeal analysis API実装の旧バージョン（現行は `apps/usda_meal_analysis_api` ディレクトリのコードに統合済み）。マージ済み |
| `web_scraping` | 2025-10-10 | 栄養データ統合システム(v2.0)のWebスクレイピング実験。未マージ |
| `llm_name_processor` | 2025-08-31 | 本番デプロイドキュメント更新（`api_deploy2`と同一コミット内容の重複ブランチ）。未マージ |

### F. 2025-12 の未完 feature 系（7本）

| ブランチ | 最終コミット | 判定理由 |
|---|---|---|
| `feature/sse-streaming-progress` | 2025-12-25 | SSEストリーミング進捗表示の未統合実装。main（2025-12-07時点）以降の未マージ作業 |
| `feature/api-resilience-improvements` | 2025-12-24 | API耐障害性改善の未統合実装。未マージ |
| `feature/config-driven-providers` | 2025-12-23 | config駆動プロバイダ切替の未統合実装。未マージ |
| `feature/freeform-api-optimization` | 2025-12-22 | freeform API最適化の未統合実装。未マージ |
| `feature/admin-config-panel` | 2025-12-22 | 管理設定パネルの未統合実装。未マージ |
| `feature/search-ux-improvements` | 2025-12-11 | 検索UX改善の未統合実装。未マージ |
| `feature/voice-input-support` | 2025-12-11 | 音声入力サポートの未統合実装。未マージ |

## 4. 実行コマンド（コメントアウト・未実行）

⚠️ **削除はユーザー明示指示があるまで実行しない（report-only）。** 以下は棚卸しの結果に基づく削除コマンドの叩き台であり、現時点ではすべてコメントアウトのまま提示する。実行する場合も、事前に各ブランチの内容（特に F カテゴリの2025-12実装群）が本当に不要か個別確認すること。

```bash
# --- Category A: 旧 deploy 系 ---
# git branch -D v3_deploy
# git branch -D freeform_usda_meal_analysis_deploy
# git branch -D feature/cloud-run-phase1-implementation
# git branch -D query_api_deploy
# git branch -D meal_analysis_api_deploy2
# git branch -D meal_analysis_api_deploy
# git branch -D api_deploy3
# git branch -D api_deploy2
# git branch -D api_deploy
# git push origin --delete v3_deploy
# git push origin --delete freeform_usda_meal_analysis_deploy
# git push origin --delete feature/cloud-run-phase1-implementation
# git push origin --delete query_api_deploy
# git push origin --delete meal_analysis_api_deploy2
# git push origin --delete meal_analysis_api_deploy
# git push origin --delete api_deploy3
# git push origin --delete api_deploy2
# git push origin --delete api_deploy

# --- Category B: elasticsearch 期 ---
# git branch -D qwen2.5-vl-32b-integration
# git branch -D elasticsearch2-mynetdiary-tier-gemma-clean
# git branch -D mynetdiary_conversion_final
# git branch -D elasticsearch2-mynetdiary-tier-gemma
# git branch -D elasticsearch2-mynetdiary-tier
# git branch -D elasticsearch2-mynetdiary
# git branch -D elasticsearch_exact_match-recursive
# git branch -D elasticsearch_exact_match
# git branch -D elasticsearch2
# git branch -D local_db
# git branch -D elasticsearch
# git push origin --delete qwen2.5-vl-32b-integration
# git push origin --delete elasticsearch2-mynetdiary-tier-gemma-clean
# git push origin --delete mynetdiary_conversion_final
# git push origin --delete elasticsearch2-mynetdiary-tier-gemma
# git push origin --delete elasticsearch2-mynetdiary-tier
# git push origin --delete elasticsearch2-mynetdiary
# git push origin --delete elasticsearch_exact_match-recursive
# git push origin --delete elasticsearch_exact_match
# git push origin --delete elasticsearch2
# git push origin --delete local_db
# git push origin --delete elasticsearch

# --- Category C: query/demo 実験 ---
# git branch -D barcode
# git branch -D word_query_demo
# git branch -D unified_api_management
# git branch -D voice_input1
# git branch -D simple_query_phase
# git branch -D query_system_demo
# git branch -D usda_dynamic_query
# git branch -D recursive-query-generation
# git branch -D usda_dynamic_query2
# git push origin --delete barcode
# git push origin --delete word_query_demo
# git push origin --delete unified_api_management
# git push origin --delete voice_input1
# git push origin --delete simple_query_phase
# git push origin --delete query_system_demo
# git push origin --delete usda_dynamic_query
# git push origin --delete recursive-query-generation
# git push origin --delete usda_dynamic_query2

# --- Category D: 2025年前半 アーキテクチャ実験 ---
# git branch -D develop
# git branch -D feature/vertex-ai-integration
# git branch -D feature/phase2-usda-integration
# git branch -D feature/usda-specification-implementation
# git branch -D feature/nutrition-calculation-dynamic-strategy
# git branch -D feature/modular-refactor-v2
# git branch -D feature/local-nutrition-db-migration
# git branch -D feature/local-db-migration
# git branch -D feature/phase1-preparation-method-enhancement
# git branch -D enhanced-cooking-state-validation
# git branch -D feature/modular-architecture
# git branch -D feature/modular-component-architecture
# git branch -D feature/module-architecture
# git push origin --delete develop
# git push origin --delete feature/vertex-ai-integration
# git push origin --delete feature/phase2-usda-integration
# git push origin --delete feature/usda-specification-implementation
# git push origin --delete feature/nutrition-calculation-dynamic-strategy
# git push origin --delete feature/modular-refactor-v2
# git push origin --delete feature/local-nutrition-db-migration
# git push origin --delete feature/local-db-migration
# git push origin --delete feature/phase1-preparation-method-enhancement
# git push origin --delete enhanced-cooking-state-validation
# git push origin --delete feature/modular-architecture
# git push origin --delete feature/modular-component-architecture
# git push origin --delete feature/module-architecture

# --- Category E: misc・backup ---
# git branch -D dev
# git branch -D apps/usda_meal_analysis_api_backup
# git branch -D apps/usda_meal_analysis_api
# git branch -D web_scraping
# git branch -D llm_name_processor
# git push origin --delete dev
# git push origin --delete apps/usda_meal_analysis_api_backup
# git push origin --delete apps/usda_meal_analysis_api
# git push origin --delete web_scraping
# git push origin --delete llm_name_processor

# --- Category F: 2025-12 の未完 feature 系 ---
# git branch -D feature/sse-streaming-progress
# git branch -D feature/api-resilience-improvements
# git branch -D feature/config-driven-providers
# git branch -D feature/freeform-api-optimization
# git branch -D feature/admin-config-panel
# git branch -D feature/search-ux-improvements
# git branch -D feature/voice-input-support
# git push origin --delete feature/sse-streaming-progress
# git push origin --delete feature/api-resilience-improvements
# git push origin --delete feature/config-driven-providers
# git push origin --delete feature/freeform-api-optimization
# git push origin --delete feature/admin-config-panel
# git push origin --delete feature/search-ux-improvements
# git push origin --delete feature/voice-input-support
```
