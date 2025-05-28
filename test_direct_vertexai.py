import vertexai
from vertexai.generative_models import GenerativeModel, Part, GenerationConfig
import os
import json

# 環境変数を設定
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/odasoya/meal_analysis_api /service-account-key.json"

# Vertex AIを初期化
vertexai.init(
    project="recording-diet-ai-3e7cf",
    location="us-central1"
)

# シンプルなスキーマ
simple_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"}
    },
    "required": ["name", "age"]
}

# 各種初期化方法をテスト
print("=== Test 1: シンプルな初期化 ===")
try:
    model = GenerativeModel("gemini-2.5-flash-preview-05-20")
    
    # シンプルなプロンプト
    response = model.generate_content("Hello, please respond with JSON containing name and age.")
    print("成功:", response.text)
except Exception as e:
    print("エラー:", type(e).__name__, str(e))

print("\n=== Test 2: response_json_schemaを使用 ===")
try:
    model = GenerativeModel("gemini-2.5-flash-preview-05-20")
    
    config = GenerationConfig(
        temperature=0.2,
        response_mime_type="application/json",
        response_json_schema=simple_schema
    )
    
    response = model.generate_content(
        "Please generate JSON with a name and age.",
        generation_config=config
    )
    print("成功:", response.text)
except Exception as e:
    print("エラー:", type(e).__name__, str(e))
    import traceback
    traceback.print_exc()

print("\n=== Test 3: response_schemaを使用 ===")
try:
    model = GenerativeModel("gemini-2.5-flash-preview-05-20")
    
    config = GenerationConfig(
        temperature=0.2,
        response_mime_type="application/json",
        response_schema=simple_schema
    )
    
    response = model.generate_content(
        "Please generate JSON with a name and age.",
        generation_config=config
    )
    print("成功:", response.text)
except Exception as e:
    print("エラー:", type(e).__name__, str(e))
    import traceback
    traceback.print_exc()

print("\n=== Test 4: 画像とJSONスキーマ ===")
try:
    model = GenerativeModel("gemini-2.5-flash-preview-05-20")
    
    # テスト画像を読み込む
    with open("test_images/food3.jpg", "rb") as f:
        image_bytes = f.read()
    
    # 画像Part作成
    image_part = Part.from_data(
        data=image_bytes,
        mime_type="image/jpeg"
    )
    
    config = GenerationConfig(
        temperature=0.2,
        response_mime_type="application/json"
    )
    
    response = model.generate_content(
        ["Analyze this food image and return JSON with dish names", image_part],
        generation_config=config
    )
    print("成功 (部分):", response.text[:200], "...")
except Exception as e:
    print("エラー:", type(e).__name__, str(e))
    import traceback
    traceback.print_exc() 