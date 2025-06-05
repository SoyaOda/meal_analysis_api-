# 食事分析 API v2.0 - コンポーネント設計

## 🏗 アーキテクチャ概要

4 つの独立したフェーズコンポーネントによる食事分析パイプライン：

```
Input (Image)
    ↓
Phase1Component (画像分析)
    ↓
USDAQueryComponent (データベース照合)
    ↓
Phase2Component (計算戦略決定)
    ↓
NutritionCalculationComponent (栄養価計算)
    ↓
Output (Complete Analysis Result)
```

## 🔧 コンポーネント設計原則

### 1. インターフェース分離

- 各コンポーネントは明確な入力/出力インターフェースを持つ
- Pydantic モデルによる型安全性
- 設定変更時の影響を最小化

### 2. 単一責任原則

- **Phase1Component**: 画像分析のみ
- **USDAQueryComponent**: データベース照合のみ
- **Phase2Component**: 計算戦略決定のみ
- **NutritionCalculationComponent**: 栄養価計算のみ

### 3. 依存性逆転

- 各コンポーネントは抽象インターフェースに依存
- 具体的な実装は注入される
- テストとモック化が容易

## 📁 新しいディレクトリ構造

```
app_v2/
├── components/
│   ├── __init__.py
│   ├── base.py                    # ベースコンポーネント抽象クラス
│   ├── phase1_component.py        # Phase1: 画像分析コンポーネント
│   ├── usda_query_component.py    # USDA照合コンポーネント
│   ├── phase2_component.py        # Phase2: 戦略決定コンポーネント
│   └── nutrition_calc_component.py # 栄養計算コンポーネント
├── models/
│   ├── __init__.py
│   ├── phase1_models.py           # Phase1の入力/出力モデル
│   ├── usda_models.py             # USDA照合の入力/出力モデル
│   ├── phase2_models.py           # Phase2の入力/出力モデル
│   └── nutrition_models.py        # 栄養計算の入力/出力モデル
├── services/
│   ├── __init__.py
│   ├── gemini_service.py          # Gemini AIサービス
│   ├── usda_service.py            # USDAサービス
│   └── nutrition_service.py       # 栄養計算サービス
├── config/
│   ├── __init__.py
│   ├── settings.py                # 設定管理
│   └── prompts/                   # プロンプトテンプレート
│       ├── phase1_prompts.py
│       └── phase2_prompts.py
├── api/
│   └── v1/
│       ├── endpoints/
│       │   └── meal_analysis.py   # 統合APIエンドポイント
│       └── schemas/
│           └── api_models.py      # API入力/出力モデル
├── pipeline/
│   ├── __init__.py
│   ├── orchestrator.py            # パイプライン統合
│   └── result_manager.py          # 結果保存/管理
└── main/
    └── app.py                     # FastAPIアプリケーション
```

## 🔄 データフロー設計

### Phase1Component

```python
Input: Phase1Input (image_bytes, mime_type, optional_text)
Output: Phase1Output (dishes: List[Dish])
```

### USDAQueryComponent

```python
Input: USDAQueryInput (ingredient_names: List[str])
Output: USDAQueryOutput (matches: Dict[str, USDAMatch])
```

### Phase2Component

```python
Input: Phase2Input (image_bytes, phase1_result, usda_matches)
Output: Phase2Output (dishes: List[RefinedDish])
```

### NutritionCalculationComponent

```python
Input: NutritionInput (refined_dishes: List[RefinedDish])
Output: NutritionOutput (total_nutrients: TotalNutrients)
```

## 🎯 主要な改善点

1. **モジュール分離**: 各フェーズが独立したモジュール
2. **型安全性**: 全てのデータフローが型チェック済み
3. **テスト容易性**: 各コンポーネントが独立してテスト可能
4. **設定管理**: プロンプトや設定の変更が容易
5. **エラーハンドリング**: 各コンポーネントでの詳細なエラー処理
6. **拡張性**: 新しいコンポーネントの追加が容易

## 🚀 実装戦略

1. **ベースコンポーネント**: 抽象クラスとインターフェースの定義
2. **モデル定義**: 各フェーズの入力/出力モデル
3. **コンポーネント実装**: 各フェーズの具体的実装
4. **パイプライン統合**: オーケストレーターによる統合
5. **API エンドポイント**: 外部インターフェースの実装
6. **テストとバリデーション**: 既存機能との互換性確認
