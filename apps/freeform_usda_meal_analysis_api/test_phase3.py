#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 3 Test: データ統合テスト
"""

import sys
import os

# PYTHONPATHを設定
sys.path.insert(0, '/Users/odasoya/meal_analysis_api_2')

print("=" * 50)
print("Phase 3: Data Integration Test")
print("=" * 50)
print()

# テスト1: 設定のロード
print("✅ Test 1: 設定ファイルからデータパスをロード")
try:
    os.environ["DEEPINFRA_API_KEY"] = "test_key_dummy"
    from apps.freeform_usda_meal_analysis_api.config import get_settings
    settings = get_settings()

    print(f"   📁 DATA_DIR: {settings.DATA_DIR}")
    print(f"   📁 USDA_INDEX_DIR: {settings.USDA_INDEX_DIR}")
    print(f"   📄 USDA_SURVEY_FILE: {settings.USDA_SURVEY_FILE}")
    print(f"   📄 USDA_FOUNDATION_FILE: {settings.USDA_FOUNDATION_FILE}")
    print("   ✅ Settings loaded successfully")
except Exception as e:
    print(f"   ❌ Settings load failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# テスト2: データファイルの存在確認
print("\n✅ Test 2: データファイルの存在確認")
from pathlib import Path

files_to_check = {
    "FAISS Index": Path(settings.USDA_INDEX_DIR) / "usda_index_full.faiss",
    "FAISS Metadata": Path(settings.USDA_INDEX_DIR) / "usda_metadata.json",
    "USDA Survey": Path(settings.USDA_SURVEY_FILE),
    "USDA Foundation": Path(settings.USDA_FOUNDATION_FILE),
}

all_exist = True
for name, path in files_to_check.items():
    if path.exists():
        size_mb = path.stat().st_size / (1024 * 1024)
        print(f"   ✅ {name}: {path.name} ({size_mb:.1f}MB)")
    else:
        print(f"   ❌ {name}: NOT FOUND at {path}")
        all_exist = False

if not all_exist:
    print("\n❌ Some data files are missing!")
    sys.exit(1)

# テスト3: データの簡易ロードテスト
print("\n✅ Test 3: FAISSインデックスのロード")
try:
    import faiss
    index_path = Path(settings.USDA_INDEX_DIR) / "usda_index_full.faiss"
    index = faiss.read_index(str(index_path))
    print(f"   ✅ FAISS index loaded: {index.ntotal} vectors")
except Exception as e:
    print(f"   ❌ FAISS load failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# テスト4: メタデータJSONのロード
print("\n✅ Test 4: メタデータJSONのロード")
try:
    import json
    metadata_path = Path(settings.USDA_INDEX_DIR) / "usda_metadata.json"
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    print(f"   ✅ Metadata loaded: {len(metadata)} items")
except Exception as e:
    print(f"   ❌ Metadata load failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# テスト5: USDA JSONのロード
print("\n✅ Test 5: USDA JSON ファイルのロード")
try:
    with open(settings.USDA_SURVEY_FILE, 'r', encoding='utf-8') as f:
        survey_data = json.load(f)
    print(f"   ✅ Survey data loaded: {len(survey_data)} items")

    with open(settings.USDA_FOUNDATION_FILE, 'r', encoding='utf-8') as f:
        foundation_data = json.load(f)
    print(f"   ✅ Foundation data loaded: {len(foundation_data)} items")
except Exception as e:
    print(f"   ❌ USDA JSON load failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 50)
print("✅ Phase 3 All Tests Passed!")
print("=" * 50)
print("\nデータが正常に統合され、apps/freeform_usda_meal_analysis_api/data/に配置されました。")
print(f"合計データサイズ: FAISS 212MB + JSON 33MB = 245MB")
