# 最終統合マッピングファイル作成レポート

## 📊 概要

base_1〜base_7.jsonを統合し、重複項目を適切に処理した最終版`mappings.json`を作成しました。

## 🎯 統合戦略

### 重複処理の方針

1. **Survey FNDDS優先**: base_1-6のSurvey FNDDSデータをベースとする
2. **Foundation Food補完**: base_7のFoundation Foodデータを補完情報として追加
3. **両データベース統合**: all_usda_mappingsに両方のデータベースから項目を収集
4. **メタ情報保持**: 統合された項目には`is_merged`フラグと`merge_info`を追加

## 📈 統合結果

### 数値サマリー

| 項目 | 数値 | 説明 |
|------|------|------|
| **総項目数** | 488 | ユニークな食品ID数 |
| **Survey FNDDS項目** | 408 | base_1-6由来の項目 |
| **Foundation Food専用** | 80 | base_7のみの項目 |
| **統合された重複** | 27 | 両データベースに存在する項目 |
| **ファイルサイズ** | 501 KB | 約33KB増加（統合情報追加） |

## 🔄 重複項目の統合例

### apple（リンゴ）の場合

```json
{
  "display_name": "Apple",
  "default_usda": {
    "name": "Apple, raw",            // Survey FNDDS版
    "database": "survey_fndds"
  },
  "foundation_alternative": {        // Foundation Food版を保持
    "name": "Apples, gala, with skin, raw",
    "database": "foundation"
  },
  "all_usda_mappings": [
    // Survey FNDDSから4項目
    "Apple, raw",
    "Apple, baked",
    ...
    // Foundation Foodから5項目追加
    "Apples, fuji, with skin, raw",
    "Apples, gala, with skin, raw",
    ...
  ],
  "is_merged": true,                // 統合フラグ
  "merge_info": {                   // 統合情報
    "survey_mappings_count": 4,
    "foundation_mappings_count": 5
  }
}
```

## 📝 新しいフィールド

### 統合項目に追加されたフィールド

| フィールド | 型 | 説明 |
|-----------|---|------|
| `foundation_alternative` | object | Foundation Foodでの代替名 |
| `databases` | array | 使用可能なデータベースリスト |
| `is_merged` | boolean | 統合された項目かどうか |
| `merge_info` | object | 統合の詳細情報 |

## ✅ 改善点

1. **重複の解消**: 29件の重複を27件に統合（2件は同一base内の重複）
2. **情報の保持**: 両データベースの情報を失わずに統合
3. **選択可能性**: アプリケーションで適切なデータベースを選択可能
4. **トレーサビリティ**: どのデータベースから来たか追跡可能

## 📊 統合された主要項目（27件）

| 食品ID | Survey FNDDS | Foundation Food |
|--------|-------------|-----------------|
| almond_milk | Almond milk, NFS | Almond milk, unsweetened, plain |
| apple | Apple, raw | Apples, gala, with skin, raw |
| banana | Banana, raw | Bananas, ripe and slightly ripe, raw |
| bacon | Bacon, NS as to type | Pork, cured, bacon, cooked |
| berries | Berry, NFS | Strawberries, raw |
| ... | ... | ... |

## 🚀 使用方法

### 基本的な使用

```python
import json

with open('mappings.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

mappings = data['mappings']
apple = mappings['apple']

# Survey FNDDS版を使用
default_name = apple['default_usda']['name']

# Foundation Food版を使用（存在する場合）
if 'foundation_alternative' in apple:
    foundation_name = apple['foundation_alternative']['name']

# 統合された項目かチェック
if apple.get('is_merged'):
    print(f"Survey: {apple['merge_info']['survey_mappings_count']} items")
    print(f"Foundation: {apple['merge_info']['foundation_mappings_count']} items")
```

## 📁 生成ファイル

1. **mappings.json** - 最終統合マッピング（v2.0）
2. **mappings.json.backup_v2** - 前バージョンのバックアップ
3. **duplicate_analysis.json** - 重複分析結果
4. **final_mappings_report.md** - このレポート

## ⚠️ 注意事項

1. **データベースの違い**: Survey FNDDSとFoundation Foodでは栄養価が異なる場合がある
2. **優先順位**: デフォルトはSurvey FNDDS（より汎用的）
3. **Foundation Food**: より具体的な品種・ブランドの栄養データが必要な場合に使用

---
作成日: 2024-10-22
バージョン: 2.0
スクリプト: create_merged_mappings.py
