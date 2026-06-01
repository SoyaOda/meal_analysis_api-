# PDCA Evaluation Framework

パイプライン全フェーズのボトルネックを特定し、継続的に精度改善するための評価フレームワーク。

## Architecture

```
[Image] → Phase 1: VLM → Phase 2: Search+Reranker → Phase 3: Nutrition Calc
              ↓                    ↓                        ↓
         食材認識F1          USDAマッチ精度            カロリーMAE
         重量MAPE            誤マッチ詳細             30%+誤差率
```

## Quick Start

```bash
cd /Users/odasoya/meal_analysis_api_2

# 全モデル×全プロンプト（config.yaml参照）
python test_scripts/pdca/run_pdca_cycle.py

# 特定モデルのみ
python test_scripts/pdca/run_pdca_cycle.py --models gemma4-26b

# 画像数を制限（高速テスト）
python test_scripts/pdca/run_pdca_cycle.py --models gemma4-26b --limit 10

# 複数モデル比較
python test_scripts/pdca/run_pdca_cycle.py --models gemini3-flash gemma4-26b
```

## Configuration

`config.yaml` を編集してモデル・プロンプト・閾値を設定:

```yaml
models:
  gemini3-flash:
    model_id: "openrouter:google/gemini-3-flash-preview"
  gemma4-26b:
    model_id: "openrouter:google/gemma-4-26b-a4b-it"

prompts:
  v11b:
    file: "freeform_prompt_usda_format_ver_v11b_gemini_component_density_20260225.txt"

targets:
  vlm:
    food_recognition_f1: 0.80
  matching:
    usda_match_accuracy: 0.70
  nutrition:
    calorie_mae: 15.0
    high_error_rate: 10.0
```

## PDCA Cycle Methodology

### Plan: 仮説を立てる

前回のレポートのボトルネックとRecommendationsを確認し、改善仮説を決定:

| Bottleneck | Action |
|-----------|--------|
| **vlm** | プロンプト改良、モデル変更、Few-shot追加 |
| **matching** | Rerankerモデル変更、BM25/Vector重み調整、USDAインデックス拡充 |
| **nutrition** | 重量推定ルール調整、後処理パイプライン追加 |

### Do: 変更を実施

1. `config.yaml` に新しいモデル/プロンプトを追加
2. または API admin panel でパラメータを変更

### Check: 評価を実行

```bash
python test_scripts/pdca/run_pdca_cycle.py --models <new_model>
```

レポート（`output/pdca_report_*.md`）を確認:
- 各フェーズのメトリクスが目標値を達成しているか
- ボトルネックが前回から変わったか
- 新たなクリティカル誤認識が発生していないか

### Act: 結果を反映

- 改善が確認できた場合: 本番設定を更新（Admin Panel）
- 改善なし: 仮説を見直し、次のPDCAサイクルへ

## Evaluation Metrics

### Phase 1: VLM Recognition

| Metric | Description | Target |
|--------|------------|--------|
| Food F1 | 食材認識のF1スコア（ラベルとの一致） | >= 0.80 |
| Food Precision | VLMが出力した食材のうち正しいもの | High |
| Food Recall | ラベルの食材をVLMが認識した割合 | High |
| Weight MAPE | 重量推定の平均絶対パーセント誤差 | <= 25% |

### Phase 2: USDA Matching

| Metric | Description | Target |
|--------|------------|--------|
| Match Accuracy | VLMクエリに対する正しいUSDAマッチ率 | >= 0.70 |
| Wrong Matches | 全く異なる食品にマッチした件数 | Minimize |

### Phase 3: Nutrition Accuracy

| Metric | Description | Target |
|--------|------------|--------|
| Calorie MAE | カロリーの平均絶対パーセント誤差 | <= 15% |
| 30%+ Error Rate | カロリー誤差30%以上のケース率 | <= 10% |

## Output Files

```
output/
├── pdca_report_YYYYMMDD_HHMMSS.md   # 人が読むレポート
└── pdca_results_YYYYMMDD_HHMMSS.json # 機械可読な詳細データ
```

## Phase-Level Improvement Guide

### VLMフェーズの改善

1. **プロンプト**: `prompts/` 配下のプロンプトを変更
   - DETECTION PRIORITYセクション: 見逃しやすい食材の検出ルール
   - PORTION ANCHORS: 重量推定の基準値
   - AMBIGUITY POLICY: 曖昧なケースの判断基準

2. **モデル**: config.yaml の model_id を変更
   - 新しいVLMモデルがリリースされたらテスト

### Matchingフェーズの改善

1. **Reranker**: Admin Panel で reranker.model を変更
   - `Qwen/Qwen3-Reranker-0.6B` → `Qwen/Qwen3-Reranker-4B` → `Qwen/Qwen3-Reranker-8B`

2. **検索重み**: Admin Panel で search.bm25_weight / vector_weight を調整

3. **USDAインデックス**: データベースに不足エントリを追加
   - 例: couscous が wheat flour にマッチする問題

### Nutritionフェーズの改善

1. 高誤差ケースの共通パターンを特定
2. VLMプロンプトに特定料理カテゴリのルールを追加
3. 後処理での異常値検出・補正
