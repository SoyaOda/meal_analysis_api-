# MODEL REFRESH OS — 2026-06-11 セッション総括 & 運用ハンドオフ

**目的**: 今後のセッションが1分でこのセッションの成果と運用方法を把握し、即作業に入れるようにする。
**セッションの依頼**: 「新モデルが出るたびに長期で精度をブラッシュアップできる仕組みを構築し、それを回して現時点最高精度のパイプラインに到達させる。コスト≤~10x・レイテンシ≤~2x。DB更新も可。米国向けcalorie tracking appに組込予定」。

---

## 1. TL;DR（このセッションの結論）

1. **仕組み（model-refresh OS）を構築・検証した** — 検知→スクリーニング→pooled判定→採用、の段階ゲートを全てコード+protocol化（§2）。
2. **第1サイクルを実走: 新世代17候補は flash に全敗** — 「モデル選択は天井」は 2026-06-11 時点でも有効。**本番構成（flash + v13_floor20 + E7 top_n=5 + 0.6B/0.6B + SC K=3）が引き続き最高精度**（§3）。
3. **異種モデル ensemble（median-of-3）も SC K=3 に優位なし** → HOLD（§3）。
4. **事故**: OpenRouter クレジット枯渇 402 → server 内 circuit breaker 開放 → 後続候補の連鎖全滅 + **本番一時停止**（同日チャージで復旧確認済み）。再発防止 = preflight スクリプト（§4）。
5. **DBレーン**はスコープ済み・未着手（P1 = FNDDS portions prior、上限±1.5-2pt・相殺破壊リスクあり）（§5）。
6. 真の精度レバーは変わらず **E13 実測収集 → E14 条件付き校正**（in-domain −18.5pt 実証済み・アプリUI/UX待ち）。

## 2. 運用OS: model-refresh サイクル（新規構築・全て検証済み）

正典 = **`docs/MODEL_REFRESH_PROTOCOL_20260611.md`**（ゲート数値・教訓の SSOT）。実行は **`/model-refresh`** skill（コスト保護のため自動起動無効・ユーザー起動のみ）。

| 部品 | パス | 役割 | 検証状況 |
|---|---|---|---|
| 検知 | `scripts/model_watch.py` | OpenRouter全カタログ→image+reasoning→per-imageコスト試算（in:out=0.12:0.88 実測シェア）→予算ゲート（≤10×baseline）→**既テスト突合**→レポート+スクリーニングconfig生成+pricing追記 | 実走済（338→未テスト×予算内75件検知） |
| 既テスト registry | `evals/knowledge/tested_models.json` | 評価済みモデルの verdict 台帳（**負け記録も必ず残す**=再評価防止）。vlm/embedding/reranker 3スロット、39 entries | `.gitignore` 例外追加済・要コミット |
| 評価 | `scripts/run_pdca_batch_eval.py` | 既存（paired BCa CIゲート）。変更なし | — |
| pooled 判定 | `scripts/pool_paired_rotation.py` | rotation 複数セットの per-image paired delta をプール→pooled BCa CI + **set間方向一貫性**（SET-SPECIFIC 検出 = E1 v18 教訓のコード化） | E1 v18 実データで run 保存正準値と**完全一致** |
| preflight | `scripts/check_openrouter_credits.py` | 残高チェック（`--min-usd`未満で exit 1） | 実走済（事故検知にも使用） |

**サイクル手順**（詳細は protocol）: `check_openrouter_credits` → `model_watch --update-pricing --emit-config` → smoke5（故障検出のみ）→ dev40 paired（粗序列・ΔMAE≤+1.0pt で shortlist）→ rotation 3セット paired + `pool_paired_rotation`（pooled CI<0 ∧ 符号一致で昇格）→ K=3 + repeated で安定性 → lesson + registry + baseline 更新。
**トリガ**: 月1 / メジャーリリース時 / baseline drift 時。**1サイクル ~$10-40**。
**罠**: ①frozen-50/dev40 の GT は GPT-5-pro 推定（GPT系の上振れ注意・weighed セット重視）②同一run内で先行候補が大量失敗すると breaker が後続を汚染→リスキーな候補は別runに分離。

## 3. 第1サイクルの結果（2026-06-11・詳細は lesson）

正典 = **`evals/lessons/20260611_model_refresh_sweep_no_new_model_beats_flash.md`**（全数値表）。

- **対象17候補**: qwen3.5-397b/3.6-plus/3.6-flash/3.7-plus、grok-4.3/4.20、kimi-k2.6、claude-haiku-4.5/sonnet-4.6、gpt-5.2/5.4-mini、seed-2.0-lite、minimax-m3、ernie-4.5-vl-424b、step-3.7-flash、nova-2-lite、perceptron-mk1
- **全敗**: 有意悪化 = minimax-m3(+10.9)/haiku-4.5(+13.7)/step-3.7(+6.7)/sonnet-4.6(+14.1, signed+24 系統過大)。latency失格(>32s) = qwen系67-68s/kimi-k2.6 116s/ernie 128s 等。最接近 = **gpt-5.2 +1.90 NS**（13.6sと flash より高速・ensemble 素材として最有力だった）
- **参照値（dev40）**: flash K=1 = 15.04-15.42（3draw, std~0.2 と安定）/ **flash K=3 = 14.22**（−1.13, pooled −2.5pt と整合）
- **異種 ensemble PoC**: 最良 flash+grok4.3+gpt5.2 median = 13.71 だが post-hoc 選択バイアス込みで SC K=3 と同等以下・コスト6.6×→ **HOLD**（再訪条件: flash 同等精度で誤差脱相関の高速モデル登場時）
- 評価実測コスト: **$5.19**（smoke $0.74 / dev40 $3.81 / K3 $0.63）+ sonnet 再評価 ~$1.6

## 4. 事故記録（402/breaker）と再発防止

- 経緯: 残高僅少のまま評価続行 → Group B 後半で 402 連発 → server 内 OpenRouter circuit breaker 開放 → sonnet 2回全滅（無効データ）+ **本番（同一キー）一時停止**。最終残高 −$0.16/total $240。
- 復旧: ユーザーチャージ（→$29.84）→ 本番プローブ HTTP 200 確認 → sonnet クリーン再評価で reject 確定。
- 再発防止（protocol Stage -1 に組込済）: 評価前に `check_openrouter_credits --min-usd <想定×2>` 必須。breaker 汚染の疑いがある結果は server 再起動後に再評価。
- 関連する既知の根本課題: DEEP_REVIEW P1「retry-over-breaker stacking」（未修正）。

## 5. DBレーン（ユーザー許可済み・スコープ済み・未着手）

背景: 誤差の~50%が density（DBマッチング）由来、grams 0.88×（過小）× density 1.14×（過大）が**相殺**して bias≈0 という構造（lesson `20260604_realistic_range_error_decomposition_*`）。

| 優先度 | 施策 | 期待 | リスク/備考 |
|---|---|---|---|
| P1 | **FNDDS portions prior**（96.2%カバレッジ・現在カロリー経路で未活用） | 上限 −1.5〜2pt | **相殺破壊リスク**（v14 portion-scaling は本命レンジ改善ゼロの失敗歴）。注入案: (a) post-hoc blend（リスク大）/(b) **two-pass**（検索→portionsをVLMへ返し再推定・+1コール・最有力）/(c) prompt prior（v14同型・非推奨）。frozen-VLM分離 + 小皿/大皿サブグループ監視で検証 |
| P2 | FNDDS 版更新 / 調理法正規化 + source-tier rerank | ±0.5〜1.5pt | 「retrieval天井」は**モデル**選択の結論で DB**内容**は未試行領域 |
| P3 | FDC Branded Foods 追加（米国パッケージ食品） | recognition/カバレッジ軸 | 50万件 → 0.6B/dim1024 で ~2GB（IVF/量子化要）。`barcode_api` との棲み分け検討 |

⚠️ 調査エージェント報告の一部に誤り（「現行 8B/dim4096」）→ ファクトチェック済の正は **0.6B/dim1024・55.5MB**（`usda_index_full.faiss`）。8B index は `.8b.faiss` としてバックアップ残置。

## 6. SSOT マップ（どの情報はどこが正典か）

| 情報 | SSOT |
|---|---|
| 運用全体・現状・次の一手 | `plans/current.md` |
| model-refresh のゲート・手順・教訓 | `docs/MODEL_REFRESH_PROTOCOL_20260611.md` |
| 第1サイクルの全数値・incident | `evals/lessons/20260611_model_refresh_sweep_no_new_model_beats_flash.md` |
| 既テストモデルと verdict | `evals/knowledge/tested_models.json` |
| 本セッション総括（このdoc） | `docs/MODEL_REFRESH_OS_20260611.md` |
| PDCA 全史 | `docs/MOZU_PDCA_COMPLETE_20260606.md` |
| rotation セット・コマンド・baseline | `docs/EXTERNAL_TESTSET_PLAN_20260603.md` |
| E13/E14（本命レバー） | `docs/E13_DATA_COLLECTION_PLAN_20260606.md` / `docs/MOZU_APP_E13_E14_UIUX_HANDOFF_20260607.md` |
| ローカル実行環境の罠 | memory `freeform-local-eval-env`（venv-with-space + env unsets） |

## 7. 次セッションの開始手順

1. `/pdca-bootstrap`（または `scripts.pdca_session_bootstrap`）
2. `scripts.check_openrouter_credits --min-usd 10`
3. 作業候補（優先順）:
   - **A. E13 物理収集の開始**（本命・アプリUI/UX前提・−18.5pt級）
   - **B. DBレーン P1: portions prior two-pass 実験**（§5。半日〜1日 + $10-30。ユーザーは着手可と認識済み）
   - **C. `/model-refresh` 次サイクル**（月1目安。前回 2026-06-11 全敗。registry が再評価を防ぐ）
4. eval 用 config は `evals/configs/pdca_model_refresh_*_20260611.json` ×5（**gitignore 対象**・必要なら `model_watch --emit-config` で再生成可。prompt は `pdca_e2_weight_floor20_full50_20260605.json` の v13_floor20 candidate = 本番同等 len2841/sha先頭 0665ac40）

## 8. 本セッションの未コミット変更（コミットはユーザー指示待ち）

- 新規: `scripts/model_watch.py` / `scripts/pool_paired_rotation.py` / `scripts/check_openrouter_credits.py` / `docs/MODEL_REFRESH_PROTOCOL_20260611.md` / 本doc / `.claude/skills/model-refresh/` / `evals/knowledge/tested_models.json` / lesson 1本 / `evals/catalog/model_watch_20260611.{json,md}`（jsonはgitignore）
- 変更: `config/model_pricing.json`（+17モデル）/ `.gitignore`（registry例外）/ `plans/current.md` / `tests/test_pdca_eval_logic.py`（+2テスト, 計84 passed）/ `evals/knowledge/experiment_log.jsonl`（再生成305行）
