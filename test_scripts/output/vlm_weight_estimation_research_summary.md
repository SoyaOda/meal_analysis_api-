# VLMによる食品重量推定：研究調査まとめ

生成日時: 2025-10-26
調査内容: 画像からの食品重量推定における最新手法

## エグゼクティブサマリー

**結論: 体積×密度方式が最も高精度**

最新研究（2024年11月）によると、体積推定＋食品別密度モデルが最高精度を達成：
- 誤差率: 3.75-5.07%（米・鶏肉での検証）
- mAP: 87.3%（物体検出精度）
- 処理時間: 2秒/食品

## 1. 重量推定手法の比較

### 方式1: 直接重量推定
- **精度**: 中程度（MAPE 6-10%）
- **利点**: シンプルな実装
- **欠点**: 物理的根拠が弱い、汎化性能が低い

### 方式2: 体積×密度推定（推奨）
- **精度**: 高（誤差 3.75-5.07%）
- **利点**: 物理的に妥当、食品タイプ別の調整可能
- **欠点**: 実装がやや複雑

## 2. 食品カテゴリー別のアプローチ

### Main Food（主要料理）
**推奨: 体積×密度方式**
```json
{
  "search_name": "pasta with tomato sauce",
  "weight_g": 280,           // = volume × density
  "volume_cm3": 350,          // VLMが視覚的に推定
  "density_g_cm3": 0.8,       // カテゴリー別の典型値
  "density_category": "MEDIUM" // 密度カテゴリー
}
```

### Extras（調味料・トッピング）
**推奨: ハイブリッドアプローチ**

#### 視覚的に測定可能な場合（かかったソース等）
```json
{
  "search_name": "ranch dressing",
  "weight_g": 30,             // = volume × density
  "volume_ml": 30,            // 薄い層として推定
  "density_g_ml": 1.0         // 液体調味料の典型値
}
```

#### 極小量・不規則な形状の場合
```json
{
  "search_name": "parmesan cheese",
  "weight_g": 5,              // 直接推定
  "estimation_method": "direct" // 体積測定が困難
}
```

## 3. 密度データベース（FAO/INFOODS）

### 主要食品カテゴリーの密度範囲

| カテゴリー | 密度 (g/cm³) | 例 |
|-----------|-------------|-----|
| **HIGH** | 1.2-2.0 | 肉類、チーズ、ナッツ |
| **MEDIUM** | 0.8-1.2 | 調理済みパスタ、米、パン |
| **LIQUID** | ~1.0 | 飲料、スープ、ソース |
| **LOW** | 0.2-0.8 | 葉物野菜、生野菜、果物 |
| **VERY LOW** | <0.2 | ポップコーン、チップス |

### 調味料・ソースの密度

| 品目 | 密度 (g/cm³) |
|------|-------------|
| マヨネーズ | 0.91 |
| ケチャップ | 1.05 |
| オリーブオイル | 0.92 |
| 醤油 | 1.20 |
| ドレッシング（平均） | 0.95-1.10 |

## 4. VLMの最新能力（2024）

### SpatialVLM（CVPR 2024）
- 2D画像から3D深度推定
- 距離推定精度: 37.2%が真値の0.5-2倍範囲内
- 99%の有効フォーマット出力

### DepthLM
- 3Bモデルで既存VLMの2倍精度
- メトリックスケールでの深度推定可能

### 食品特化の課題
- 主要食材認識: 80% EWR（Expert-Weighted Recall）
- 調理スタイル認識: 50% EWR（課題あり）
- 細かい属性の認識が困難

## 5. 実装推奨事項

### プロンプトへの実装案

```text
WEIGHT ESTIMATION METHOD:

For MAIN FOODS (>50g typical):
1. Estimate visual volume (cm³) based on:
   - Comparison with plate size (25cm standard)
   - Depth estimation from visual cues
   - Shape approximation (cylinder, sphere, etc.)
2. Apply density category (HIGH/MEDIUM/LOW)
3. Calculate: weight_g = volume_cm3 × density_g_cm3

For EXTRAS (<50g typical):
- Visible liquids/sauces: volume × density
- Sprinkled items: direct weight estimation
- When uncertain: use typical portion sizes

OUTPUT FIELDS:
{
  "weight_g": integer,          // 最終的な重量
  "volume_cm3": integer,         // main_foodのみ必須
  "density_category": string,   // main_foodのみ必須
  "estimation_method": string   // "volume_density" or "direct"
}
```

## 6. 精度向上のポイント

1. **階層的推定**: 全体重量→個別配分
2. **検証ステップ**: 合計が妥当か確認
3. **参照基準の活用**: プレートサイズ、手のサイズ
4. **物理的制約**: 1皿1000g以下が典型

## 結論

**体積×密度方式を基本とし、小量調味料は直接推定のハイブリッドアプローチが最適**

- 主要料理: 体積推定＋密度カテゴリー
- 液体調味料: 可視体積×密度
- 極小トッピング: 直接重量推定
- 全体検証: 階層的チェック

この方式により、現在の誤差（平均27.8%）を10%以下に削減可能と推定。