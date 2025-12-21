"""
Settings and configuration for Freeform USDA Meal Analysis API
"""
import os
from pathlib import Path
from functools import lru_cache
from typing import Optional
from dotenv import load_dotenv

# .envファイルを自動的に読み込む
load_dotenv()


class Settings:
    """API設定クラス（Fullインデックスのみ使用）"""

    def __init__(self):
        # プロジェクトルート
        self.PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

        # ========== 環境設定 ==========
        # ENVIRONMENT: "development" または "production"
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
        self.IS_PRODUCTION = self.ENVIRONMENT == "production"

        # 許可するオリジン（本番環境用）
        # カンマ区切りで複数指定可能: "https://app1.com,https://app2.com"
        self.ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")

        # API設定
        self.API_VERSION = "1.0.0"
        self.API_TITLE = "Freeform USDA Meal Analysis API"
        self.API_DESCRIPTION = """
        USDA FNDDSデータベースを使用した食事分析API

        ## 機能
        - 画像から食事を分析し栄養価を計算
        - 音声入力による食事分析
        - カスタマイズ可能なVLMモデル設定
        - 柔軟なプロンプト選択

        ## デフォルト設定
        - モデル: OpenRouter GPT-5.1
        - プロンプト: v7_experimental
        - 検索: Fullインデックスのみ使用
        """

        # ========== VLMモデル設定 ==========
        # デフォルト: OpenRouter GPT-5.1
        self.DEFAULT_VLM_MODEL_ID = os.getenv(
            "VLM_MODEL_ID",
            "openrouter:openai/gpt-5.1"
        )

        # デフォルト: v7_experimental with meal_title プロンプト
        self.DEFAULT_PROMPT_FILE = os.getenv(
            "DEFAULT_PROMPT_FILE",
            "freeform_prompt_usda_format_ver_v7_experimental_with_meal_title_20251207.txt"
        )

        # プロンプトディレクトリ
        self.PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

        # VLMトークン設定
        # Qwen3-VL-30B-A3B-Thinking推奨設定
        # - コンテキストウィンドウ: 256K (最大1Mまで拡張可能)
        # - 出力トークン数: 16384 (実際の上限はDeepInfra APIにより動的に制限される)
        # - Temperature: 0.6 (Qwen公式推奨値。0.0は性能劣化と無限ループの原因となるため非推奨)
        self.DEFAULT_MAX_TOKENS = int(os.getenv("VLM_MAX_TOKENS", "16384"))
        self.DEFAULT_TEMPERATURE = float(os.getenv("VLM_TEMPERATURE", "0.6"))  # Qwen公式推奨値
        self.DEFAULT_SEED = int(os.getenv("VLM_SEED", "123456"))

        # Reasoning Effort設定 (OpenRouter用)
        # minimal(10%), low(20%), medium(50%), high(80%), xhigh(95%)
        self.DEFAULT_REASONING_EFFORT = os.getenv("VLM_REASONING_EFFORT", "medium")

        # ========== VLM Provider API設定 ==========
        # DeepInfra API Key（デフォルトプロバイダー）
        self.DEEPINFRA_API_KEY = os.getenv("DEEPINFRA_API_KEY")
        if not self.DEEPINFRA_API_KEY:
            raise ValueError("DEEPINFRA_API_KEY environment variable is required")

        # Alibaba Cloud API Key（オプション）
        # provider:model_id形式で "alibaba:qwen-vl-plus" などを指定する場合に必要
        self.ALIBABA_API_KEY = os.getenv("ALIBABA_API_KEY")

        # OpenRouter API Key（オプション）
        # provider:model_id形式で "openrouter:qwen/qwen3-vl-235b-a22b-thinking" などを指定する場合に必要
        self.OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

        # ========== USDA検索設定 ==========
        # データディレクトリ（自己完結型）
        self.DATA_DIR = Path(__file__).parent.parent / "data"

        # FAISSインデックスディレクトリ（Fullインデックスのみ）
        self.USDA_INDEX_DIR = os.getenv(
            "USDA_INDEX_DIR",
            str(self.DATA_DIR / "faiss")
        )

        # USDA Metadata ファイル (栄養素データを含む)
        self.USDA_METADATA_FILE = os.getenv(
            "USDA_METADATA_FILE",
            str(Path(self.USDA_INDEX_DIR) / "usda_metadata.json")
        )

        # 検索設定デフォルト値（Fullインデックスのみ）
        # Stage1 FAISS検索で取得する候補数
        self.DEFAULT_STAGE1_TOP_K = int(os.getenv("STAGE1_TOP_K", "50"))

        # デバッグ情報として返す候補数（search()メソッドのtop_kパラメータ）
        self.DEFAULT_DEBUG_TOP_K = int(os.getenv("DEBUG_TOP_K", "50"))

        # コネクションエラー時のリトライ回数
        self.DEFAULT_MAX_RETRIES = int(os.getenv("MAX_RETRIES", "5"))

        # 計算デバイス設定
        self.DEFAULT_DEVICE = os.getenv("DEVICE", "cpu")

        # ========== ハイブリッド検索設定 ==========
        # BM25 + Vector検索の重み設定
        self.DEFAULT_BM25_WEIGHT = float(os.getenv("BM25_WEIGHT", "0.4"))
        self.DEFAULT_VECTOR_WEIGHT = float(os.getenv("VECTOR_WEIGHT", "0.6"))
        self.DEFAULT_RRF_K = int(os.getenv("RRF_K", "60"))
        # RRF融合スコアの重み（最終スコア計算時に使用）
        self.DEFAULT_RRF_WEIGHT = float(os.getenv("RRF_WEIGHT", "0.5"))

        # Embedding Instruction（Qwen3-Embedding-8B用）
        # 短いクエリでも正しくUSDA食材にマッチさせるための指示
        self.DEFAULT_EMBEDDING_INSTRUCTION = os.getenv(
            "EMBEDDING_INSTRUCTION",
            "Match food names to USDA FoodData Central database entries for nutrition lookup"
        )

        # 検索結果数の設定
        self.DEFAULT_SEARCH_TOP_K = int(os.getenv("SEARCH_TOP_K", "100"))
        self.DEFAULT_SEARCH_STAGE1_TOP_K = int(os.getenv("SEARCH_STAGE1_TOP_K", "100"))
        # Cloud Run最適化設定
        self.PRELOAD_INDEXES_ON_STARTUP = os.getenv("PRELOAD_INDEXES_ON_STARTUP", "false").lower() == "true"

        # ========== Reranker設定 ==========
        # Rerankerモデル設定
        self.DEFAULT_RERANKER_MODEL = os.getenv("RERANKER_MODEL", "Qwen/Qwen3-Reranker-8B")

        # Reranker instruction (USDA食材マッチング用に最適化)
        self.DEFAULT_RERANKER_INSTRUCTION = os.getenv(
            "RERANKER_INSTRUCTION",
            """Match USDA food database entries that exactly match the query's food name, cooking/preparation method, and form.

Nutritional values (calories, protein, fat, carbs per 100g) vary significantly based on preparation method, so precise matching is essential for accurate nutrition calculation.

Examples:
- 'grilled chicken' → 'Chicken, grilled' NOT 'Chicken, raw'
- 'caesar salad' → 'Caesar salad, with romaine' NOT 'Caesar dressing'
- 'fried rice' → 'Rice, fried' NOT 'Rice, white, cooked'

Prioritize: Complete phrase match > Preparation method match > Ingredient name similarity"""
        )

        # Reranker top_n (返す結果数、Noneの場合は全件)
        self.DEFAULT_RERANKER_TOP_N = int(os.getenv("RERANKER_TOP_N", "0")) if os.getenv("RERANKER_TOP_N") else None

        # ========== Thinkingモデル推奨設定 ==========
        # Thinkingモデル使用時の推奨パラメータ
        self.THINKING_RECOMMENDED_TEMPERATURE = float(os.getenv("THINKING_RECOMMENDED_TEMP", "0.6"))
        self.THINKING_TOP_P = float(os.getenv("THINKING_TOP_P", "0.95"))
        self.THINKING_TOP_K = int(os.getenv("THINKING_TOP_K", "20"))

        # 通常モデル使用時のパラメータ
        self.NORMAL_MODEL_TOP_P = float(os.getenv("NORMAL_MODEL_TOP_P", "1.0"))

        # ========== Voice分析設定 ==========
        # Voice用LLM/VLMモデル（テキストモード）
        # デフォルト: gemma-3-27b-it（軽量で高速なLLM）
        # VLMモデル（Qwen3-VL等）もテキストモードで使用可能
        self.DEFAULT_VOICE_MODEL_ID = os.getenv(
            "VOICE_MODEL_ID",
            "google/gemma-3-27b-it"
        )

        # Voice用プロンプトファイル
        self.DEFAULT_VOICE_PROMPT_FILE = os.getenv(
            "DEFAULT_VOICE_PROMPT_FILE",
            "freeform_voice_prompt_usda.txt"
        )

        # 音声認識設定
        self.DEFAULT_WHISPER_MODEL = os.getenv(
            "WHISPER_MODEL",
            "openai/whisper-large-v3-turbo"
        )

        # Voice用LLMパラメータ
        self.DEFAULT_VOICE_MAX_TOKENS = int(os.getenv("VOICE_MAX_TOKENS", "4096"))
        self.DEFAULT_VOICE_TEMPERATURE = float(os.getenv("VOICE_TEMPERATURE", "0.3"))

        # ========== Google Cloud設定 ==========
        self.GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")

        # ========== ログ設定 ==========
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    def get_prompt_path(self, prompt_filename: Optional[str] = None) -> str:
        """
        プロンプトファイルの絶対パスを取得

        Args:
            prompt_filename: プロンプトファイル名（Noneの場合はデフォルト）

        Returns:
            プロンプトファイルの絶対パス

        Raises:
            ValueError: プロンプトファイル名が不正な場合
            FileNotFoundError: プロンプトファイルが存在しない場合
        """
        if prompt_filename is None:
            prompt_filename = self.DEFAULT_PROMPT_FILE

        # バリデーション: ファイル名ではなくプロンプトテキストが渡された場合のチェック
        if len(prompt_filename) > 200 or '\n' in prompt_filename:
            raise ValueError(
                "Invalid prompt_path: expected a file name, but received text content.\n"
                "Please provide only the file name (e.g., 'freeform_prompt_usda_format_ver_v7_experimental_20251027.txt'),\n"
                "not the full prompt text.\n\n"
                f"Available prompts in {self.PROMPTS_DIR}:\n" +
                "\n".join(f"  - {p.name}" for p in self.PROMPTS_DIR.glob("*.txt"))
            )

        prompt_path = self.PROMPTS_DIR / prompt_filename

        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Prompt file not found: {prompt_path}\n"
                f"Available prompts in {self.PROMPTS_DIR}:\n" +
                "\n".join(f"  - {p.name}" for p in self.PROMPTS_DIR.glob("*.txt"))
            )

        return str(prompt_path)

    def get_voice_prompt_path(self, prompt_filename: Optional[str] = None) -> str:
        """
        Voice用プロンプトファイルの絶対パスを取得

        Args:
            prompt_filename: プロンプトファイル名（Noneの場合はデフォルト）

        Returns:
            プロンプトファイルの絶対パス

        Raises:
            ValueError: プロンプトファイル名が不正な場合
            FileNotFoundError: プロンプトファイルが存在しない場合
        """
        if prompt_filename is None:
            prompt_filename = self.DEFAULT_VOICE_PROMPT_FILE

        # バリデーション: ファイル名ではなくプロンプトテキストが渡された場合のチェック
        if len(prompt_filename) > 200 or '\n' in prompt_filename:
            raise ValueError(
                "Invalid voice prompt_path: expected a file name, but received text content.\n"
                "Please provide only the file name (e.g., 'freeform_voice_prompt_usda.txt'),\n"
                "not the full prompt text.\n\n"
                f"Available voice prompts in {self.PROMPTS_DIR}:\n" +
                "\n".join(f"  - {p.name}" for p in self.PROMPTS_DIR.glob("*voice*.txt"))
            )

        prompt_path = self.PROMPTS_DIR / prompt_filename

        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Voice prompt file not found: {prompt_path}\n"
                f"Available prompts in {self.PROMPTS_DIR}:\n" +
                "\n".join(f"  - {p.name}" for p in self.PROMPTS_DIR.glob("*.txt"))
            )

        return str(prompt_path)


@lru_cache()
def get_settings() -> Settings:
    """設定のシングルトンインスタンスを取得"""
    return Settings()
