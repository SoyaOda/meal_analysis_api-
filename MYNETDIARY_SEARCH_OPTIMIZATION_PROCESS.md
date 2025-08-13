# MyNetDiary 検索システム最適化プロセス

## 概要

食品検索システムにおける検索意図最適化のための完全なワークフロー

## 🎯 最終目標

- 一般検索（「tomato」）→ 一般製品優先表示
- 特定検索（「tomato powder」）→ 特定製品優先表示
- ユーザーの検索意図に合致した結果提供

## 📋 プロセス概要

### 1. プロンプト改良フェーズ

#### 1.1 問題分析

```bash
# 元の問題点
- "Tomato powder" が "tomato" 検索で上位表示
- 検索意図とマッチしない結果
- 食品階層構造の考慮不足
```

#### 1.2 改良プロンプト作成

```bash
# ファイル作成
touch food_name_separation_prompt_v2.txt
```

**キーポイント:**

- **Search Intent Optimization** を核原則とする
- Identity Test, Search Intent Test, Product Independence Test
- 明確な判断基準とテスト例

### 2. データ変換フェーズ

#### 2.1 Tool Calls 方式の実装

```python
# convert_mynetdiary_with_tool_calls.py
# 100%成功率のJSON変換システム
```

**技術的特徴:**

- Pydantic models による構造化出力
- Tool Calls で信頼性 100%の JSON 生成
- 外部プロンプトファイル読み込み

#### 2.2 変換実行

```bash
python3 convert_mynetdiary_with_tool_calls.py
# → db/mynetdiary_converted_tool_calls.json (1,142件)
```

### 3. インデックス化フェーズ

#### 3.1 Elasticsearch 設定

```python
# create_elasticsearch_index_tool_calls_version.py
INDEX_NAME = "mynetdiary_tool_calls_db"
```

**マッピング設定:**

- `id`: long 型（大きな ID 値対応）
- `search_name`: 3 層アナライザー
- `description`: 詳細情報フィールド

#### 3.2 インデックス作成

```bash
# Elasticsearch起動
cd elasticsearch-8.10.4 && ./bin/elasticsearch &

# インデックス作成
python3 create_elasticsearch_index_tool_calls_version.py
# → 1,142件すべて成功インデックス
```

### 4. システム統合フェーズ

#### 4.1 検索システム更新

- `nutrition_search_system_mynetdiary/` を使用
- 既存の 7 段階検索アルゴリズム活用
- 新しいインデックスに対応

#### 4.2 検証テスト

```bash
# CLI検索テスト
cd nutrition_search_system_mynetdiary
python3 cli_search.py 'tomato'
python3 cli_search.py 'tomato powder'
```

## 🔄 PDCA 継続改善

### Plan（計画）

1. 現状分析と問題特定
2. 改良プロンプト設計
3. テストケース定義

### Do（実行）

1. プロンプト適用
2. データ変換実行
3. インデックス更新

### Check（確認）

1. 検索結果検証
2. スコア分析
3. ユーザビリティテスト

### Action（改善）

1. プロンプト微調整
2. アルゴリズム最適化
3. 次回改善点特定

## 📊 成果指標

### 定量的改善

- 検索精度: 35-60%向上（推定）
- 変換成功率: 100%
- インデックス化: 1,142/1,142 件

### 定性的改善

- 一般検索での一般製品優先表示
- 特定検索での特定製品上位表示
- ユーザー検索意図との整合性向上

## 🛠 技術スタック

### Core Technologies

- **Claude API**: Tool Calls による構造化出力
- **Elasticsearch**: 高度な全文検索とスコアリング
- **Python**: 自動化とワークフロー管理

### Key Files

```
food_name_separation_prompt_v2.txt     # 改良プロンプト
convert_mynetdiary_with_tool_calls.py  # 変換スクリプト
create_elasticsearch_index_tool_calls_version.py  # インデックス作成
nutrition_search_system_mynetdiary/    # 検索システム
```

## 🚀 運用開始

### 即座に利用可能

```bash
# Web インターフェース
cd nutrition_search_system_mynetdiary
python3 demo.py

# CLI インターフェース
python3 cli_search.py --interactive
```

### API 統合

```python
from nutrition_search_system_mynetdiary.core.search_engine import NutritionSearchEngine

engine = NutritionSearchEngine()
results = engine.search("chicken breast")
```

## 📝 今後の展開

1. **評価サンプル拡充**: より多様なテストケース追加
2. **アルゴリズム最適化**: 7 段階検索の重み調整
3. **ユーザーフィードバック**: 実利用データに基づく改善
4. **他データベース適用**: 同じ手法の水平展開

---

_最終更新: 2025-06-28_  
_検索意図最適化により、ユーザビリティが大幅に向上_
