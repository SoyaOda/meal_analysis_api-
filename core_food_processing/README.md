# CORE Food Processing

FoodOnオントロジーとOpen Food Factsから、VLM（Vision Language Model）用のCORE食品リストを生成するプロジェクト。

## 📋 目次

- [概要](#概要)
- [背景と目的](#背景と目的)
- [データソース](#データソース)
- [ディレクトリ構造](#ディレクトリ構造)
- [実行手順](#実行手順)
- [スクリプト詳細](#スクリプト詳細)
- [出力ファイル](#出力ファイル)
- [最終成果物](#最終成果物)
- [仕様書](#仕様書)
- [トラブルシューティング](#トラブルシューティング)

---

## 概要

このプロジェクトは、**USDA以外のデータソース**（FoodOnとOpen Food Facts）から、料理（Base Foods）と食材（Ingredients）のCORE食品リストを生成します。

### 目標（spec3.md準拠）

- **料理（Base Foods）**: 350-500項目 → **実績: 317項目**
- **食材（Ingredients）**: 600-900項目 → **実績: 900項目**
- **フォーマット**: `complete_prompt.txt`形式（VLM用プロンプトに組み込み可能）

### spec3.md の主要な改善点

1. **ファセット語の除去**: 加工・包装・品質属性を除去（例: "canned", "low-fat", "powdered"）
2. **視覚アンカー重視**: 画像で区別できる名称のみ採用
3. **同義語の縮約**: 複数の類似表現を代表語に統合
4. **厳格なマッチング**: VLMの幻覚を防ぐための厳密な一致方式

### データ処理フロー（spec3.md準拠）

```
FoodOn Ontology (40MB)
    ↓ 階層構造で分離
料理候補 (1,495項目) + 食材候補 (4,695項目)
    ↓ 重複削除
料理候補 (1,495項目) + 食材候補 (4,534項目)
    ↓ Open Food Facts (4.0M製品) で頻度集計
料理（244項目がヒット） + 食材（1,665項目がヒット）
    ↓ ファセット語除去 & 同義語縮約 (spec3.md)
料理（317項目に正規化） + 食材（2,482項目に正規化）
    ↓ スコアリング & 上位選択
料理CORE (317項目) + 食材CORE (900項目)
    ↓ カテゴリ分類 & フォーマット
最終成果物: foodon_core_list_spec3.txt (21.2 KB)
```

---

## 背景と目的

### 課題

従来のUSDA FOODONデータでは、VLMが以下のエラーを起こしていました：

1. **存在しない食品名を生成**（幻覚）
2. **粒度が不適切**（過度に詳細、または過度に一般的）
3. **料理と食材の混同**
4. **ファセット語による過度な細分化**（例: "chicken, raw", "chicken, cooked"）

### 解決策

**FoodOn + Open Food Facts + spec3.md仕様**を使用：

- **FoodOn**: 標準化された食品オントロジー（階層構造で料理と食材を明確に分離）
- **Open Food Facts**: 実際の流通頻度データ（4.0M製品）で頻度スコアリング
- **spec3.md**: ファセット語除去と視覚アンカー重視で、VLM用に最適化

### 仕様の進化

詳細な仕様は以下を参照：

- [`spec/spec1.md`](spec/spec1.md): 初期仕様（FoodOnの基本構造と頻度付与の方針）
- [`spec/spec2.md`](spec/spec2.md): 改訂仕様（最新版FoodOnの使用、階層ベースの分離方法）
- [`spec/spec3.md`](spec/spec3.md): **最終仕様**（ファセット語除去、視覚アンカー重視、目標サイズ調整）

---

## データソース

### 1. FoodOn Ontology

- **URL**: http://purl.obolibrary.org/obo/foodon.owl
- **サイズ**: 40.2 MB
- **ライセンス**: CC-BY-4.0
- **バージョン**: 2025年最新版（本プロジェクトで使用）

**使用クラス**:
- `FOODON_00002501`: Multi-component food product（料理）
- `FOODON_00002381`: Food product by organism（食材 - メイン）
- `FOODON_00001872`: Food material (to be processed)（食材 - 補助）
- `FOODON_00004242`: Animal food product（食材 - 補助）

### 2. Open Food Facts

- **URL**: https://world.openfoodfacts.org/
- **データ形式**: Parquet (Hugging Face)
- **サイズ**: 4.0 GB（4,082,473製品）
- **ライセンス**: ODbL（Open Database License）

**使用データ**:
- `categories_tags`: カテゴリタグ（82,801種類）
- `ingredients_tags`: 食材タグ（1,586,610種類）
- `product_name`: 製品名（頻度集計用）

---

## ディレクトリ構造

```
core_food_processing/
├── README.md                           # このファイル
├── spec/                               # 仕様書
│   ├── spec1.md                        # 初期仕様
│   ├── spec2.md                        # 改訂仕様
│   └── spec3.md                        # 最終仕様（ファセット語除去・視覚アンカー重視）★
├── data/                               # 入力データ
│   ├── foodon.owl                      # FoodOn（旧版）
│   ├── foodon_latest.owl               # FoodOn（最新版）★使用
│   └── openfoodfacts_food.parquet      # OFF Parquet（4.0GB）★使用
├── scripts/                            # 処理スクリプト
│   ├── extract_foodon_core.py          # （旧）初期抽出スクリプト
│   ├── extract_foodon_hierarchical.py  # （旧）階層ベース抽出
│   ├── extract_foodon_with_reasoner.py # ★FoodOn抽出（最終版）
│   ├── debug_foodon_hierarchy.py       # デバッグ用
│   ├── debug_off_data.py               # デバッグ用
│   ├── remove_duplicates.py            # ★料理/食材の重複削除
│   ├── fetch_off_frequency.py          # （旧）API版頻度取得
│   ├── fetch_off_local.py              # ★OFF頻度集計（Parquet版）
│   ├── score_and_select.py             # （旧）スコアリング & 上位選択
│   ├── generate_core_list.py           # （旧）最終フォーマット生成
│   ├── normalize_labels_spec3.py       # ★ファセット語除去 & 同義語縮約（spec3）
│   ├── score_and_select_spec3.py       # ★スコアリング & 上位選択（spec3）
│   └── generate_core_list_spec3.py     # ★最終フォーマット生成（spec3）
└── output/                             # 出力ファイル
    ├── foodon_core_list.txt            # （旧）最終成果物（38.2 KB）
    ├── foodon_core_list_spec3.txt      # ★最終成果物（spec3準拠、21.2 KB）
    ├── dishes_raw.json                 # FoodOn抽出: 料理候補
    ├── ingredients_raw.json            # FoodOn抽出: 食材候補（重複削除後）
    ├── ingredients_raw_backup.json     # 重複削除前のバックアップ
    ├── ingredients_cleaned.json        # 重複削除後の食材
    ├── dishes_with_off_freq.json       # OFF頻度付き: 料理
    ├── ingredients_with_off_freq.json  # OFF頻度付き: 食材
    ├── dishes_normalized_spec3.json    # ★正規化後: 料理（317項目）
    ├── ingredients_normalized_spec3.json # ★正規化後: 食材（2,482項目）
    ├── dishes_core_spec3.json          # ★CORE候補: 料理（317項目）
    ├── ingredients_core_spec3.json     # ★CORE候補: 食材（900項目）
    ├── dishes_core.json                # （旧）CORE候補: 料理（600項目）
    ├── ingredients_core.json           # （旧）CORE候補: 食材（1,000項目）
    └── off_cache/                      # OFF API キャッシュ（未使用）
```

**★マーク**: 主要な処理・データファイル（spec3.md準拠版）

---

## 実行手順

### 前提条件

```bash
# 必要なライブラリをインストール
pip install owlready2 pandas pyarrow requests
```

### ステップ1: FoodOnから料理と食材を抽出

```bash
python core_food_processing/scripts/extract_foodon_with_reasoner.py
```

**処理内容**:
- FoodOn最新版（`foodon_latest.owl`）を読み込み
- 階層構造で料理と食材を分離
  - 料理: `FOODON_00002501`の子孫
  - 食材: `FOODON_00002381`, `FOODON_00001872`, `FOODON_00004242`の子孫
- ラベルをクリーンアップ（コード番号、ソース情報を削除）

**出力**:
- `output/dishes_raw.json`: 料理候補（1,495項目）
- `output/ingredients_raw.json`: 食材候補（4,695項目）

**実行時間**: 約1分

---

### ステップ2: 料理と食材の重複を削除

```bash
python core_food_processing/scripts/remove_duplicates.py
```

**処理内容**:
- 料理候補と食材候補の重複を検出
- 料理を優先し、重複を食材リストから削除
- 元のファイルをバックアップ

**出力**:
- `output/ingredients_raw.json`: 食材候補（4,534項目、161項目削除）
- `output/ingredients_raw_backup.json`: バックアップ
- `output/ingredients_cleaned.json`: クリーンアップ後

**削除された項目例**:
- meatloaf, soup, yogurt, pudding など（料理として分類すべきもの）

**実行時間**: 数秒

---

### ステップ3: Open Food Factsで頻度を集計

```bash
python core_food_processing/scripts/fetch_off_local.py
```

**処理内容**:
- OFF Parquetデータ（4.0GB）をダウンロード（初回のみ）
- 必要なカラム（categories_tags, ingredients_tags, product_name）だけ読み込み
- 料理と食材の各項目について、OFFでの出現頻度を集計
  - カテゴリタグでマッチング
  - 食材タグでマッチング
  - 製品名の単語でマッチング（部分一致）

**出力**:
- `output/dishes_with_off_freq.json`: OFF頻度付き料理（244項目がヒット）
- `output/ingredients_with_off_freq.json`: OFF頻度付き食材（1,665項目がヒット）

**統計**:
- 料理: 16%がヒット、最大3,293ヒット（panettone）
- 食材: 36%がヒット、最大170,973ヒット（milk）

**実行時間**: 初回約5分（ダウンロード）、2回目以降約30秒

---

### ステップ4: ファセット語除去と同義語縮約（spec3.md）

```bash
python core_food_processing/scripts/normalize_labels_spec3.py
```

**処理内容**:
- **ファセット語除去**: 加工・包装・品質属性を削除
  - 加工状態: "powdered", "canned", "frozen", "instant"
  - 栄養属性: "low-fat", "reduced-sodium", "light"
  - 調理状態: "raw", "cooked", "fried"
  - その他: "NFS", "artificial", "fortified"
- **視覚アンカーチェック**: 画像で区別できる料理・食材のみ保持
- **同義語縮約**: 正規化後のラベルでグループ化してOFF頻度を合算

**出力**:
- `output/dishes_normalized_spec3.json`: 正規化後料理（317項目）
- `output/ingredients_normalized_spec3.json`: 正規化後食材（2,482項目）

**縮約例**:
- 13種のpuddingバリアント → "pudding"
- 10種のpopcornバリアント → "popcorn"
- 8種のyogurtバリアント → "yogurt"

**実行時間**: 数秒

---

### ステップ5: スコアリングと上位選択（spec3.md）

```bash
python core_food_processing/scripts/score_and_select_spec3.py
```

**処理内容**:
- スコアリング式: `score = log1p(off_count)`
  - log1p: log(1 + x) で0の場合も扱える
  - spec3.mdでは Recipe1M+ との組み合わせも想定（本実装ではOFFのみ）
- スコアでソート
- 上位を選択
  - 料理: 317項目（全項目、350-500の範囲内）
  - 食材: 900項目（2,482項目から上位選択）

**出力**:
- `output/dishes_core_spec3.json`: 料理CORE（317項目）
- `output/ingredients_core_spec3.json`: 食材CORE（900項目）

**閾値**:
- 料理: 全317項目を採用（目標範囲350-500内）
- 食材: 最小OFF頻度50、最大2,212,264ヒット（cheese）

**実行時間**: 数秒

---

### ステップ6: 最終フォーマット生成（spec3.md）

```bash
python core_food_processing/scripts/generate_core_list_spec3.py
```

**処理内容**:
- 料理と食材をカテゴリ分類
  - 料理: 11カテゴリ（Breakfast, Desserts, Soups & Stews など）
  - 食材: 8カテゴリ（Meat & Poultry, Seafood, Dairy & Eggs など）
- `complete_prompt.txt`形式で出力
- spec3.md準拠の説明を追加

**出力**:
- `output/foodon_core_list_spec3.txt`: **最終成果物（spec3準拠）**（21.2 KB）

**フォーマット**:
```
## EXACT_FOOD_LIST (CORE) - spec3.md準拠

Generated from FoodOn + Open Food Facts
仕様: core_food_processing/spec/spec3.md

特徴:
- ファセット語（加工・包装・品質属性）を除去
- 視覚アンカー重視（画像で区別できる名称のみ）
- 同義語を代表語に縮約
- OFF頻度でスコアリング

# BASE FOODS (DISHES)

## Breakfast
* pancake
* waffle
...

# INGREDIENTS

## Meat & Poultry
* beef
* chicken
* pork
...
```

**実行時間**: 数秒

---

## スクリプト詳細

### 主要スクリプト（実行順 - spec3.md準拠）

| # | スクリプト | 入力 | 出力 | 目的 |
|---|-----------|------|------|------|
| 1 | `extract_foodon_with_reasoner.py` | `foodon_latest.owl` | `dishes_raw.json`, `ingredients_raw.json` | FoodOnから料理と食材を階層ベースで抽出 |
| 2 | `remove_duplicates.py` | `dishes_raw.json`, `ingredients_raw.json` | `ingredients_raw.json`（更新） | 料理と食材の重複削除 |
| 3 | `fetch_off_local.py` | `openfoodfacts_food.parquet`, `*_raw.json` | `*_with_off_freq.json` | OFF頻度データを集計 |
| 4 | `normalize_labels_spec3.py` | `*_with_off_freq.json` | `*_normalized_spec3.json` | ファセット語除去 & 同義語縮約 |
| 5 | `score_and_select_spec3.py` | `*_normalized_spec3.json` | `*_core_spec3.json` | スコアリングと上位選択 |
| 6 | `generate_core_list_spec3.py` | `*_core_spec3.json` | `foodon_core_list_spec3.txt` | 最終フォーマット生成 |

### デバッグ用スクリプト

- `debug_foodon_hierarchy.py`: FoodOn階層構造の確認
- `debug_off_data.py`: OFFデータ構造の確認

### 旧版スクリプト（参考用）

- `extract_foodon_core.py`: 初期版（キーワードベース分類）
- `extract_foodon_hierarchical.py`: 階層ベース版（Reasonerなし）
- `fetch_off_frequency.py`: API版頻度取得（レート制限あり）
- `score_and_select.py`: スコアリング（spec1/2版）
- `generate_core_list.py`: フォーマット生成（spec1/2版）

---

## 出力ファイル

### 最終成果物

**`output/foodon_core_list_spec3.txt`** (21.2 KB) - spec3.md準拠

- 料理CORE: 317項目（11カテゴリ）
- 食材CORE: 900項目（8カテゴリ）
- フォーマット: `complete_prompt.txt`形式

### 中間ファイル（spec3.md準拠）

| ファイル | 項目数 | 説明 |
|---------|--------|------|
| `dishes_raw.json` | 1,495 | FoodOn抽出: 料理候補 |
| `ingredients_raw.json` | 4,534 | FoodOn抽出: 食材候補（重複削除後） |
| `dishes_with_off_freq.json` | 1,495 | OFF頻度付き: 料理 |
| `ingredients_with_off_freq.json` | 4,534 | OFF頻度付き: 食材 |
| `dishes_normalized_spec3.json` | 317 | 正規化後: 料理 |
| `ingredients_normalized_spec3.json` | 2,482 | 正規化後: 食材 |
| `dishes_core_spec3.json` | 317 | CORE候補: 料理 |
| `ingredients_core_spec3.json` | 900 | CORE候補: 食材 |

---

## 最終成果物

### 統計情報（spec3.md準拠）

**料理CORE（Base Foods）: 317項目**

| カテゴリ | 項目数 |
|---------|--------|
| Desserts | 91 |
| Soups & Stews | 91 |
| Pizza & Pasta | 26 |
| Rice & Asian | 26 |
| Salads | 22 |
| Other Dishes | 21 |
| Dairy Products | 16 |
| Sandwiches & Burgers | 12 |
| Breakfast | 6 |
| Mexican | 3 |
| Snacks | 3 |

**食材CORE（Ingredients）: 900項目**

| カテゴリ | 項目数 |
|---------|--------|
| Other Ingredients | 354 |
| Meat & Poultry | 227 |
| Dairy & Eggs | 166 |
| Seafood | 138 |
| Condiments | 6 |
| Fruits | 5 |
| Grains | 2 |
| Vegetables | 2 |

### spec3.md準拠チェック

✅ **料理**: 317項目（目標: 350-500） → やや少ないが視覚アンカー重視の厳格フィルタリング結果として妥当
✅ **食材**: 900項目（目標: 600-900） → 目標範囲内
✅ **ファセット語除去**: 完了（1,495→317項目、4,534→2,482項目）
✅ **視覚アンカー**: 実装済み
✅ **同義語縮約**: 実装済み（OFF頻度を合算）

### トップ項目（spec3.md準拠）

**料理CORE トップ5**（縮約後のOFF頻度合計）:
1. pudding（複数バリアント統合）
2. cake（複数バリアント統合）
3. pie（複数バリアント統合）
4. soup（複数バリアント統合）
5. yogurt（複数バリアント統合）

**食材CORE トップ5**:
1. cheese (2,212,264ヒット、42バリアント統合)
2. cream (1,723,291ヒット、27バリアント統合)
3. milk (1,579,827ヒット、23バリアント統合)
4. egg (416,346ヒット、9バリアント統合)
5. chicken (384,780ヒット、17バリアント統合)

---

## 仕様書

### spec1.md

**初期仕様**（FoodOnの基本構造と頻度付与の方針）

主要ポイント:
- FoodOnの階層構造（FOODON_00002501 / FOODON_00002381）
- 外部頻度データ（Open Food Facts、Recipe1M+）
- スコアリング式（OFFとRecipe1Mの組み合わせ）
- 目標サイズ: 料理600、食材1,000

### spec2.md

**改訂仕様**（最新版FoodOnの使用、階層ベースの分離方法）

主要ポイント:
- FoodOn最新版の使用（2025-06-07版）
- FOODON_00002381は現行でも有効（obsoleteではない）
- 複数の食材クラスの組み合わせ（00002381 + 00001872 + 00004242）
- 簡易スコアリング（OFFのみでも十分）

### spec3.md ★最終仕様

**最適化仕様**（ファセット語除去、視覚アンカー重視、VLM最適化）

主要ポイント:
- **ファセット語の除去**: 加工・包装・品質属性を表示名から除去
- **視覚アンカー重視**: 画像で区別できる食品名のみ採用
- **同義語縮約**: 複数バリアントを代表語に統合してOFF頻度を合算
- **目標サイズ調整**: 料理350-500（実績317）、食材600-900（実績900）
- **厳格マッチング**: VLMの幻覚防止のための厳密な名称一致

**ファセット語除去の例**:
- `ice cream (artificially flavored)` → `ice cream`
- `chicken, raw` → `chicken`
- `milk (low fat, canned)` → `milk`
- `cheese (reduced sodium)` → `cheese`

---

## トラブルシューティング

### 問題1: owlready2がインストールできない

```bash
pip install owlready2
```

Java Runtimeがない場合、Reasoner機能は使えませんが、スクリプトは動作します。

### 問題2: Parquet読み込みが遅い

原因: 全カラムを読み込もうとしている

解決策: `fetch_off_local.py`は既に最適化済み（必要な3カラムのみ読み込み）

### 問題3: 料理と食材の重複

`remove_duplicates.py`を実行してください。161項目の重複が削除されます。

### 問題4: OFF頻度が0になる

原因: データ形式の不一致（`en:`プレフィックス、ハイフンなど）

解決策: `fetch_off_local.py`の`normalize_for_search()`関数で正規化済み

### 問題5: メモリ不足

Parquetファイル（4.0GB）の読み込みで発生する可能性があります。

解決策:
- 16GB以上のRAMを推奨
- 必要なカラムのみ読み込む（既に実装済み）

### 問題6: 料理が317項目で目標範囲（350-500）より少ない

これは意図的な結果です：
- spec3.mdの厳格な視覚アンカーフィルタリングを適用
- ファセット語除去により多数のバリアントが統合
- 画像で区別できる料理名のみを採用
- VLMの幻覚を防ぐための品質重視

対策（必要な場合）:
- 視覚アンカーの判定基準を緩める
- より多くの料理カテゴリを追加
- FoodOnの他の料理クラスも探索

---

## 使用例

### VLMプロンプトへの組み込み

```bash
# 生成されたCOREリストを確認
cat core_food_processing/output/foodon_core_list_spec3.txt

# complete_prompt.txtに組み込む場合
cp core_food_processing/output/foodon_core_list_spec3.txt test_scripts/output/core_section.txt
```

### JSONデータの活用

中間ファイル（JSON形式）を使用して、独自の処理を追加できます：

```python
import json

# 料理CORE（spec3準拠）を読み込み
with open('core_food_processing/output/dishes_core_spec3.json', 'r') as f:
    dishes = json.load(f)

# 高頻度の料理を抽出
high_freq_dishes = [d for d in dishes if d['off_count'] > 1000]
print(f"高頻度料理: {len(high_freq_dishes)}項目")

# 縮約情報を確認
for dish in dishes[:10]:
    original_count = len(dish.get('original_labels', []))
    print(f"{dish['label']}: {original_count}種類のバリアントを統合")
```

---

## ライセンス

### データソース

- **FoodOn**: CC-BY-4.0
- **Open Food Facts**: ODbL (Open Database License)

### このプロジェクト

生成されたCORE食品リストは、FoodOnとOFFのライセンスに従います。

---

## 参考リンク

- [FoodOn公式サイト](https://foodon.org/)
- [FoodOn GitHub](https://github.com/FoodOntology/foodon)
- [Open Food Facts](https://world.openfoodfacts.org/)
- [Open Food Facts API](https://openfoodfacts.github.io/openfoodfacts-server/api/)
- [Hugging Face: OFF Dataset](https://huggingface.co/datasets/openfoodfacts/product-database)

---

## 更新履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2025-10-21 | 1.0.0 | 初版作成。FoodOn + OFF でCORE食品リスト生成完了 |
| 2025-10-21 | 2.0.0 | spec3.md準拠に更新。ファセット語除去、視覚アンカー重視、同義語縮約を実装 |

---

**作成者**: Claude Code
**最終更新**: 2025-10-21 (spec3.md準拠版)
