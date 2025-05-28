import asyncio
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

# 実際に使用されるスキーマ
MEAL_ANALYSIS_GEMINI_SCHEMA = {
    "type": "object",
    "properties": {
        "dishes": {
            "type": "array",
            "description": "画像から特定された料理のリスト。",
            "items": {
                "type": "object",
                "properties": {
                    "dish_name": {"type": "string", "description": "特定された料理の名称。"},
                    "type": {"type": "string", "description": "料理の種類（例: 主菜, 副菜, スープ, デザート）。"},
                    "quantity_on_plate": {"type": "string", "description": "皿の上に載っている料理のおおよその量や個数（例: '1杯', '2切れ', '約200g'）。"},
                    "ingredients": {
                        "type": "array",
                        "description": "この料理に含まれると推定される材料のリスト。",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ingredient_name": {"type": "string", "description": "材料の名称。"},
                                "weight_g": {"type": "number", "description": "その材料の推定重量（グラム単位）。"}
                            },
                            "required": ["ingredient_name", "weight_g"]
                        }
                    }
                },
                "required": ["dish_name", "type", "quantity_on_plate", "ingredients"]
            }
        }
    },
    "required": ["dishes"]
}

async def test_async():
    print("=== Test 1: 非同期 - シンプルなプロンプト ===")
    try:
        model = GenerativeModel("gemini-2.5-flash-preview-05-20")
        
        # シンプルなプロンプト
        response = await model.generate_content_async("Hello, please respond with JSON containing name and age.")
        print("成功:", response.text)
    except Exception as e:
        print("エラー:", type(e).__name__, str(e))
        import traceback
        traceback.print_exc()

    print("\n=== Test 2: 非同期 - response_schemaを使用 ===")
    try:
        model = GenerativeModel("gemini-2.5-flash-preview-05-20")
        
        config = GenerationConfig(
            temperature=0.2,
            response_mime_type="application/json",
            response_schema=simple_schema
        )
        
        response = await model.generate_content_async(
            "Please generate JSON with a name and age.",
            generation_config=config
        )
        print("成功:", response.text)
    except Exception as e:
        print("エラー:", type(e).__name__, str(e))
        import traceback
        traceback.print_exc()

    print("\n=== Test 3: 非同期 - 実際のスキーマを使用 ===")
    try:
        model = GenerativeModel("gemini-2.5-flash-preview-05-20")
        
        config = GenerationConfig(
            temperature=0.2,
            top_p=0.9,
            top_k=20,
            max_output_tokens=2048,
            response_mime_type="application/json",
            response_schema=MEAL_ANALYSIS_GEMINI_SCHEMA
        )
        
        # テスト画像を読み込む
        with open("test_images/food3.jpg", "rb") as f:
            image_bytes = f.read()
        
        # プロンプトの構築
        prompt_text = """あなたは熟練した料理分析家です。あなたのタスクは、食事の画像を分析し、料理とその材料の詳細な内訳をJSON形式で提供することです。

提供された食事の画像を分析してください。"""
        
        # コンテンツリストを作成
        contents = [
            Part.from_text(prompt_text),
            Part.from_data(
                data=image_bytes,
                mime_type="image/jpeg"
            )
        ]
        
        response = await model.generate_content_async(
            contents=contents,
            generation_config=config
        )
        print("成功 (部分):", response.text[:200], "...")
    except Exception as e:
        print("エラー:", type(e).__name__, str(e))
        import traceback
        traceback.print_exc()

# 実行
asyncio.run(test_async()) 