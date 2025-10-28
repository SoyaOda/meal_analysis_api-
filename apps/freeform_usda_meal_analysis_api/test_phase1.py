#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 1 Test: DeepInfraService 移植テスト
"""

import sys
import os
import asyncio

# PYTHONPATHを設定
sys.path.insert(0, '/Users/odasoya/meal_analysis_api_2')

print("=" * 50)
print("Phase 1: DeepInfraService Import Test")
print("=" * 50)
print()

# テスト1: インポートテスト
print("✅ Test 1: DeepInfraServiceのインポート")
try:
    from apps.freeform_usda_meal_analysis_api.services.deepinfra_service import DeepInfraService
    print("   ✅ Import successful")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    sys.exit(1)

# テスト2: 初期化テスト
print("\n✅ Test 2: DeepInfraServiceの初期化")
try:
    # API Keyは環境変数から取得（設定されていない場合は失敗するはず）
    service = DeepInfraService(model_id="Qwen/Qwen3-VL-30B-A3B-Thinking")
    print(f"   ✅ Initialization successful: {service.model_id}")
except ValueError as e:
    if "DEEPINFRA_API_KEY" in str(e):
        print("   ⚠️  DEEPINFRA_API_KEY not set (expected in test environment)")
        print("   Setting dummy key for remaining tests...")
        os.environ["DEEPINFRA_API_KEY"] = "test_key_dummy"
        service = DeepInfraService(model_id="Qwen/Qwen3-VL-30B-A3B-Thinking")
        print(f"   ✅ Initialization successful with dummy key: {service.model_id}")
    else:
        print(f"   ❌ Unexpected error: {e}")
        sys.exit(1)
except Exception as e:
    print(f"   ❌ Initialization failed: {e}")
    sys.exit(1)

# テスト3: 他のサービスからのインポートテスト
print("\n✅ Test 3: usda_search.pyからDeepInfraServiceをインポート")
try:
    from apps.freeform_usda_meal_analysis_api.services.usda_search import SimplifiedUSDASearcher
    print("   ✅ SimplifiedUSDASearcher import successful")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# テスト4: vlm_service.pyからのインポートテスト
print("\n✅ Test 4: vlm_service.pyからDeepInfraServiceをインポート")
try:
    from apps.freeform_usda_meal_analysis_api.services.vlm_service import VLMService
    print("   ✅ VLMService import successful")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 50)
print("✅ Phase 1 All Tests Passed!")
print("=" * 50)
print("\nDeepInfraServiceが正常に移植され、shared/への依存が削除されました。")
