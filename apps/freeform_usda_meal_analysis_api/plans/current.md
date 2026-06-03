# Phase: mozu API（2026-06-03〜）

このアプリ（`freeform_usda_meal_analysis_api`）を **mozu**（Finch 型の高単価 calorie tracker app）用 API として開発するフェーズ。ブランチ `feature/mozu-api`。
前フェーズ（PDCA 土台整備＋モデル探索）は `plans/done/deep_review_improvements_20260601.md` にアーカイブ。

## 引き継ぎ（Handoff — 他PC / Codex 用, 2026-06-03 時点）
**現在地**: pro(`gemini-3.1-pro-preview`) を mozu の採用候補に決定し、コード既定(settings.py/config_manager)とドキュメントを pro に更新済。本番(Cloud Run/Firestore)は未変更。直近で「naming 回復 reranker A/B(#1)」を実施し**不成立**（lesson 記録）。次は「公開分布への汎化検証用の外部データ取得が可能か」を調査中。
**最初に読む**: この `plans/current.md` → `docs/MOZU_MODEL_DECISION_20260603.md`（モデル決定の SSOT）→ `evals/lessons/`（特に `20260603_*` 5本: pro採用/stability/calorie-bias/naming-A-B、`20260602_reranker_instruction_was_inert_bug_fixed`）。
**再開手順**: `git checkout feature/mozu-api && git pull`。セッション開始時 `pdca_session_bootstrap` で現行 baseline/config 確認。eval は `scripts/run_pdca_batch_eval` + 別途 `scripts/run_judge_eval`（judge は OpenRouter sonnet）。
**鍵**: OpenRouter / DeepInfra キーは**リポジトリに無い**（env で渡す）。他PCでは `OPENROUTER_API_KEY` / `DEEPINFRA_API_KEY`(=`DEEPINFRA_TOKEN`) を設定。`evals/runs/` は gitignore（run artifact は転送されない＝結論は lesson に集約済）。
**Gotchas（実害あり, 注意）**:
- OpenRouter クレジット残 ~\$11（2026-06-03）。judge は1画像~\$0.02＋本日 rate-limit で低速。eval 多用前に補充推奨。
- `run_judge_eval` を**複数同時起動しない**（OpenRouter rate-limit で全部低速化し判定ファイルが出ない事象あり）。**1本ずつ・完了を judge ファイルの存在で確認**（background の "completed" 通知が python 完了前に出ることがある）。env は**コマンド先頭にinline**で渡す（背景タスクで export が伝播しない事象あり）。
- ローカルサーバ起動は `PORT=8006 python -m apps.freeform_usda_meal_analysis_api.main`（FAISS index は `data/faiss/` にローカル存在）。
**直近の数値（pro vs flash, 同v13）**: recognition F1 pro>flash 4/4 run、conviction 4/4 で+方向(各NS)、latency 同等(+0.2s)、cost ~3.2x(+\$16-28/user/yr)。calorie は calibration(外部fit)前提で pro+calib 13.98%>flash+calib 15.61%(held-out n=10)。naming は pro -0.125(reranker で回復せず)。

## Goal
mozu に組み込む写真カロリー推定 API を、採用候補 **gemini-3.1-pro** を軸に本番投入できる品質まで仕上げる。

## 採用済み決定（SSOT: `docs/MOZU_MODEL_DECISION_20260603.md`）
- **VLM 採用候補 = `openrouter:google/gemini-3.1-pro-preview`**（settings.py / config_manager 既定を更新済）。
  - recognition が flash 比 4/4 run 再現的に向上、conviction も 4/4 で +方向（個別 NS）、**レイテンシ同等（+0.2s）**、コスト ~3.2x（高単価アプリで許容）。
  - flash は安価代替として保持。
- 本番 Cloud Run / Firestore は未変更（deploy は別工程）。

## Exit Criteria（本番投入の条件）
| 項目 | 閾値 | 現在 |
|------|------|------|
| calorie under-bias 補正 | 外部held-out fit の calibration で signed≈0 | pro: eval内fitで -5.3%→-1.6%（**外部fit未**） |
| naming 回帰の解消/許容 | naming_db_match が flash 同等以上 or 許容判断 | pro -0.125（4/4, 未解消） |
| judge を真のゲート化 | human golden κ≥0.6 | 未（draft 準備済） |
| 本番 deploy | Firestore model=pro + calibration 配備 | 未（要明示指示・予算確認） |

## Roadmap（推奨順）
1. ~~naming 回帰の回収（reranker）~~ → **実施済・不成立**（form-tuned reranker は naming 回復せず raw_vs_cooked 悪化。naming は VLM クエリに形態が無く reranker 非対応）。pro 小回帰(-0.125)は**据え置き許容**。lesson `20260603_pro_naming_reranker_form_did_not_recover`。
2. **calorie calibration の本番化準備（次の本命）**: 外部（eval50 と disjoint な mozu 実データ等）ラベルを収集 →`fit_calorie_calibration.py` で fit → held-out 検証 → `config/calorie_calibration.json` を enable。pro の -5.3% under-bias 補正に必須。
3. **judge golden 確定**: `evals/judge/golden_set.draft_claude_v2.jsonl` を人手レビュー → `golden_set.jsonl` → `run_judge_validation --golden` で κ。合格次第 conviction を採用ゲートに。
4. **外部テストセット（自律取得・一部実装済）**: 徹底リサーチ→`docs/EXTERNAL_TESTSET_PLAN_20260603.md`。**Nutrition5k（実測GT・CC BY 4.0・gsutil匿名DL）→ `scripts/build_nutrition5k_evalset.py` で harness形式に自動変換**（20枚で end-to-end検証済, loader互換確認）。harness に `--images-dir/--labels-dir` 追加。**残**: (a)本番N(~200-300)構築は per-image DL が遅く `gsutil -m` 並列化が必要 (b)pro vs flash 評価＋外部calibration fit は OpenRouter credits 要。**限界**: Nutrition5k も Western/cafeteria＝多cuisineカロリーは依然未閉（公開後の実データが唯一の本物）。認識多様性は UEC-Food256(アジア)等で別途。
5. **本番 deploy**: 上記が揃い次第、Firestore `config.vlm.model_id`=pro ＋ calibration を配備（要ユーザ明示指示・予算確認）。
- 余技 follow-up: full-fat-default 単独 reranker で決定的 cal_MAE 改善（24.55→19.67 観測）が残るか isolate。

## 引き継ぎ済みの土台（前フェーズ成果, 全て利用可）
- PDCA: paired BCa bootstrap CI ゲート + 強制 stability（`scripts/run_pdca_batch_eval.py` 他）。
- portion = 決定的メトリクス（`dish_match_metrics.portion_score_0_5`）、LLM portion は advisory。
- calorie calibration 層（`core/calorie_calibration.py`, default OFF, affine）。
- LLM-judge（`scripts/run_judge_eval.py`, rubric v2, advisory）+ 0.944 discriminative gate 合格。
- 検索: hybrid（FAISS IP cosine + BM25 + RRF + Qwen3-Reranker）。**reranker instruction bug 修正済**（query 焼込）。
- self-verification 2nd pass（opt-in, default OFF。同一tier verifier は非有効）。
- 知見は `evals/lessons/`（20+本）に蓄積。

## Non-Negotiables（前フェーズから継続）
- 採用判定は原則50例フル評価 + Ground truth総カロリー比較 + 安定性（複数 run）。
- 過学習防止: prompt に評価データ固有情報を埋め込まない。calibration は eval と disjoint なデータで fit。
- PDCA評価は原則 `use_vlm_cache=false`（同一VLMの reranker-only A/B 等の isolation 目的では cache=true を justified exception として明記）。
- 本番（Cloud Run/Firestore）操作・deploy は要ユーザ明示指示。
- promote 主張は run 自身の artifact のみ引用（cross-run 値は文脈）。

## Session Log
| Date | Session | 作業内容 |
|------|---------|---------|
| 2026-06-03 | mozu-pivot | **mozu phase 開始**。pro を採用候補に決定（recognition 4/4再現・速度同等・コスト ~3.2x/+$16-28/ユーザー/年）。settings.py/config_manager 既定を pro に、model-focus doc 4箇所更新、決定記録 `docs/MOZU_MODEL_DECISION_20260603.md` 作成。前フェーズを `plans/done/` にアーカイブ。ブランチ `feature/mozu-api` 作成。 |
| 2026-06-03 | mozu-pivot | **naming回復 A/B(#1) → 不成立**: pro+形態双方向reranker vs pro+現行(cache共有でreranker isolate, 39/40でレコード変化)。判定: **raw_vs_cooked 20→25悪化・correct% 19.1→16.4↓・conviction↓**で naming回復せず(over-steering)。但し**決定的cal_MAE 24.55→19.67(-4.9pt)改善**(主にfull-fat-default由来と推定)。**naming は reranker非対応(形態signalがVLMクエリに不在)→ VLMプロンプト側課題**。pro小回帰(-0.125)は据え置き。follow-up: full-fat-default単独でcal改善が残るか。lesson: `20260603_pro_naming_reranker_form_did_not_recover.md`。 |
| 2026-06-03 | mozu-pivot | **外部データ取得 徹底リサーチ＋自律構築開始**: 結論=PARTIAL-YES。**Nutrition5k(実測GT・CC BY 4.0)が gsutil匿名DL可・schema が harnessに対応**と検証 → `build_nutrition5k_evalset.py`(CSV→harnessラベル+rgb.png DL)作成、harnessに`--images-dir/--labels-dir`追加、**20枚で end-to-end検証成功**(独立実測GT, loader互換)。残=本番N構築(gsutil -m並列化)+評価(credits)。限界=Nutrition5kもWestern/cafeteriaで多cuisineカロリーは未閉(公開後実データ必須)。doc: `EXTERNAL_TESTSET_PLAN_20260603.md`。58 tests passed。 |
