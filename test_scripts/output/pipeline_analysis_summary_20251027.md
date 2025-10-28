# Pipeline分析: エグゼクティブサマリー

**分析日時**: 2025年10月27日
**テスト画像数**: 50枚
**プロンプト**: v6_balanced, v6_corrected, v6_enhanced

---

## 📊 主要な発見

### 1. プロンプト別パフォーマンス

| プロンプト | 30%以上誤差件数 | Critical（全失敗） | 特徴 |
|-----------|-----------------|-------------------|------|
| **v6_balanced** | 8件 | 3件 | ✅ 最も安定したパフォーマンス |
| **v6_corrected** | 11件 | 3件 | ⚠️ 中程度の安定性 |
| **v6_enhanced** | 21件 | 3件 | ❌ 最も不安定（誤差2.6倍） |

### 2. Critical画像（全プロンプトで30%以上誤差）

#### test_food25.jpg - チリドッグとポテトチップス
- **ラベル**: 748.1 kcal（270g: ホットドッグ120g、チリ90g、チーズ20g、チップス40g）
- **問題**: 全プロンプトで過大評価
  - v6_balanced: +40.0% (1047 kcal)
  - v6_corrected: +82.8% (1368 kcal)
  - v6_enhanced: **+148.5% (1859 kcal)** ← 2.5倍の過大評価
- **根本原因**:
  - 重量の体系的な過大評価
  - v6_enhancedの「MINIMUM WEIGHTS」ルールが逆効果
  - ポテトチップスを「Main starch ≥120g」として過大評価した可能性

#### test_food3.jpg - ビーフステーキディナー
- **ラベル**: 1000.5 kcal（585g: ステーキ180g、ポテト220g、アスパラガス130g、等）
- **問題**: 全プロンプトで過小評価
  - v6_balanced: -43.0% (571 kcal)
  - v6_corrected: -38.5% (616 kcal)
  - v6_enhanced: -36.1% (640 kcal)
- **根本原因**:
  - 高カロリー小物（ガーリックアイオリ 170kcal/25g）の見逃し
  - 脂質の過小評価（-56%～-65%）
  - 付け合わせの重量過小評価

#### test_food45.jpg - プロシュートサンドイッチ
- **ラベル**: 791.2 kcal（265g: サンドイッチ220g、チップス45g）
- **問題**: 全プロンプトで約2倍の過大評価
  - v6_balanced: +79.8% (1422 kcal)
  - v6_corrected: +93.9% (1535 kcal)
  - v6_enhanced: +90.2% (1505 kcal)
- **根本原因**:
  - サンドイッチの重量を大幅に過大評価
  - パンの密度値（0.35 g/cm³）が正しく適用されていない可能性
  - サンドイッチ全体を肉の密度（1.05 g/cm³）で計算している可能性

---

## 🔍 体系的な問題パターン

### 問題1: v6_enhancedの過剰な指示
- **COMPREHENSIVE ITEM DETECTION** の systematic scan が複雑すぎる
- **MINIMUM WEIGHTS** ルールが過大評価を誘発:
  - "Main protein: ≥100g"
  - "Main starch: ≥120g"
  - 小さいポーション（40gのチップス）も最小値に引き上げられる

### 問題2: 重量推定の基準点の欠如
- プレート参照（25cm）は提供されているが、VLMが正確に活用できていない
- 「chain-of-thought」を要求しても、実際の計算過程が見えない（JSONのみ出力）
- 重量推定の検証メカニズムが不足

### 問題3: 小さい高カロリーアイテムの見逃し
- test_food3のガーリックアイオリ（25g, 170kcal）
- ソース、ドレッシング、調味料の検出率が低い
- "NEVER MISS" リストがあっても実効性が低い

### 問題4: 密度値の不適切な適用
- サンドイッチなどの複合食品で、単一材料の密度を適用
- パン（0.35）、肉（1.05）、野菜（0.6-0.8）の組み合わせを正しく加重平均できていない

---

## 💡 改善推奨事項

### 推奨1: v6_balancedをベースに最適化
**理由**: 最も安定したパフォーマンス（8件のみ高誤差）

**改善点**:
1. **小物検出の強化**:
   ```
   CRITICAL: Small high-calorie items often missed:
   - Dressings/sauces: Even 15-30g can add 100-200 kcal
   - Cheese toppings: 20g = 80 kcal
   - Butter/oil coatings: Visible shine indicates 10-20g fat

   DETECTION PRIORITY:
   1. Main items first (proteins, starches)
   2. THEN systematically scan for small items
   3. Check plate edges for sauces/garnishes
   4. Look for glossy surfaces (oil/butter)
   ```

2. **重量検証ルールの追加**:
   ```
   WEIGHT VALIDATION CHECKLIST:
   - If total < 300g for full plate → Review for missing items
   - If total > 800g for single plate → Recalculate weights
   - Compare each item to reference:
     • Deck of cards = 85g
     • Tennis ball = 150g
     • Baseball = 145g
   ```

3. **複合食品の密度計算**:
   ```
   COMPOSITE FOOD DENSITY:
   - Sandwiches: 0.6-0.7 g/cm³ (average of bread, filling)
   - Burgers: 0.7-0.8 g/cm³
   - Pizza: 0.5-0.6 g/cm³
   - Salads with dressing: 0.4-0.5 g/cm³
   ```

### 推奨2: v6_enhanced の簡略化
**削除すべき要素**:
- ❌ MINIMUM WEIGHTS ルール（過大評価の原因）
- ❌ 5段階の systematic scan（過剰に複雑）
- ❌ 詳細な weight_reasoning（トークン浪費、効果不明）

**保持すべき要素**:
- ✅ CORRECTED DENSITY VALUES（科学的根拠あり）
- ✅ PORTION VALIDATION FRAMEWORK（上限値は有効）
- ✅ DETECTION CHECKLIST（簡略版）

### 推奨3: プロンプトテスト優先順位

**Phase 1: 即座にテスト**
- v6_balanced + 小物検出強化 + 重量検証チェックリスト

**Phase 2: 検証後にテスト**
- v6_balanced + 複合食品密度計算

**Phase 3: 必要に応じて**
- v6_correctedのファインチューニング（密度値の微調整）

---

## 📈 期待される改善効果

### 現状（v6_balanced）
- 30%以上誤差: 8/50 (16%)
- 平均絶対誤差: ~20%

### 目標（改善版v6_balanced）
- 30%以上誤差: ≤4/50 (8%)
- 平均絶対誤差: ≤15%

### 重点改善対象
1. **test_food25（チリドッグ）**: 過大評価 → 正確な重量推定
2. **test_food3（ステーキ）**: ソース検出強化 → 過小評価の解消
3. **test_food45（サンドイッチ）**: 複合食品密度 → 過大評価の解消

---

## 🎯 次のステップ

1. **v6_balanced改良版の作成**（1時間）
   - 小物検出の強化
   - 重量検証チェックリスト追加
   - 複合食品密度テーブル追加

2. **Critical画像3枚でのクイックテスト**（30分）
   - test_food25, test_food3, test_food45で検証
   - 改善効果の確認

3. **50枚フルテスト**（2時間）
   - 統計的な改善効果の測定
   - 新たな問題パターンの特定

4. **必要に応じた反復**
   - 問題が残る画像の個別分析
   - プロンプトの微調整

---

## 📎 関連ドキュメント

- 詳細レポート: `pipeline_detailed_analysis_20251027.md`
- テスト結果JSON: `vlm_prompt_nutrition_comparison_20251027_144355.json`
- プロンプトファイル: `apps/freeform_usda_meal_analysis_api/prompts/`
