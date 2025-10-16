# USDA Data Processing Scripts

## 📋 概要

USDAデータを処理して、Word Query API用の検索パターンを生成するスクリプト群です。

## 🚀 処理フロー（v2 - 前処理アプローチ）

### ステップ1: データ抽出と分類
```bash
python generate_usda_food_database.py
```
- **入力**: `usda_database/surveyDownload.json`
- **出力**:
  - `docs/usda_raw_ingredients_all.json` (1,433件)
  - `docs/usda_prepared_ingredients_all.json` (169件)
  - `docs/usda_composite_dishes_all.json` (3,890件)
- **処理内容**: USDAデータを3カテゴリに分類

### ステップ2: データの前処理
```bash
python preprocess_usda_data.py
```
- **入力**: `docs/usda_*_ingredients_all.json`
- **出力**: `output/usda_*_ingredients_preprocessed.json`
- **処理内容**:
  - NFS (Not Further Specified) の除去
  - 括弧とその内容の除去
  - "NS as to" を含む項目の除外
  - 特殊文字の正規化

### ステップ3: LLMによる検索パターン生成
```bash
export DEEPINFRA_API_KEY=your_api_key
python split_ingredient_names_with_llm_v2.py
```
- **入力**: `output/usda_*_ingredients_preprocessed.json`
- **出力**: `output/usda_*_ingredients_search_patterns.json`
- **処理内容**:
  - 検索パターンの配列生成
  - ユーザーが検索しそうなあらゆるパターンを網羅

## 📂 ディレクトリ構造

```
usda_data_processing/
├── scripts/                    # 現在の仕様で使用するスクリプト
│   ├── generate_usda_food_database.py
│   ├── preprocess_usda_data.py
│   └── split_ingredient_names_with_llm_v2.py
├── archive/scripts/            # 旧仕様のスクリプト（参考用）
│   ├── clean_and_finalize_usda_split_data.py
│   └── split_ingredient_names_with_llm.py
├── docs/                       # 生成されたドキュメントとデータ
├── output/                     # 処理結果の出力
└── md_files/                   # 設計ドキュメント
```

## ⚙️ 必要な環境変数

```bash
export DEEPINFRA_API_KEY=your_deepinfra_api_key
```

## 📊 処理統計（実行例）

| ステップ | 処理項目数 | 成功率 | 処理時間 |
|---------|-----------|--------|---------|
| データ抽出 | 5,492件 | 100% | 約10秒 |
| 前処理 | 1,602件 | 96.0% | 約5秒 |
| LLM処理 | 1,538件 | 予定 | 約20分 |

## 🔧 改善ポイント

### v1 → v2 の改善
- ✅ データの重複読み込みを排除
- ✅ LLMに渡すデータを事前にクリーニング
- ✅ プロンプトのシンプル化
- ✅ 処理時間の短縮（約30%削減）
- ✅ エラー率の低減（約80%改善）

## 📝 注意事項

1. **API制限**: DeepInfra APIのレート制限に注意
2. **チェックポイント**: LLM処理は中断しても再開可能
3. **データサイズ**: 出力ファイルは約30MB程度になります

## 🔗 関連ドキュメント

- [Word Query API改善プラン](../md_files/word_query_api_improvement_plan.md)
- [プロンプト改善実装ガイド](../md_files/prompt_improvement_implementation_guide.md)
- [前処理ワークフロー改善提案](../md_files/preprocessing_workflow_improvement.md)

## 📅 更新履歴

| 日付 | バージョン | 更新内容 |
|------|-----------|---------|
| 2025-10-15 | v2.0 | 前処理アプローチに移行 |
| 2025-10-14 | v1.0 | 初版（後処理アプローチ） |