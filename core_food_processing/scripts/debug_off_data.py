#!/usr/bin/env python3
"""
debug_off_data.py

OFFデータの構造をデバッグするスクリプト
"""

import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
PARQUET_FILE = PROJECT_ROOT / "core_food_processing" / "data" / "openfoodfacts_food.parquet"

print("📖 Parquetファイルを読み込み中...")
required_columns = ['categories_tags', 'ingredients_tags', 'product_name']
df = pd.read_parquet(PARQUET_FILE, columns=required_columns)

print(f"✅ 読み込み完了: {len(df):,} 製品")
print()

# categories_tagsのサンプルを確認
print("="*80)
print("categories_tags のサンプル（最初の10個の非NULL値）:")
print("="*80)
for i, val in enumerate(df['categories_tags'].dropna().head(10), 1):
    print(f"{i}. タイプ: {type(val)}, 値: {val}")
print()

# ingredients_tagsのサンプルを確認
print("="*80)
print("ingredients_tags のサンプル（最初の10個の非NULL値）:")
print("="*80)
for i, val in enumerate(df['ingredients_tags'].dropna().head(10), 1):
    print(f"{i}. タイプ: {type(val)}, 値: {val}")
print()

# product_nameのサンプルを確認
print("="*80)
print("product_name のサンプル（最初の10個）:")
print("="*80)
for i, val in enumerate(df['product_name'].dropna().head(10), 1):
    print(f"{i}. {val}")
print()
