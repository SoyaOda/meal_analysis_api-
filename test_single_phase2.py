#!/usr/bin/env python3
"""
単一画像でフェーズ2をテストするスクリプト
"""

import requests
import json

# APIのベースURL
BASE_URL = "http://localhost:8000/api/v1"

# まずフェーズ1を実行
print("=== Phase 1 ===")
with open('test_images/food3.jpg', 'rb') as f:
    files = {'image': ('food3.jpg', f, 'image/jpeg')}
    response = requests.post(f"{BASE_URL}/meal-analyses", files=files)
    
if response.status_code == 200:
    phase1_result = response.json()
    print(f"Phase 1 成功: {len(phase1_result['dishes'])} 個の料理を検出")
    print(json.dumps(phase1_result, ensure_ascii=False, indent=2))
    
    # フェーズ2を実行
    print("\n=== Phase 2 ===")
    with open('test_images/food3.jpg', 'rb') as f:
        files = {'image': ('food3.jpg', f, 'image/jpeg')}
        data = {'initial_analysis_data': json.dumps(phase1_result, ensure_ascii=False)}
        response2 = requests.post(f"{BASE_URL}/meal-analyses/refine", files=files, data=data)
        
    print(f"Status Code: {response2.status_code}")
    print(f"Response: {response2.text}")
else:
    print(f"Phase 1 エラー: {response.status_code}")
    print(response.text) 