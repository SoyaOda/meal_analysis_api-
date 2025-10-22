# 統合マッピングファイル作成レポート

## 概要

base_1.json〜base_7.jsonを統合して一つの`mappings.json`ファイルを作成しました。

## 統合結果

### ファイル統計

| ファイル | 項目数 | 重複数 | データベース |
|---------|-------|--------|------------|
| base_1.json | 51 | 0 | Survey FNDDS |
| base_2.json | 58 | 0 | Survey FNDDS |
| base_3.json | 77 | 1 | Survey FNDDS |
| base_4.json | 55 | 0 | Survey FNDDS |
| base_5.json | 57 | 0 | Survey FNDDS |
| base_6.json | 112 | 1 | Survey FNDDS |
| base_7.json | 107 | 27 | Foundation Food |
| **合計** | **517** | **29** | - |

### 最終結果

- **総項目数**: 517項目
- **ユニーク項目数**: 488項目
- **重複除外数**: 29項目
- **ファイルサイズ**: 468KB

## 重複項目の処理

### 重複の内訳

1. **base_3での重複** (1件)
   - `hamburger`

2. **base_6での重複** (1件)
   - `dumplings`

3. **base_7での重複** (27件)
   - Survey FNDDSとFoundation Foodで同じ食品IDを使用
   - 例: `almond_milk`, `soy_milk`, `apple`, `banana`, `bacon`, etc.

### 重複時の優先順位

**先に読み込まれたファイルの項目を優先**（First-in wins）

- base_1-6 (Survey FNDDS) の項目が優先される
- base_7 (Foundation Food) の重複項目は除外される

## データベース構成

### Survey FNDDS (base_1-6)
- **項目数**: 410項目（重複除外後）
- **特徴**: 汎用名（NFS）が多い、調理済み食品を含む

### Foundation Food (base_7)
- **項目数**: 78項目（重複除外後）
- **特徴**: 具体的な品種、主に生の食材

## ファイル構造

```json
{
  "_metadata": {
    "description": "Unified food name mappings from base_1 to base_7",
    "source_files": ["base_1.json", ..., "base_7.json"],
    "total_foods": 488,
    "databases_used": ["survey_fndds", "foundation"],
    "version": "1.0"
  },
  "mappings": {
    "food_id_1": { ... },
    "food_id_2": { ... },
    ...
  }
}
```

## 検証状況

すべてのソースファイルは対応するUSDAデータベースに対して100%検証済み：

- ✅ base_1-6: Survey FNDDS (survey_food_names.txt)
- ✅ base_7: Foundation Food (foundation_food_names.txt)

## 使用方法

```python
import json

# マッピングを読み込み
with open('mappings/mappings.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# メタデータを取得
metadata = data['_metadata']
print(f"Total foods: {metadata['total_foods']}")

# マッピングを取得
mappings = data['mappings']

# 特定の食品を検索
apple_mapping = mappings.get('apple')
if apple_mapping:
    print(f"Default USDA: {apple_mapping['default_usda']['name']}")
```

## 注意事項

1. **重複項目**: Survey FNDDSとFoundation Foodで同じ食品IDがある場合、Survey FNDDSを優先
2. **データベースの違い**: 同じ食品でもデータベースによって栄養価が異なる可能性あり
3. **バックアップ**: 既存のmappings.jsonがあった場合は`.backup`ファイルに保存済み

---
生成日: 2025-10-22
スクリプト: create_unified_mappings.py
