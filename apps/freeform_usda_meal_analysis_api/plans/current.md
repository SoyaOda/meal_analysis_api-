# Phase: mozu API（2026-06-03〜）

このアプリ（`freeform_usda_meal_analysis_api`）を **mozu**（Finch 型の高単価 calorie tracker app）用 API として開発するフェーズ。ブランチ `feature/mozu-api`。
前フェーズ（PDCA 土台整備＋モデル探索）は `plans/done/deep_review_improvements_20260601.md` にアーカイブ。

## 引き継ぎ（Handoff — 他PC / Codex 用, 2026-06-03 時点）
**現在地**: pro を採用候補に決定(コード既定/doc 更新済, 本番未変更)。**🔴重要: frozen-50 GT は GPT-5-pro推定と判明→calorie系数値は実精度でなく一致度。両 calibration JSON は VOID, follow-up#1(bias補正)停止。TWO-GATE採用(N5k実測カロリー＋50画像)**。**3 独立セットで pro の calorie 優位が非頑健と判明**: frozen-50(GPT-5-pro推定)=pro≈flash NS／N5k(俯瞰実測,2run)=pro −7pt borderline／**NutritionVerse-Real(eye-level実測,104 content-verified)=flash わずか良 +2.2pt NS**。pro−flash の符号が flip。**pro 採用根拠は recognition(F1 4/4)のみに縮小、全 calorie 数値を根拠から除外**。pro は run間再現性も低い(identical 20% vs 52%)。実 mozu データが唯一の最終arbiter。**次=実ドメイン実測アンカー構築/recognition多様性(ISIA等)**。
**最初に読む**: この `plans/current.md` → **`docs/MOZU_PDCA_SUMMARY_20260604.md`（PDCA総括・結論）** → `docs/MOZU_MODEL_DECISION_20260603.md`（モデル決定の SSOT）→ `evals/lessons/`（特に `20260603_*` 5本: pro採用/stability/calorie-bias/naming-A-B、`20260602_reranker_instruction_was_inert_bug_fixed`）。
**再開手順**: `git checkout feature/mozu-api && git pull`。セッション開始時 `pdca_session_bootstrap` で現行 baseline/config 確認。eval は `scripts/run_pdca_batch_eval` + 別途 `scripts/run_judge_eval`（judge は OpenRouter sonnet）。
**鍵**: OpenRouter / DeepInfra キーは**リポジトリに無い**（env で渡す）。他PCでは `OPENROUTER_API_KEY` / `DEEPINFRA_API_KEY`(=`DEEPINFRA_TOKEN`) を設定。`evals/runs/` は gitignore（run artifact は転送されない＝結論は lesson に集約済）。
**Gotchas（実害あり, 注意）**:
- OpenRouter クレジット残 ~\$11（2026-06-03）。judge は1画像~\$0.02＋本日 rate-limit で低速。eval 多用前に補充推奨。
- `run_judge_eval` を**複数同時起動しない**（OpenRouter rate-limit で全部低速化し判定ファイルが出ない事象あり）。**1本ずつ・完了を judge ファイルの存在で確認**（background の "completed" 通知が python 完了前に出ることがある）。env は**コマンド先頭にinline**で渡す（背景タスクで export が伝播しない事象あり）。
- ローカルサーバ起動は `PORT=8006 python -m apps.freeform_usda_meal_analysis_api.main`（FAISS index は `data/faiss/` にローカル存在）。
**直近の数値（pro vs flash, 同v13）**: recognition F1 pro>flash 4/4(決定的, 信頼), latency 同等, cost ~3.2x。**calorie は 3 独立セットで pro 優位が非頑健**: frozen-50 ~18%(=GPT-5-pro一致度,実精度でない)／N5k 実測 2run flash66-68/pro58-62%(denoised -7.2pt, CI[-15.2,+0.9] borderline)／**NutritionVerse-Real eye-level実測 104 flash40.0/pro42.2%(pro−flash +2.2pt CI[-2.4,6.5] NS, flash わずか良)**。**符号 flip = pro に頑健な calorie 優位なし→採用根拠は recognition のみ**。conviction/naming は judge(advisory)。**OpenRouter キーは 2026-06-04 に新キーへ更新(.env)**。

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
| calorie accuracy（実世界） | 実ドメイン実測アンカーで許容MAE | **frozen-50 GT=GPT-5-pro推定→「~18%」は一致度で実精度でない**。実精度レンジ 50~18%床/N5k~58%天井。bias符号反転(50過小=labeler artifact/N5k過大+31%)。**両calibration VOID**。要・実測アンカー構築 |
| naming 回帰の解消/許容 | naming_db_match が flash 同等以上 or 許容判断 | pro -0.125（4/4, 未解消） |
| judge を真のゲート化 | human golden κ≥0.6 | 未（draft 準備済） |
| 本番 deploy | Firestore model=pro + calibration 配備 | 未（要明示指示・予算確認） |

## Roadmap（推奨順）
1. ~~naming 回帰の回収（reranker）~~ → **実施済・不成立**（form-tuned reranker は naming 回復せず raw_vs_cooked 悪化。naming は VLM クエリに形態が無く reranker 非対応）。pro 小回帰(-0.125)は**据え置き許容**。lesson `20260603_pro_naming_reranker_form_did_not_recover`。
2. **🔴 calorie GT 戦略の是正（最優先・2026-06-03 GT妥当性レビュー）**: **frozen-50 GT は GPT-5-pro 推定**＝calorie系は「実精度」でなく「一致度」。**TWO-GATE 採用**: GATE A=Nutrition5k 総カロリー(独立実測・方向チェック, totals-only)／GATE B=frozen-50 **画像**(phone-angle現実性＋相対A/B, ラベルは真値扱いしない)。**両 calibration JSON は VOID**（50-fit=gemini→GPT-5-pro学習, N5k-fit=自前held-out 132%暴発）。**真のゲート=実ドメイン実測アンカー要構築**（Western eye-level phone 20-50枚を実測×USDA）→ そこで**乗算的(slope-only)に再 calibration**。lesson: `20260603_frozen50_gt_is_gpt5pro_estimate_two_gate_strategy`。
3. **judge golden 確定**: `evals/judge/golden_set.draft_claude_v2.jsonl` を人手レビュー → `golden_set.jsonl` → `run_judge_validation --golden` で κ。合格次第 conviction を採用ゲートに。
4. **外部テストセット（自律取得・一部実装済）**: 徹底リサーチ→`docs/EXTERNAL_TESTSET_PLAN_20260603.md`。**Nutrition5k（実測GT・CC BY 4.0・gsutil匿名DL）→ `scripts/build_nutrition5k_evalset.py` で harness形式に自動変換**（20枚で end-to-end検証済, loader互換確認）。harness に `--images-dir/--labels-dir` 追加。**実装済**: ダウンローダを ThreadPoolExecutor 並列化(`--workers`)、**本番250枚を構築完了**(test_images_n5k/, GT median 222kcal, loader 249/250 OK, gitignore・seed7 で再現可)。**評価=2 run 完了**(run1 `162853`/run2 `191805`): pro 優位は方向一貫だが BORDERLINE(denoised CI[-15.2,+0.9])・pro 再現性が flash より低い(lesson `20260603_n5k_pro_advantage_test_retest_borderline`)。**NutritionVerse-Real も完了**(eye-level実測): Codex が Kaggle 取得→**id-join バグ(40% GT誤り)を検出し COCO 内容 join に修正→104 content-verified**(lesson `20260603_nutritionverse_real_broken_id_mapping`)。eval(run `232505`)= **flash40.0/pro42.2% pro−flash +2.2pt NS**→pro 優位再現せず。**3セットで符号 flip=pro の calorie 優位は非頑健**(lesson `20260604_nutritionverse_real_eyelevel_eval_pro_calorie_edge_not_robust`)。**残**: 外部calibration は実データ待ち(分布で bias 符号 flip するため不可)。**結論=calorie の最終arbiter は実 mozu データのみ。pro 採用根拠は recognition に縮小**。認識多様性は UEC-Food256(アジア)等で別途。
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
| 2026-06-03 | mozu-pivot | **(b)無料の本番構築＋並列化 完了**: `build_nutrition5k_evalset.py` を ThreadPoolExecutor 並列DL化(`--workers`, buffer選択でlimit到達)、**Nutrition5k 250枚 evalset を構築**(images+harnessラベル, GT median 222kcal/max1238, items/dish med4, loader 249/250 OK, 13MB, gitignore・seed7再現可)。harness `--images-dir/--labels-dir` で評価可能。残=評価(credits)＋外部calibration fit。 |
| 2026-06-03 | mozu-pivot | **N5k外部評価(250, 独立実測GT) 完了**: cal_MAE flash 68.4/pro 58.4%（**frozen-50 ~18%の約3倍悪化＝50枚は実世界精度を大幅過大評価, 汎化懸念実証**）。**pro vs flash paired CI[-18.5,-1.3]＝pro有意に良い**(50ではNS→独立大Nで有意化)。bias反転(50過小/N5k過大+31%)。**外部calibration fit失敗**(held-out CAL 132%悪化, affine intercept が広レンジ破壊→乗算的・分布依存)。注: N5kは俯瞰角でpessimistic stress-test, 真値は50とN5kの間=要実データ。recognition/portionはname不一致で N5k では不可信(calorieが信頼軸)。**結論: pro維持(独立で有意)・calibrationは要実データ・精度はrange報告**。lesson: `20260603_nutrition5k_external_eval_generalization_gap.md`。 |
| 2026-06-03 | mozu-pivot | **🔴 GT妥当性レビュー（4視点workflow）→ 重大訂正**: **frozen-50 GT は GPT-5-pro推定**(confidence/5g丸め重量で確定)。**「cal_MAE~18%」は実精度でなくGPT-5-pro一致度**、**pro「-5.3%過小」は labeler artifact**(実測GTで+30.7%過大に反転)→ **follow-up#1(calorie bias補正)とcalibration両JSONをVOID/停止**(適用で実精度悪化)。**pro採用は維持**(独立N5kで有意+recognition F1 4/4)だが根拠から50のcalorie数値を除外。**TWO-GATE採用**(GATE A=N5k総カロリー実測/GATE B=50画像のphone現実性・相対A/B、ラベルは真値扱いせず)。N5k全面切替はしない(分布違い)。**真のゲート=実測アンカー要構築**。生存=ranking/recognition/50画像/naming診断。lesson: `20260603_frozen50_gt_is_gpt5pro_estimate_two_gate_strategy`。 |
| 2026-06-04 | mozu-pivot | **portion 過小是正 PDCA（v14）→ 採用せず・本命レンジに効かず**: 診断=N5k/NVReal 両方で pred/GT が小皿過大(1.3x)・大皿過小(0.6→0.2x)に圧縮(ハードキャップは非binding, anchor 固定が真因)。v14=「anchor を標準1人前とし視覚量にスケール(大1.5-3×/小0.3-0.6×)＋重量上限緩和(main400→700/extras120→300)＋全component計上」。A/B(flash, NVReal104, run `090008`): **calib_slope 0.118→0.170(圧縮緩和は機能)** だが **MAE 改善は特大>1500(非現実的巨大皿)のみ由来、現実的200-1500kcalは 27.1→27.0%で改善ゼロ・全帯NS**。→ **portion-scaling は本命レンジの誤差(27%)の lever でない**(本命誤差は per-item グラム/マッチング)。v14 不採用(v13維持)。次=本命レンジ誤差の分解には per-item 実測GTが要る=実 mozu データが bottleneck。小皿過大は weight floor 80→20 で別途安価に試せる。lesson: `20260604_v14_portion_scaling_helps_slope_but_not_realistic_range`。 |
| 2026-06-04 | mozu-pivot | **NutritionVerse-Real eye-level eval 完了＋pro calorie 優位が非頑健と判明**: Codex が Kaggle DL→変換に **id-join バグ(画像 dish_N ≠ metadata dish_id, 40% GT誤り)** を目視で検出→**COCO 内容ベース join に根本修正**(`build_nutritionverse_evalset.py`)→**104 content-verified dish** 再構築(image↔GT 104/104, 目視 pear/rib/hamburger 一致)。eval(run `232505`)= **flash 40.0/pro 42.2%, pro−flash +2.2pt CI[-2.4,6.5] NS**(flash わずか良)。**3 独立セットで pro−flash 符号 flip**(frozen-50≈/N5k −7pt/NVReal +2.2)＝**pro の calorie 優位は分布依存で非頑健→採用根拠を recognition のみに縮小**。bias も分布で flip(NVReal は pro −13.6% UNDER)。途中 **OpenRouter/DeepInfra キー失効(401)→ユーザ提供の新キーを .env に登録**して実行。lessons: `20260603_nutritionverse_real_broken_id_mapping` / `20260604_nutritionverse_real_eyelevel_eval_pro_calorie_edge_not_robust`。 |
| 2026-06-03 | mozu-pivot | **N5k 再走(run2 `191805`)＋ test-retest 解析 完了**: 2 run の per-image を平均しノイズ除去 → **pro 優位は方向一貫(両run pro<flash)・~7pt(flash67.4/pro60.2%)だが「有意」でなく BORDERLINE**(denoised paired CI[-15.2,+0.9] p=0.076; run1単独の CI[-18.5,-1.3] は楽観 draw)。**再現性差を発見**: 2 run で bit-identical な画像 flash 131/250(52%) vs pro 50/250(20%), median|Δrun| flash0/pro10pt, max tail flash308/pro941pt(cache OFF 確認済＝真の生成確率性)。安定再現: N5k は両 run 過大(flash+46〜49/pro+31〜34%)・**pro の過大が小さい**。→ SSOT/plans の「有意」を「方向一貫・borderline＋再現性トレードオフ」に訂正。lesson: `20260603_n5k_pro_advantage_test_retest_borderline`。**(a) NutritionVerse-Real は Codex Computer-Use 用指示書 `docs/CODEX_TASK_nutritionverse_real.md` を作成**(参照パス/フラグ/ラベルスキーマを harness コードと照合済)。 |
