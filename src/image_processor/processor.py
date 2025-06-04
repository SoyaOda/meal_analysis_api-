"""
Image Processor - Phase1ロジック

画像入力と前処理を担当するモジュール
現在のGemini Phase1ロジックをカプセル化
"""

from typing import Dict, Any, Optional
import logging
from pathlib import Path

from .image_models import ImageInput, IdentifiedItem, ProcessedImageData
from ..common.exceptions import InvalidImageFormatError, FoodRecognitionError

logger = logging.getLogger(__name__)


class ImageProcessor:
    """画像処理クラス - Phase1機能をカプセル化"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        設定で初期化
        
        Args:
            config: 画像処理設定（MLモデルパス、サイズ制限など）
        """
        self.config = config
        self.max_image_size_mb = config.get("MAX_IMAGE_SIZE_MB", 10)
        self.allowed_extensions = config.get("ALLOWED_EXTENSIONS", [".jpg", ".jpeg", ".png"])
        
        # 将来的にはGeminiサービスの依存関係をここで初期化
        self._gemini_service = None
        
        logger.info(f"ImageProcessor initialized with config: {config}")
    
    def set_gemini_service(self, gemini_service):
        """Geminiサービスの設定（依存関係注入）"""
        self._gemini_service = gemini_service
    
    async def process_image(self, image_input: ImageInput) -> ProcessedImageData:
        """
        Phase1の主要ロジック：画像処理とUSDAクエリ候補生成
        
        Args:
            image_input: 画像入力データ
            
        Returns:
            ProcessedImageData: 処理済み画像データ
            
        Raises:
            InvalidImageFormatError: 無効な画像形式
            FoodRecognitionError: 食品認識エラー
        """
        try:
            # 1. 画像の検証
            image_bytes, mime_type = await self._validate_and_load_image(image_input)
            
            # 2. Gemini Phase1による分析（既存ロジックを活用）
            if not self._gemini_service:
                raise FoodRecognitionError("Gemini service not configured")
            
            # 既存のGemini Phase1ロジックを呼び出し
            gemini_result = await self._gemini_service.analyze_image_phase1(
                image_bytes=image_bytes,
                image_mime_type=mime_type,
                optional_text=None
            )
            
            # 3. Gemini結果を標準化されたフォーマットに変換
            identified_items = self._convert_gemini_to_identified_items(gemini_result)
            
            return ProcessedImageData(
                identified_items=identified_items,
                original_image_ref=str(image_input.image_path) if image_input.image_path else "bytes_input",
                processing_metadata={
                    "gemini_dishes_count": len(gemini_result.get('dishes', [])),
                    "total_usda_queries": sum(len(dish.get('usda_query_candidates', [])) for dish in gemini_result.get('dishes', [])),
                    "processing_method": "gemini_phase1"
                }
            )
            
        except Exception as e:
            logger.error(f"Error in image processing: {e}")
            if isinstance(e, (InvalidImageFormatError, FoodRecognitionError)):
                raise
            raise FoodRecognitionError(f"Image processing failed: {str(e)}") from e
    
    async def _validate_and_load_image(self, image_input: ImageInput) -> tuple[bytes, str]:
        """画像の検証とロード"""
        if image_input.image_bytes:
            # バイト列からの処理
            if not image_input.mime_type:
                raise InvalidImageFormatError("mime_type required when using image_bytes")
            
            if not image_input.mime_type.startswith("image/"):
                raise InvalidImageFormatError("Invalid MIME type")
                
            if len(image_input.image_bytes) > self.max_image_size_mb * 1024 * 1024:
                raise InvalidImageFormatError(f"Image too large (max {self.max_image_size_mb}MB)")
                
            return image_input.image_bytes, image_input.mime_type
        
        elif image_input.image_path:
            # ファイルパスからの処理
            image_path = Path(image_input.image_path)
            
            if not image_path.exists():
                raise InvalidImageFormatError(f"Image file not found: {image_path}")
            
            if image_path.suffix.lower() not in self.allowed_extensions:
                raise InvalidImageFormatError(f"Unsupported file extension: {image_path.suffix}")
            
            file_size = image_path.stat().st_size
            if file_size > self.max_image_size_mb * 1024 * 1024:
                raise InvalidImageFormatError(f"Image too large (max {self.max_image_size_mb}MB)")
            
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            
            # MIME typeを拡張子から推定
            mime_type = self._get_mime_type_from_extension(image_path.suffix)
            
            return image_bytes, mime_type
        
        else:
            raise InvalidImageFormatError("No image data provided")
    
    def _get_mime_type_from_extension(self, extension: str) -> str:
        """拡張子からMIME typeを取得"""
        mime_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.webp': 'image/webp'
        }
        return mime_map.get(extension.lower(), 'image/jpeg')
    
    def _convert_gemini_to_identified_items(self, gemini_result: Dict[str, Any]) -> list[IdentifiedItem]:
        """Gemini結果を標準化されたIdentifiedItemリストに変換"""
        identified_items = []
        
        for dish in gemini_result.get('dishes', []):
            # 料理レベルのアイテム
            dish_item = IdentifiedItem(
                name=dish.get('dish_name', 'Unknown Dish'),
                quantity_estimate=dish.get('quantity_on_plate'),
                attributes={
                    'type': dish.get('type'),
                    'is_dish': True,
                    'usda_query_candidates': dish.get('usda_query_candidates', [])
                }
            )
            identified_items.append(dish_item)
            
            # 材料レベルのアイテム
            for ingredient in dish.get('ingredients', []):
                ingredient_item = IdentifiedItem(
                    name=ingredient.get('ingredient_name', 'Unknown Ingredient'),
                    weight_g=ingredient.get('weight_g', 0),
                    state=ingredient.get('state'),
                    attributes={
                        'parent_dish': dish.get('dish_name'),
                        'is_ingredient': True
                    }
                )
                identified_items.append(ingredient_item)
        
        return identified_items 