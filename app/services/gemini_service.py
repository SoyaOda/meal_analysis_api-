import vertexai
from vertexai.generative_models import GenerativeModel, Part, GenerationConfig, HarmCategory, HarmBlockThreshold
from typing import Dict, Optional
import json
import logging
from PIL import Image
import io

from ..api.v1.schemas.meal import REFINED_MEAL_ANALYSIS_GEMINI_SCHEMA

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
    """Vertex AI経由でGeminiを使用して食事画像を分析するクラス"""
    
    def __init__(self, project_id: str, location: str, model_name: str = "gemini-1.5-flash"):
        """
        初期化
        
        Args:
            project_id: GCPプロジェクトID
            location: Vertex AIのロケーション（例: us-central1）
            model_name: 使用するモデル名
        """
        # Vertex AIの初期化
        vertexai.init(project=project_id, location=location)
        
        # システムインストラクション
        system_instruction = """あなたは熟練した料理分析家です。あなたのタスクは、食事の画像を分析し、料理とその材料の詳細な内訳をJSON形式で提供することです。

以下の点に注意してください：
1. 皿を含む画像を注意深く観察し、周囲の文脈に基づいて詳細な推定を行ってください。
2. 画像に存在するすべての料理を特定し、それらの種類、皿の上の各料理の量、そして含まれる材料とそれぞれの量を決定してください。
3. 1つの画像に複数の料理が含まれる場合があるため、各料理とその材料に関する情報を個別に提供してください。
4. あなたの出力は栄養価計算に使用されるため、推定が可能な限り正確であることを確認してください。
5. 応答には、提供されたJSONスキーマに厳密に従ってください。"""

        # フェーズ2用のシステムインストラクション
        system_instruction_phase2 = """あなたは経験豊富な栄養士であり、食事分析の専門家です。提供された食事画像、初期AI分析結果、およびUSDA食品データベースからの候補情報を総合的に評価し、初期AI分析結果を精緻化してください。

あなたのタスクは以下の通りです：
1. 初期AI分析結果に含まれる各料理および食材について、提示されたUSDA食品候補の中から最も適切と思われるものを一つ選択してください。選択の際には、画像の内容、食材の一般的な使われ方、栄養価の妥当性を考慮してください。
2. 選択したUSDA食品のFDC IDを特定してください。
3. 最終的な料理・食材名、その種類、皿の上の量、そして各材料（選択したUSDA食品に対応する）の名称、推定重量（グラム）、およびFDC IDを、指定されたJSONスキーマに厳密に従って出力してください。
4. もし初期AI分析結果の食材がUSDA候補に適切なものがない場合、または画像と著しく異なる場合は、その旨を考慮し、最も妥当な判断を下してください。
5. あなたの出力は、正確な栄養価計算の基礎となります。"""
        
        # モデルの初期化
        self.model = GenerativeModel(
            model_name=model_name,
            system_instruction=[system_instruction]  # Vertex AIではリストで渡す
        )
        
        # フェーズ2用のモデル初期化
        self.model_phase2 = GenerativeModel(
            model_name=model_name,
            system_instruction=[system_instruction_phase2]
        )
        
        # generation_configを作成
        self.generation_config = GenerationConfig(
            temperature=0.2,
            top_p=0.9,
            top_k=20,
            max_output_tokens=2048,
            response_mime_type="application/json",
            response_schema=MEAL_ANALYSIS_GEMINI_SCHEMA
        )
        
        # セーフティ設定
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
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
            contents = []
            
            # 画像データの追加（Vertex AIではPartオブジェクトを使用）
            image_part = Part.from_data(
                data=image_bytes,
                mime_type=image_mime_type
            )
            contents.append(image_part)
            
            # テキストプロンプトの追加
            if optional_text and optional_text.strip():
                text_prompt = f"提供された食事の画像を分析してください。ユーザーからの補足情報: {optional_text}"
            else:
                text_prompt = "提供された食事の画像を分析してください。"
            
            text_part = Part.from_text(text_prompt)
            contents.append(text_part)
            
            # Gemini APIを呼び出し（非同期メソッドを使用）
            response = await self.model.generate_content_async(
                contents=contents,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
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
            logger.error(f"Vertex AI/Gemini API error: {e}")
            raise RuntimeError(f"Vertex AI/Gemini APIリクエストが失敗しました: {e}") from e
    
    async def analyze_image_with_usda_context(
        self,
        image_bytes: bytes,
        image_mime_type: str,
        usda_candidates_text: str,
        initial_ai_output_text: Optional[str] = None
    ) -> Dict:
        """
        USDAコンテキストを使用して画像を再分析（フェーズ2）
        
        Args:
            image_bytes: 画像のバイトデータ
            image_mime_type: 画像のMIMEタイプ
            usda_candidates_text: USDA候補情報のフォーマット済みテキスト
            initial_ai_output_text: フェーズ1のAI出力（JSON文字列）
            
        Returns:
            精緻化された分析結果の辞書
            
        Raises:
            RuntimeError: Gemini APIエラー時
        """
        try:
            # プロンプトの構築
            contents = []
            
            # 画像データの追加
            image_part = Part.from_data(
                data=image_bytes,
                mime_type=image_mime_type
            )
            contents.append(image_part)
            
            # テキストプロンプトの構築
            prompt_parts = []
            
            if initial_ai_output_text:
                prompt_parts.append(f"初期AI分析結果:\n{initial_ai_output_text}\n")
            
            prompt_parts.append(f"上記分析結果と画像に関するUSDA食品データベースの候補情報:\n{usda_candidates_text}\n")
            prompt_parts.append("これらの情報を踏まえ、システムインストラクションに従って最終的な分析結果をJSON形式で生成してください。")
            
            full_prompt_text = "\n".join(prompt_parts)
            text_part = Part.from_text(full_prompt_text)
            contents.append(text_part)
            
            # フェーズ2用のGeneration Config
            phase2_generation_config = GenerationConfig(
                temperature=0.2,
                top_p=0.9,
                top_k=20,
                max_output_tokens=2048,
                response_mime_type="application/json",
                response_schema=REFINED_MEAL_ANALYSIS_GEMINI_SCHEMA
            )
            
            # Gemini APIを呼び出し（フェーズ2モデルを使用）
            response = await self.model_phase2.generate_content_async(
                contents=contents,
                generation_config=phase2_generation_config,
                safety_settings=self.safety_settings
            )
            
            # レスポンスのテキストを取得
            if not response.text:
                raise ValueError("Gemini（フェーズ2）からレスポンスが返されませんでした。")
            
            # JSONレスポンスをパース
            result = json.loads(response.text)
            
            logger.info(f"Gemini phase 2 analysis completed successfully. Found {len(result.get('dishes', []))} dishes.")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in phase 2: {e}. Raw response: {getattr(response, 'text', 'N/A')}")
            raise RuntimeError(f"Gemini（フェーズ2）からの応答処理中にエラー: {e}") from e
        except Exception as e:
            logger.error(f"Vertex AI/Gemini API error in phase 2: {e}")
            raise RuntimeError(f"Vertex AI/Gemini（フェーズ2）APIリクエスト失敗: {e}") from e 