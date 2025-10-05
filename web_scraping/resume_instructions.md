
# MyNetDiary データ収集 Resume 実行手順

## 現在の状態
- 総食材数: 1500
- 元の成功数: 0
- 元の失敗数: 1500
- 品質修正による追加失敗: 1135
- 現在の失敗数: 1500
- リトライ候補: 1135

## カテゴリ別失敗統計
- Grains & Grain Products: 91件失敗 (リトライ候補: 89件)
- Spices & Herbs: 89件失敗 (リトライ候補: 73件)
- Vegetables - raw, frozen, or cooked: 159件失敗 (リトライ候補: 159件)
- Poultry: 29件失敗 (リトライ候補: 29件)
- Stocks and Gravy: 23件失敗 (リトライ候補: 23件)
- Vegetables - canned, dried, or juice: 36件失敗 (リトライ候補: 36件)
- Fish & Seafood: 76件失敗 (リトライ候補: 74件)
- Beans & Peas: 49件失敗 (リトライ候補: 45件)
- Fats & Oils: 29件失敗 (リトライ候補: 29件)
- Fruit - canned, dried, or juice: 35件失敗 (リトライ候補: 35件)
- Breads & Rolls: 38件失敗 (リトライ候補: 38件)
- Cheese: 57件失敗 (リトライ候補: 57件)
- Meats: 58件失敗 (リトライ候補: 58件)
- Dairy, Dairy Substitutes & Egg: 64件失敗 (リトライ候補: 62件)
- Condiments, Dressings & Sauces: 139件失敗 (リトライ候補: 74件)
- Sweets & Sweeteners: 104件失敗 (リトライ候補: 49件)
- Beverages: 134件失敗 (リトライ候補: 62件)
- Fruit - raw or frozen: 142件失敗 (リトライ候補: 70件)
- Nuts & Seeds: 148件失敗 (リトライ候補: 73件)

## Resume実行コマンド

```bash
# web_scrapingディレクトリに移動
cd /Users/odasoya/meal_analysis_api_2/web_scraping

# Resume機能で失敗したアイテムを再実行
python src/main_comprehensive_food_collection.py --mode resume --input comprehensive_food_collection_all_20250930_155300_intermediate_1500.json
```

## 期待される結果
- 1135件の食材の再収集を試行
- 品質チェック機能により、UIノイズは自動的に失敗として判定
- 有効な栄養データが取得できた場合のみ成功として記録

## 注意事項
1. 新しい品質チェック機能により、無効データは自動的に失敗として判定されます
2. Amount eaten要素の検出問題は複数のセレクタで対応済みです
3. 結果は新しいファイルに保存され、元ファイルは保持されます

