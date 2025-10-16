# USDAデータセット比較分析レポート

## 📊 概要

USDAのFoodData Centralには3つの主要なデータセットが存在します：

| データセット | 件数 | 最終更新 | データサイズ |
|-------------|------|---------|------------|
| **Foundation Foods** | 340件 | 2025年4月 | 6.3 MB |
| **SR Legacy** | 7,793件 | 2018年4月（最終版） | 201 MB |
| **Survey (FNDDS)** | 5,432件 | - | 63 MB |
| **合計** | **13,565件** | - | - |

---

## 🎯 各データセットの目的と特徴

### 1. Foundation Foods（基礎食品データ）

**目的:**
- 基本的な食品の詳細な栄養プロファイルを提供
- 生データや軽度加工食品に焦点
- 食品の変動性を重視した科学的アプローチ

**特徴:**
- **詳細なメタデータ**: サンプル数、採取場所、採取日、分析手法、農業情報（遺伝子型、生産方法）などを含む
- **透明性**: 平均値の背後にある個別データポイントにアクセス可能
- **変動性の可視化**: 生産地、季節、収穫後処理、分析方法などの影響を確認可能
- **栄養素が豊富**: 平均 **82.4 栄養素/食品**

**カテゴリ別内訳（上位）:**
- 野菜・野菜製品: 78件
- 果物・果汁: 48件
- 乳製品・卵製品: 42件
- 穀物・パスタ: 41件
- 豆類・豆製品: 37件

**具体例:**
- Hummus, commercial (119栄養素項目)
- Tomatoes, grape, raw (53栄養素項目)
- Nuts, almonds, dry roasted, with salt added (117栄養素項目)

---

### 2. SR Legacy（標準参照レガシーデータベース）

**目的:**
- 包括的な栄養・食品成分値のリストを提供
- 分析、計算、公開文献から導出されたデータ

**特徴:**
- **最も包括的**: 7,793件の食品アイテム
- **2018年4月で最終版**: これ以上更新されない歴史的データ
- **広範な食品**: 単一食材、ホールフード、一部のブランド品、調理済み料理を含む
- **栄養素データが充実**: 平均 **84.9 栄養素/食品**、最大150以上の栄養素フィールド
- **FNDDSのベース**: FNDDSはSR LegacyとFoundation Foodsのデータを基に構築

**カテゴリ別内訳（上位）:**
- 牛肉製品: 954件
- 野菜・野菜製品: 814件
- ベーカリー製品: 517件
- 羊肉・子牛肉・ジビエ: 464件
- 鶏肉製品: 383件
- 飲料: 366件
- 菓子類: 358件

**具体例:**
- Beef, round, bottom round, roast, separable lean only, trimmed to 0" fat, choice, cooked, roasted
- WENDY'S, Double Stack, with cheese
- Macaroni and cheese, box mix with cheese sauce, unprepared
- Peanuts, all types, raw

---

### 3. Survey (FNDDS - Food and Nutrient Database for Dietary Studies)

**目的:**
- **実際の食事調査**で報告された食品の栄養・食品成分値を提供
- NHANES（National Health and Nutrition Examination Survey）の「What We Eat in America」調査コンポーネントで報告された食品

**特徴:**
- **実際の消費データ**: 人々が実際に食べている食品に基づく
- **調理済み・加工食品が多い**: ホールフード、ブランド品、調理済み料理を含む
- **中程度の栄養素データ**: 平均 **63.7 栄養素/食品**、約60栄養素（ほとんど欠損なし）
- **期間情報**: startDate、endDateフィールドで調査期間を記録
- **WWEIAカテゴリ**: 独自の食品カテゴリ分類（wweiaFoodCategory）

**具体例:**
- Milk, human (foodCode: 11000000)
- Milk, whole (foodCode: 11111000)
- Milk, reduced fat (2%) (foodCode: 11112110)

---

## 🔍 フィールド構造の比較

### 共通フィールド（全データセット）
- `dataType` - データタイプ
- `description` - 食品の説明
- `fdcId` - FoodData Central ID
- `foodAttributes` - 食品属性
- `foodClass` - 食品クラス
- `foodNutrients` - 栄養素リスト
- `foodPortions` - 食品ポーション情報
- `inputFoods` - 原材料食品
- `publicationDate` - 公開日

### Foundation Foods & SR Legacy のみ
- `foodCategory` - 食品カテゴリ（詳細）
- `isHistoricalReference` - 歴史的参照フラグ
- `ndbNumber` - NDB番号
- `nutrientConversionFactors` - 栄養素変換係数

### Survey (FNDDS) のみ
- `foodCode` - **FNDDS食品コード**（重要！）
- `startDate` - 調査開始日
- `endDate` - 調査終了日
- `footnote` - 注釈
- `wweiaFoodCategory` - WWEIAカテゴリ（実際の食事調査用分類）

---

## 📈 データセット間の関係

```
┌─────────────────────┐
│  Foundation Foods   │ (340件)
│  最新の基礎食品     │
│  詳細メタデータ     │
└──────────┬──────────┘
           │
           ├──────────────┐
           │              │
           ▼              ▼
┌─────────────────┐  ┌─────────────────┐
│   SR Legacy     │  │ Survey (FNDDS)  │
│   (7,793件)     │  │   (5,432件)     │
│  最終版: 2018   │◄─┤ 実際の食事調査  │
│  歴史的データ   │  │ NHANES使用      │
└─────────────────┘  └─────────────────┘

※ FNDDSはFoundation FoodsとSR Legacyを基に構築
```

---

## 💡 使い分けのガイドライン

### Foundation Foods を使うべき場合
- ✅ 基本食材の詳細な栄養情報が必要
- ✅ 食品の変動性や農業情報（品種、産地など）が重要
- ✅ 最新の分析データが必要
- ✅ データの透明性（個別データポイント、分析手法）が重要

### SR Legacy を使うべき場合
- ✅ 最も広範な食品リストが必要
- ✅ ブランド品や特定の調理済み料理を含む包括的なデータベースが必要
- ✅ 100以上の栄養素フィールドが必要
- ✅ 歴史的データとの比較が必要

### Survey (FNDDS) を使うべき場合
- ✅ 実際に消費されている食品のデータが必要
- ✅ 食事調査や栄養疫学研究を行う
- ✅ **食品コード（foodCode）での検索・マッチングが必要**
- ✅ NHANES調査との互換性が必要
- ✅ 調理済み・複合料理のデータが必要

---

## 🎯 現在のプロジェクトでの活用

### 現在使用中
- ✅ **Survey (FNDDS)**: `usda_data_processing/`で処理
  - `usda_raw_ingredients_split_cleaned.json` (1,399件)
  - `usda_prepared_ingredients_split_cleaned.json` (143件)
  - **foodCodeベースで食材をマッチング**

### 今後の活用可能性

#### 1. Foundation Foods の統合
- より詳細な基本食材データの追加
- 農業情報（品種、産地）を活用した栄養素バリエーションの提供
- 340件と少ないが、高品質なメタデータ

#### 2. SR Legacy の統合
- より広範な食品カバレッジ（7,793件）
- ブランド品や特定の調理済み料理の追加
- より多くの栄養素フィールド（150+）

#### 3. データ統合戦略
```
FNDDS (foodCode) ←─→ 食材マッチング ←─→ Foundation/SR (description, ndbNumber)
      ↓                                              ↓
  実際の食事                                    詳細な栄養情報
  食品コード                                    メタデータ
```

---

## 📌 重要なポイント

1. **FNDDS（Survey）は実際の食事調査データ**: 人々が実際に食べている食品に基づいているため、食事分析APIに最適

2. **foodCodeが重要**: FNDDSの`foodCode`は食品を一意に識別し、調査データとリンクするための重要なキー

3. **SR Legacyは最終版**: 2018年4月で更新終了。Foundation Foodsが今後の主要な更新対象

4. **栄養素の充実度**:
   - SR Legacy: 84.9 栄養素/食品（最も充実）
   - Foundation Foods: 82.4 栄養素/食品（メタデータが充実）
   - FNDDS: 63.7 栄養素/食品（実用的、欠損が少ない）

5. **データの補完関係**: 3つのデータセットは互いに補完し合う関係
   - Foundation Foods: 最新の基礎食品
   - SR Legacy: 最も包括的な歴史的データ
   - FNDDS: 実際の消費パターンに基づくデータ

---

## 🔗 参考資料

- USDA FoodData Central: https://fdc.nal.usda.gov/
- Foundation Foods Documentation: https://fdc.nal.usda.gov/Foundation_Foods_Documentation/
- FNDDS Documentation: https://www.ars.usda.gov/ARSUserFiles/80400530/pdf/fndds/2021_2023_FNDDS_Doc.pdf
- 研究論文: "USDA's FoodData Central: what is it and why is it needed today?" (2021)
