# Nutrition Analysis API - モジュール化版

食事画像から栄養素を推定するモジュール化された API システム

## 🏗️ アーキテクチャ概要

このシステムは 4 つの独立したフェーズに分かれており、各フェーズは独立して設定とデータベース/プロンプト戦略を変更できるよう設計されています。

```
📸 Phase 1: Image Processing → 🔍 Phase 2: Database Query →
📊 Phase 3: Data Interpretation → 🧮 Phase 4: Nutrition Calculation
```

### 主要コンポーネント

- **Image Processor** - 画像認識と Gemini 統合
- **DB Interface** - 抽象化されたデータベースアクセス層（USDA 対応）
- **Data Interpreter** - 戦略パターンによるデータ解釈
- **Nutrition Calculator** - 栄養素集計と最終レポート生成
- **Workflow Manager** - 4 フェーズのオーケストレーション

## 🚀 使用方法

### 基本的な実行

```bash
# 環境変数設定
export USDA_API_KEY="your_usda_api_key"
export GEMINI_API_KEY="your_gemini_api_key"
export GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"

# 栄養推定実行
python -m src.main images/food.jpg
```

### オプション付き実行

```bash
# 設定ファイル指定
python -m src.main images/food.jpg --config configs/main_config.yaml

# 結果をJSONファイルに出力
python -m src.main images/food.jpg --output results/nutrition_report.json

# デバッグモード
python -m src.main images/food.jpg --debug

# クワイエットモード（エラーのみ表示）
python -m src.main images/food.jpg --quiet
```

## ⚙️ 設定システム

### YAML 設定ファイル (`configs/main_config.yaml`)

```yaml
# データベース設定
DB_CONFIG:
  TYPE: "USDA" # 将来的に他のDBも対応可能
  DEFAULT_QUERY_STRATEGY: "default_usda_search_v1"

# プロンプト戦略（コード変更なしで修正可能）
PROMPTS:
  default_usda_search_v1: "{food_name}"
  usda_raw_food_search: "raw {food_name}"
  usda_cooked_food_search: "cooked {food_name}"

# データ解釈戦略
INTERPRETER_CONFIG:
  STRATEGY_NAME: "DefaultUSDA"
  STRATEGY_CONFIGS:
    DefaultUSDA:
      NUTRIENT_MAP:
        "Protein": "PROTEIN"
        "Total lipid (fat)": "TOTAL_FAT"
        # ... 他の栄養素マッピング
```

### 環境変数

```bash
USDA_API_KEY=your_api_key_here
GEMINI_API_KEY=your_gemini_key
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
LOG_LEVEL=INFO
DEBUG_MODE=false
```

## 🔧 カスタマイズ

### 新しいデータベースを追加

1. `src/db_interface/` に新しいハンドラーを作成:

```python
class NewDatabaseHandler(DBHandler):
    async def fetch_nutrition_data(self, params: QueryParameters) -> RawDBResult:
        # 新しいDBの実装
        pass
```

2. `configs/main_config.yaml` で設定:

```yaml
DB_CONFIG:
  TYPE: "NewDatabase"
  NewDatabase:
    API_KEY: "new_db_api_key"
```

### 新しい解釈戦略を追加

1. `src/data_interpreter/strategies/` に新しい戦略を作成:

```python
class CustomInterpretationStrategy(BaseInterpretationStrategy):
    async def interpret(self, raw_food_data: RawFoodData, identified_item_info=None):
        # カスタム解釈ロジック
        pass
```

2. 設定で戦略を選択:

```yaml
INTERPRETER_CONFIG:
  STRATEGY_NAME: "CustomStrategy"
```

## 📁 ディレクトリ構造

```
nutrition_api/
├── src/
│   ├── image_processor/          # Phase 1: 画像処理
│   ├── db_interface/             # Phase 2: データベースクエリ
│   ├── data_interpreter/         # Phase 3: データ解釈
│   ├── nutrition_calculator/     # Phase 4: 栄養計算
│   ├── orchestration/            # ワークフロー統括
│   ├── common/                   # 共通ユーティリティ
│   └── main.py                   # メインエントリポイント
├── configs/
│   └── main_config.yaml          # メイン設定ファイル
├── tests/
│   ├── unit/                     # 単体テスト
│   └── integration/              # 統合テスト
└── README.md
```

## 🧪 開発とテスト

### 既存テストとの互換性

既存の `test_english_phase1_v2.py` と `test_english_phase2_v2.py` は引き続き動作します：

```bash
# 既存テスト実行
python test_english_phase1_v2.py images/food2.jpg
python test_english_phase2_v2.py
```

### 新しいモジュールテスト

```bash
# 単体テスト（将来実装）
python -m pytest tests/unit/

# 統合テスト（将来実装）
python -m pytest tests/integration/
```

## 📊 出力例

```json
{
  "total_nutrients": {
    "CALORIES": {
      "total_amount": 523.2,
      "unit": "kcal",
      "contributing_foods": [
        "Grilled chicken breast (185 kcal)",
        "Rice (338 kcal)"
      ]
    },
    "PROTEIN": {
      "total_amount": 31.5,
      "unit": "g",
      "contributing_foods": ["Grilled chicken breast (28.2 g)", "Rice (3.3 g)"]
    }
  },
  "detailed_items": [
    {
      "selected_food_description": "Chicken, broilers or fryers, breast, meat only, cooked, grilled",
      "processed_nutrients": {
        "PROTEIN": { "amount": 28.2, "unit": "g" },
        "CALORIES": { "amount": 185, "unit": "kcal" }
      }
    }
  ],
  "metadata": {
    "calculation_timestamp": "2024-01-01T12:00:00Z",
    "num_food_items_processed": 2,
    "nutrition_completeness_score": 0.95
  }
}
```

## 🔄 従来システムからの移行

モジュール化版は既存の機能を完全に包含しており、段階的な移行が可能です：

1. **Phase 1**: 既存スクリプトと新しいモジュール版を並行実行
2. **Phase 2**: 設定ファイルでプロンプト戦略を調整
3. **Phase 3**: 新しいデータベースや解釈戦略を追加
4. **Phase 4**: 既存スクリプトを完全に新システムに置き換え

## 🛠️ トラブルシューティング

### 設定の確認

```bash
python -c "from src.common.config_loader import ConfigLoader; import json; print(json.dumps(ConfigLoader.load_config(), indent=2))"
```

### ログの確認

```bash
# デバッグログ付きで実行
python -m src.main images/food.jpg --debug
```

### 環境変数の確認

```bash
echo $USDA_API_KEY
echo $GEMINI_API_KEY
```

## 📈 今後の拡張予定

- [ ] OpenFoodFacts データベース対応
- [ ] 複数データベース結果の統合
- [ ] Web API (FastAPI) 対応
- [ ] ユーザープロファイル対応
- [ ] 栄養推奨量との比較機能
- [ ] バッチ処理対応

## 🤝 コントリビューション

1. 新しい機能は独立したモジュールとして実装
2. 設定駆動での動作変更を優先
3. 既存 API との互換性を維持
4. 適切なテストを追加
