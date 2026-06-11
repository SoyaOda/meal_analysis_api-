# MODEL REFRESH PROTOCOL（新モデル定期評価・入れ替えプロトコル）

作成: 2026-06-11。長期にわたり「新しいVLMモデルが出るたびに、同一ゲートで機械的に評価し、勝ったときだけ入れ替える」を再現可能にする運用 SSOT。
背景: モデル選択は現時点で天井（`docs/MOZU_PDCA_COMPLETE_20260606.md` §5.1, cross-provider 全スロットでクリーン勝ちなし）。ただし**新世代モデルの登場でこの結論は陳腐化し得る**ため、低コストの定期スイープで継続検証する。期待値は低く保ち、ゲートは厳格に。

## 0. 制約（ユーザー指定の予算・2026-06-11）
- **コスト**: パイプライン全体 per-image ≤ **現行baseline × 10**（SC K 込み。例: baseline $0.00716/枚 → 上限 ~$0.072/枚。K=3 なら per-call ~3.3×まで、K=1 なら ~10×まで）
- **レイテンシ**: ≤ **現行 × 2**（avg_latency_sec 基準。現行 ~16s → 上限 ~32s）
- 精度が最重要。同等精度なら安価・高速側を採用（cost-rational 原則, pro 撤回の教訓）

## 1. ツールチェーン
| 段階 | ツール | 役割 |
|---|---|---|
| 検知・選定 | `scripts/model_watch.py` | OpenRouter 全カタログ取得（top-N カット無し）→ image+reasoning フィルタ → per-image コスト試算で予算ゲート → **既テスト集合**（`evals/knowledge/tested_models.json`）突合 → 未テスト候補レポート + スクリーニング config 自動生成 + `config/model_pricing.json` 自動追記 |
| 評価 | `scripts/run_pdca_batch_eval.py` | 既存の paired BCa CI ゲート付き評価（変更なし） |
| pooled 判定 | `scripts/pool_paired_rotation.py` | rotation 複数セットの per-image paired delta をプールし pooled BCa CI + **set 間方向一貫性**を判定（E1 v18 の set-specific 教訓をコード化） |
| 安定性 | `scripts/run_pdca_repeated_eval.py` | 既存（変更なし） |
| 記録 | `evals/lessons/` + `tested_models.json` 更新 + `export_pdca_knowledge` | 同じモデルを二度評価しないための registry 更新が**採用判定の一部** |

## 2. ステージとゲート

### Stage -1: プリフライト（必須・2026-06-11 事故からの教訓）
```bash
python -m apps.freeform_usda_meal_analysis_api.scripts.check_openrouter_credits --min-usd <サイクル想定コスト×2>
```
- 残高不足のまま評価を始めない。**枯渇すると 402 連発 → サーバ内 circuit breaker が開き、同一 run の後続候補が連鎖全滅 + 本番（同一キー）も停止する**（lesson `20260611_model_refresh_sweep_*` の incident 節）。
- 失敗が出やすい候補（新規プロバイダ・重いモデル）は**別 run に分離**する。同一 run 内で先行候補が大量失敗した場合、後続候補の結果は breaker 汚染を疑い、サーバ再起動後に再評価する。

### Stage 0: smoke（5枚, K=1）— 故障検出のみ
```bash
python -m apps.freeform_usda_meal_analysis_api.scripts.run_pdca_batch_eval \
  --config <model_watch が生成した config> --api-url http://localhost:8006 \
  --limit 5 --required-image-count 5 --no-use-vlm-cache
```
- 落とす条件: failure_count>0（JSON 破壊・refusal・timeout）/ MAE が壊滅的（>60%）/ latency > 2×制約
- n=5 の MAE で優劣判断をしない（故障スクリーニングのみ）

### Stage 1: dev40 paired（K=1）— 粗い序列
- config: 生存候補 + `v13f_flash`（現行 prod 構成 = flash + v13_floor20 prompt + reranker_top_n=5）を**同一 run に併走**（paired_baseline_candidate）
```bash
python -m ... run_pdca_batch_eval --config <cfg> --api-url http://localhost:8006 \
  --image-index-file apps/freeform_usda_meal_analysis_api/evals/splits/dev_40_v1.txt \
  --required-image-count 40 --no-use-vlm-cache
```
- 通過条件（shortlist 行き）: paired ΔMAE 点推定 ≤ +1.0pt（=明確に悪くない）∧ latency ≤ 2× ∧ cost 予算内 ∧ failure 0
- ⚠️ **GT-artifact guard**: dev40/frozen-50 の GT は **GPT-5-pro 推定**。GPT 系候補はここで labeler-artifact の上振れがあり得る（pro 撤回の教訓の逆向き）。dev40 の勝ちだけで昇格判断しない。

### Stage 2: rotation paired（K=1）— 本判定
shortlist 候補 + `v13f_flash` を rotation 3セットで paired 実行（コマンド詳細は `docs/EXTERNAL_TESTSET_PLAN_20260603.md`）:
- **JFB-100**（実ユーザー eye-level・最 in-domain・GT は専門家推定）
- **NVReal-104**（eye-level・weighed）
- **N5k-100**（overhead・weighed, split `n5k_test_100.txt`）
- （frozen-50 は補助。GT artifact のため重み最小）

```bash
python -m ... pool_paired_rotation \
  --runs <jfb_run> <nvreal_run> <n5k_run> \
  --candidate <name> --baseline-candidate v13f_flash
```
- **昇格条件（全て必須）**: pooled paired BCa 95% CI 全体 < 0 ∧ **3セットの Δ符号が一致**（set-specific は E1 v18 同様 REJECT）∧ high30 非悪化 ∧ latency ≤ 2× ∧ cost 予算内
- weighed セット（NVReal/N5k）の方向を JFB より重視（JFB GT は推定値）

### Stage 3: 本番形態の確認 + 安定性
- 勝者を **SC K=3** で再評価（本番形態。cost = 3×/枚 が予算内であること）
- `run_pdca_repeated_eval.py --repeats 2`（mae_std ≤ 1.0 / high30_std ≤ 2.0）
- reasoning_effort / temperature の軽い再適合は**この段階のみ**（screening は medium/0.3 固定で公平比較）

### Stage 4: 採用処理
1. lesson 記録（worked/did-not-work 分離・prompt_sha256・run dir）
2. `tested_models.json` に verdict を追記（**負けでも必ず記録** = 再評価防止）
3. `evals/baselines/current_baseline.json` 更新（採用時のみ）
4. 本番反映（Firestore/deploy）は**ユーザー明示指示が必要**（`DEPLOY_RUNBOOK_E7_LIGHT_20260605.md` 準拠）

## 3. 運用サイクル
- **トリガ**: ①月1回の定期実行、②メジャーモデルリリース時（Gemini/GPT/Claude/Qwen/Grok の新世代）、③baseline drift 検知時（同一構成の frozen-50 が ±3pt を超えて動いたとき = 11.38%→20% 回帰の教訓）
- **1サイクルの想定コスト**: smoke ~$1 + dev40 ~$10 + rotation（shortlist 2-3 候補）~$15-30 = **$30-40/サイクル**
- 実行手順は `/model-refresh` skill（`.claude/skills/model-refresh/`）に固定化
- セッション開始は従来どおり `/pdca-bootstrap` 必須

## 4. 失敗知見の継承（このプロトコルが前提とする教訓）
- **n=50 単独は draw-noise ±3pt** → 小差は pooled rotation でのみ判定
- **frozen-50 GT = GPT-5-pro 推定 / JFB GT = 専門家推定** → 絶対値は一致度。weighed（NVReal/N5k）が真のアンカー
- **set-specific な勝ちは global deflation の疑い**（E1 v18）→ 方向一貫性必須
- **provider 非決定性** → 採用は反復評価の平均/分散で判断
- **過学習防止**: prompt に評価データ固有情報を埋め込まない。screening は全候補同一 prompt（v13_floor20）
- **SC K>1 の cost 過小計上**: eval の avg_cost_usd は選択された 1 サンプル分のみ（K=3 の実コストは ~3×。予算判定時に手動で K 倍する）
- **モデル乗り換え時の波及確認**: VLM を変えたら E7 密度混合・E2 floor・SC median の各 lever が新モデルでも成立するかを rotation で確認（lever はモデル特性に依存し得る）

## 5. 現行 baseline 参照値（2026-06-11 時点）
| 指標 | 値 | 出典 |
|---|---|---|
| 構成 | flash + v13_floor20 + E7(top_n=5) + 0.6B/0.6B + SC K=3 | prod revision 00041-sfj |
| frozen-50 MAE | 20.65%（公式 baseline, v13/K=1, 2026-06-01）/ 直近 draw 15.97%（E7 込み） | `current_baseline.json` / run 20260606_065251 |
| NVReal-104 MAE | 45.20%（v13, K=1） | run 20260606_065312 |
| N5k-100 MAE | 74.75%（v13, K=1） | run 20260606_065337 |
| JFB-100 MAE | 53.8% / signed +43.9%（v13, K=1） | run 20260606_102611 |
| cost / latency | $0.00716/枚（K=1, flash）/ 15.8s | `current_baseline.json` |
