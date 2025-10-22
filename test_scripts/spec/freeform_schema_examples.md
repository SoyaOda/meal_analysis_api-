# 自由生成版スキーマの出力例

## スキーマ定義（自由生成版）

### 基本構造
```typescript
interface DishAnalysis {
  dish_name: string;
  unit_count: number;
  confidence: number;
  analysis_method: "USE_AS_IS" | "HYBRID_DECOMPOSITION" | "DECOMPOSE_TO_INGREDIENTS";
  base_food: FoodItem | null;
  ingredients: FoodItem[];
}

interface FoodItem {
  item_name: string;  // VLMが自由に生成する説明的な名前
  weight_g: number;
  // nutrition_per_100g は不要（削除）
  // found_in_list も不要（削除）
}
```

## 主な特徴

1. **食品名の自由度**: VLMが観察に基づいて説明的な名前を生成
2. **栄養情報なし**: nutrition_per_100gフィールドを削除
3. **リスト依存なし**: found_in_listフィールドを削除
4. **シンプルな構造**: 必要最小限のフィールドのみ

## 出力例

### 1. USE_AS_IS の例

シンプルな料理：
```json
{
  "dishes": [
    {
      "dish_name": "grilled chicken plate",
      "unit_count": 1,
      "confidence": 0.90,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "grilled chicken breast with herbs",
        "weight_g": 180
      },
      "ingredients": []
    }
  ]
}
```

複合的な料理：
```json
{
  "dishes": [
    {
      "dish_name": "cheeseburger meal",
      "unit_count": 1,
      "confidence": 0.85,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "cheeseburger with lettuce, tomato and fries",
        "weight_g": 350
      },
      "ingredients": []
    }
  ]
}
```

### 2. DECOMPOSE_TO_INGREDIENTS の例

サラダの分解：
```json
{
  "dishes": [
    {
      "dish_name": "mixed green salad",
      "unit_count": 1,
      "confidence": 0.88,
      "analysis_method": "DECOMPOSE_TO_INGREDIENTS",
      "base_food": null,
      "ingredients": [
        {
          "item_name": "mixed salad greens",
          "weight_g": 80
        },
        {
          "item_name": "cherry tomatoes",
          "weight_g": 60
        },
        {
          "item_name": "sliced cucumbers",
          "weight_g": 40
        },
        {
          "item_name": "crumbled feta cheese",
          "weight_g": 30
        },
        {
          "item_name": "balsamic vinaigrette dressing",
          "weight_g": 25
        }
      ]
    }
  ]
}
```

プレートランチの分解：
```json
{
  "dishes": [
    {
      "dish_name": "dinner plate",
      "unit_count": 1,
      "confidence": 0.82,
      "analysis_method": "DECOMPOSE_TO_INGREDIENTS",
      "base_food": null,
      "ingredients": [
        {
          "item_name": "pan-seared salmon fillet",
          "weight_g": 150
        },
        {
          "item_name": "garlic mashed potatoes",
          "weight_g": 120
        },
        {
          "item_name": "steamed asparagus spears",
          "weight_g": 80
        },
        {
          "item_name": "lemon butter sauce",
          "weight_g": 20
        }
      ]
    }
  ]
}
```

### 3. HYBRID_DECOMPOSITION の例

ピザにトッピング追加：
```json
{
  "dishes": [
    {
      "dish_name": "customized pizza",
      "unit_count": 1,
      "confidence": 0.87,
      "analysis_method": "HYBRID_DECOMPOSITION",
      "base_food": {
        "item_name": "thin crust margherita pizza",
        "weight_g": 200
      },
      "ingredients": [
        {
          "item_name": "sliced pepperoni",
          "weight_g": 30
        },
        {
          "item_name": "sautéed mushrooms",
          "weight_g": 25
        },
        {
          "item_name": "fresh basil leaves",
          "weight_g": 5
        }
      ]
    }
  ]
}
```

パスタに追加要素：
```json
{
  "dishes": [
    {
      "dish_name": "pasta with extras",
      "unit_count": 1,
      "confidence": 0.79,
      "analysis_method": "HYBRID_DECOMPOSITION",
      "base_food": {
        "item_name": "spaghetti with marinara sauce",
        "weight_g": 250
      },
      "ingredients": [
        {
          "item_name": "grilled chicken strips",
          "weight_g": 80
        },
        {
          "item_name": "grated parmesan cheese",
          "weight_g": 15
        }
      ]
    }
  ]
}
```

## 複数料理の例

朝食セット：
```json
{
  "dishes": [
    {
      "dish_name": "scrambled eggs",
      "unit_count": 1,
      "confidence": 0.92,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "fluffy scrambled eggs with butter",
        "weight_g": 120
      },
      "ingredients": []
    },
    {
      "dish_name": "breakfast sides",
      "unit_count": 1,
      "confidence": 0.85,
      "analysis_method": "DECOMPOSE_TO_INGREDIENTS",
      "base_food": null,
      "ingredients": [
        {
          "item_name": "crispy bacon strips",
          "weight_g": 40
        },
        {
          "item_name": "whole wheat toast with butter",
          "weight_g": 60
        },
        {
          "item_name": "hash brown patty",
          "weight_g": 80
        }
      ]
    },
    {
      "dish_name": "orange juice",
      "unit_count": 1,
      "confidence": 0.95,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "fresh squeezed orange juice",
        "weight_g": 250
      },
      "ingredients": []
    }
  ]
}
```

## 食品名の記述ガイドライン

### 良い例 ✅
- "grilled chicken breast with herbs" （調理法と特徴を含む）
- "steamed white rice" （調理法と種類を含む）
- "mixed green salad with ranch dressing" （内容と調味料を含む）
- "pan-fried salmon fillet with skin" （調理法と部位を含む）

### 悪い例 ❌
- "chicken" （詳細不足）
- "rice" （調理法不明）
- "salad" （内容不明）
- "fish" （種類と調理法不明）

## バリデーションチェックリスト

1. ✅ USE_AS_IS: base_food存在、ingredients空配列
2. ✅ DECOMPOSE_TO_INGREDIENTS: base_food=null、ingredients非空
3. ✅ HYBRID_DECOMPOSITION: 両方非空
4. ✅ item_nameが説明的で具体的
5. ✅ weight_g > 0 の整数
6. ✅ 調理法が視覚的に判別可能な場合は含まれている
7. ✅ 同じ応答内で一貫した命名スタイル