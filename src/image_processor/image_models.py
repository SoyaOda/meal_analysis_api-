"""
Image Processor用のPydanticモデル定義

画像処理フェーズの入出力データ構造
"""

from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from pathlib import Path


class ImageInput(BaseModel):
    """画像入力データ"""
    image_path: Optional[Union[str, Path]] = None
    image_bytes: Optional[bytes] = None
    mime_type: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True
    
    def model_post_init(self, __context: Any) -> None:
        if not self.image_path and not self.image_bytes:
            raise ValueError("Either image_path or image_bytes must be provided")


class IdentifiedItem(BaseModel):
    """認識された食品アイテム"""
    name: str = Field(..., description="食品アイテム名")
    confidence: Optional[float] = Field(None, description="認識信頼度")
    quantity_estimate: Optional[str] = Field(None, description="推定量（例: '1 cup', '100g'）")
    attributes: Optional[Dict[str, Any]] = Field(None, description="調理法、ブランドなどの属性")
    weight_g: Optional[float] = Field(None, description="推定重量（グラム）")
    state: Optional[str] = Field(None, description="調理状態（例: 'cooked', 'raw'）")


class ProcessedImageData(BaseModel):
    """画像処理結果データ"""
    identified_items: List[IdentifiedItem] = Field(..., description="認識された食品アイテムのリスト")
    original_image_ref: Optional[str] = Field(None, description="元画像への参照")
    processing_metadata: Optional[Dict[str, Any]] = Field(None, description="処理メタデータ")
    
    class Config:
        json_encoders = {
            Path: str
        } 