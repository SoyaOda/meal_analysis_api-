# USDA食品マッピング生成プロンプト - 汎用テンプレート v4.0

## 🎯 目的と背景

このプロンプトは、USDA食品データベース（Survey FNDDS/Foundation Food）の食品名を、AI画像認識システム用の実用的なマッピングに変換するためのものです。

### システムアーキテクチャ
```
1. 画像入力 → VLM（Vision Language Model）が食品を識別
2. 識別結果 → EXACT_FOOD_LIST (CORE)と照合
3. マッチした食品 → analysis_methodを決定
4. 栄養計算 → USDAデータベースから栄養価を取得
```

## 📋 マッピング構造と必須フィールド

### 必須フィールド

```json
{
  "food_key": {
    "display_name": "Food Name",        // EXACT_FOOD_LISTに使用される正式名称
    "category": "category_name",        // 食品カテゴリ
    "role": "is_base | ingredient_only | sauce_only | either",  // 役割分類
    "role_reason": "役割判定の理由",
    "analysis_priority": ["DIRECT_MATCH", "HYBRID_DECOMPOSITION", "INGREDIENT_BASED"],  // 推奨順
    "default_usda": {
      "name": "⚠️ 必ず食品名リストから番号ごと完全一致でコピー（例: 123. Food name）",
      "reason": "選定理由"
    },
    "all_usda_mappings": [
      "⚠️ 食品名リストから番号ごと完全一致でコピー1（例: 123. Food name 1）",
      "⚠️ 食品名リストから番号ごと完全一致でコピー2（例: 456. Food name 2）",
      "⚠️ 食品名リストから番号ごと完全一致でコピー3（例: 789. Food name 3）"
    ],
    "aliases": [
      "別名1", "別名2", "別名3", "別名4", "別名5",
      "別名6", "別名7"
      // ⚠️ 5-10個を目標に設定
    ]
  }
}
```

**⚠️ 重要な注意事項**:
- **`default_usda`の`name`**: 食品名リストから**番号ごと一字一句そのままコピー**すること（例: "123. Caesar salad, with romaine, no dressing"）
- **`all_usda_mappings`**: 文字列配列で、各項目は食品名リストから**番号ごと完全一致でコピー**（例: "456. Food name"）
- **`all_usda_mappings`**: オブジェクト配列ではなく、**文字列配列**
- **`aliases`**: 5-10個を目標に設定（番号は不要、食品名のみ）

## 🎯 roleフィールドの定義と使用ルール

### role分類の定義

#### is_base
- **定義**: 他の材料を追加可能な基本料理
- **例**: Pizza, Salad, Sandwich, Burger, Taco, Burrito, Pasta dish, banana（単体で食べる場合）
- **特徴**: それ自体で完結した料理だが、カスタマイズ可能
- **HYBRID_DECOMPOSITION**: base_foodとして使用可能

#### ingredient_only
- **定義**: 単体では料理にならない材料・部品
- **例**: Tortilla, Bread slice, Pasta (uncooked), Lettuce, Cheese (as ingredient)
- **特徴**: 他の食材と組み合わせて初めて料理になる
- **HYBRID_DECOMPOSITION**: ingredientsリストでのみ使用可

#### sauce_only
- **定義**: ソース・調味料・ドレッシング類
- **例**: Ketchup, Mayo, Ranch dressing, Gravy, Salsa
- **特徴**: 料理に追加される調味要素
- **HYBRID_DECOMPOSITION**: ingredientsリストで使用可

#### either
- **定義**: 文脈により料理にも材料にもなる
- **例**: Rice (cooked), Pasta (cooked), French fries, Mashed potatoes, Chicken breast
- **特徴**: 単品でも提供され、付け合わせにもなる
- **HYBRID_DECOMPOSITION**: 状況に応じて判断

### バリデーションルール

```python
# HYBRID_DECOMPOSITIONの検証
if analysis_method == "HYBRID_DECOMPOSITION":
    assert base_food.role == "is_base", "base_foodはis_baseのみ"
    for ingredient in ingredients:
        assert ingredient.role != "is_base", "ingredientsにis_base禁止"
        assert ingredient.role in ["ingredient_only", "sauce_only", "either"], "適切なrole"
```

## 📊 カテゴリ定義（推奨）

### 主要カテゴリ
- `sandwiches` - サンドイッチ類（role: is_base多）
- `salads` - サラダ類（role: is_base多）
- `pizza` - ピザ類（role: is_base）
- `mexican` - メキシコ料理（Taco, Burrito等 role: is_base）
- `pasta_dishes` - パスタ料理（role: is_base）
- `meat_dishes` - 肉料理（role: either多）
- `seafood` - シーフード（role: either）
- `soups_stews` - スープ・シチュー（role: is_base）
- `rice_dishes` - 米料理（role: either）
- `vegetables` - 野菜類（role: ingredient_only/either）
- `fruits` - 果物（role: ingredient_only/either）
- `dairy` - 乳製品（role: ingredient_only/either）
- `sauces` - ソース類（role: sauce_only）
- `beverages` - 飲料（role: either）
- `desserts` - デザート（role: is_base/either）
- `snacks` - スナック（role: either）
- `breakfast` - 朝食（role: is_base/either）
- `poultry` - 鶏肉料理（role: either）
- その他適切なものがあれば

## 🔧 マッピング生成戦略

### 1. display_name設計原則

#### 明確性
- 一般的な英語表記を使用
- 略語（NFS, NS）は除去
- 自然な語順（"Chicken Caesar salad" not "Salad, Caesar, with chicken"）

#### 識別性
- 視覚的に区別可能なレベルで命名
- 過度に詳細な修飾語は避ける
- 例: "Pizza" (good) vs "Pizza, pepperoni, thick crust, from restaurant" (too specific)

#### 一貫性
- 同一カテゴリ内で命名規則統一
- 単数形/複数形の統一
- タイトルケース使用

### 2. role判定フローチャート

```
料理か？
├─ Yes → 他の材料を追加してカスタマイズ可能か？
│   ├─ Yes → is_base（Pizza, Salad, Sandwich等）
│   └─ No → either（Steak, Grilled chicken等）
└─ No → 材料/調味料か？
    ├─ 調味料/ソース → sauce_only
    ├─ 単体で食べられる → either（Fruit, Nuts等）
    └─ 料理の部品 → ingredient_only（Bread slice, Tortilla等）
```

### 3. マッピング判断フローチャート（重要）

```
食品名を評価
│
├─【ステップ1: 写真での識別可能性】
│  └─ 写真で視覚的に識別可能か？
│     ├─ NO → 除外リスト（写真認識不可）
│     └─ YES → ステップ2へ
│
├─【ステップ2: 出現頻度】
│  └─ 日常的な食事で頻出するか？
│     ├─ NO（極めて稀） → 除外リスト（稀少食品）
│     └─ YES → ステップ3へ
│
└─【ステップ3: 統合/分離判断】
   └─ 既存/他の類似食品と比較
      │
      ├─ 視覚的に区別可能か？
      │  ├─ NO（区別困難） → さらに栄養価を確認
      │  │  └─ 単位gあたりの栄養価が類似（±20%以内）？
      │  │     ├─ YES → 統合（all_usda_mappingsにまとめる）
      │  │     └─ NO → 別項目として分離（栄養価が大きく異なる）
      │  │
      │  └─ YES（明確に区別可能） → 別項目として分離
      │
      └─ 決定: マッピング項目作成 or 既存項目に統合
```

### 4. 統合ルール詳細

#### 積極統合するケース（all_usda_mappingsにまとめる）
- **視覚的区別不可 AND 栄養価類似**
  - 例: "Beef stew made with lean meat" vs "Beef stew made with regular meat"
  - 判断: 見た目同じ、カロリー差15% → 統合
- **調理法の微差**
  - 例: "deep fried" vs "pan fried" vs "stir fried"
  - 判断: 揚げ物の違いは写真で判別困難 → 統合
- **ブランド違い**
  - 例: 各社のコーラ製品 → "Cola"に統合

#### 分離維持するケース（別マッピング項目）
- **視覚的に明確に異なる**
  - 例: "Pizza" vs "Pizza rolls" （形状が全く異なる）
- **栄養価が大きく異なる（±50%以上）**
  - 例: "Ice cream" vs "Frozen yogurt"
  - 判断: 見た目類似でもカロリー差60% → 分離
- **roleが異なる**
  - 例: "Caesar salad"(is_base) vs "Caesar dressing"(sauce_only)

#### 除外リスト行きのケース
1. **写真に直接見えることがない**
   - 透明な液体（水、ブロス等）
   - 微量の調味料（塩、胡椒等）

2. **極めて稀な食品**
   - 特定地域の郷土料理で全国的に無名
   - 廃盤商品
   - 実験的/研究用食品

3. **Baby/Toddler/Infant food全般**
   - 一般的な食事写真に出現しない

4. **学校給食専用/WIC商品**
   - 一般市場で入手困難

5. **既に他のマッピングに統合済み**
   - 既存マッピングの`all_usda_mappings`に含まれる食品

### 5. 優先順位（全roleが重要）

#### 最高優先度（全て重要）
- **role: is_base** - HYBRID_DECOMPOSITIONの基本料理として必須
- **role: ingredient_only** - HYBRID_DECOMPOSITIONの材料として必須
- **role: sauce_only** - 調味料・ソースとして必須
- **role: either** - 柔軟な使用が可能な汎用食品として重要

#### 高優先度
- 視覚的に特徴的で識別容易な料理
- レストランメニューの定番
- 家庭料理の主要カテゴリ

#### 中優先度
- 地域料理の代表的なもの
- 季節性のある食品

#### 低優先度（除外検討）
- NFSの過度に細分化された項目
- ブランド固有商品の詳細バリエーション
- 栄養調整版の細かな違い（light, reduced fat, low sodium等）

## 📝 完全マッピング例

```json
{
  "caesar_salad": {
    "display_name": "Caesar salad",
    "category": "salads",
    "role": "is_base",
    "role_reason": "サラダは基本料理で、チキン等の追加が可能",
    "analysis_priority": ["HYBRID_DECOMPOSITION", "DIRECT_MATCH"],
    "default_usda": {
      "name": "1234. Caesar salad, with romaine, no dressing",
      "reason": "最も基本的な構成、ドレッシング別添想定"
    },
    "all_usda_mappings": [
      "1234. Caesar salad, with romaine, no dressing",
      "1235. Caesar salad, with romaine, with dressing",
      "1236. Caesar salad, with romaine, with chicken, no dressing",
      "1237. Caesar salad, with romaine, with chicken, with dressing"
    ],
    "aliases": [
      "caesar", "caesar salad", "romaine caesar",
      "classic caesar", "chicken caesar", "caesar with chicken",
      "caesar side salad", "caesar entree salad"
    ]
  },

  "chicken_breast": {
    "display_name": "Chicken breast",
    "category": "poultry",
    "role": "either",
    "role_reason": "単品料理にも、他料理の材料にもなる",
    "analysis_priority": ["DIRECT_MATCH", "INGREDIENT_BASED"],
    "default_usda": {
      "name": "2345. Chicken breast, grilled without sauce, skin not eaten",
      "reason": "最も一般的な調理法と提供形態"
    },
    "all_usda_mappings": [
      "2345. Chicken breast, grilled without sauce, skin not eaten",
      "2346. Chicken breast, baked or broiled, skin not eaten",
      "2347. Chicken breast, pan fried, skin not eaten"
    ],
    "aliases": [
      "grilled chicken", "chicken", "chicken fillet",
      "chicken breast fillet", "boneless chicken breast",
      "skinless chicken breast", "chicken breast meat"
    ]
  },

  "ranch_dressing": {
    "display_name": "Ranch dressing",
    "category": "sauces",
    "role": "sauce_only",
    "role_reason": "ドレッシング・調味料として使用",
    "analysis_priority": ["INGREDIENT_BASED"],
    "default_usda": {
      "name": "3456. Ranch dressing",
      "reason": "標準的なランチドレッシング"
    },
    "all_usda_mappings": [
      "3456. Ranch dressing",
      "3457. Ranch dressing, low calorie",
      "3458. Ranch dressing, fat free",
      "3459. Ranch dressing, reduced fat"
    ],
    "aliases": [
      "ranch", "ranch sauce", "ranch salad dressing",
      "buttermilk ranch", "creamy ranch", "ranch dip",
      "ranch style dressing"
    ]
  },

  "pasta_cooked": {
    "display_name": "Pasta",
    "category": "pasta_dishes",
    "role": "either",
    "role_reason": "単品でも提供、他料理のベースにもなる",
    "analysis_priority": ["DIRECT_MATCH", "INGREDIENT_BASED"],
    "default_usda": {
      "name": "4567. Pasta, cooked",
      "reason": "調理済みパスタの汎用表現"
    },
    "all_usda_mappings": [
      "4567. Pasta, cooked",
      "4568. Pasta, cooked, with salt",
      "4569. Pasta, cooked, without salt",
      "4570. Pasta, whole wheat, cooked",
      "4571. Pasta, enriched, cooked"
    ],
    "aliases": [
      "cooked pasta", "plain pasta", "noodles",
      "boiled pasta", "pasta noodles", "pasta base",
      "spaghetti", "penne", "fettuccine"
    ]
  }
}
```


## 📌 生成ガイドライン

### 出力形式
1. **JSON形式**で出力
2. インデント: 2スペース
3. UTF-8エンコーディング
4. 日本語コメント可（role_reason等）

### チェックリスト
- [ ] display_nameはEXACT_FOOD_LISTに適切か？
- [ ] roleは正しく設定されているか？
- [ ] role_reasonは明確か？
- [ ] analysis_priorityは適切な順序か？
- [ ] default_usdaのnameは食品名リストから番号ごと完全一致でコピーしたか？⚠️（例: "123. Food name"）
- [ ] all_usda_mappingsの各項目は食品名リストから番号ごと完全一致でコピーしたか？⚠️（例: "456. Food name"）
- [ ] all_usda_mappingsは文字列配列になっているか？（オブジェクト配列ではない）⚠️
- [ ] aliasesは5-10個設定されているか？⚠️（番号なし、食品名のみ）

### バリデーション確認
```python
# 生成後の検証コード例
for food_key, mapping in generated_mappings.items():
    # roleの妥当性チェック
    assert mapping["role"] in ["is_base", "ingredient_only", "sauce_only", "either"]

    # all_usda_mappingsが文字列配列であることを確認
    assert isinstance(mapping["all_usda_mappings"], list)
    for item in mapping["all_usda_mappings"]:
        assert isinstance(item, str), f"{food_key}: all_usda_mappingsは文字列配列のみ"

    # aliasesの数を確認
    assert 5 <= len(mapping["aliases"]) <= 10, f"{food_key}: aliasesは5-10個"

    # default_usdaのnameが食品名リストに存在するか確認（番号付きで）
    assert mapping["default_usda"]["name"] in food_name_list, \
        f"{food_key}: default_usdaのnameは食品名リストから番号ごと完全一致でコピー（例: '123. Food name'）"

    # all_usda_mappingsの各項目が食品名リストに存在するか確認（番号付きで）
    for usda_name in mapping["all_usda_mappings"]:
        assert usda_name in food_name_list, \
            f"{food_key}: all_usda_mappingsの'{usda_name}'は食品名リストから番号ごと完全一致でコピー（例: '456. Food name'）"
```

## 📦 期待する成果物

**⚠️ 重要**: 以下の2つのファイルを生成し、**ダウンロード可能なファイルとして提供**してください。

### 1. JSONマッピング（usda_food_mappings.json）

**ファイル名**: `usda_food_mappings.json`

上記形式での食品マッピングをJSON形式で出力してください。

**出力形式**:
- UTF-8エンコーディング
- インデント: 2スペース
- 拡張子: `.json`
- ダウンロード可能なファイルとして提供

### 2. 除外リスト（excluded_foods.txt）

**ファイル名**: `excluded_foods.txt`

**重要**: 除外リストには、**生成対象食品リストにある項目のうち、どのマッピングの`default_usda.name`や`all_usda_mappings`にも含まれなかった食品を全て**記載してください。

**出力形式**:
- UTF-8エンコーディング
- 拡張子: `.txt`
- ダウンロード可能なファイルとして提供

フォーマット（例）:
```txt
# 除外食品リスト
# 生成日: YYYY-MM-DD
# 総除外数: XXX個
# 元の食品リスト総数: YYY個
# マッピング生成数: ZZZ個

## 1. 写真認識不可（XX個）
- 123. Water, bottled - 理由: 透明な液体で視覚的判別不可
- 456. Salt - 理由: 微量調味料で写真に写らない

## 2. 稀少食品（XX個）
- 789. Exotic regional dish name - 理由: 極めて限定的な地域料理
- 1011. Discontinued product - 理由: 廃盤商品

## 3. Baby/学校給食/WIC専用（XX個）
- 1234. Baby food, carrots - 理由: Baby food
- 5678. School lunch pizza - 理由: 学校給食専用メニュー

## 4. 統合済み（XX個）
- 1235. Caesar salad, with romaine, with dressing - 統合先: "caesar_salad"のall_usda_mappingsに含む
- 2346. Chicken breast, baked or broiled, skin not eaten - 統合先: "chicken_breast"のall_usda_mappingsに含む
- 4568. Pasta, cooked, with salt - 統合先: "pasta_cooked"のall_usda_mappingsに含む

## 5. その他（XX個）
- 9999. Other food name - 理由: [具体的な理由]
```

**検証**: 以下の式が成立すること
```
元の食品リスト総数 = (全マッピングのall_usda_mappingsの重複なし合計数) + (除外リスト総数)
```

---

## 📤 成果物の提出方法

生成が完了したら、以下の2つのファイルを**必ずダウンロード可能な形式**で提供してください：

1. **`usda_food_mappings.json`** - 食品マッピングのJSONファイル
2. **`excluded_foods.txt`** - 除外食品リストのテキストファイル

**提出形式例**:
```
📎 成果物ファイル:
- usda_food_mappings.json (XXX KB) [ダウンロード]
- excluded_foods.txt (YYY KB) [ダウンロード]

統計:
- マッピング生成数: ZZZ個
- 除外食品数: AAA個
- 入力食品リスト総数: BBB個
```

---

## 🎯 生成対象食品リスト

以下に食品名リストを貼り付けてください（番号付き形式: "1. Food name"）：

```

```

