# Test Results Directory

このディレクトリには、MyNetDiary web scrapingのテスト結果が保存されます。

## ファイル形式

### Raw Serving Extractor テスト結果
- **ファイル名**: `raw_serving_extractor_test_results_YYYYMMDD_HHMMSS.json`
- **内容**: コンポーネント版テストの結果
- **構造**: 生serving data + テスト統計

### Complete Serving Data
- **ファイル名**: `complete_serving_data_YYYYMMDD_HHMMSS.json`
- **内容**: 従来版抽出の結果
- **構造**: 完全serving options

## データ形式例

```json
{
  "test_summary": {
    "total_tests": 4,
    "successful_tests": 4,
    "total_raw_serving_options": 16
  },
  "test_results": [
    {
      "food_name": "Almond milk unsweetened fortified",
      "raw_serving_options": [
        {
          "radio_value": "1_1",
          "raw_text": "cup 30cals / 245 g",
          "option_index": 1
        }
      ]
    }
  ]
}
```

## 自動生成ファイル

- ⚠️ このディレクトリ内のJSONファイルは自動生成されます
- 📁 `.gitignore`により、結果ファイルはGit管理対象外です
- 🔄 定期的にクリーンアップすることを推奨します