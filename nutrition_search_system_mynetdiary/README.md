# 🍎 MyNetDiary 専用栄養検索システム

手動修正・改良された MyNetDiary データベース（1,142 項目）専用の高速検索システム

## ✨ 特徴

- 🎯 **MyNetDiary 専用** - 手動修正済みの高品質データベース
- 🔍 **7 段階検索戦略** - 完全一致からファジー検索まで
- 📝 **見出し語化対応** - 複数形・単数形の自動変換 (tomatoes → tomato)
- ⚡ **高速検索** - 平均 100-500ms
- 🌐 **Web UI** - 美しいユーザーインター face
- 🔌 **REST API** - プログラマブルなアクセス

## 🗂️ データベース詳細

- **総項目数**: 1,142 件
- **データソース**: MyNetDiary（手動修正版）
- **構造**: search_name（主要名称）+ description（修飾語）
- **栄養情報**: カロリー、タンパク質、脂質、炭水化物
- **処理品質**: original_success, retry_success, manual_correction

## 🚀 クイックスタート

### 1. システムチェック

```bash
python start_demo.py --check
```

### 2. Web UI 起動（推奨）

```bash
python start_demo.py --flask --port 5002
```

→ http://localhost:5002 でアクセス

### 3. API サーバー起動

```bash
python start_demo.py --api --port 8000
```

→ http://localhost:8000/docs で Swagger UI

### 4. CLI 検索

```bash
python cli_search.py "chicken breast"
python cli_search.py -i  # インタラクティブモード
```

## 🔍 検索例

### Web UI

- chicken breast
- tomatoes (見出し語化: tomato)
- beans
- beef ribeye
- apples

### CLI

```bash
# 単一検索
python cli_search.py "chicken breast"

# バッチ検索
python cli_search.py -b "chicken" "beef" "fish"

# 詳細オプション
python cli_search.py "tomatoes" --limit 5 --min-score 1.0
```

### API

```bash
# GET検索
curl "http://localhost:8000/search?q=chicken%20breast&limit=5"

# POST バッチ検索
curl -X POST "http://localhost:8000/search/batch" \
  -H "Content-Type: application/json" \
  -d '{"queries": ["chicken", "beef"], "limit": 10}'
```

## 🏗️ アーキテクチャ

```
nutrition_search_system_mynetdiary/
├── core/
│   ├── search_engine.py    # 7段階検索エンジン
│   └── models.py          # データモデル
├── utils/
│   ├── elasticsearch_client.py  # ES接続管理
│   └── lemmatization.py        # 見出し語化
├── api/
│   └── search_api.py      # FastAPI REST API
├── demo.py               # Flask Web UI
├── cli_search.py         # コマンドラインツール
└── start_demo.py         # 統合起動スクリプト
```

## 🔧 技術仕様

- **検索エンジン**: Elasticsearch 8.x
- **インデックス名**: `mynetdiary_fixed_db`
- **見出し語化**: NLTK WordNet Lemmatizer
- **Web Framework**: Flask (UI) + FastAPI (API)
- **データ形式**: JSON

## 📊 検索戦略（7 段階）

1. **見出し語化完全一致** (boost: 6.0)
2. **見出し語化一致** (boost: 4.0)
3. **元語完全一致** (boost: 1.8)
4. **元語一致** (boost: 1.5)
5. **見出し語化部分一致** (boost: 2.0)
6. **元語部分一致** (boost: 1.0)
7. **ファジー検索** (boost: 0.5)

## 🎯 パフォーマンス

- **検索速度**: 100-500ms 平均
- **データベースサイズ**: 0.36MB
- **マッチ率**: 高精度マッチング
- **同時接続**: 複数クライアント対応

## 🛠️ 開発者向け

### カスタム設定

```python
from core.search_engine import NutritionSearchEngine
from core.models import SearchQuery

engine = NutritionSearchEngine()
query = SearchQuery(query="chicken", max_results=20)
result = await engine.search(query)
```

### 統計情報

```python
stats = engine.get_stats()
print(f"Total searches: {stats['total_searches']}")
print(f"Average response time: {stats['average_response_time_ms']}ms")
```

## 📝 ライセンス

このプロジェクトは MyNetDiary データの改良版を使用しており、研究・開発目的での利用を想定しています。
