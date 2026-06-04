# mozu PDCA サマリ & 結論（2026-06-03〜06-04）

このアプリ（`freeform_usda_meal_analysis_api` = mozu 用「写真→カロリー推定」API）の、モデル採用（gemini-3.1-pro vs gemini-3-flash）と「欧米料理で十分汎用的か」を巡る PDCA の総括。詳細根拠は各 `evals/lessons/` と `MOZU_MODEL_DECISION_20260603.md`（SSOT）。

## 問い
「mozu に gemini-3.1-pro を採用すべきか。そのモデルは実世界の欧米料理で十分なカロリー精度を持つか。」

## 経緯（Plan→Do→Check→Act）
1. **当初**: frozen-50（社内50枚, eye-level 盛付）で pro を採用候補に決定（recognition 4/4・速度同等・コスト ~3.2x）。calorie MAE ~18% と良好に見えた。
2. **🔴 方法論の重大訂正**: frozen-50 の **GT は GPT-5-pro の推定値**（confidence・5g丸め重量で確定）。よって「~18%」は実精度でなく **GPT-5-pro との一致度**。これに合わせた calibration や bias 補正は「gemini→GPT-5-pro 学習」で実精度を保証しない → **calibration JSON を全 VOID、follow-up の bias 補正を停止**。eval は **TWO-GATE**（実測GTゲート＋50画像の現実性ゲート）へ。
3. **独立 measured-GT セットを3つ構築して Check**:
   - **Nutrition5k**（俯瞰・実測, 250, 2 run）
   - **NutritionVerse-Real**（eye-level・実測, 104 content-verified）
   - frozen-50 は「画像の現実性」用に残置（ラベルは真値扱いせず）

## 主要な発見（honest）
### A. 実世界カロリー精度は frozen-50 が示すより大幅に悪い
| セット | 角度/GT | flash MAE | pro MAE |
|---|---|---:|---:|
| frozen-50 | eye-level / GPT-5-pro推定 | ~18-20% | ~17-18%（=一致度, 実精度でない） |
| Nutrition5k | 俯瞰 / 実測 | 66-68% | 58-62% |
| NutritionVerse-Real | eye-level / 実測 | **40.0%** | **42.2%** |
→ 実測では **~40-60%**。狭い社内50枚は実世界精度を **約3倍 楽観的に過大評価**していた（汎化ギャップ実証）。

### B. pro の calorie 優位は「非頑健」（分布依存で符号が flip）
- frozen-50: pro≈flash（NS）／ N5k: pro −7pt（borderline, 2 run の denoised CI[-15.2,+0.9]）／ NVReal: **flash が +2.2pt 良い（NS）**。
- **3 セットで pro−flash の符号が反転 → pro に頑健な calorie 優位は無い**。N5k 単独 run1 の「有意」は楽観 draw だった。
- bias 方向も分布依存（frozen-50 pro −5%／N5k 両者 +30-49% 過大／NVReal pro −14% 過小）。→ **単一の calibration は不可能、実データ必須**。

### C. 共通の弱点 = 大皿の過小評価
- 両モデルとも calib_slope ≈ 0.12-0.72：料理が大きいほど予測が圧縮され、大型マルチ品プレートを大幅過小評価。portion 推定が本質的弱点（モデル差より大きい）。

### D. pro の recognition 優位も独立 GT で消滅（最後の砦が崩れた・2026-06-04）
- frozen-50 では recognition F1 が flash 比 4/4 向上に見えたが、それは **GPT-5-pro の命名との一致度**。
- **クリーンな独立 GT（NutritionVerse-Real の COCO 食材ラベル, 104画像/309食材）で再測定**（既存 flash/pro 予測を Claude judge で意味採点, OpenRouter課金ゼロ）: **flash recall 82.5% vs pro 80.6%（pro やや劣・誤認多・per-image 引き分け75/104）**。→ **pro に recognition の実優位は無い**。
- recognition 自体は良好（~82% recall）。token-F1 0.12 は名前形式のマッチング artifact だった。失敗モード=lobster見落とし/jam-toast果物誤認/cucumber。
- pro は run 間再現性も flash より低い（bit-identical 20% vs 52%）。

### E. 運用上の落とし穴（記録済）
- 外部 eval セットは **必ず画像を目視**：NutritionVerse-Real は image `dish_N` ≠ metadata `dish_id` で、naive id-join が **40% の GT を誤らせた**。schema/合計チェックでは検出不能。COCO 内容ベース join + 目視で 104 件に是正。

## 結論 / 推奨（2026-06-04 最終）
- 🔴 **pro 採用を撤回し flash を推奨**。pro は **calorie でも recognition でも、独立 GT に対し flash への頑健な優位が無い**（calorie=符号 flip／recognition=クリーン GT で flash 82.5 vs pro 80.6%）。**~3.2x のコストを正当化できない → flash（同等精度・1/3コスト）**。コード既定は現状 pro のまま＝**要 flash へ戻す（ユーザ明示指示待ち）**。
- **「欧米料理で十分汎用的か」への答え**: 現状の v13 + USDA 検索パイプラインは、**実世界の欧米料理で総カロリー MAE ~40-60%**（本命 200-1500kcal で ~27%, near-unbiased）。frozen-50 が示した ~18% は楽観。誤差は**系統 bias でなく純粋分散**（portion:matching = 50:50）で、prompt-tuning では動かない。recognition は良好（~82%）。
- **残る本物の lever**（モデル選択でなくこれが本質）: ①**分散低減（self-consistency）= 検証済・有効**（flash temp0.5 K=3 median で本命 28.6→21.6%, 有意。採用候補）②実 mozu measured データでの per-food-type calibration ③recognition 個別失敗（lobster/jam/cucumber）の是正。
- **calorie の最終 arbiter は実 mozu ユーザーの measured データのみ**。3つの公開セットはいずれも lab/studio で、真の本番分布ではない。

## 本命レンジ誤差の分解（2026-06-04・無料診断）
現実的レンジ(200-1500kcal)の ~27% MAE を `calorie比 = grams比 × density比` に分解（NVReal+N5k で確認）:
- **両セットで calorie bias ほぼゼロ**（NVReal 0.98 / N5k 1.02）＝**系統的に直せる偏りが無い純粋な分散**。
- **誤差寄与 ~50:50（portion : 食材マッチング density）**（NVReal 50:50 / N5k 54:46）。
- 個別偏り（NVReal の grams 0.88過小 / density 1.14過大）は**セット固有で相殺**＝一般 lever でない。片方だけ直すと相殺が崩れ悪化。
- 反実仮想: grams 完璧でも 23.7% / density 完璧でも 19.7% 残る＝**写真推定の分散は本質的**。
→ **calorie の残る lever は「分散低減（self-consistency / multi-view 平均）」か「実データでの per-food-type calibration」のみ**。prompt-tuning では本命レンジを動かせない（lesson `20260604_realistic_range_error_decomposition_grams_vs_density`）。

## ✅ 分散低減（self-consistency）が効いた — セッション初の本物 calorie lever（2026-06-04）
分解診断で「本命誤差=純粋分散」と分かったので、flash を temp0.5・K sample し total-calorie を集約:
- **本命 200-1500kcal: 本番 temp0.3 single 28.6% → K=3 median ensemble 21.6%（Δ−6.9pt, paired CI[-13.7,-0.7] 有意, n=40 NVReal）**。
- **median > mean**、**K=3 が sweet spot**（K=4/5 頭打ち）、temp~0.5 の多様性（CV0.13）が必須（temp0.3 は再現的すぎて効かない）。
- コスト 3×flash ≈ single pro だが精度は pro 超（21.6% vs pro ~27%+）。
- **採用候補: flash, temp~0.5, K=3, median(total-calorie)**。要 pipeline に self-consistency wrapper／N5k で汎化確認／temp・K sweep。lesson `20260604_self_consistency_median_ensemble_significant_calorie_win`。

## 次の一手（優先順）
1. **実 mozu ドメインの measured アンカー構築**（Western・eye-level phone 20-50枚を実測×USDA）→ ここで初めて calorie の本採用判定 & 乗算的 calibration が可能。
2. ~~**portion 過小（大皿圧縮）の是正**~~ → **試行済・本命レンジに効かず（2026-06-04）**。v14（anchor を視覚量にスケール＋重量上限緩和）は **calib_slope 0.118→0.170 と圧縮を緩和したが、MAE 改善は非現実的な特大>1500kcal 巨大皿のみ由来で、現実的 200-1500kcal は 27.1→27.0% と改善ゼロ（全帯 NS）**。→ **本命レンジの ~27% 誤差は「圧縮」でなく per-item（グラム/マッチング）が要因**。prompt-portion は lever でない。不採用（v13維持）。lesson `20260604_v14_portion_scaling_helps_slope_but_not_realistic_range`。残: 小皿過大は weight floor 80→20 で別途試行可。
3. ~~**recognition で pro の優位が保たれるか確認**~~ → **実施済・pro優位なし（2026-06-04）**。クリーン独立 GT（NVReal COCO）で flash 82.5 vs pro 80.6% recall。recognition 自体は ~82% で良好。改善するなら個別失敗（lobster見落とし/jam-toast果物誤認/cucumber）を狙う。lesson `20260604_recognition_clean_gt_pro_no_edge_flash_cost_rational`。
4. **モデル既定を flash へ戻す**（settings.py/config_manager, 現状 pro）＝要ユーザ明示指示。
5. 本番 deploy は上記が揃ってから（要ユーザ明示指示・予算確認）。
