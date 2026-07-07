# 🦙 Llama-4-Maverick-17B テスト結果レポート

**テスト日時**: 2025-10-19  
**モデル**: meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8  
**テスト画像**: food1.jpg ~ food5.jpg（計5枚）

---

## 📊 総合結果

| 指標 | スコア | ランキング |
|------|--------|------------|
| 平均マッチ率 | **47.0%** | 🥉 3位/4モデル |
| 平均処理時間 | **10.1秒** | 🥈 2位/4モデル |
| 成功率 | 80% (4/5) | ⚠️ food4で失敗 |
| 平均料理数 | 2.4 | - |
| 平均材料数 | 2.8 | - |

---

## 🔍 詳細分析

### ✅ 成功事例

#### food3（グリルチキン + ポテト + サラダ）: 80%マッチ 🏆

```json
{
  "dishes": 3,
  "ingredients": 5,
  "calories": 441.4 kcal,
  "match_rate": 80.0%,  // 全モデル中トップレベル！
  "time": 13.4秒
}
```

- **Mistral（100%）に次ぐ高マッチ率**
- food5でもタコスを正しく1つとして認識（Qwenの重複バグなし）

#### food1（シーザーサラダ + パスタ）: 75%マッチ

```json
{
  "dishes": ["Caesar Salad", "Pasta with Tomato Sauce", "Iced Tea"],
  "match_rate": 75.0%,  // Mistralと同率
  "time": 15.1秒
}
```

### ❌ 問題事例

#### food4（マッシュポテト + 芽キャベツ + 肉料理）: 完全失敗 🔴

```
エラー: "Phase1Component processing failed: 'str' object has no attribute 'get'"
```

**原因（詳細分析済み）**:
- ✅ **Llama-4が不正なJSON構造を返した**（確認済み）
- ❌ `ingredients` 配列に**文字列を直接含めた**:
  ```json
  "ingredients": [
    {"ingredient_name": "Potato, mashed...", "weight_g": 200},  // ✅ 正常
    "Butter, stick",     // ❌ 文字列（辞書であるべき）
    "weight_g: 20"       // ❌ 文字列（辞書であるべき）
  ]
  ```
- ❌ `dishes` 配列が途中で終了し、2番目の料理が配列外に配置
- Phase1Componentが文字列 `"Butter, stick"` に対して `.get()` メソッドを呼び出し → `AttributeError`

**詳細**: [LLAMA4_FOOD4_ERROR_ANALYSIS.md](./LLAMA4_FOOD4_ERROR_ANALYSIS.md) 参照

#### food2（5品の複雑な料理）: 0%マッチ

```json
{
  "dishes": 5,
  "ingredients": 0,  // 材料を認識できず
  "match_rate": 0.0%,
  "calories": 1142.5 kcal
}
```

---

## 📈 他モデルとの比較

| モデル | マッチ率 | 処理時間 | 成功率 | 総合評価 |
|--------|----------|----------|--------|----------|
| 🥇 **Mistral-Small** | **58.3%** | 14.7秒 | 100% | ⭐⭐⭐⭐⭐ |
| 🥈 **gemma-3-27b-it** | 51.8% | 25.1秒 | 100% | ⭐⭐⭐⭐ |
| 🥉 **Llama-4-Maverick** | **47.0%** | **10.1秒** | 80% | ⭐⭐⭐ |
| 4位 **Qwen3-VL-4B** | 39.3% | **6.2秒** | 100% | ⭐⭐⭐ |

---

## 💡 Llama-4の特徴

### ✅ 強み

1. **処理速度が速い**（10.1秒）
   - Qwen（6.2秒）には及ばない
   - しかしMistral（14.7秒）やgemma（25.1秒）より高速

2. **food3とfood5で高マッチ率**
   - food3: 80%（Mistralの100%に次ぐ）
   - food5: 80%（タコスを正しく1つとして認識）

3. **重複バグなし**
   - Qwenのように同じ料理を3回重複する問題なし

### ❌ 弱み

1. **マッチ率が中程度**（47.0%）
   - Mistral（58.3%）より -11.3%
   - gemma（51.8%）より -4.8%
   - Qwen（39.3%）より +7.7%

2. **food4で致命的エラー**
   - JSON形式の出力に失敗
   - `'str' object has no attribute 'get'`エラー
   - 成功率80%（5枚中1枚失敗）

3. **food2で0%マッチ**
   - 5品の複雑な料理を認識できない
   - 材料数0（分解失敗）

---

## 🎯 評価まとめ

### 総合評価: ⭐⭐⭐ (3/5)

**使用推奨度**:
- 🔴 **本番環境**: ❌ 推奨しない
  - 理由: food4で完全失敗、成功率80%は不安定
  - Mistralの方が安定

- 🟡 **開発・テスト環境**: △ 条件付きで使用可能
  - 理由: 処理速度が速い（10.1秒）
  - ただしエラーハンドリングが必要

- 🟢 **リアルタイム処理**: △ 検討の余地あり
  - 理由: Qwen（6.2秒）より遅い
  - エラー率を考慮するとリスク

### 推奨順位（4モデル中）

1. 🥇 **Mistral-Small-3.2-24B-Instruct-2506** - 最高精度、安定性
2. 🥈 **gemma-3-27b-it** - 詳細分析、安定性（ただし遅い）
3. 🥉 **Llama-4-Maverick-17B** - バランス型だが不安定
4. **Qwen3-VL-4B-Instruct** - 最速だが精度低い、重複バグ

---

## 🔧 Llama-4 改善の余地

### 1. **JSON出力の安定性向上** 🔴 最優先

**現在の問題**:
- food4で `ingredients` 配列に文字列を直接含める
- `dishes` 配列の構造を途中で崩壊させる
- 複雑な料理（3品以上）でJSON生成能力が低下

**解決策**:
- ✅ **短期**: Phase1Componentにエラーハンドリング追加（不正な要素をスキップ）
- △ **中期**: Promptを改善してより厳格なJSON構造を強制
- ⭐ **長期**: Mistral-Small-3.2-24B-Instruct-2506への移行（推奨）

### 2. **複雑な料理の認識強化**

**現在の問題**:
- food2（5品構成）で0%マッチ
- 材料分解に失敗（ingredients: 0）

**解決策**:
- Promptの改善
- より詳細な料理分解ロジックの実装

---

## 📄 関連ドキュメント

- **詳細なエラー分析**: [LLAMA4_FOOD4_ERROR_ANALYSIS.md](./LLAMA4_FOOD4_ERROR_ANALYSIS.md)
  - food4エラーの根本原因
  - Llama-4が返した不正なJSON構造の詳細
  - 解決策の比較と推奨事項

- **マッチ率の計算ロジック**: [MATCH_RATE_ANALYSIS.md](./MATCH_RATE_ANALYSIS.md)
  - マッチ率の定義と計算方法
  - 100%マッチを達成するための方法

- **モデル比較レポート**: [MODEL_COMPARISON_REPORT.md](./MODEL_COMPARISON_REPORT.md)
  - 4モデルの総合比較
  - 各モデルの強み・弱み

---

**結論**: Llama-4は**処理速度とマッチ率のバランス型**だが、**JSON生成能力の不安定性**（成功率80%）により本番環境では使用不可。**Mistral-Small-3.2-24B-Instruct-2506**への移行を強く推奨。

