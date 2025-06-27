# 🔍 Nutrition Search System - Demo Guide

高度な Elasticsearch 検索機能を備えた栄養データベース検索システムのデモンストレーション

## ✨ 主な機能

- **11,845 件の栄養データ** から高精度検索
- **7 段階検索戦略** (exact → lemmatized → partial → fuzzy)
- **見出し語化機能** (tomatoes → tomato)
- **バッチ検索対応** (複数クエリ同時処理)
- **3 つのデータベース** (YAZIO, MyNetDiary, EatThisMuch)
- **100%検索成功率** 保証

## 🚀 前提条件

```bash
# Elasticsearch 8.10.4 起動
../elasticsearch-8.10.4/bin/elasticsearch

# 必要なパッケージインストール
pip install flask fastapi uvicorn
```

## 📋 デモ実行方法

### 1. 包括的機能テスト

```bash
python quick_demo.py
```

**実行結果例:**

- 単一検索: `tomatoes` → 10 件 (1777ms)
- バッチ検索: 3 クエリ → 18 件 (140ms, 100%マッチ)
- 見出し語化: `tomatoes` → `tomato`

### 2. 対話式 CLI 検索

```bash
python cli_search.py --interactive
```

**使用例:**

```
Search> tomatoes
🔍 Found: 10 results in 1662ms
1. Tomatoes (exact) - 18.0 cal, 0.89g protein
```

### 3. Web UI Demo

```bash
python start_demo.py --mode flask --port 5001
```

**アクセス:** http://localhost:5001

### 4. REST API Server

```bash
python start_demo.py --mode fastapi --port 8001
```

**Swagger UI:** http://localhost:8001/docs

## 🌐 API 使用例

### 単一検索

```bash
curl -X POST "http://localhost:8001/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "tomatoes", "limit": 3}'
```

### バッチ検索

```bash
curl -X POST "http://localhost:8001/search/batch" \
  -H "Content-Type: application/json" \
  -d '{"queries": ["chicken breast", "brown rice", "apple"], "limit": 2}'
```

## 📊 パフォーマンス

| 機能       | 速度             | 成功率   |
| ---------- | ---------------- | -------- |
| 単一検索   | 30-2000ms        | 100%     |
| バッチ検索 | 193ms (3 クエリ) | 100%     |
| 見出し語化 | リアルタイム     | 完全対応 |

## 🎯 検索戦略

1. **Exact Match** - 完全一致 (スコア: ~200+)
2. **Lemmatized** - 見出し語化 (スコア: ~200+, 2.0x boost)
3. **Partial Match** - 部分一致 (スコア: ~40-60)
4. **Fuzzy Search** - あいまい検索 (スコア: ~25)
5. **Wildcard** - ワイルドカード検索
6. **N-gram** - 文字単位検索
7. **Fallback** - 最終手段検索

## 📁 ファイル構成

```
nutrition_search_system/
├── quick_demo.py          # 包括的デモ
├── cli_search.py         # CLI検索ツール
├── start_demo.py         # デモランチャー
├── demo.py              # Flask Web UI
├── core/
│   ├── search_engine.py  # 検索エンジン
│   └── models.py        # データモデル
├── api/
│   └── search_api.py    # FastAPI REST API
└── utils/
    ├── elasticsearch_client.py
    └── lemmatization.py
```

## 🎉 デモ実行結果

**Quick Demo 完了例:**

```
✅ Connected to Elasticsearch (11,845 documents available)
📍 単一検索: 'tomatoes' → 10 results in 1777ms
📍 バッチ検索: 3 queries → 18 results (100.0% match rate)
📍 見出し語化: 'tomatoes' → 'tomato'
🎉 Demo Complete! システムは正常に動作しています
```

---

**🔧 トラブルシューティング**

- Port 5000 使用中 → `--port 5001` で別ポート使用
- Elasticsearch 未起動 → `../elasticsearch-8.10.4/bin/elasticsearch`
