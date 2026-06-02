# Phase: Deep Review Improvements (2026-06-01〜)

`docs/DEEP_REVIEW_20260601.md` の所見に基づく整備フェーズ。ブランチ `feature/deep-review-improvements`。

## Goal
精度PDCAの土台を信頼できるものにし（採用ゲート・config整合・検索の正しさ）、Claude Codeベースで長期開発しやすい状態に整える。精度A/Bはゲート堅牢化の後に行う。

## Exit Criteria
| 項目 | 閾値 | 現在 |
|------|------|------|
| 採用ゲートが統計的に妥当 | paired bootstrap CI ベース | **done**（BCa CI + 強制stability） |
| eval↔prod config 整合 | served==candidate を assert / drift検出 | **code done**（本番promoteは要ユーザー実行） |
| 検索スコア計算 | IP類似度を直接使用 + クエリ正規化 | **done**（要: 融合weight再sweep） |
| Claude Code 開発基盤 | hooks/skills/subagent/rules/plans 整備 | **done** |

## Progress
| トラック | 施策 | ファイル | Status |
|--------|------|---------|--------|
| D | Claude Code開発環境整備 | `.claude/`(root) hooks, app `.claude/skills` `agents` `rules`, `plans/` | done |
| A | Evalゲート堅牢化（paired BCa bootstrap CI + 強制stability） | `scripts/run_pdca_batch_eval.py`, `run_pdca_repeated_eval.py` | done |
| B | 検索の数学バグ修正（`1/(1+d)`→直接similarity, クエリnormalize_L2） | `services/hybrid_search.py` | done（要weight再sweep） |
| C | 本番configドリフト対応（config-fidelity assert, /health drift, schema_version） | `scripts/run_pdca_batch_eval.py`, `admin/config_manager.py`, `routers/health.py`, `models/response_models.py` | code done（要prod promote） |

## Recommended Task Order
D → A → B → C（A=精度A/Bの前提、Bの効果測定はAのゲートに依存、Cのprod promoteは認証が必要なのでユーザー対応）。
整備完了後に P1: portion推定promptのA/B（hardened gateで）、metric分解（signed bias / calibration slope / macro / Hungarian dish-match）。

### 2026-06-01 追記: 本番実態の訂正 & ローカルeval環境の制約
- **本番は v7 を配信していない**（DEEP_REVIEWの前提は2/25時点で古い）。実態（2/26 admin設定）: model=gemini-3-flash・temp0.3/medium/12288（正）、prompt_file=v7（**ラベルのみ**）、**prompt_text=2841字のカスタムprompt = v11b＋飲料対応**（char2402で分岐: 飲料主体の写真をdish化）。どのcommit済promptとも不一致だったため `prompts/freeform_prompt_usda_format_ver_v13_beverage_subject_prodcapture_20260226.txt` として保全。
- **方針（ユーザー選択）**: v13-beverage vs v11b を paired gate で検証 → 勝者を prod + baseline + settings default へ。結論まで本番現状維持。
- **ローカルeval不可**: ローカル `.env` のキーが無効（OpenRouter 401 "User not found" / DeepInfra embedding 401 invalid_api_key、既知lesson）。→ **Item 1 はリモート本番APIで実行**（per-request override、prod設定は不変）。
- **Item 2（検索weight再sweep）はブロック**: Track Bの検索修正はローカルコードのみで本番未デプロイ。リモートは修正前。正しい計測には (a) 有効なローカルキー or (b) Track Bをdev Cloud Runへデプロイ が必要。config準備済: `evals/configs/pdca_retrieval_weight_sweep_fixedfusion_20260601.json`（6候補・paired gate）。

### Item 1 結果（run 20260601_204037, 完了）
- **v13 ≈ v11b（同等）**: paired Δ(v13−v11b)=+0.46, 95%CI [-4.73,+4.56], p=0.84 → calorie MAEで有意差なし。→ **prod現行v13を維持**（v11b上書きせず）。v13は飲料対応の改良を含み非劣性。
- v13 を `prompts/` に保全し、`settings.py`/`config_manager` のコード既定を v13 に昇格。baselineは**更新しない**。
- **🚨 baseline非再現**: v11b 同一構成で mae 11.38%→**20.27%**（10/50枚>30%）。model/infraドリフト疑い。lesson: `20260601_v13_vs_v11b_tie_and_baseline_regression.md`。

### 2026-06-01 追記: 再ベースライン＋ドリフト調査の結果
- **新モデルは精度回復せず**（run 20260601_221426, full50, fixed retrieval, v13）: gemini-3-flash-preview=20.65%, gemini-3.5-flash=24.95%(悪化), gemini-3.1-flash-lite=20.86%(同等+2x遅い)。paired全件 hold。→ **gemini-3-flash-preview 維持が最善**（モデルアップグレード不要）。
- **~20%は安定・再現的**（remote 20.27% / local-fixed 20.65%, std~0.3pt）。検索でもモデル版でもない。**11→20劣化の根本原因は未特定**（gemini-flash系の広範な portion推定劣化 or 2月prodとのpipeline/data差異）。
- **baseline をリセット**: `current_baseline.json` を現実(20.65%, gemini-3-flash-preview+v13+fixed retrieval)へ更新。旧11.38%は `baseline_20260225_...json` に保持。lesson: `20260601_model_drift_newer_gemini_no_recovery.md`。
- **metric分解 実装＆局在化 完了**（run_pdca_batch_eval に `compute_decomposed_metrics`/`dish_match_metrics`/`extract_pred_items`/`load_label_items` 追加、future runは `decomposed`+`dish_match_agg` 自動出力, per-image `pred_items` 永続化=PART A, markdownに診断セクション）。**既存runに遡って局在化**: **20%は系統的なportion過小推定（calibration slope ≈0.47, signed -3〜-7%, 大盛りほど過小）。VLMのportion問題で検索/マッチではない**。fat MAE%最大（隠れ油）。gemini-3.5は更に悪い(slope0.21)。lesson: `20260601_metric_decomposition_localizes_portion_underestimation.md`。
- **portion推定プロンプト A/B 完了（v14 vs v13, dev40, run 20260601_232440）**: v14（キャップ撤廃＋スケールアンカー＋高さ＋隠れ油）は **TS slope 0.42→0.66 と改善（診断確証=キャップが圧縮要因）** だが **signed -5.3%→+14.8% と過補正**、MAE 22→24・high30 20→32.5 で**採用不可(hold)**。→ **プロンプト単独は過補正。slopeを1.0へ landする principled fix は post-hoc calibration層（外部held-out fit）**。lesson: `20260601_v14_scale_anchor_raises_slope_but_overcorrects.md`。
- **2026最新ベストプラクティス調査 完了**: `docs/PIPELINE_IMPROVEMENT_PROPOSALS_20260601.md`。根本改修が要るのは2箇所(=portion prompt 微調整 + calibration層)のみ。model/retrieval/eval設計/ensemblingは現状が best-practice で変更不要。現実的目標は 20-30% MAPE（11.4%はartifact）。
- **eval強化（A 完了）**: `compute_decomposed_metrics` に Theil-Sen slope 追加（OLSは attenuated・保持、Demingはδ依存で不採用）。markdownに ts_slope 列。
- **post-hoc calibration層 実装完了（default OFF）**: `core/calorie_calibration.py`(affine map+clamp) / `config/calorie_calibration.json`(disabled no-op) / pipeline `_apply_calorie_calibration`(total+dish+ingredient+weightを同一factorで整合スケール, __init__でload, 2箇所wired) / `scripts/fit_calorie_calibration.py`(Theil-Sen fit+held-out検証+config書出) / テスト8件(venv 43 passed)。**held-out検証(dev40 fit→holdout10): MAE 18.7→15.0%, bias -6.5→-0.5%**。lesson: `20260602_calorie_calibration_layer_implemented.md`。
- **本番有効化の前提（未完）**: 外部held-out取得→fit→`enabled=true`→frozen50で再検証。現状は disabled no-op で挙動不変。改善の大半はbias除去(R²~0.16が弱いため)で、slope自体の改善には portion推定向上が別途必要。
- **v14b A/B 完了（run 20260602_090935）**: v14b は過補正せずバイアス中和（signed -6.68→+0.77）・slope微増(0.32→0.40)だが **MAE不変**(20.59 vs 20.78, p=0.95)。calibration併用(2-fold CV dev40): v13+calib=**16.89%** > v14b+calib=17.58% → **v14bのprompt de-biasは calibration と冗長**。**v13維持 + calibration層が最良**。lesson: `20260602_v14b_mild_redundant_with_calibration.md`。
- **広いVLM/thinkingスイープ 完了（run 20260602_092436, dev40, 8候補, v13固定, 全40/0成功）**: RAW MAEでは**有意な勝者なし**（全paired CIが0またぎ, ~20%）。だが **TS slope は thinking上位ほど高い**: gemini-3.1-pro **0.67** > flash-high 0.53 > flash-medium(現行) 0.40 > gpt-5.1 0.47 > 3.5-flash 0.24。**calibration併用(2-fold CV)**: gemini-3.1-pro+calib **14.72** > flash-high+calib 15.77 > 現行+calib 16.42。
- **結論（「thinking上位が良い」仮説 = slope経由で検証）**: モデルの差は「分量の判別力(slope)」に出て、RAW MAEではバイアスに埋もれて見えない。calibrationがバイアスを消すと、高slopeモデルが calibrated MAE で勝つ。→ 以前の「モデル凍結・交換は無駄」結論を**改訂**（RAW MAEでは正しいが、calibration前提では誤り）。lesson: `20260602_broad_vlm_sweep_thinking_helps_slope.md`。
- **アップグレード候補2つ**: (安価) 現行モデルで `reasoning_effort=high`（config変更のみ, slope 0.40→0.53, calib~15.8%, やや遅い）/ (最良) `gemini-3.1-pro-preview`（slope 0.67, calib~14.7%, ~4x高価・遅い）。要 full50 + 外部held-out calibration で確認。
- 敗者確定: 3.5-flash(slope0.24), kimi-k2.5(55%・崩壊), qwen3-vl-235b(過大+15.6%), gpt-5.1(凡庸)。

### Judge Eval トラック（full-output / user-conviction KPI）
- 設計正典: `docs/JUDGE_EVAL_DESIGN_20260602.md`、運用rubric: `docs/EVAL_RUBRIC.md`。最終KPI=user-conviction（認識/命名/分量/栄養/総合）。total-calorie MAEは補完。
- **v0 実装済（依存ゼロ・LLM不要）**: `dish_match_metrics` の similarity を difflib→`max(char-LCS, token-overlap)` + matched_desc併用 + T=0.75。portion bands・nutrient self-consistency 追加。summary.json 追加キー `recognition_agg`/`portion_bands`/`nutrient_self_consistency_rate`。**実データで recognition F1 0.068→0.259**（gemini-3-flash, run 20260602_092436再計算）、nutrient自己整合0.967。venv 46 tests passed。
- **judge機構 整備済（scaffold）**: subagent `.claude/agents/meal-output-judge.md`（Claude(VLM)-as-judge, 写真+GT grounding, 6次元0-5, locked JSON, bias対策込）。
- **v1（要ユーザ承認）**: `scripts/run_judge_eval.py`（finished run後処理）+ golden 15-25枚人手ラベル + perturbation検証。要決定: (1) recognition F1向上のための **embedding依存追加の可否**, (2) **golden_set ラベリング**, (3) v1 judge実行（Claude vision, APIコスト）のgo/no-go。
- **v1 judge runner 実装＋実評価済（advisory）**: `scripts/run_judge_eval.py`（OpenRouter経由Claude vision、写真+GT+候補、幾何平均conviction、bootstrap CI、failure_tag集計、cache、judge_contract）。rubric `evals/judge/judge_rubric_v1.txt`。**3モデル×dev40 実評価（run 20260602_092436, judge=sonnet-4.6）**: conviction 全モデル ~38-39/100 で **CI重複＝モデル差なし**。**最弱=naming_db_match 1.6**、failure_tags は bad_usda_match 39/wrong_food_identity 38/raw_vs_cooked 23 が支配 → **user-convictionの最大ボトルネックはUSDA照合品質**（calorie MAEでは「検索非ボトルネック」だがKPI別に訂正）。~5 edits/img・45%要人手。lesson: `20260602_judge_conviction_usda_matching_is_top_bottleneck.md`。**advisory（golden未検証、絶対水準は要校正・相対パターンは頑健）**。
- **USDA照合品質 着手→診断完了**: /retrieve 探針で **クリーンGT名なら検索は~8/9で正解**（retrievalは非ボトルネック、予測名==matched_descで検索は忠実）。誤マッチはVLMの食品命名/識別由来と判明。
- **v15(自然名)仮説 棄却**（run 20260602_133904 + judge 20枚）: naming_db_match 1.9→1.8/conviction 44.7→41.7 で**改善せず**（CI重複）。`wrong_food_identity` は両promptで~20/20。命名スタイルは非レバー。**照合誤りは VLM食品識別(capability, モデル横並び)＋認識取りこぼし＋GT細粒度/judge厳しさ の複合**。token-F1とjudgeが食い違い→**未検証judgeへの最適化の罠を実証**。**v13維持**。lesson: `20260602_v15_natural_names_rejected_matching_is_capability_bound.md`。
- **judge discriminative-power ゲート 合格**（`run_judge_validation.py`, 合成劣化注入）: wrong_food→recognition 0.83 / portion_2x→portion 1.0 / calorie_inflate→nutrient 1.0、**総合 0.944, gate_pass=True**。→ **judgeは誤りを実際に検出でき、相対ランキング/検出は信頼可**。これまでの所見（naming弱・v15棄却・conviction~39）は実在で、judge厳しさのアーティファクトではない可能性が高い。lesson: `20260602_judge_passes_discriminative_power_gate.md`。
- **残: 絶対校正（golden κ）**。golden雛形 `evals/judge/golden_set.template.jsonl`（6枚分生成済、15-25枚へ拡張）。要ユーザ: human_scores 0-5 をラベル → `--golden` で κ/Pearson 検証 → 合格で絶対floorをゲートに(v2)。
- **judge golden キット 整備完了 ＋ Opus高精度ドラフト ＋ 暫定一致**:
  - キット: `docs/GOLDEN_LABELING_GUIDE.md`、`run_judge_validation.py --golden`(quadratic-weighted κ + Pearson, 依存なし)、`evals/judge/labeling/*.json`(20入力)、`evals/judge/golden_set.draft_claude.jsonl`(Opus 4.8 max-care ドラフト、**人手レビュー用**)。
  - 暫定一致(judge vs Opusドラフト, ※循環の限界・人手確定が真の検証): **naming κ0.67 / conviction κ0.57 は頑健**(照合最弱・conviction低の所見を裏付け)、**portion κ0.17 / nutrient κ0.22 は不安定**(rubric定義が曖昧、特にnutrient: Opus 4.0 vs judge 2.4)。composite r0.71, gate未通過。lesson: `20260602_golden_kit_and_judge_self_agreement.md`。
- **rubric v2 厳格化 完了＋検証**: `evals/judge/judge_rubric_v2.txt`(既定化, `--rubric-version`)。nutrient定義を「加算整合≠nutrient validity / density＋macro vs GT」に明確化、portionを帯域化。再検証(judge-v2 vs Opus-draft-v2): **nutrient κ 0.22→0.64(合格)・r 0.64→0.81**、total/composite改善。**portionは r 0.39→0.63 だが κ 0.19(band閾値の絶対差残る→v3課題)**。lesson: `20260602_rubric_v2_stabilizes_nutrient.md`。
- **rubric v3(portion機械化) 検証→棄却(未昇格)**: `judge_rubric_v3.txt`(EXPERIMENTAL, default維持=v2)。portionを「マッチ集合特定＋per-item rel_err＋f25/f10閾値表」に機械化。再走(judge-v3＋Opus-draft-v3): **portion r 0.63→0.42に悪化・κ 0.27**（系統+1オフセット→マッチ/算術ノイズに転化。fast judgeが per-item計算を安定実行できず1↔5に振れる）。**rubric未変更のnutrientまで κ 0.64→0.41 に動いた＝n≈20自己一致は再走ノイズ±0.4で過小検出力**。**結論: portionはNUMBERS問題でLLM judge向きでない**。既存の決定的 `dish_match_metrics.portion_bands`(Hungarian, ばらつきゼロ)から0-5化すると **Opus draftとの一致 κ=0.50 > fast judge 0.27** かつ自己一致κ=1.0。残ギャップ=token/charマッチャ(T=0.75)の意味的取りこぼし(test_food11/13でdet=0)→embedding化で縮小。lesson: `20260602_rubric_v3_portion_should_be_deterministic.md`。
- **(A) portion決定的化 実装完了(ユーザ承認済)**: `portion_score_from_bands()` 追加、`dish_match_metrics` に `portion_score_0_5` additive key、batch summary に `portion_score_0_5_mean`。`run_judge_eval` は conviction を **決定的portionで再構成**(LLM portionは `source:llm_advisory` で残す・融合に不使用)、judge summary に `portion_deterministic_mean`/`portion_source`。dev40検証(run 20260602_092436): portion_deterministic_mean=3.025, conviction=36.04。tests 46→48 passed, ruff clean。EVAL_RUBRIC.md 更新。
- **(B) matcher embedding化 実装＆検証→negative(既定はtoken維持)**: `EmbeddingSimilarity`/`build_embedding_fn`(既存 `EmbeddingProviderFactory`/Qwen3-Embedding再利用、新規依存なし)を追加、`run_judge_eval --match-embeddings`(opt-in, default off)で配線。**検証(20 golden vs Opus-draft-v3)**: embeddingはrecall↑(matched/GT 0.31→0.44, test_food4/11/13のdet=0解消)だが**正マッチも落とし(food6/7: 5→0)κが 0.503→0.12-0.16に悪化**。instruction有/無・閾値0.75-0.94スイープでも token(κ0.503)を超えず(最良0.164)。句レベル食品名cosineはHungarian一対一に識別力不足。**token/char matcherを既定維持**、`--match-embeddings`はEXPERIMENTAL(有効化非推奨)。次のmatchingレバーはbi-encoderでなく**cross-encoder/reranker(既存Qwen3-Reranker)or held-out閾値校正**。lesson: `20260602_embedding_matcher_does_not_beat_token.md`。50 tests passed(+2)。
- **(C) 残: 人手golden**: ユーザがドラフト(`golden_set.draft_claude_v2.jsonl`)をレビュー→`golden_set.jsonl`確定→人手κ。naming/conviction/nutrientは相対A/Bに使用可。

### Matching品質 PDCA（cross-encoder/reranker, ultracode research+診断+A/B）
- **リサーチ+診断 workflow(7 agents)**: 本番は既に **Qwen3-Reranker(4B/8B) がStage-5セレクタ**(hybrid_search.py:1253)。149 per-dishマッチ欠陥のうち **~74(~50%)が reranker修正可能**(形態誤り33+粒度誤り41)、(c)VLM誤認55は不可。主バイアス=「最低脂肪/淡白を選ぶ」「generic>specific」。
- **🔴 根本バグ発見・修正**: **`config.reranker.instruction` は本番でずっと no-op**。DeepInfra rerank は payload の `instruction` を無視(検証: fat-free優先 vs full-fat優先でスコア完全一致)。Qwen3は instruction を **queryに焼き込む**必要(`Instruct:..\nQuery:..`)。`deepinfra_service.format_reranker_query` で修正(`rerank`/`rerank_batch`両方)、4 tests。**これが「低脂肪バイアス」の一因**。
- **dev40 3-arm A/B(同一VLM=cache共有でreranker単独分離, Firestore非変更)**: raw(現状=instruction無効) / default(修正=既定instruction適用) / hardened(+低脂肪/composite/cooked規則)。**結果(judge v2 advisory)**: default が naming 1.675→**1.825**・per-dish correct 14.5→**16.3%**・worst-tail cal 27.5→**15.0%** と mild改善。**hardened は棄却**(correct 13.1%/conviction最低, 過剰steeringで巻添え誤マッチ)。**reranker は conviction主レバーでない**(支配=wrong_food 78-84/hallucinated 57-62=VLM認識)。
- **結論/次**: (1) **バグ修正をship**(=intended `config.reranker.instruction` を有効化, **本番挙動変更→deploy判断は要ユーザ**, 既定instructionはmild-positiveで安全)。(2) hardened不採用。(3) **次PDCAはVLM認識**(hallucination/missed/wrong-food削減)へpivot=conviction真の天井。lesson: `20260602_reranker_instruction_was_inert_bug_fixed.md`。

### VLM認識 PDCA（conviction真の天井, ultracode research+診断+A/B）
- **リサーチ+診断 workflow(7 agents)**: dev40の認識失敗を定量化 — hallucinated ~1.55/img(phantom apples 11/40枚, phantom標準サイド, phantom調味料/油), missed ~2.1/img, wrong_food ~2.0/img(couscous→rice 5/5, caesar既定, mac&cheese→plain pasta, broccoli→cabbage)。研究: 最大レバー=visibility-grounding + 強制abstention + self-verification。
- **v16(grounding+visible_evidence field+全皿scan+describe-shape) → 棄却**: anti-hallucination狙い外れ(**幻覚むしろ増** 1.90→2.02, evidence-field/scanが列挙促進)。但し**describe-shapeで wrong_food 76→61減**。conviction横ばい。lesson: `20260602_v16_grounding_mixed_identity_helps_evidence_field_backfires.md`。
- **v17(describe-shape識別のみ isolate) → candidate(未promote)**: wrong_food **78→68減(v16と2回再現)**, correct% 13.6→15.4, conviction 31.47→33.67(+2.2), 幻覚スパイクなし。但し**全てn=40 judgeノイズ域の縁**, cal_MAE 16→21微悪化(cooked-default高密度寄り)。lesson: `20260602_v17_describe_shape_identity_mild_win_near_noise.md`。
- **メタ結論**: **conviction は gemini-3-flash で ~32/100 の天井**、単一prompt/rerankerレバーは全て n=40 judgeノイズを超えない=VLM認識capability-bound。非marginalな改善には**self-verification 2nd pass / 上位VLM / multi-sample**等の大投資が必要。
- **次options(要判断)**: (1)v17を50枚full+安定性+calorie方向確認→promote (2)self-verification 2nd pass実装(config flag, ~2x cost) (3)モデル選定見直し。
- **v2（judge golden検証合格後）**: `gate_decision` に judge floor（naming等）+ conviction delta を flag配線（default OFF）。

### 要フォローアップ
- **本番 prompt_file label 修正**: v13デプロイ後に prompt_file=v13 + prompt_text=null へ（今は v13未デプロイのため不可。現状のoverrideがv13内容の唯一の保持先）。
- **Item 2 (weight sweep) 完了**: 有効キーでローカル起動（Track B修正済み検索, v13, in-memory）→ dev40で6候補評価（run 20260601_211040）。**どのweightも calorie MAEを有意改善せず**（全paired CIが0をまたぐ, p>0.3）。検索weightはcalorie MAEのボトルネックでない（VLM portion推定＋model劣化が支配）。Track B修正は安全（現行weight 21%＝full50の~20%と整合）。lesson: `20260601_retrieval_weight_sweep_no_promote.md`。code default weightは据え置き。
  ```bash
  PROD=https://freeform-usda-meal-analysis-api-1077966746907.us-central1.run.app
  # 方法1: 対象フィールドのみ更新（推奨・他のprod設定を温存）
  curl -X PUT "$PROD/admin/api/config?updated_by=ops_v11b_promote" -H "Content-Type: application/json" \
    -d '{"updates": {"vlm.prompt_file": "freeform_prompt_usda_format_ver_v11b_gemini_component_density_20260225.txt", "vlm.prompt_text": null}}'
  # 方法2: 全体をコード既定へreset（他のprod独自設定も初期化されるので注意）
  # curl -X POST "$PROD/admin/api/config/reset?updated_by=ops_reset_v11b"
  # 検証
  curl -s "$PROD/admin/api/config?refresh=true" | python -m json.tool | grep -E "prompt_file|prompt_text|updated_at"
  curl -s "$PROD/health" | python -m json.tool | grep -E "config_drift|prompt_file|prompt_text_override"
  ```
  実施後は `evals/lessons/` に記録する。注意: `/admin` は現状**未認証**（別途P3: 認証付与）。

### 要フォローアップ（API実行が必要）
- **検索融合weightの再sweep**: Track Bで `1/(1+d)`→直接類似度 + クエリ正規化に修正。現行の bm25/vector/rrf weight は歪んだ目的関数でチューニング済のため、hardened gate（paired CI）で `stage1_top_k` / `bm25_weight` / `vector_weight` / `rrf_k` / `rrf_weight` を再探索する。
- **paired gateの使い方**: 実験configに現行baseline構成を1候補として併走させ、`--paired-baseline-candidate <その候補名>` を指定。promoteは paired 95%CI上限<0 のときのみ。昇格前に `run_pdca_repeated_eval`（最低2-3反復, stability=stable）も必須。

## 次セッション参照
- `docs/DEEP_REVIEW_20260601.md`（§6 ロードマップ18項目, §7 整備プラン, §8 次アクション）
- `docs/PDCA_SESSION_START_CHECKLIST.md` / `AGENTS.md`
- 精度PDCA着手前に `/pdca-bootstrap` を実行

## Session Log
| Date | Session | 作業内容 |
|------|---------|---------|
| 2026-06-01 | deep-review | 15エージェントworkflowで全体レビュー→`DEEP_REVIEW_20260601.md`生成。主要P0をコード検証。Track D（Claude Code基盤）完了。 |
| 2026-06-01 | deep-review | Track A: paired BCa bootstrap CIゲート + sign-flip検定 + own-MAE CI + per-image誤差永続化 + seed/gen_id記録（`run_pdca_batch_eval.py`）、コード強制stability判定（`run_pdca_repeated_eval.py`）。後方互換維持（既存3テスト通過、計15テスト）、ruff/py_compile OK。**知見**: 同一構成2runで MAE 9.95 vs 13.28（paired CI [0.83,8.25], p=0.04）= run間VLM非決定性が大。→ paired gateは同一invocation併走baseline必須（実装で強制）+ 反復stability必須。 |
| 2026-06-01 | deep-review | Track B: `hybrid_search.py` の dense score を `1/(1+d)`→直接コサイン類似度に修正（3 rerankerパス）+ 全4 search呼び出しにクエリL2正規化（`l2_normalize_rows`, corpus構築と同式）。`apply_weighted_fusion`/`search_vector` の旧経路は既に直接類似度で正・両経路を整合。ruff/py_compile OK, テスト追加（dotenv不在のためCI以外でskip, ロジックはスタンドアロン検証済）。**要**: 融合weight再sweep。 |
| 2026-06-01 | deep-review | Track C: config-fidelity assert（`--assert-config-fidelity`、served model/prompt≠candidateでconfig_drift失敗→hold gate, opt-in後方互換）、`ConfigManager.detect_config_drift()` + `/health` に config_drift/drift_fields/prompt_text_override_active/schema_version 公開 + WARNINGログ、`APIConfig.schema_version` 追加。settings既定=v11bでprod=v7のdriftを自動検出可能に。19 passed・ruff/py_compile OK。**本番promoteは未認証/本番操作のためユーザー実行待ち**（手順上記）。 |
| 2026-06-01 | deep-review | 全コード変更を敵対的レビュー（3観点workflow→独立検証）。統計(BCa)/検索修正/後方互換は問題なし。確定1件: paired要求時にCI degenerate/不可なら黙って1.0pt marginに降格していた→`gate_decision` に `paired_requested` 追加し、その場合は fail-loud で `hold`(gate_mode=`paired_unavailable`)。テスト+3で計22 passed, ruff/compile OK。 |
| 2026-06-01 | deep-review | Item1完了: 本番実態=v13(v11b+飲料対応, 2/26 admin, 未ベンチ)を保全。リモートprodで v13 vs v11b paired評価(run 20260601_204037)→ **同等(p=0.84)**, prod現行v13維持。コード既定をv13に昇格。**🚨 v11b baseline非再現(11.38%→20.27%)=model/infraドリフト疑い**→lesson記録, 再ベースライン要。Item2(weight sweep)はローカルキー無効でブロック→ユーザーがキー設定後に実行。 |
| 2026-06-01 | deep-review | Item2完了: 有効キーでローカル起動(Track B修正検索, v13)→ weight sweep(dev40, run 20260601_211040)→ **どのweightも有意改善せず**(全paired CI 0またぎ), 検索はcalorie MAEのボトルネックでない。再ベースライン+ドリフト調査(full50, run 20260601_221426): **新gemini群は回復せず**(3.5悪化/3.1-lite同等), gemini-3-flash-preview維持。~20%は安定再現。**baseline を 20.65% にリセット**(旧11.38%保持)。劣化根本原因未特定→次はmetric分解で局在化。サーバ停止(キー除去)。 |
| 2026-06-01 | deep-review | metric分解 実装(signed bias/calibration slope/abs kcal/macro MAE + Hungarian dish-match, PART A永続化, markdown診断section)+ 既存runに遡って局在化 → **20%=portion過小推定(calib slope≈0.47, 大盛りほど過小, fat最悪)=VLM問題で検索でない**。30 tests passed, ruff/compile OK。次レバー=portion推定prompt。 |
| 2026-06-01 | deep-review | パイプライン改修提案workflow(11 agents)→ `docs/PIPELINE_IMPROVEMENT_PROPOSALS_20260601.md`: 根本改修は portion prompt + calibration層の2点のみ、model/retrieval/eval/ensembleは現状best-practice。realistic目標20-30%。load-bearing主張(v13キャップ実在/clamp無/calibration無/外部held-out無)をコード検証済。 |
| 2026-06-01 | deep-review | (A) eval に Theil-Sen slope 追加(robust, OLS保持, Deming不採用), markdown ts_slope列。31 tests。(B) v14(scale anchor+uncap) vs v13 A/B(dev40, run 20260601_232440): **slope 0.42→0.66改善=診断確証**だが signed -5.3→+14.8%過補正・MAE悪化→**hold**。プロンプト単独は過補正→次はcalibration層(外部held-out要)。サーバ停止(キー除去, repoにキー無し確認)。 |
| 2026-06-02 | deep-review | post-hoc calibration層 実装(core/calorie_calibration.py + config + pipeline統合(整合スケール) + fit_calorie_calibration.py + tests)。**held-out検証 dev40→holdout10: MAE 18.7→15.0%, bias -6.5→-0.5%**。default OFF(disabled no-op)。本番有効化は外部held-out fitが前提。venv 43 tests passed, ruff/compile OK。 |
| 2026-06-02 | deep-review | v14b A/B(run 20260602_090935): 過補正回避でbias中和(slope0.32→0.40)だがMAE不変、calibrationと冗長→hold, v13維持。広いVLMスイープ(run 20260602_092436, 8候補): RAW有意差なしだが **thinking上位ほどslope高**(gemini-3.1-pro 0.67>flash-high 0.53>現行0.40), **calib併用で pro 14.7%<flash-high 15.8%<現行16.4%**。「thinking最良」仮説をslope経由で検証、「モデル凍結」結論を改訂。アップグレード候補: reasoning高(安価)/gemini-3.1-pro(最良・高価)。要full50+外部held-out確認。 |
| 2026-06-02 | deep-review | Judge eval 設計workflow(8 agents)→ `JUDGE_EVAL_DESIGN_20260602.md`(40+出典)。KPIを user-conviction に再定義。**v0実装**(認識similarity difflib→token+string, matched_desc併用, T=0.75, portion bands, nutrient self-consistency, summary追加キー): 実データで F1 0.068→0.259, 46 tests passed。judge subagent `meal-output-judge` + `EVAL_RUBRIC.md` + AGENTS.md/plans 更新。 |
| 2026-06-02 | deep-review | **v1 judge runner 実装＋実評価**(`run_judge_eval.py`, OpenRouter Claude vision, rubric_v1)。3モデル×dev40 (run 20260602_092436): **conviction ~38-39で全モデル差なし(CI重複)**、**naming_db_match 1.6 が最弱**、failure_tags=bad_usda_match39/wrong_food_identity38/raw_vs_cooked23支配 → **user-convictionの最大ボトルネック=USDA照合品質**(calorie別では検索非ボトルネックを訂正)。advisory(golden未検証)。lesson: `20260602_judge_conviction_usda_matching_is_top_bottleneck.md`。次=照合品質改善+judge golden検証。 |
| 2026-06-02 | deep-review | USDA照合品質 着手: /retrieve探針で**クリーンGT名なら検索~8/9正解**(retrieval非ボトルネック確定)。**v15(自然名)仮説をA/B+再judge→棄却**(run 20260602_133904): naming 1.9→1.8/conviction 44.7→41.7 改善なし、wrong_food_identity 両prompt~20/20。照合誤りはVLM食品識別(capability)＋認識取りこぼし＋GT細粒度/judge厳しさの複合で命名スタイル非レバー。**token-F1とjudgeが食い違い→未検証judge最適化の罠を実証**。v13維持。lesson: `20260602_v15_natural_names_rejected_matching_is_capability_bound.md`。 |
| 2026-06-02 | deep-review | **judge検証: discriminative-power ゲート合格**(`run_judge_validation.py`, 合成劣化注入)。wrong_food→recognition 0.83/portion_2x→portion 1.0/calorie_inflate→nutrient 1.0、**総合0.944 gate_pass=True**。→ judgeは誤りを実検出でき相対ランキングは信頼可。これまでの所見(naming弱/v15棄却/conviction~39)は実在の問題でjudge厳しさ由来でない可能性大。残=絶対校正(golden κ, 要ユーザラベル)。golden雛形生成済。lesson: `20260602_judge_passes_discriminative_power_gate.md`。 |
| 2026-06-02 | deep-review | **golden検証キット完成 ＋ Opus 4.8 max-care ドラフトgolden(20枚) ＋ `--golden` κ/Pearson実装**。暫定一致(judge vs Opusドラフト): naming κ0.67/conviction κ0.57頑健、portion κ0.17/nutrient κ0.22不安定(rubric要強化)。`GOLDEN_LABELING_GUIDE.md`。次=ユーザがドラフトをレビュー→確定golden→人手κ→v2ゲート化、＋rubric v2でnutrient/portion厳格化。lesson: `20260602_golden_kit_and_judge_self_agreement.md`。 |
| 2026-06-02 | deep-review | **rubric v2 厳格化＋検証**: `judge_rubric_v2.txt`(既定化, `--rubric-version`, 出力`_v2`接尾)。nutrient=「加算≠validity / density＋macro vs GT」、portion帯域化。judge-v2＋Opus-draft-v2再走で再検証→ **nutrient κ 0.22→0.64合格・r 0.81**, total/composite改善, portion r改善(0.63)もκ低位(0.19, v3課題)。lesson: `20260602_rubric_v2_stabilizes_nutrient.md`。 |
| 2026-06-02 | deep-review | **rubric v3(portion機械化)→棄却(未昇格)**: `judge_rubric_v3.txt`(EXPERIMENTAL, default=v2維持)。per-item rel_err＋f25/f10閾値表に機械化→judge-v3＋Opus-draft-v3再走で **portion r 0.63→0.42悪化・κ0.27**(fast judgeが計算を安定実行できず1↔5に振れる)。**未変更のnutrientもκ0.64→0.41＝n≈20自己一致はノイズ過大**。**結論=portionはLLM不要、決定的`portion_bands`で0-5化すると Opus draftとの κ=0.50>fast judge0.27・自己一致κ=1.0**。残=token/charマッチャの取りこぼし→embedding化。lesson: `20260602_rubric_v3_portion_should_be_deterministic.md`。要サインオフ: portion決定的ゲート化(convictionの0.20重み変更)＋matcher embedding(新依存)。 |
| 2026-06-02 | deep-review | **(A)portion決定的化 実装(ユーザ承認3点: 決定的化+LLM advisory / embedding承認 / commit)**: `portion_score_from_bands()`＋`dish_match_metrics.portion_score_0_5`＋batch summary `portion_score_0_5_mean`。`run_judge_eval` conviction を決定的portionで再構成(LLM portionは `source:llm_advisory`)、judge summary に `portion_deterministic_mean`/`portion_source`。dev40検証: portion_deterministic_mean=3.025, conviction=36.04。**48 tests passed(+2)・ruff clean**。EVAL_RUBRIC.md更新。commit e0cb962。 |
| 2026-06-02 | deep-review | **(B)matcher embedding化 実装＆検証→negative**: `EmbeddingSimilarity`/`build_embedding_fn`(既存Qwen3-Embedding再利用, 新規依存なし)＋`run_judge_eval --match-embeddings`(opt-in)。**20 golden検証: embeddingはrecall↑(0.31→0.44)も正マッチ脱落でκ 0.503→0.12-0.16に悪化(instruction有無・全閾値でtoken未達)**。既定はtoken維持、flagはEXPERIMENTAL(非推奨)。次レバー=cross-encoder/reranker or held-out閾値校正。**50 tests passed(+2)・ruff clean**。lesson: `20260602_embedding_matcher_does_not_beat_token.md`。 |
| 2026-06-02 | deep-review | **Matching PDCA(reranker): リサーチ+診断workflow(7 agents)→ 🔴根本バグ発見・修正**: `config.reranker.instruction` は本番でno-op(DeepInfra が payload `instruction` 無視、検証済)。Qwen3はquery焼込必須→`deepinfra_service.format_reranker_query`で修正(4 tests)。**dev40 3-arm A/B(同一VLM=reranker単独分離)**: バグ修正(default)で naming 1.675→1.825/correct 14.5→16.3%/worst-tail cal 27.5→15.0% mild改善、**hardened棄却**(過剰steering)、**reranker は conviction主レバーでない(VLM認識が支配)**。→(1)バグ修正ship(本番挙動変更=deploy要ユーザ)(2)hardened不採用(3)次PDCA=VLM認識へpivot。lesson: `20260602_reranker_instruction_was_inert_bug_fixed.md`。 |
| 2026-06-02 | deep-review | **VLM認識 PDCA(conviction天井): research+診断(7 agents)→ v16/v17 A/B**。診断: hallucinated ~1.55/img(phantom apples 11/40)/missed ~2.1/wrong_food ~2.0(couscous→rice 5/5等)。**v16(grounding+evidence field)棄却**(幻覚増, describe-shapeのみ wrong_food↓)。**v17(describe-shape isolate)=candidate**: wrong_food 78→68(2回再現)/conviction 31.5→33.7だが**n=40ノイズ域・cal_MAE微悪化**で未promote。**メタ: conviction ~32天井=VLM capability-bound, 単一レバーはノイズ超えず**。次=self-verification 2nd pass or 上位VLm。lessons: v16_grounding/v17_describe_shape。 |
