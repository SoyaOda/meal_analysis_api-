#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
単一画像でVLMが正常動作するかテスト
"""

import asyncio
import json
import sys
from pathlib import Path

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.freeform_usda_meal_analysis_api.services.vlm_service import VLMService


async def test_vlm():
    # VLMService初期化
    vlm_service = VLMService()

    # テスト画像
    image_path = "test_images/images/test_food1.jpg"

    print("=" * 100)
    print(f"VLM単一画像テスト: {image_path}")
    print("=" * 100)
    print()

    try:
        # VLM解析実行
        vlm_response, usage = await vlm_service.analyze_image_from_file(image_path)

        print("✅ VLM解析成功")
        print()
        print("【VLM Response】")
        print(json.dumps(vlm_response, indent=2, ensure_ascii=False))
        print()
        print("【Usage】")
        print(json.dumps(usage, indent=2, ensure_ascii=False))
        print()

        # dishes配列の確認
        dishes = vlm_response.get("dishes", [])
        print(f"認識された料理数: {len(dishes)}")
        for i, dish in enumerate(dishes, 1):
            print(f"  {i}. {dish.get('main_food', '')} ({dish.get('weight_g', 0)}g)")

    except Exception as e:
        print(f"❌ VLM解析失敗: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 100)


if __name__ == "__main__":
    asyncio.run(test_vlm())
