# 新しいスキーマの出力例

## スキーマ定義

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
  item_name: string;  // リストにある場合は正確な名前、ない場合は説明的な名前
  weight_g: number;
  found_in_list: boolean;
  nutrition_per_100g: NutritionData | null;
}

interface NutritionData {
  calorie: number;
  protein_g: number;
  fat_g: number;
  carbs_g: number;
}
```

## ルール

### analysis_method別の出力ルール

| Method | base_food | ingredients | 用途 |
|--------|-----------|-------------|------|
| USE_AS_IS | 必須（1個） | 空配列 [] | 料理全体が1つのリスト項目に一致 |
| DECOMPOSE_TO_INGREDIENTS | null | 必須（1個以上） | 個別食材に完全分解 |
| HYBRID_DECOMPOSITION | 必須（1個） | 必須（1個以上） | ベース料理＋追加要素 |

### nutrition_per_100gの出力ルール

- `found_in_list: true` → `nutrition_per_100g: null`
- `found_in_list: false` → `nutrition_per_100g: { calorie, protein_g, fat_g, carbs_g }`
- 栄養素の妥当性チェック: calorie ≈ 4*protein_g + 9*fat_g + 4*carbs_g (±20%)

## 出力例

### 1. USE_AS_IS の例

リストに完全一致する料理の場合：
```json
{
  "dishes": [
    {
      "dish_name": "pepperoni pizza",
      "unit_count": 1,
      "confidence": 0.90,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "pizza, pepperoni, regular crust",
        "weight_g": 250,
        "found_in_list": true,
        "nutrition_per_100g": null
      },
      "ingredients": []
    }
  ]
}
```

リストにない料理の場合：
```json
{
  "dishes": [
    {
      "dish_name": "homemade quiche",
      "unit_count": 1,
      "confidence": 0.65,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "quiche with vegetables and cheese",
        "weight_g": 180,
        "found_in_list": false,
        "nutrition_per_100g": {
          "calorie": 250,
          "protein_g": 12,
          "fat_g": 18,
          "carbs_g": 10
        }
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
      "dish_name": "garden salad",
      "unit_count": 1,
      "confidence": 0.85,
      "analysis_method": "DECOMPOSE_TO_INGREDIENTS",
      "base_food": null,
      "ingredients": [
        {
          "item_name": "lettuce, romaine, raw",
          "weight_g": 100,
          "found_in_list": true,
          "nutrition_per_100g": null
        },
        {
          "item_name": "tomatoes, red, raw",
          "weight_g": 80,
          "found_in_list": true,
          "nutrition_per_100g": null
        },
        {
          "item_name": "cucumber, with peel, raw",
          "weight_g": 50,
          "found_in_list": true,
          "nutrition_per_100g": null
        },
        {
          "item_name": "ranch dressing",
          "weight_g": 30,
          "found_in_list": true,
          "nutrition_per_100g": null
        }
      ]
    }
  ]
}
```

リストにない食材を含む場合：
```json
{
  "dishes": [
    {
      "dish_name": "custom stir-fry",
      "unit_count": 1,
      "confidence": 0.70,
      "analysis_method": "DECOMPOSE_TO_INGREDIENTS",
      "base_food": null,
      "ingredients": [
        {
          "item_name": "chicken breast, cooked",
          "weight_g": 150,
          "found_in_list": true,
          "nutrition_per_100g": null
        },
        {
          "item_name": "broccoli, cooked",
          "weight_g": 100,
          "found_in_list": true,
          "nutrition_per_100g": null
        },
        {
          "item_name": "homemade teriyaki sauce",
          "weight_g": 40,
          "found_in_list": false,
          "nutrition_per_100g": {
            "calorie": 89,
            "protein_g": 2,
            "fat_g": 0.5,
            "carbs_g": 20
          }
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
      "dish_name": "cheese pizza with extras",
      "unit_count": 1,
      "confidence": 0.88,
      "analysis_method": "HYBRID_DECOMPOSITION",
      "base_food": {
        "item_name": "pizza, cheese, regular crust",
        "weight_g": 200,
        "found_in_list": true,
        "nutrition_per_100g": null
      },
      "ingredients": [
        {
          "item_name": "pepperoni",
          "weight_g": 30,
          "found_in_list": true,
          "nutrition_per_100g": null
        },
        {
          "item_name": "mushrooms, white, cooked",
          "weight_g": 40,
          "found_in_list": true,
          "nutrition_per_100g": null
        }
      ]
    }
  ]
}
```

ハンバーガーにカスタムトッピング：
```json
{
  "dishes": [
    {
      "dish_name": "burger with special sauce",
      "unit_count": 1,
      "confidence": 0.75,
      "analysis_method": "HYBRID_DECOMPOSITION",
      "base_food": {
        "item_name": "hamburger, regular, single patty, with condiments",
        "weight_g": 200,
        "found_in_list": true,
        "nutrition_per_100g": null
      },
      "ingredients": [
        {
          "item_name": "bacon, cooked",
          "weight_g": 20,
          "found_in_list": true,
          "nutrition_per_100g": null
        },
        {
          "item_name": "special house sauce",
          "weight_g": 25,
          "found_in_list": false,
          "nutrition_per_100g": {
            "calorie": 350,
            "protein_g": 1,
            "fat_g": 35,
            "carbs_g": 8
          }
        }
      ]
    }
  ]
}
```

## 複数料理の例

```json
{
  "dishes": [
    {
      "dish_name": "grilled chicken",
      "unit_count": 1,
      "confidence": 0.92,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "chicken breast, grilled",
        "weight_g": 150,
        "found_in_list": true,
        "nutrition_per_100g": null
      },
      "ingredients": []
    },
    {
      "dish_name": "side salad",
      "unit_count": 1,
      "confidence": 0.85,
      "analysis_method": "DECOMPOSE_TO_INGREDIENTS",
      "base_food": null,
      "ingredients": [
        {
          "item_name": "mixed greens",
          "weight_g": 80,
          "found_in_list": true,
          "nutrition_per_100g": null
        },
        {
          "item_name": "italian dressing",
          "weight_g": 25,
          "found_in_list": true,
          "nutrition_per_100g": null
        }
      ]
    },
    {
      "dish_name": "french fries",
      "unit_count": 1,
      "confidence": 0.95,
      "analysis_method": "USE_AS_IS",
      "base_food": {
        "item_name": "french fries, restaurant",
        "weight_g": 120,
        "found_in_list": true,
        "nutrition_per_100g": null
      },
      "ingredients": []
    }
  ]
}
```

## バリデーションチェックリスト

1. ✅ USE_AS_IS: base_food存在、ingredients空配列
2. ✅ DECOMPOSE_TO_INGREDIENTS: base_food=null、ingredients非空
3. ✅ HYBRID_DECOMPOSITION: 両方非空
4. ✅ found_in_list=true → nutrition_per_100g=null
5. ✅ found_in_list=false → nutrition_per_100g必須
6. ✅ 栄養素の妥当性（calorie計算）
7. ✅ weight_g > 0