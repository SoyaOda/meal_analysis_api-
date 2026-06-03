# Codex 作業指示書: NutritionVerse-Real を取得して mozu の外部評価セットに変換する

> この文書は **Codex（Computer Use 可）** 向けの自己完結タスク指示です。Claude Code 側は Kaggle 認証が無く取得できないため、**Kaggle からのダウンロードだけ** Codex に依頼します。変換スクリプトは既に用意した雛形に倣えば作れます。

## 0. 背景（なぜやるか）
このリポジトリ（`/Users/odasoya/meal_analysis_api_2`, ブランチ `feature/mozu-api`）は **mozu**（高単価 calorie tracker app）用の「写真→カロリー推定 API」。
判明した重大問題: 既存の評価用 50 枚の **GT は GPT-5-pro の推定値**で、「実精度」でなく「LLM との一致度」を測っていた（詳細 `evals/lessons/20260603_frozen50_gt_is_gpt5pro_estimate_two_gate_strategy.md`）。
対策として **独立した実測 GT** の評価セットが必要。既に **Nutrition5k**（俯瞰/cafeteria）は構築済。今回ほしいのは **phone カメラ角度＋実測 GT** の **NutritionVerse-Real**（iPhone 撮影・成分を秤で実測）で、mozu の実利用に近い角度の独立カロリーゲートにする。

## 1. ゴール（成果物）
`test_images_nvreal/` 配下に、既存 harness がそのまま読める形式で NutritionVerse-Real を変換配置する:
- `test_images_nvreal/images/test_food{N}.jpg`（N=1,2,3,…）
- `test_images_nvreal/images_label_with_nutrition/test_food{NN}.json`（NN=2桁ゼロ詰め: 01,02,…）
- `test_images_nvreal/manifest.json`（dish_id ↔ idx ↔ GT総カロリー の対応）

## 2. Codex がやること（Computer Use）
### Step A. ダウンロード
- Kaggle データセット: **https://www.kaggle.com/datasets/nutritionverse/nutritionverse-real**（889 枚 / 251 dish / 実測重量・栄養, CC-by 系）。
- ブラウザで Kaggle にログイン（ユーザーの Kaggle アカウント）し、"Download" で zip を取得。
- 解凍先: `/Users/odasoya/meal_analysis_api_2/data/nutritionverse_real/`（無ければ作成）。
- ※ `data/nutritionverse_real/` と `test_images_nvreal/` は **gitignore 済**にすること（後述）。巨大データ・画像は **コミットしない**。

### Step B. 構造を把握して報告（重要）
解凍後、以下を**確認して報告**（Claude が変換スクリプトを書く/検証するため）:
- ディレクトリ構成（画像フォルダの場所・命名規則。1 dish が複数アングル画像を持つか）。
- 栄養 GT が入っているファイル（CSV/JSON）の **パスと列名**。特に: dish 識別子、成分名、**成分ごとの実測重量(g)**、成分ごと or dish 合計の **calories / protein / fat / carbs**。
- 画像ファイル名 ↔ dish ↔ 栄養レコードの **対応関係**（どのキーで結びつくか）。
- 例として最初の 1 dish 分の生レコードを貼る。

### Step C.（任意・できれば）変換まで実施
構造が分かれば、`apps/freeform_usda_meal_analysis_api/scripts/build_nutrition5k_evalset.py` を**雛形**に変換スクリプト `build_nutritionverse_evalset.py` を作って実行してよい（下の §3 の出力スキーマに厳密に合わせる）。**自信が無ければ Step B の報告だけでよい**（Claude が変換を書く）。

## 3. 出力ラベルスキーマ（harness が読む正確な形式）
各画像に対応する `test_food{NN}.json` は **必ず**この構造にする（`scripts/run_pdca_batch_eval.py` の `load_label_nutrition` / `load_label_items` がこれを読む）:
```json
{
  "dishes": [
    {
      "main_food": {
        "search_name": "<最大重量の成分名>",
        "weight_g": 170,
        "nutrition": { "calorie": 425.0, "protein_g": 44.2, "fat_g": 28.9, "carbs_g": 0.0 }
      },
      "extras": [
        { "search_name": "<次の成分>", "weight_g": 60, "nutrition": { "calorie": 30.0, "protein_g": 1.0, "fat_g": 0.5, "carbs_g": 6.0 } }
      ]
    }
  ]
}
```
変換ルール（Nutrition5k 版と同じ）:
- 1 dish = 1 要素の `dishes`。dish の成分を重量降順にし、**最大重量の成分を `main_food`、残りを `extras`** に。
- `search_name`=成分名、`weight_g`=実測 g、`nutrition.calorie/protein_g/fat_g/carbs_g`=成分ごとの値（無ければ dish 合計を 1 アイテムに）。
- total（合計カロリー等）は harness が `main_food`+`extras` から自動集計するので、**合計が dish 実測値に一致**するように成分値を入れる。
- 1 dish に複数アングル画像がある場合は **dish ごとに 1 枚（俯瞰 or 代表 1 枚）** を採用（重複評価を避ける）。
- 画像は jpg（png なら PIL で `convert("RGB").save(..., "JPEG", quality=92)`）。

## 4. gitignore（必須・巨大データをコミットしない）
リポジトリ root の `.gitignore` に未追記なら追加:
```
data/nutritionverse_real/
test_images_nvreal/
```
（Nutrition5k と同様、生データ・変換画像はコミットせず、**変換スクリプトと manifest だけ**が再現の根拠。）

## 5. 受け入れ基準（Claude 側で検証）
変換後、Claude が次で検証する（Codex も実行して確認可）:
```
cd /Users/odasoya/meal_analysis_api_2 && PYTHONPATH=$PWD venv/bin/python - <<'PY'
import glob, json
from apps.freeform_usda_meal_analysis_api.scripts.run_pdca_batch_eval import load_label_nutrition, load_label_items
from pathlib import Path
ok=0; n=0
for f in sorted(Path('test_images_nvreal/images_label_with_nutrition').glob('*.json')):
    n+=1; nut=load_label_nutrition(f); items=load_label_items(f)
    if nut['calories']>0 and items: ok+=1
print(f"labels readable: {ok}/{n}; sample total={load_label_nutrition(sorted(Path('test_images_nvreal/images_label_with_nutrition').glob('*.json'))[0])}")
PY
```
合格条件: 画像数=ラベル数、`load_label_*` が大半で `calories>0` & items を返す、GT 総カロリーが現実的なレンジ（数十〜千 kcal）。

## 6. 評価（参考・Claude が回す。OpenRouter 課金が要るので Codex は不要）
```
# ローカルサーバ起動後（pro が既定モデル）:
PYTHONPATH=$PWD venv/bin/python -m apps.freeform_usda_meal_analysis_api.scripts.run_pdca_batch_eval \
  --config apps/freeform_usda_meal_analysis_api/evals/configs/pdca_gemini31pro_vs_flash_dev40_20260602.json \
  --api-url http://localhost:8006 \
  --images-dir test_images_nvreal/images \
  --labels-dir test_images_nvreal/images_label_with_nutrition \
  --limit 250 --no-use-vlm-cache
```

## 7. 完了報告
Codex は以下を報告: ①ダウンロード/解凍したパスとサイズ ②§B の構造（列名・対応関係・サンプル1件）③（変換した場合）`test_images_nvreal/` の画像/ラベル数と §5 検証結果。
**画像・生データはコミットしない**。変換スクリプトを書いた場合のみ `scripts/build_nutritionverse_evalset.py` をコミット可。
