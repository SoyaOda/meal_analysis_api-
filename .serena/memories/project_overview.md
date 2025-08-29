# Meal Analysis API v2.0 プロジェクト概要

## プロジェクトの目的
Google Gemini AI と Elasticsearch ベースマルチデータベース栄養検索システムを使用した高度な食事画像分析システム。動的栄養計算機能により、料理の特性に応じて最適な栄養計算戦略を自動選択し、正確な栄養価情報を提供する。

## 技術スタック
- **フレームワーク**: FastAPI 0.104+
- **AI サービス**: Google Vertex AI (Gemini 2.5 Flash)
- **データベース**: Elasticsearch (栄養データ検索用)
- **認証**: Google Cloud サービスアカウント
- **Python バージョン**: 3.9+

## 主要ライブラリ
- `fastapi==0.104.1`: Web API フレームワーク
- `uvicorn==0.24.0`: ASGI サーバー
- `google-generativeai==0.8.5`: Gemini AI連携
- `httpx==0.25.2`: 非同期 HTTP クライアント
- `pydantic==2.5.0`: データバリデーション
- `pillow==11.2.1`: 画像処理

## アーキテクチャ
- **app_v2/**: コンポーネントベース設計の新アーキテクチャ
- **components/**: 再利用可能なコンポーネント
- **pipeline/**: パイプライン管理とオーケストレーション
- **models/**: データモデル定義
- **api/**: エンドポイント定義
- **config/**: 設定管理

## データベース構成
- YAZIO: 1,825 項目 (バランスの取れた食品カテゴリ)
- MyNetDiary: 1,142 項目 (科学的/栄養学的アプローチ)
- EatThisMuch: 8,878 項目 (最大かつ最も包括的)