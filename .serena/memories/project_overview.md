# プロジェクト概要

## プロジェクトの目的
食事分析API v2.0 - Google Gemini AIとElasticsearchベースマルチデータベース栄養検索システムを使用した高度な食事画像分析システム

## 主要機能
- **Gemini 2.5 Flash AI画像分析**: 食事画像から料理識別、食材抽出、重量推定
- **Elasticsearch栄養検索**: MyNetDiaryデータベース(1,142項目)による高速検索
- **動的栄養計算**: AI駆動の計算戦略決定と高精度栄養価算出
- **Cloud Run本番環境**: スケーラブルなサーバーレス実行環境
- **複数料理対応**: 1枚の画像で複数料理を同時分析
- **多言語対応**: 英語・日本語での食材・料理認識

## 技術スタック
- **言語**: Python 3.9+
- **Webフレームワーク**: FastAPI 0.104.1
- **AI/ML**: Google Cloud Vertex AI (Gemini 2.5 Flash)
- **検索エンジン**: Elasticsearch 8.15.1 + NLTK 3.9.1
- **クラウド**: Google Cloud Run + Compute Engine VM
- **データ検証**: Pydantic 2.5.0
- **画像処理**: Pillow 11.2.1
- **HTTP**: httpx (非同期)
- **テスト**: pytest 7.4.3

## 現在の本番環境
- **API URL**: https://meal-analysis-api-1077966746907.us-central1.run.app
- **Elasticsearch VM**: elasticsearch-vm (us-central1-a)
- **データベース**: MyNetDiaryインデックス (mynetdiary_nutrition_db)

## 開発環境
- **OS**: Darwin (macOS)
- **プロジェクトルート**: /Users/odasoya/meal_analysis_api_2
- **Python環境**: venv推奨