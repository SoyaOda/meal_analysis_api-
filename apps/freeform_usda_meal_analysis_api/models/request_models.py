"""
Request models for Freeform USDA Meal Analysis API
"""
from typing import Optional
from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    """VLMモデル設定"""
    model_config = {"protected_namespaces": ()}

    model_id: Optional[str] = Field(
        None,
        description="DeepInfra VLMモデルID（例: 'Qwen/Qwen2-VL-72B-Instruct'）。指定しない場合はデフォルト30Bモデル",
        example="Qwen/Qwen2-VL-72B-Instruct"
    )

    prompt_path: Optional[str] = Field(
        None,
        description="プロンプトファイルの相対パス（prompts/以下）。指定しない場合はv7_experimentalを使用",
        example="freeform_prompt_usda_format_ver_v7_production_20251027.txt"
    )

    thinking_budget: Optional[int] = Field(
        None,
        description="思考トークン数（QVQモデル使用時のみ有効）",
        ge=1,
        le=32768,
        example=4096
    )

    enable_thinking: Optional[bool] = Field(
        None,
        description="Thinking modeのon/off（Alibabaのqwen3-vl-plus等で使用）",
        example=True
    )

    temperature: Optional[float] = Field(
        None,
        description="生成温度（0.0-2.0）",
        ge=0.0,
        le=2.0,
        example=0.7
    )

    max_tokens: Optional[int] = Field(
        None,
        description="最大トークン数",
        ge=1,
        le=32768,
        example=4096
    )


class SearchConfig(BaseModel):
    """検索設定（Fullインデックスのみ使用）"""
    model_config = {"protected_namespaces": ()}

    stage1_top_k: Optional[int] = Field(
        None,
        description="Stage1で取得する候補数",
        ge=1,
        le=200,
        example=40
    )


class ImageAnalysisRequest(BaseModel):
    """画像分析リクエスト"""
    model_config = {"protected_namespaces": ()}

    user_context: Optional[str] = Field(
        None,
        description="ユーザーコンテキスト（食事の説明など）",
        example="lunch analysis"
    )

    model_config_override: Optional[ModelConfig] = Field(
        None,
        description="モデル設定のオーバーライド"
    )

    search_config_override: Optional[SearchConfig] = Field(
        None,
        description="検索設定のオーバーライド"
    )


class VoiceAnalysisRequest(BaseModel):
    """音声分析リクエスト"""
    model_config = {"protected_namespaces": ()}

    user_context: Optional[str] = Field(
        None,
        description="ユーザーコンテキスト",
        example="voice lunch analysis"
    )

    language_code: str = Field(
        "en-US",
        description="音声認識言語コード",
        example="ja-JP"
    )

    model_config_override: Optional[ModelConfig] = Field(
        None,
        description="モデル設定のオーバーライド"
    )

    search_config_override: Optional[SearchConfig] = Field(
        None,
        description="検索設定のオーバーライド"
    )
