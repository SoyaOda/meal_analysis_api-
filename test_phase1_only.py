import requests
import json

# API設定
BASE_URL = "http://localhost:8000/api/v1"

# テスト画像のパス
image_path = "test_images/food3.jpg"

print("=== Phase 1 API Test ===")

# 画像ファイルを開く
with open(image_path, "rb") as f:
    files = {"image": ("food3.jpg", f, "image/jpeg")}
    
    # Phase 1 APIを呼び出し
    response = requests.post(
        f"{BASE_URL}/meal-analyses",
        files=files
    )

print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    print("成功! 結果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 検出された料理数を表示
    if "dishes" in result:
        print(f"\n検出された料理数: {len(result['dishes'])}")
        for dish in result['dishes']:
            print(f"- {dish['dish_name']} ({dish['type']})")
            print(f"  材料数: {len(dish['ingredients'])}")
else:
    print("エラー:", response.text) 