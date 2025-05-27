import google.generativeai as genai
from typing import Dict, Optional
import json
import logging
from google.generativeai.types import HarmCategory, HarmBlockThreshold

logger = logging.getLogger(__name__)

# Geminiの構造化出力のためのJSONスキーマを定義
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


class GeminiMealAnalyzer:
    """Gemini APIを使用して食事画像を分析するクラス"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        """
        初期化
        
        Args:
            api_key: Gemini API キー
            model_name: 使用するモデル名
        """
        genai.configure(api_key=api_key)
        
        # システムインストラクション
        system_instruction = """あなたは熟練した料理分析家です。あなたのタスクは、食事の画像を分析し、料理とその材料の詳細な内訳をJSON形式で提供することです。

以下の点に注意してください：
1. 皿を含む画像を注意深く観察し、周囲の文脈に基づいて詳細な推定を行ってください。
2. 画像に存在するすべての料理を特定し、それらの種類、皿の上の各料理の量、そして含まれる材料とそれぞれの量を決定してください。
3. 1つの画像に複数の料理が含まれる場合があるため、各料理とその材料に関する情報を個別に提供してください。
4. あなたの出力は栄養価計算に使用されるため、推定が可能な限り正確であることを確認してください。
5. 応答には、提供されたJSONスキーマに厳密に従ってください。"""
        
        # モデルの初期化
        # 新しいAPIでは、generation_configを後で設定します
        self.model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
        )
        
        # generation_configを作成
        self.generation_config = {
            "temperature": 0.2,
            "top_p": 0.9,
            "top_k": 20,
            "max_output_tokens": 2048,
            "response_mime_type": "application/json",
            "response_schema": MEAL_ANALYSIS_GEMINI_SCHEMA
        }
    
    async def analyze_image_and_text(
        self, 
        image_bytes: bytes, 
        image_mime_type: str, 
        optional_text: Optional[str] = None
    ) -> Dict:
        """
        画像とテキストを分析して食事情報を抽出
        
        Args:
            image_bytes: 画像のバイトデータ
            image_mime_type: 画像のMIMEタイプ
            optional_text: オプションのテキスト説明
            
        Returns:
            分析結果の辞書
            
        Raises:
            RuntimeError: Gemini APIエラー時
        """
        try:
            # プロンプトの構築
            prompt_parts = []
            
            # 画像データの追加（新しいAPIでは辞書形式ではなく、Imageオブジェクトを使用）
            from PIL import Image
            import io
            
            # バイトデータからPIL Imageオブジェクトを作成
            image = Image.open(io.BytesIO(image_bytes))
            prompt_parts.append(image)
            
            # テキストプロンプトの追加
            if optional_text and optional_text.strip():
                text_prompt = f"提供された食事の画像を分析してください。ユーザーからの補足情報: {optional_text}"
            else:
                text_prompt = "提供された食事の画像を分析してください。"
            
            prompt_parts.append(text_prompt)
            
            # Gemini APIを呼び出し（generation_configを渡す）
            response = self.model.generate_content(
                prompt_parts,
                generation_config=self.generation_config
            )
            
            # レスポンスのテキストを取得
            if not response.text:
                raise ValueError("Geminiからレスポンスが返されませんでした。")
            
            # JSONレスポンスをパース
            result = json.loads(response.text)
            
            logger.info(f"Gemini analysis completed successfully. Found {len(result.get('dishes', []))} dishes.")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            raise RuntimeError(f"Geminiからの応答処理中にエラーが発生しました: {e}") from e
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise RuntimeError(f"Gemini APIリクエストが失敗しました: {e}") from e 