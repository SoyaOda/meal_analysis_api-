"""
Dynamic Configuration Manager with Firestore backend and TTL cache
"""

import os
import time
import logging
from typing import Any, Dict, Optional
from functools import lru_cache
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


# ========== Configuration Models ==========


class VLMConfig(BaseModel):
    """VLM (Vision Language Model) Configuration"""

    model_config = ConfigDict(protected_namespaces=())

    model_id: str = Field(
        default="openrouter:google/gemini-3-flash-preview",
        description="VLM Model ID (mozu default 2026-06-04: 'openrouter:google/gemini-3-flash-preview'; alt: 'openrouter:google/gemini-3.1-pro-preview'. pro retracted — no robust edge on independent GT)",
    )
    prompt_file: str = Field(
        default="freeform_prompt_usda_format_ver_v13_beverage_subject_prodcapture_20260226.txt",
        description="Prompt file name (in prompts/ directory). v13 = 本番稼働中のv11b+飲料対応 (settings.py 参照)",
    )
    prompt_text: Optional[str] = Field(
        default=None, description="Direct prompt text (overrides prompt_file if set)"
    )
    temperature: float = Field(
        default=0.3, ge=0.0, le=2.0, description="Generation temperature"
    )
    max_tokens: int = Field(
        default=12288, ge=1, le=32768, description="Maximum output tokens"
    )
    reasoning_effort: str = Field(
        default="medium",
        description="Reasoning effort level: minimal/low/medium/high/xhigh",
    )
    seed: int = Field(default=123456, description="Random seed for reproducibility")
    use_cache: bool = Field(
        default=True,
        description="Whether to use VLM response cache",
    )
    self_consistency_k: int = Field(
        default=1,
        ge=1,
        le=9,
        description=(
            "Self-consistency samples: run the analysis K times with K distinct "
            "seeds and return the median-total-calorie result. 1 = off (single "
            "call, default). K=3 cut realistic-range calorie MAE ~2pt (pooled "
            "p=0.02); see evals/lessons/20260604_self_consistency_median_ensemble_"
            "significant_calorie_win.md. Runs SEQUENTIALLY (latency ~Kx)."
        ),
    )


class SearchConfig(BaseModel):
    """Hybrid Search Configuration"""

    stage1_top_k: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Number of candidates to retrieve in Stage 1",
    )
    bm25_weight: float = Field(
        default=0.4, ge=0.0, le=1.0, description="BM25 search score weight"
    )
    vector_weight: float = Field(
        default=0.6, ge=0.0, le=1.0, description="Vector search score weight"
    )
    rrf_k: int = Field(
        default=60, ge=1, le=200, description="RRF (Reciprocal Rank Fusion) k parameter"
    )
    rrf_weight: float = Field(
        default=0.55, ge=0.0, le=2.0, description="RRF fusion score weight"
    )
    embedding_instruction: str = Field(
        default="Match food names to USDA FoodData Central database entries for nutrition lookup",
        description="Instruction for embedding model to improve food name matching",
    )


class RerankerConfig(BaseModel):
    """Reranker Configuration"""

    model_config = ConfigDict(protected_namespaces=())

    model: str = Field(
        default="Qwen/Qwen3-Reranker-0.6B", description="Reranker model name"
    )
    instruction: str = Field(
        default="""Match USDA food database entries that exactly match the query's food name, cooking/preparation method, and form.

Nutritional values (calories, protein, fat, carbs per 100g) vary significantly based on preparation method, so precise matching is essential for accurate nutrition calculation.

Examples:
- 'grilled chicken' → 'Chicken, grilled' NOT 'Chicken, raw'
- 'caesar salad' → 'Caesar salad, with romaine' NOT 'Caesar dressing'
- 'fried rice' → 'Rice, fried' NOT 'Rice, white, cooked'

Prioritize: Complete phrase match > Preparation method match > Ingredient name similarity""",
        description="Reranker instruction for USDA food matching",
    )
    top_n: Optional[int] = Field(
        default=5,
        ge=1,
        le=100,
        description="Reranker top-k. >1 で top-k density mixture(E7)を有効化（既定5）。1=従来top-1",
    )


class VoiceConfig(BaseModel):
    """Voice Analysis Configuration (音声入力用設定)"""

    model_config = ConfigDict(protected_namespaces=())

    model_id: str = Field(
        default="openrouter:openai/gpt-5-mini",
        description="Voice解析用LLM/VLMモデルID (e.g., 'openrouter:openai/gpt-5-mini', 'google/gemma-3-27b-it')",
    )
    prompt_file: str = Field(
        default="freeform_voice_prompt_usda.txt",
        description="Voice解析用プロンプトファイル名 (in prompts/ directory)",
    )
    prompt_text: Optional[str] = Field(
        default=None,
        description="カスタムプロンプトテキスト (overrides prompt_file if set)",
    )
    whisper_model: str = Field(
        default="openai/whisper-large-v3-turbo", description="Whisper STTモデルID"
    )
    temperature: float = Field(default=0.3, ge=0.0, le=2.0, description="生成温度")
    max_tokens: int = Field(
        default=4096, ge=1, le=32768, description="最大出力トークン数"
    )
    seed: int = Field(default=123456, description="Random seed for reproducibility")


class RuntimeConfig(BaseModel):
    """Runtime Configuration (環境依存設定)"""

    device: str = Field(
        default="cpu", description="Computation device: 'cpu' or 'cuda'"
    )


class APIConfig(BaseModel):
    """Complete API Configuration"""

    vlm: VLMConfig = Field(default_factory=VLMConfig)
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    reranker: RerankerConfig = Field(default_factory=RerankerConfig)
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
    updated_at: Optional[str] = Field(default=None, description="Last update timestamp")
    updated_by: Optional[str] = Field(default=None, description="Last updated by")
    schema_version: int = Field(
        default=1, description="Config schema version for one-shot migrations"
    )


# ========== Configuration Manager ==========


class ConfigManager:
    """
    Dynamic Configuration Manager with Firestore backend and TTL cache

    Features:
    - Firestore persistence (Cloud Run production)
    - In-memory fallback (local development)
    - TTL-based cache (default: 60 seconds)
    - Thread-safe singleton pattern
    """

    _instance: Optional["ConfigManager"] = None
    _initialized: bool = False

    # Firestore collection name
    COLLECTION_NAME = "api_configs"
    DOCUMENT_ID = "freeform_usda_meal_analysis"

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        use_firestore: bool = None,
        cache_ttl_seconds: int = 5,  # デバッグ用に短縮
    ):
        if self._initialized:
            return

        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: Optional[APIConfig] = None
        self._cache_timestamp: float = 0
        self._firestore_client = None

        # Auto-detect Firestore availability
        if use_firestore is None:
            use_firestore = os.getenv("GOOGLE_CLOUD_PROJECT") is not None

        self.use_firestore = use_firestore

        if self.use_firestore:
            try:
                from google.cloud import firestore

                # 明示的にプロジェクトを指定（ローカル環境でも正しいプロジェクトに接続）
                project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
                self._firestore_client = firestore.Client(project=project_id)
                logger.info(
                    f"ConfigManager initialized with Firestore backend (project: {project_id})"
                )
            except Exception as e:
                logger.warning(
                    f"Firestore initialization failed, falling back to in-memory: {e}"
                )
                self.use_firestore = False
                self._firestore_client = None

        if not self.use_firestore:
            logger.info(
                "ConfigManager initialized with in-memory backend (local development mode)"
            )
            # Load defaults from environment/settings
            self._cache = self._load_defaults_from_settings()

        self._initialized = True

    def _load_defaults_from_settings(self) -> APIConfig:
        """Load default configuration from settings.py"""
        try:
            from ..config.settings import get_settings

            settings = get_settings()

            return APIConfig(
                vlm=VLMConfig(
                    model_id=settings.DEFAULT_VLM_MODEL_ID,
                    prompt_file=settings.DEFAULT_PROMPT_FILE,
                    temperature=settings.DEFAULT_TEMPERATURE,
                    max_tokens=settings.DEFAULT_MAX_TOKENS,
                    reasoning_effort=settings.DEFAULT_REASONING_EFFORT,
                    seed=settings.DEFAULT_SEED,
                    use_cache=settings.DEFAULT_VLM_USE_CACHE,
                ),
                voice=VoiceConfig(
                    model_id=settings.DEFAULT_VOICE_MODEL_ID,
                    prompt_file=settings.DEFAULT_VOICE_PROMPT_FILE,
                    whisper_model=settings.DEFAULT_WHISPER_MODEL,
                    temperature=settings.DEFAULT_VOICE_TEMPERATURE,
                    max_tokens=settings.DEFAULT_VOICE_MAX_TOKENS,
                    seed=settings.DEFAULT_SEED,
                ),
                search=SearchConfig(
                    stage1_top_k=settings.DEFAULT_STAGE1_TOP_K,
                    bm25_weight=settings.DEFAULT_BM25_WEIGHT,
                    vector_weight=settings.DEFAULT_VECTOR_WEIGHT,
                    rrf_k=settings.DEFAULT_RRF_K,
                    rrf_weight=settings.DEFAULT_RRF_WEIGHT,
                    embedding_instruction=settings.DEFAULT_EMBEDDING_INSTRUCTION,
                ),
                reranker=RerankerConfig(
                    model=settings.DEFAULT_RERANKER_MODEL,
                    instruction=settings.DEFAULT_RERANKER_INSTRUCTION,
                    top_n=settings.DEFAULT_RERANKER_TOP_N,
                ),
                runtime=RuntimeConfig(
                    device=settings.DEFAULT_DEVICE,
                ),
            )
        except Exception as e:
            logger.warning(
                f"Failed to load from settings, using hardcoded defaults: {e}"
            )
            return APIConfig()

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        if self._cache is None:
            return False
        return (time.time() - self._cache_timestamp) < self.cache_ttl_seconds

    def get_config(self, force_refresh: bool = False) -> APIConfig:
        """
        Get current configuration (with caching)

        Args:
            force_refresh: Force reload from Firestore, ignoring cache

        Returns:
            Current APIConfig
        """
        if not force_refresh and self._is_cache_valid():
            return self._cache

        if self.use_firestore and self._firestore_client:
            try:
                doc_ref = self._firestore_client.collection(
                    self.COLLECTION_NAME
                ).document(self.DOCUMENT_ID)
                doc = doc_ref.get()

                if doc.exists:
                    data = doc.to_dict()
                    self._cache = APIConfig(**data)
                    self._cache_timestamp = time.time()
                    logger.debug("Configuration loaded from Firestore")
                else:
                    # Document doesn't exist, create with defaults
                    self._cache = self._load_defaults_from_settings()
                    self._save_to_firestore(self._cache)
                    self._cache_timestamp = time.time()
                    logger.info("Created default configuration in Firestore")

            except Exception as e:
                logger.error(f"Firestore read error: {e}")
                if self._cache is None:
                    self._cache = self._load_defaults_from_settings()
                    self._cache_timestamp = time.time()
        else:
            # In-memory mode - cache is always valid
            if self._cache is None:
                self._cache = self._load_defaults_from_settings()
            self._cache_timestamp = time.time()

        return self._cache

    def detect_config_drift(self) -> Dict[str, Any]:
        """Compare the SERVED (persisted) config against the code defaults.

        get_config() returns the persisted Firestore doc verbatim and only seeds
        defaults on a MISSING doc, so a doc written under an older default keeps
        serving stale values forever (e.g. prod serving an old prompt while the
        code default and the benchmarked baseline have moved on). This surfaces
        that mismatch for /health and ops, instead of relying on manual checks.

        Returns:
            {"drift": bool, "fields": {field: {"served": ..., "default": ...}}}
        """
        served = self.get_config()
        defaults = self._load_defaults_from_settings()
        checks = {
            "vlm.model_id": (served.vlm.model_id, defaults.vlm.model_id),
            "vlm.prompt_file": (served.vlm.prompt_file, defaults.vlm.prompt_file),
            # A server-side prompt_text override silently wins over prompt_file,
            # so flag it explicitly (the most dangerous drift case).
            "vlm.prompt_text_active": (
                served.vlm.prompt_text is not None,
                defaults.vlm.prompt_text is not None,
            ),
            # F1-f: drift must also cover retrieval/reranker/self-consistency, since
            # these silently change benchmarked accuracy/latency just like the prompt.
            "vlm.self_consistency_k": (
                served.vlm.self_consistency_k,
                defaults.vlm.self_consistency_k,
            ),
            "reranker.model": (served.reranker.model, defaults.reranker.model),
            "search.bm25_weight": (
                served.search.bm25_weight,
                defaults.search.bm25_weight,
            ),
            "search.vector_weight": (
                served.search.vector_weight,
                defaults.search.vector_weight,
            ),
        }
        fields: Dict[str, Any] = {}
        for name, (served_value, default_value) in checks.items():
            if served_value != default_value:
                fields[name] = {"served": served_value, "default": default_value}
        return {"drift": bool(fields), "fields": fields}

    def _save_to_firestore(self, config: APIConfig) -> bool:
        """Save configuration to Firestore"""
        if not self.use_firestore or not self._firestore_client:
            return False

        try:
            doc_ref = self._firestore_client.collection(self.COLLECTION_NAME).document(
                self.DOCUMENT_ID
            )
            doc_ref.set(config.model_dump())
            return True
        except Exception as e:
            logger.error(f"Firestore write error: {e}")
            return False

    def update_config(
        self, updates: Dict[str, Any], updated_by: str = "admin"
    ) -> APIConfig:
        """
        Update configuration

        Args:
            updates: Dictionary of updates (supports nested keys like "vlm.temperature")
            updated_by: Who made the update

        Returns:
            Updated APIConfig
        """
        from datetime import datetime

        # Get current config
        current = self.get_config(force_refresh=True)
        current_dict = current.model_dump()

        # Apply updates
        for key, value in updates.items():
            keys = key.split(".")
            target = current_dict
            for k in keys[:-1]:
                target = target.setdefault(k, {})
            target[keys[-1]] = value

        # Add metadata
        current_dict["updated_at"] = datetime.utcnow().isoformat()
        current_dict["updated_by"] = updated_by

        # Create new config
        new_config = APIConfig(**current_dict)

        # Save to Firestore
        if self.use_firestore:
            self._save_to_firestore(new_config)

        # Update cache
        self._cache = new_config
        self._cache_timestamp = time.time()

        logger.info(f"Configuration updated by {updated_by}: {list(updates.keys())}")

        return new_config

    def reset_to_defaults(self, updated_by: str = "admin") -> APIConfig:
        """Reset configuration to defaults"""
        from datetime import datetime

        default_config = self._load_defaults_from_settings()
        default_dict = default_config.model_dump()
        default_dict["updated_at"] = datetime.utcnow().isoformat()
        default_dict["updated_by"] = updated_by

        new_config = APIConfig(**default_dict)

        if self.use_firestore:
            self._save_to_firestore(new_config)

        self._cache = new_config
        self._cache_timestamp = time.time()

        logger.info(f"Configuration reset to defaults by {updated_by}")

        return new_config

    def invalidate_cache(self):
        """Force cache invalidation"""
        self._cache_timestamp = 0
        logger.debug("Configuration cache invalidated")


# ========== Singleton accessor ==========


@lru_cache()
def get_config_manager() -> ConfigManager:
    """Get singleton ConfigManager instance"""
    return ConfigManager()
