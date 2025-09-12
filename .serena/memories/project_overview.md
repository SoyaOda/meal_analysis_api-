# 食事分析API v2.0 プロジェクト概要

## プロジェクトの目的
- 食事画像を分析して栄養価を計算するAPIシステム
- Deep Infra AIモデル（Qwen2.5-VL、Gemma 3等）を使用した画像分析
- Elasticsearch基盤の栄養データベース検索システム
- 写真とテキスト入力→JSON結果出力

## 主要コンポーネント
- **MealAnalysisPipeline**: メイン分析パイプライン（`app_v2/pipeline/orchestrator.py`）
- **Phase1Component**: 画像分析コンポーネント（Deep Infra連携）
- **FuzzyIngredientSearchComponent**: Elasticsearch栄養検索
- **FastAPI**: Web API（`app_v2/main/app.py`）

## 技術スタック
- **Backend**: Python 3.9, FastAPI, Uvicorn
- **AI/ML**: Deep Infra API（複数モデル対応）
- **検索**: Elasticsearch 8.15.1
- **その他**: Pydantic, python-dotenv, Pillow
- **デプロイ**: Google Cloud Run, Firebase

## プロジェクト構造
```
meal_analysis_api_2/
├── app_v2/                    # メインアプリケーション
│   ├── pipeline/orchestrator.py   # 分析パイプライン
│   ├── components/            # 分析コンポーネント
│   ├── main/app.py           # FastAPI アプリケーション
│   ├── api/v1/               # API エンドポイント
│   └── config/               # 設定管理
├── test_single_image_analysis.py  # テストスクリプト
├── test_images/              # テスト画像
└── requirements.txt          # 依存関係
```

## エントリーポイント
- **テスト実行**: `source venv/bin/activate && python test_single_image_analysis.py`
- **API起動**: `python -m app_v2.main.app`
- **FastAPI**: `/api/v1/meal-analyses/complete` エンドポイント