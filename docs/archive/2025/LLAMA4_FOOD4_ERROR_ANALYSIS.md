# 🔍 Llama-4 food4エラー原因分析

**エラー**: `'str' object has no attribute 'get'`
**発生箇所**: `shared/components/phase1_component.py:224`
**モデル**: `meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8`

---

## 📋 エラーの詳細

### スタックトレース

```
File "/Users/odasoya/meal_analysis_api_2/shared/components/phase1_component.py", line 224, in process
    error_msg = f"Missing required field 'weight_g' for ingredient '{ingredient_data.get('ingredient_name', 'unknown')}'. AI model must provide weight estimation for all ingredients."
AttributeError: 'str' object has no attribute 'get'
```

### エラー発生コード（phase1_component.py:187-224）

```python
for ingredient_index, ingredient_data in enumerate(dish_data.get("ingredients", [])):
    # 構造化属性を従来形式に変換
    ingredient_attributes = []
    if "attributes" in ingredient_data:
        for attr_data in ingredient_data["attributes"]:
            # ...

    # weight_gが必須フィールドなので、存在しない場合はエラー
    if "weight_g" not in ingredient_data:  # ← ここで失敗
        error_msg = f"Missing required field 'weight_g' for ingredient '{ingredient_data.get('ingredient_name', 'unknown')}'. AI model must provide weight estimation for all ingredients."
        self.logger.error(error_msg)
        raise ValueError(error_msg)
```

**問題**: `ingredient_data` が辞書ではなく**文字列**になっているため、`.get()` メソッドが存在しない。

---

## 🔎 Llama-4が返した不正なJSON構造

### 期待される正しい構造

```json
{
  "dishes": [
    {
      "dish_name": "Mashed Potatoes",
      "confidence": 0.95,
      "analysis_method": "DECOMPOSE_TO_INGREDIENTS",
      "ingredients": [
        {
          "ingredient_name": "Potato, mashed, from fresh, NFS",
          "weight_g": 200
        },
        {
          "ingredient_name": "Butter, stick",
          "weight_g": 20
        }
      ]
    },
    {
      "dish_name": "Meatloaf",
      "confidence": 0.9,
      "analysis_method": "DECOMPOSE_TO_INGREDIENTS",
      "ingredients": [
        {
          "ingredient_name": "Beef, for use with vegetables",
          "weight_g": 120
        },
        {
          "ingredient_name": "Tomato chili sauce",
          "weight_g": 50
        }
      ]
    }
  ]
}
```

### Llama-4が実際に返した不正な構造

```json
{
  "dishes": [
    {
      "dish_name": "Mashed Potatoes",
      "confidence": 0.95,
      "analysis_method": "DECOMPOSE_TO_INGREDIENTS",
      "base_food": {
        "item_name": null,
        "weight_g": 0
      },
      "ingredients": [
        {
          "ingredient_name": "Potato, mashed, from fresh, NFS",
          "weight_g": 200
        },
        "Butter, stick",     // ❌ ERROR: これは文字列！辞書であるべき
        "weight_g: 20"       // ❌ ERROR: これも文字列！
      ]
    }
  ],
  "dish_name": "Meatloaf",   // ❌ ERROR: dishes配列の外に出ている！
  "confidence": 0.9,
  "analysis_method": "DECOMPOSE_TO_INGREDIENTS",
  "base_food": {
    "item_name": null,
    "weight_g": 0
  },
  "ingredients": [
    {
      "ingredient_name": "Beef, for use with vegetables",
      "weight_g": 120
    },
    {
      "ingredient_name": "Tomato chili sauce",
      "weight_g": 50
    }
  ]
}
```

---

## ❌ 3つの致命的な構造エラー

### エラー1: ingredients配列内に文字列が混在

```json
"ingredients": [
  {
    "ingredient_name": "Potato, mashed, from fresh, NFS",
    "weight_g": 200
  },
  "Butter, stick",     // ❌ 文字列（辞書であるべき）
  "weight_g: 20"       // ❌ 文字列（辞書であるべき）
]
```

**期待される形式**:
```json
"ingredients": [
  {
    "ingredient_name": "Potato, mashed, from fresh, NFS",
    "weight_g": 200
  },
  {
    "ingredient_name": "Butter, stick",
    "weight_g": 20
  }
]
```

### エラー2: dishes配列が途中で終了

```json
{
  "dishes": [
    {
      "dish_name": "Mashed Potatoes",
      ...
    }
    // ❌ ここで配列が閉じてしまっている
  ],
  "dish_name": "Meatloaf",  // ❌ 2番目の料理が配列外に出ている
  ...
}
```

### エラー3: JSONの階層構造が崩壊

- `"Meatloaf"` の料理データが `dishes` 配列の**外側**に配置されている
- これにより、`dishes[1]` としてアクセスできない

---

## 🎯 なぜこのエラーが発生したか

### Phase1Componentの処理フロー

1. `vision_result = parse_json_from_string(raw_response)`
   → JSONパースは成功（Llama-4の出力は一応valid JSONだった）

2. `for dish_data in analysis_result.get("dishes", []):`
   → `dishes` 配列をループ（Mashed Potatoes のみ含まれる）

3. `for ingredient_data in enumerate(dish_data.get("ingredients", [])):`
   → `ingredients` をループ開始

4. **1回目のループ**: `ingredient_data` = `{"ingredient_name": "Potato...", "weight_g": 200}`
   → 正常に処理

5. **2回目のループ**: `ingredient_data` = `"Butter, stick"`（文字列！）
   → `if "weight_g" not in ingredient_data:` でエラーチェック実行
   → `ingredient_data.get(...)` を呼び出そうとする
   → **AttributeError: 'str' object has no attribute 'get'**

---

## 📊 他のモデルとの比較

### Mistral-Small（food4処理成功）

```json
{
  "dishes": [
    {
      "dish_name": "Roasted Brussels Sprouts",
      "ingredients": [
        {
          "ingredient_name": "Brussels sprouts, cooked",
          "weight_g": 100
        }
      ]
    },
    {
      "dish_name": "Mashed Potatoes",
      "ingredients": [
        {
          "ingredient_name": "Potato, mashed, from fresh",
          "weight_g": 150
        },
        {
          "ingredient_name": "Butter",
          "weight_g": 10
        }
      ]
    },
    {
      "dish_name": "Meat with Gravy",
      "ingredients": [
        {
          "ingredient_name": "Beef, roasted",
          "weight_g": 100
        },
        {
          "ingredient_name": "Gravy, brown",
          "weight_g": 50
        }
      ]
    }
  ]
}
```

✅ **完璧な構造**: 全ての料理が `dishes` 配列内に正しく配置され、全ての材料が辞書形式。

### Llama-4（food4処理失敗）

❌ **不正な構造**:
- `ingredients` 配列に文字列が混在
- `dishes` 配列が途中で終了
- 2番目の料理が配列外に配置

---

## 💡 根本原因

### Llama-4の問題点

1. **JSON生成能力が低い**
   - 複雑な構造（ネストした配列と辞書）を正しく生成できない
   - 配列の途中で構造を壊す

2. **Promptの指示に従えない**
   - Promptでは全ての材料を `{"ingredient_name": "...", "weight_g": ...}` の形式で出力するよう指示
   - しかし、`"Butter, stick"` という文字列を出力

3. **一貫性がない**
   - food1, food2, food3, food5では正しいJSONを生成
   - food4（複雑な料理）でのみ失敗

### food4の特徴（なぜ難しいか）

- **3つの料理**（Mashed Potatoes, Brussels Sprouts, Meat with Gravy）
- **複数の材料を持つ料理**（Mashed Potatoes = Potato + Butter）
- **全モデルで苦戦**（Mistral以外はマッチ率0%）

Llama-4は複雑な料理を処理する際に、**JSON構造を保つことに失敗**。

---

## 🛠️ 解決策

### 短期対策: エラーハンドリングの追加

Phase1Componentに不正な要素をスキップする処理を追加:

```python
for ingredient_index, ingredient_data in enumerate(dish_data.get("ingredients", [])):
    # 🆕 型チェックを追加
    if not isinstance(ingredient_data, dict):
        self.logger.warning(f"Skipping invalid ingredient (not a dict): {ingredient_data}")
        continue

    # 構造化属性を従来形式に変換
    ingredient_attributes = []
    # ...
```

**メリット**: エラーを回避してパーシャルな結果を返せる
**デメリット**: 不完全なデータを返す（Butterが欠落）

### 中期対策: Promptの改善

より厳密なJSON構造を強制するPrompt:

```
重要:
- 全ての材料は必ず {"ingredient_name": "...", "weight_g": ...} の辞書形式で出力すること
- 文字列のみの材料名は絶対に出力しないこと
- 全ての料理は必ず "dishes" 配列内に配置すること
```

**メリット**: モデルの出力を改善できる可能性
**デメリット**: Llama-4の能力不足で効果が限定的な可能性

### 長期対策: より信頼性の高いモデルの使用

**推奨**: Mistral-Small-3.2-24B-Instruct-2506

- **food4成功率**: 100%（全ての料理を正しく認識）
- **平均マッチ率**: 58.3%（Llama-4の47.0%より高い）
- **JSON生成能力**: 高い（全5画像で構造エラーなし）
- **総合評価**: ⭐⭐⭐⭐⭐（Llama-4は⭐⭐⭐）

---

## 📈 影響範囲

### Llama-4の成功率

- **food1**: ✅ 成功（75%マッチ）
- **food2**: ✅ 成功（0%マッチだが構造は正常）
- **food3**: ✅ 成功（80%マッチ）
- **food4**: ❌ **完全失敗**（JSON構造エラー）
- **food5**: ✅ 成功（80%マッチ）

**全体成功率**: 80% (4/5)
**本番環境での使用**: ❌ 推奨しない（20%のエラー率は高すぎる）

---

## 🎯 結論

### Llama-4のfood4エラーの原因

**Llama-4が不正なJSON構造を返したため**:

1. `ingredients` 配列に文字列 `"Butter, stick"` を含めた
2. `dishes` 配列を途中で終了させた
3. 2番目の料理を配列外に配置した

これらの構造エラーにより、Phase1Componentが文字列に対して `.get()` メソッドを呼び出し、`AttributeError` が発生。

### 推奨事項

- ✅ **本番環境**: Mistral-Small-3.2-24B-Instruct-2506を使用
- △ **開発環境**: Llama-4はテスト用途のみ（エラーハンドリング追加が必要）
- ❌ **本番環境でLlama-4を使用しない**: 20%のエラー率は許容できない

---

**作成日**: 2025-10-19
**分析対象**: Llama-4-Maverick-17B food4処理エラー
**結論**: モデルのJSON生成能力不足が原因
