# Test Queries for Retriever/Reranker Quality Testing

VLMが出力しそうな難しめのクエリを集めたテストセット。

## ファイル構成

```
test_queries/
├── README.md
├── challenging_food_queries.json   # テストクエリ定義
└── test_reranker_quality.py        # テストスクリプト
```

## クエリカテゴリ

| カテゴリ | 説明 | クエリ数 | 難易度 |
|---------|------|---------|-------|
| `similar_vegetables` | 見た目が似ている野菜 (broccoli/cauliflower等) | 11 | 高 |
| `asian_noodles` | アジア麺類の紛らわしい名前 | 9 | 高 |
| `cooking_method_variations` | 同じ食材の調理法違い | 10 | 中 |
| `compound_dishes` | 複合料理・ミックス料理 | 8 | 高 |
| `ambiguous_terms` | 地域差・別名がある食品 | 8 | 中 |
| `portion_descriptors` | 部位・カットの記述 | 6 | 中 |
| `dairy_alternatives` | 乳製品と植物性代替品 | 7 | 中 |
| `grains_and_starches` | 似た穀物・澱粉類 | 8 | 中 |

## 使用方法

### クイックテスト (8クエリ)
```bash
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 python test_queries/test_reranker_quality.py --quick
```

### フルテスト (全67クエリ)
```bash
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 python test_queries/test_reranker_quality.py
```

### 特定カテゴリのみ
```bash
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 python test_queries/test_reranker_quality.py --category similar_vegetables
```

### モデル・TopK指定
```bash
# 4Bモデル、TopK=30でテスト
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 python test_queries/test_reranker_quality.py --model Qwen/Qwen3-Reranker-4B --topk 30

# 8Bモデル、TopK=50でテスト
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 python test_queries/test_reranker_quality.py --model Qwen/Qwen3-Reranker-8B --topk 50
```

## テスト結果

| モデル | パス率 | 時間/クエリ | 備考 |
|--------|-------|------------|------|
| **4B** | 67/67 (100%) | 608ms | 推奨 |
| 8B | 67/67 (100%) | ~650ms | 4Bと同等精度 |
| 0.6B | 57/67 (85.1%) | 471ms | 品質低下 |

## 既知の問題

### 0.6Bモデルの問題
- `Broccoli, green, cooked` → `Cauliflower` を誤選択
- 全てのスコアが 0.9999 になる（過信）
- 麺類・穀物類で多数の誤マッチ
- **本番環境では使用非推奨**

### 推奨設定
- **本番環境**: `Qwen/Qwen3-Reranker-4B`, TopK=50
- **速度重視**: `Qwen/Qwen3-Reranker-4B`, TopK=30 (品質維持)

## 参考資料

- [USDA FoodData Central](https://fdc.nal.usda.gov/)
- [Food Recognition Benchmark (Frontiers)](https://www.frontiersin.org/articles/10.3389/fnut.2022.875143/full)
- [FAO INFOODS Guidelines for Food Matching](https://www.fao.org/fileadmin/templates/food_composition/documents/upload/INFOODSGuidelinesforFoodMatching_final_july2011.pdf)
- [Asian Noodle Guide](https://www.choochoocachew.com/ultimatenoodleguide/)
