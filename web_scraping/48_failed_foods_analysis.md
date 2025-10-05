# 48失敗食材の分析レポート

## 1. 48食材の導出過程

### 1.1 元データソース
- **ファイル**: `data/retry_failed_foods_20251001_184207.json`
- **生成元スクリプト**: `retry_failed_foods_main.py`
- **実行日時**: 2025-10-01 18:42:07

### 1.2 失敗食材の定義
- スクレイピング結果で `improved_servings` が0個の食材
- つまり、serving情報（unit、grams、calories）が適切に抽出できなかった食材

### 1.3 抽出ロジック
```python
# test_processor_on_failed_food.py より
failed_foods = []
for food in results:
    comp_data = food.get('comprehensive_data', {})
    serving_opts = comp_data.get('serving_options', {})
    improved_servings = serving_opts.get('improved_servings', [])

    if len(improved_servings) == 0:
        failed_foods.append(food)
```

### 1.4 結果
- **総食材数**: 48個
- **成功**: 24個 (improved_servings > 0)
- **失敗**: 24個 (improved_servings == 0)

---

## 2. データの保存状態

### 2.1 失敗食材リスト
- **ファイル**: `data/failed_foods_list.json`
- **構造**:
```json
{
  "total_count": 48,
  "failed_foods": ["食材名1", "食材名2", ...],
  "extracted_at": "2025-10-01T...",
  "reason": "insufficient_serving"
}
```

### 2.2 スクレイピング結果データ
- **ファイル**: `data/retry_failed_foods_20251001_184207.json`
- **構造**:
```json
{
  "collection_results": [
    {
      "food_name": "...",
      "comprehensive_data": {
        "serving_options": {
          "raw_serving_data": [...],  // ← 実はデータは取得できている
          "improved_servings": []      // ← 後処理で抽出失敗
        }
      }
    }
  ]
}
```

### 2.3 重要な発見
✅ **全48食材について `raw_serving_data` は取得できている**
- スクレイピング自体は成功
- 問題は後処理の抽出ロジックにある

---

## 3. 後処理の問題点

### 3.1 対象スクリプト
- **ファイル**: `web_scraping/scripts/food_data_processor.py`
- **メソッド**: `FoodDataProcessor._fallback_serving_extraction()`
- **呼び出し元**: `FoodDataProcessor.clean_serving_data()`

### 3.2 テストケース: Cajun seasoning salt free
#### 期待される9個のserving
```
1. tsp 0cals / 3.2 g
2. 0.25 tsp 0cals / 0.8 g
3. tablespoon 0cals / 9.6 g
4. gram 0cals / 1 g
5. cup 0cals / 153.6 g
6. oz 0cals / 28.3 g
7. ml 0cals / 0.6 g
8. fl oz 0cals / 19.2 g
9. lb 0cals / 453.6 g
```

#### 実際に抽出された7個
```
1. ✅ teaspoon (3.2g)
2. ❌ 0.25 tsp - 欠落
3. ✅ tablespoon (9.6g)
4. ⚠️ gram (0.1g) - グラム数が誤り（1gのはずが0.1g）
5. ✅ cup (153.6g)
6. ✅ oz (28.3g)
7. ✅ ml (0.6g)
8. ❌ fl oz - 欠落
9. ✅ lb (453.6g)
```

#### 成功率: 7/9 = 77.8%

### 3.3 具体的な問題

#### 問題1: gramのグラム数が誤り
- **期待値**: `gram 0cals / 1 g` → 1g
- **実際**: 0.1g
- **原因**: 不明（要デバッグ）

#### 問題2: `0.25 tsp` が抽出できない
- **raw data**: `[19] 0.25 tsp 0cals / 0.8 g`
- **パターン**: `(\d+(?:\.\d+)?)\s+([a-zA-Z\s\.]+?)\s+(\d+(?:,\d{3})*(?:\.\d+)?)\s*cals?\s*/\s*(\d+(?:\.\d+)?)\s*g`
- **原因**: パターンマッチしているはずだが、抽出されていない（要デバッグ）

#### 問題3: `fl oz` が抽出できない
- **raw data**:
  - `[37] fl oz 0cals / 19.2 g`
  - `[38] fl oz` (単独)
- **除外パターン**: `^(oz|ml|fl\s*oz|lb|...)$` (完全一致)
- **原因**: 単独の `fl oz` が除外される可能性あり（要デバッグ）

---

## 4. 現在の抽出ロジック

### 4.1 前処理（重複削除）
```python
# 除外パターン1: "/ X g" のような断片的なパターン
if re.match(r'^\s*/\s*\d+(?:\.\d+)?\s*g\s*$', text):
    continue

# 除外パターン2: 単位名のみ（oz, ml, fl oz, lb など）
if re.match(r'^(oz|ml|fl\s*oz|lb|lbs|g|cup|tsp|tbsp|teaspoon|tablespoon|gram)$', text, re.IGNORECASE):
    continue
```

### 4.2 結合
```python
combined_text = " ".join(cleaned_data)
```

### 4.3 抽出パターン
```python
patterns = [
    # パターン1: 数字で始まる形式（0.25 tsp など）
    r'(\d+(?:\.\d+)?)\s+([a-zA-Z\s\.]+?)\s+(\d+(?:,\d{3})*(?:\.\d+)?)\s*cals?\s*/\s*(\d+(?:\.\d+)?)\s*g',

    # パターン2: 通常の形式（tsp, tablespoon, fl oz など）
    r'([a-zA-Z\s\.]+?)\s+(\d+(?:,\d{3})*(?:\.\d+)?)\s*cals?\s*/\s*(\d+(?:\.\d+)?)\s*g'
]
```

### 4.4 正規化
- パターン1でマッチした場合、1単位あたりに正規化
  - 例: `0.25 tsp 0cals / 0.8 g` → `1 tsp = 3.2g`
  - 計算: `grams_per_unit = 0.8 / 0.25 = 3.2`

---

## 5. 修正履歴

### v1: 0カロリー食材の除外問題
- **問題**: `0 < calories` の条件で0カロリー食材が除外
- **修正**: `0 <= calories` に変更（Line 369）

### v2: 結合時の境界問題
- **問題**: `"/ 9.6 g tablespoon 0cals"` → `"g tablespoon"` という誤ったunit
- **修正**: 重複断片（`/ X g`）と単独単位名を除外してから結合

### v3（現在）: 部分的成功
- **成功**: 7/9のserving抽出
- **残課題**:
  - `0.25 tsp` の抽出失敗
  - `fl oz` の抽出失敗
  - `gram` のグラム数誤り

---

## 6. 次のステップ

### 6.1 デバッグが必要な項目
1. cleaned_dataとcombined_textの内容確認
2. パターンマッチの動作確認
3. 正規化計算の検証

### 6.2 目標
- **短期**: Cajun seasoningで9/9抽出達成
- **中期**: 全24失敗食材に適用
- **長期**: 全48食材の品質向上

### 6.3 テストスクリプト
- `test_processor_on_failed_food.py`: 失敗食材でのprocessorテスト
- `test_failed_food.py`: Playwright経由での直接スクレイピングテスト（比較用）

---

## 7. 関連ファイル一覧

### データファイル
- `data/failed_foods_list.json` - 48失敗食材リスト
- `data/retry_failed_foods_20251001_184207.json` - 再スクレイピング結果
- `debug/processor_test_Cajun_seasoning_salt_free,_tsp.json` - 個別テスト結果

### スクリプト
- `retry_failed_foods_main.py` - 失敗食材の再スクレイピング
- `test_processor_on_failed_food.py` - processor単体テスト
- `test_failed_food.py` - Playwright直接スクレイピングテスト
- `web_scraping/scripts/food_data_processor.py` - 後処理ロジック本体

### コンポーネント
- `src/components/playwright_multi_food_navigator.py` - ナビゲーション
- `src/components/playwright_food_data_collector.py` - データ収集

---

*最終更新: 2025-10-01*
*分析者: Claude Code (Serena MCP)*
