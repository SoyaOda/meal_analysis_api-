#!/usr/bin/env python3
"""
fetch_off_local.py

Open Food FactsのParquetデータベースをダウンロードして、
ローカルで頻度データを集計するスクリプト（API呼び出しなし）

利点:
- API呼び出しなし = レート制限なし
- 全6,190項目を数秒〜数分で処理
- オフラインで再利用可能

Usage:
    python core_food_processing/scripts/fetch_off_local.py
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List
from collections import Counter

PROJECT_ROOT = Path(__file__).parent.parent.parent

try:
    import requests
except ImportError:
    print("❌ エラー: requestsがインストールされていません")
    print("  pip install requests")
    sys.exit(1)

try:
    import pandas as pd
except ImportError:
    print("❌ エラー: pandasがインストールされていません")
    print("  pip install pandas pyarrow")
    sys.exit(1)


# Open Food Facts Parquet データURL
OFF_PARQUET_URL = "https://huggingface.co/datasets/openfoodfacts/product-database/resolve/main/food.parquet"

# データディレクトリ
DATA_DIR = PROJECT_ROOT / "core_food_processing" / "data"
PARQUET_FILE = DATA_DIR / "openfoodfacts_food.parquet"


def download_off_parquet():
    """Open Food Facts Parquetデータをダウンロード"""
    if PARQUET_FILE.exists():
        print(f"✅ Parquetファイルは既に存在します: {PARQUET_FILE}")
        print(f"   サイズ: {PARQUET_FILE.stat().st_size / (1024*1024):.1f} MB")
        return

    print(f"📥 Open Food Facts Parquetデータをダウンロード中...")
    print(f"   URL: {OFF_PARQUET_URL}")
    print(f"   ※ 数百MB〜数GBのダウンロードが発生します")
    print()

    try:
        response = requests.get(OFF_PARQUET_URL, stream=True)
        response.raise_for_status()

        # ファイルサイズを取得
        total_size = int(response.headers.get('content-length', 0))
        print(f"   ファイルサイズ: {total_size / (1024*1024):.1f} MB")

        # ダウンロード
        DATA_DIR.mkdir(exist_ok=True, parents=True)
        downloaded = 0

        with open(PARQUET_FILE, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    progress = downloaded * 100 / total_size
                    print(f"\r   進捗: {progress:.1f}% ({downloaded / (1024*1024):.1f} MB)", end='')

        print()
        print(f"✅ ダウンロード完了: {PARQUET_FILE}")

    except Exception as e:
        print(f"❌ エラー: ダウンロード失敗: {e}")
        if PARQUET_FILE.exists():
            PARQUET_FILE.unlink()
        sys.exit(1)


def normalize_for_search(text: str) -> str:
    """検索用に正規化"""
    text = text.lower()

    # 'en:' プレフィックスを削除
    text = re.sub(r'^en:', '', text)

    # ハイフンをスペースに変換
    text = text.replace('-', ' ')

    # 括弧内削除
    text = re.sub(r'\([^)]*\)', '', text)

    # 余分な空白削除
    text = ' '.join(text.split())

    return text.strip()


def main():
    """メイン処理"""
    print("="*80)
    print("Open Food Facts ローカル頻度集計スクリプト（Parquet版）")
    print("="*80)
    print()

    # 入力ファイル
    dishes_json = PROJECT_ROOT / "core_food_processing" / "output" / "dishes_raw.json"
    ingredients_json = PROJECT_ROOT / "core_food_processing" / "output" / "ingredients_raw.json"

    if not dishes_json.exists() or not ingredients_json.exists():
        print("❌ エラー: 入力ファイルが存在しません")
        sys.exit(1)

    # FoodOnデータを読み込み
    print("📖 FoodOnデータを読み込み中...")
    with open(dishes_json, 'r', encoding='utf-8') as f:
        dishes = json.load(f)
    with open(ingredients_json, 'r', encoding='utf-8') as f:
        ingredients = json.load(f)

    print(f"  料理候補: {len(dishes):,} 項目")
    print(f"  食材候補: {len(ingredients):,} 項目")
    print()

    # Parquetデータをダウンロード（必要に応じて）
    download_off_parquet()
    print()

    # Parquetデータを読み込み（必要なカラムだけ読み込んで高速化）
    print("📖 Open Food Facts Parquetデータを読み込み中...")
    print("   ※ 必要なカラムだけ読み込むため、10〜30秒程度で完了します")
    try:
        # 必要なカラムだけ読み込む（高速化＆メモリ節約）
        required_columns = ['categories_tags', 'ingredients_tags', 'product_name']
        df = pd.read_parquet(PARQUET_FILE, columns=required_columns)
        print(f"✅ 読み込み完了: {len(df):,} 製品")
        print(f"   読み込んだカラム: {len(df.columns)} ({', '.join(df.columns)})")
        print()

        # 主要カラムを確認
        print("📋 主要カラム:")
        key_columns = ['categories_tags', 'ingredients_tags', 'product_name']
        for col in key_columns:
            if col in df.columns:
                non_null = df[col].notna().sum()
                print(f"  {col}: {non_null:,} 非NULL ({non_null*100//len(df)}%)")
        print()

    except Exception as e:
        print(f"❌ エラー: Parquet読み込み失敗: {e}")
        sys.exit(1)

    # カテゴリと食材の頻度を集計
    print("📊 カテゴリと食材の頻度を集計中...")

    # カテゴリ頻度
    category_counter = Counter()
    if 'categories_tags' in df.columns:
        for categories in df['categories_tags'].dropna():
            # numpy配列またはリスト
            try:
                for cat in categories:
                    if cat and cat != 'en:null':  # nullを除外
                        normalized = normalize_for_search(str(cat))
                        if normalized:
                            category_counter[normalized] += 1
            except:
                pass

    print(f"  カテゴリ種類数: {len(category_counter):,}")

    # 食材頻度
    ingredient_counter = Counter()
    if 'ingredients_tags' in df.columns:
        for ingredients_list in df['ingredients_tags'].dropna():
            # numpy配列またはリスト
            try:
                for ing in ingredients_list:
                    if ing and ing != 'en:null':  # nullを除外
                        normalized = normalize_for_search(str(ing))
                        if normalized:
                            ingredient_counter[normalized] += 1
            except:
                pass

    print(f"  食材種類数: {len(ingredient_counter):,}")
    print()

    # 製品名頻度（カテゴリにマッチしないものの補助）
    product_name_counter = Counter()
    if 'product_name' in df.columns:
        for name_data in df['product_name'].dropna():
            # 配列の辞書形式: [{'lang': 'en', 'text': 'Green Tea'}]
            try:
                if isinstance(name_data, (list, tuple)):
                    for item in name_data:
                        if isinstance(item, dict) and 'text' in item:
                            text = item['text']
                            normalized = normalize_for_search(text)
                            # 個別の単語もカウント（部分一致用）
                            words = normalized.split()
                            for word in words:
                                if len(word) > 2:  # 3文字以上
                                    product_name_counter[word] += 1
            except:
                pass

    print(f"  製品名単語種類数: {len(product_name_counter):,}")
    print()

    # 料理候補に頻度を付与
    print("🔍 料理候補に頻度を付与中...")
    for dish in dishes:
        label = dish['label']
        normalized = normalize_for_search(label)

        # カテゴリから検索
        count = category_counter.get(normalized, 0)

        # 製品名からも検索（部分一致）
        if count == 0:
            for word in normalized.split():
                if len(word) > 2:
                    count += product_name_counter.get(word, 0)

        dish['off_count'] = count

    print(f"  完了: {len(dishes):,} 項目")

    # 食材候補に頻度を付与
    print("🔍 食材候補に頻度を付与中...")
    for ingredient in ingredients:
        label = ingredient['label']
        normalized = normalize_for_search(label)

        # 食材タグから検索
        count = ingredient_counter.get(normalized, 0)

        # カテゴリからも検索（補助）
        if count == 0:
            count = category_counter.get(normalized, 0)

        # 製品名からも検索（部分一致）
        if count == 0:
            for word in normalized.split():
                if len(word) > 2:
                    count += product_name_counter.get(word, 0)

        ingredient['off_count'] = count

    print(f"  完了: {len(ingredients):,} 項目")
    print()

    # 結果を保存
    output_dir = PROJECT_ROOT / "core_food_processing" / "output"
    dishes_with_freq = output_dir / "dishes_with_off_freq.json"
    ingredients_with_freq = output_dir / "ingredients_with_off_freq.json"

    print("💾 結果を保存中...")
    with open(dishes_with_freq, 'w', encoding='utf-8') as f:
        json.dump(dishes, f, indent=2, ensure_ascii=False)
    print(f"  料理候補: {dishes_with_freq}")

    with open(ingredients_with_freq, 'w', encoding='utf-8') as f:
        json.dump(ingredients, f, indent=2, ensure_ascii=False)
    print(f"  食材候補: {ingredients_with_freq}")
    print()

    # 統計情報
    print("="*80)
    print("統計情報")
    print("="*80)

    # 料理の統計
    dish_counts = [d['off_count'] for d in dishes]
    dish_with_hits = [c for c in dish_counts if c > 0]
    print(f"料理候補:")
    print(f"  総数: {len(dishes):,}")
    print(f"  OFFでヒットした項目: {len(dish_with_hits):,} ({len(dish_with_hits)*100//len(dishes)}%)")
    if dish_with_hits:
        print(f"  平均ヒット数: {sum(dish_with_hits)//len(dish_with_hits):,}")
        print(f"  最大ヒット数: {max(dish_with_hits):,}")
    print()

    # 食材の統計
    ing_counts = [i['off_count'] for i in ingredients]
    ing_with_hits = [c for c in ing_counts if c > 0]
    print(f"食材候補:")
    print(f"  総数: {len(ingredients):,}")
    print(f"  OFFでヒットした項目: {len(ing_with_hits):,} ({len(ing_with_hits)*100//len(ingredients)}%)")
    if ing_with_hits:
        print(f"  平均ヒット数: {sum(ing_with_hits)//len(ing_with_hits):,}")
        print(f"  最大ヒット数: {max(ing_with_hits):,}")
    print()

    # トップ10を表示
    print("料理候補トップ10（OFFヒット数）:")
    print("-"*80)
    dishes_sorted = sorted(dishes, key=lambda x: x['off_count'], reverse=True)
    for i, dish in enumerate(dishes_sorted[:10], 1):
        print(f"{i:3d}. {dish['label']:50s} ({dish['off_count']:,} ヒット)")
    print()

    print("食材候補トップ10（OFFヒット数）:")
    print("-"*80)
    ingredients_sorted = sorted(ingredients, key=lambda x: x['off_count'], reverse=True)
    for i, ing in enumerate(ingredients_sorted[:10], 1):
        print(f"{i:3d}. {ing['label']:50s} ({ing['off_count']:,} ヒット)")
    print()

    print("✅ 次のステップ:")
    print("  1. スコアリング（0.5*log1p(OFF) + 0.4*log1p(Recipe1M) + 0.1*WWEIA）")
    print("  2. 上位選択（Base ~600、Ingredient ~1000）")
    print("  3. CORE食品リストの生成")
    print()


if __name__ == "__main__":
    main()
