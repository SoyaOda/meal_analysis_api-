# コードスタイルとコンベンション

## Python コードスタイル

### 命名規則
- **クラス名**: PascalCase (`MealAnalysisPipeline`, `Phase1Component`)
- **関数・メソッド名**: snake_case (`execute_complete_analysis`, `get_pipeline_info`)
- **変数名**: snake_case (`pipeline_id`, `vision_service`)
- **定数**: UPPER_CASE (`USE_ELASTICSEARCH_SEARCH`)

### インポート規則
```python
# 標準ライブラリ
import os
import asyncio
import logging

# サードパーティライブラリ
from fastapi import FastAPI
from pydantic import BaseModel

# ローカルモジュール
from ..config import get_settings
from ..pipeline.orchestrator import MealAnalysisPipeline
```

### ドキュメント
- **クラス**: docstring あり
- **メソッド**: 重要なメソッドにはdocstring
- **型ヒント**: 一部使用（Pydantic モデル等）

### エラーハンドリング
```python
try:
    result = await pipeline.execute_complete_analysis(...)
except Exception as e:
    print(f"❌ 分析エラー: {str(e)}")
    traceback.print_exc()
```

## FastAPI 設計パターン

### ルーター構成
```
app_v2/
├── main/app.py          # メインアプリケーション
├── api/v1/endpoints/    # APIエンドポイント
└── models/              # Pydanticモデル
```

### エンドポイント命名
- **完全分析**: `/api/v1/meal-analyses/complete`
- **ヘルスチェック**: `/health`
- **API ドキュメント**: `/docs`

## ログ出力形式
```python
print(f"🚀 分析開始")
print(f"✅ 完了")  
print(f"❌ エラー")
print(f"📊 結果サマリー")
```

## 設定管理
- **環境変数**: `.env` ファイル + `python-dotenv`
- **設定クラス**: Pydanticベース
- **デフォルト値**: 適切なフォールバック設定