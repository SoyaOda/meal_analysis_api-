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

### D. pro で生き残る根拠 = recognition のみ（ただし狭い）
- frozen-50 で recognition F1 が flash 比 **4/4 run 再現的に向上**（決定的・信頼）。
- ただし N5k/NVReal では成分名が USDA 形式と token 不一致で recognition を測れず、**外部での再確認ができていない**。
- pro は run 間再現性が flash より低い（bit-identical 20% vs 52%）＝本番で「同写真→kcal 揺れ」が大きいトレードオフ。

### E. 運用上の落とし穴（記録済）
- 外部 eval セットは **必ず画像を目視**：NutritionVerse-Real は image `dish_N` ≠ metadata `dish_id` で、naive id-join が **40% の GT を誤らせた**。schema/合計チェックでは検出不能。COCO 内容ベース join + 目視で 104 件に是正。

## 結論 / 推奨
- **pro 採用の calorie 根拠は崩れた**。calorie だけ見れば pro と flash は実測で互角〜分布次第で flash 優位もあり、**追加コスト ~3.2x を calorie 精度で正当化できない**。
- **pro を採るなら根拠は recognition（4/4）に限定**し、それを実 mozu データで再確認することが前提。コスト優先なら **flash で十分**という判断も合理的。
- **「欧米料理で十分汎用的か」への答え**: 現状の v13 + USDA 検索パイプラインは、**実世界の欧米料理で総カロリー MAE ~40-60%**。frozen-50 が示した ~18% は楽観。大皿の portion 過小評価が主因で、これは **モデル選択でなくプロンプト/portion 設計の課題**。
- **calorie の最終 arbiter は実 mozu ユーザーの measured データのみ**。3つの公開セットはいずれも lab/studio で、真の本番分布ではない。

## 次の一手（優先順）
1. **実 mozu ドメインの measured アンカー構築**（Western・eye-level phone 20-50枚を実測×USDA）→ ここで初めて calorie の本採用判定 & 乗算的 calibration が可能。
2. **portion 過小（大皿圧縮）の是正**：v13 の portion anchor / density 指示を大型マルチ品向けに改善（モデル非依存で効く本丸）。
3. **recognition の多 cuisine 汎化チェック**（UEC-Food256 等）で pro の唯一の優位が保たれるか確認。
4. 本番 deploy は上記が揃ってから（要ユーザ明示指示・予算確認）。
