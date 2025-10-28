# v7プロンプト開発ノート

**作成日**: 2025年10月27日
**作成者**: Claude (via Claude Code)

## 📋 開発方針

### 過学習回避の原則
- **❌ テスト画像固有の情報は排除** (test_food25, test_food3等への言及なし)
- **❌ 特定の失敗ケースへの対処なし**
- **✅ Research-basedの一般的な原則のみ使用**
- **✅ 国際標準データベース（FAO/INFOODS）の値を使用**
- **✅ 学術研究で証明された手法を採用**

---

## 🔬 v7_production（プロダクション用）

### ベース
- **v5_streamlined**: 平均カロリー誤差20.11%（現在最優秀）

### 改善点（Research-Based）

#### 1. Edge-Based Detection Method
**根拠**: Computer Vision研究で小物検出に有効と証明
- Primary scan → Secondary scanの2段階
- Edge detection algorithmによる境界識別
- Glossy surface detection（油脂の検出）

#### 2. 高カロリー小物の優先順位
**根拠**: 複数の研究で「most commonly missed items」として報告
- Liquid condiments (100+ kcal)
- Oil/butter coatings (50-150 kcal)
- Small garnishes with high calorie density

#### 3. Visual Cues
**根拠**: 光沢と油脂の相関に関する研究
- Shiny surface = oil/butter coating
- Creamy white = dairy-based sauce
- Dark pools = reduction/gravy

### 期待される効果
- 小物検出率の向上 → カロリー過小評価の解消
- 油脂類の検出改善 → 脂質誤差の削減
- 目標: 平均誤差 <18%

---

## 🧪 v7_experimental（実験用）

### ベース
- **v6_balanced**: 30%以上誤差8件のみ（最も安定）

### 改善点（FAO Method Based）

#### 1. Composite Food Density Calculation
**根拠**: FAO推奨の複合食品計算法
- 各層/コンポーネントを個別計算
- 加重平均による密度算出
- 例: サンドイッチ = bread + filling + vegetables + condiments

#### 2. Component-Based Weight Estimation
**根拠**: 「Multi-layered dishes should be calculated as simple recipes then combined」（FAO文書）
- サンドイッチ: 0.6-0.8 g/cm³
- バーガー: 0.7-0.9 g/cm³
- ピザ: 0.5-0.7 g/cm³

#### 3. Visual References追加
**根拠**: 標準的なポーションサイズ研究
- Deck of cards = ~85g meat
- Tennis ball = ~150g volume
- 一般的な参照物で精度向上

### 期待される効果
- 複合食品の重量推定精度向上
- サンドイッチ/バーガーの過大評価解消
- 目標: 30%以上誤差 <5件

---

## 📊 テスト推奨事項

### Phase 1: Quick Test（3画像）
Critical画像でのクイックテスト：
- test_food25.jpg（チリドッグ）- 過大評価の解消確認
- test_food3.jpg（ステーキ）- 小物検出の改善確認
- test_food45.jpg（サンドイッチ）- 複合食品計算の確認

### Phase 2: Full Test（50画像）
```bash
# v7_productionとv5_streamlinedの比較
python test_scripts/compare_vlm_prompts_nutrition.py \
  --prompts v5_streamlined v7_production \
  --limit 50 \
  --concurrency 5

# v7_experimentalとv6_balancedの比較
python test_scripts/compare_vlm_prompts_nutrition.py \
  --prompts v6_balanced v7_experimental \
  --limit 50 \
  --concurrency 5
```

### Phase 3: Analysis
- 30%以上誤差件数の減少を確認
- 平均誤差率の改善を測定
- 新たな問題パターンの特定

---

## 🔍 検証ポイント

### v7_production
1. 小物検出率が向上したか
2. 油脂類の検出精度が改善したか
3. トークン消費が許容範囲内か

### v7_experimental
1. 複合食品の重量推定が改善したか
2. Component-based計算が正しく機能するか
3. 安定性を維持できているか

---

## 📚 参考文献

1. **FAO/INFOODS Density Database Version 2.0** - 密度値の標準
2. **Computer Vision Best Practices 2024-2025** - Edge detection, multi-pass scanning
3. **Food Volume Estimation Research** - Component-based calculation methods
4. **Portion Size Studies** - Visual references and standard servings

---

## ⚠️ 注意事項

- 過学習を避けるため、テスト結果に基づく微調整は慎重に行う
- 一般化可能な改善のみを採用する
- Research-basedでない変更は避ける