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
        description="プロンプトファイルの相対パス（prompts/以下）。prompt_textと同時に指定した場合はprompt_textが優先される",
        example="freeform_prompt_usda_format_ver_v7_production_20251027.txt"
    )

    prompt_text: Optional[str] = Field(
        None,
        description="プロンプトテキストの全文。指定した場合はprompt_pathより優先される",
        example="You are an expert food analyst. Analyze the meal image..."
    )

    reasoning_effort: Optional[str] = Field(
        None,
        description="Reasoning effortレベル。'minimal', 'low', 'medium', 'high', 'xhigh' から選択。未指定時はモデルのデフォルト動作。",
        example="medium"
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
        example=50
    )

    # ========== Hybrid Search パラメータ ==========
    bm25_weight: Optional[float] = Field(
        None,
        description="BM25検索のスコア重み（0.0-1.0）",
        ge=0.0,
        le=1.0,
        example=0.4
    )

    vector_weight: Optional[float] = Field(
        None,
        description="Vector検索のスコア重み（0.0-1.0）",
        ge=0.0,
        le=1.0,
        example=0.6
    )

    rrf_k: Optional[int] = Field(
        None,
        description="RRF（Reciprocal Rank Fusion）のkパラメータ",
        ge=1,
        le=200,
        example=60
    )

    # ========== Reranker パラメータ ==========
    reranker_model: Optional[str] = Field(
        None,
        description="Rerankerモデル名（DeepInfra）",
        example="Qwen/Qwen3-Reranker-8B"
    )

    reranker_instruction: Optional[str] = Field(
        None,
        description="Reranker用のinstruction（タスク特化の指示文）",
        example="For food matching, prioritize exact ingredient names and preparation methods."
    )

    reranker_top_n: Optional[int] = Field(
        None,
        description="Rerankerで返す結果数（Noneの場合は全件）",
        ge=1,
        le=100,
        example=10
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
