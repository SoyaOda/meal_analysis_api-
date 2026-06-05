"""
Settings and configuration for Freeform USDA Meal Analysis API
"""

import os
from pathlib import Path
from functools import lru_cache
from typing import Optional
from dotenv import load_dotenv

# プロジェクトルートの.envファイルを自動的に読み込む
# Path: meal_analysis_api_2/.env
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"
if _ENV_FILE.exists():
    load_dotenv(_ENV_FILE)
else:
    # フォールバック: カレントディレクトリの.envを試行
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
        - モデル: Gemini 3 Flash Preview
        - プロンプト: v11b_component_density
        - 検索: Fullインデックスのみ使用
        """

        # ========== VLMモデル設定 ==========
        # デフォルト: Gemini 3 Flash Preview（2026-06-04, pro 採用を撤回し flash に復帰）。
        #   2026-06-03 に pro を採用候補としたが、独立 GT 検証で pro は calorie でも
        #   recognition でも flash への頑健な優位が無いと判明（calorie=3独立セットで符号flip、
        #   recognition=クリーンGT NVReal COCO で flash 82.5% > pro 80.6% recall）。frozen-50
        #   の pro 優位は GPT-5-pro 命名との一致度で実性能でなかった。同等精度なら ~1/3 コストの
        #   flash が合理的。詳細: docs/MOZU_MODEL_DECISION_20260603.md（冒頭 2026-06-04 最終結論）/
        #   evals/lessons/20260604_recognition_clean_gt_pro_no_edge_flash_cost_rational.md。
        self.DEFAULT_VLM_MODEL_ID = os.getenv(
            "VLM_MODEL_ID", "openrouter:google/gemini-3-flash-preview"
        )

        # デフォルト: v13 (= 本番稼働中のv11b+飲料対応。v11bとはcalorie MAE非劣性
        #   [paired 95%CI -4.73..+4.56, p=0.84, run 20260601_204037]。本番prompt_textを
        #   prompts/に保全しコード既定に昇格。本番prompt_file label修正はデプロイ後に実施)
        self.DEFAULT_PROMPT_FILE = os.getenv(
            "DEFAULT_PROMPT_FILE",
            "freeform_prompt_usda_format_ver_v13_beverage_subject_prodcapture_20260226.txt",
        )

        # プロンプトディレクトリ
        self.PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

        # VLMパラメータ設定（Gemini 3 Flash運用の安定値）
        # - 出力トークン数: 12288
        # - Temperature: 0.3
        self.DEFAULT_MAX_TOKENS = int(os.getenv("VLM_MAX_TOKENS", "12288"))
        self.DEFAULT_TEMPERATURE = float(os.getenv("VLM_TEMPERATURE", "0.3"))
        self.DEFAULT_SEED = int(os.getenv("VLM_SEED", "123456"))
        self.DEFAULT_VLM_USE_CACHE = (
            os.getenv("VLM_USE_CACHE", "true").lower() == "true"
        )

        # Reasoning Effort設定 (OpenRouter用)
        # minimal(10%), low(20%), medium(50%), high(80%), xhigh(95%)
        self.DEFAULT_REASONING_EFFORT = os.getenv("VLM_REASONING_EFFORT", "medium")

        # ========== VLM Provider API設定 ==========
        # DeepInfra API Key（デフォルトプロバイダー）
        self.DEEPINFRA_API_KEY = os.getenv("DEEPINFRA_API_KEY")
        if not self.DEEPINFRA_API_KEY:
            raise ValueError(
                "DEEPINFRA_API_KEY environment variable is required. "
                "USDA retrieval (embedding/reranker) depends on DeepInfra even when VLM uses OpenRouter."
            )

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
        self.USDA_INDEX_DIR = os.getenv("USDA_INDEX_DIR", str(self.DATA_DIR / "faiss"))

        # USDA Metadata ファイル (栄養素データを含む)
        self.USDA_METADATA_FILE = os.getenv(
            "USDA_METADATA_FILE", str(Path(self.USDA_INDEX_DIR) / "usda_metadata.json")
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
        self.DEFAULT_RRF_WEIGHT = float(os.getenv("RRF_WEIGHT", "0.55"))

        # Embedding Instruction（Qwen3-Embedding-8B用）
        # 短いクエリでも正しくUSDA食材にマッチさせるための指示
        self.DEFAULT_EMBEDDING_INSTRUCTION = os.getenv(
            "EMBEDDING_INSTRUCTION",
            "Match food names to USDA FoodData Central database entries for nutrition lookup",
        )

        # 検索結果数の設定
        self.DEFAULT_SEARCH_TOP_K = int(os.getenv("SEARCH_TOP_K", "100"))
        self.DEFAULT_SEARCH_STAGE1_TOP_K = int(os.getenv("SEARCH_STAGE1_TOP_K", "100"))
        # Cloud Run最適化設定
        # デフォルトをtrueに変更（本番環境で推奨、コールドスタート時間削減）
        self.PRELOAD_INDEXES_ON_STARTUP = (
            os.getenv("PRELOAD_INDEXES_ON_STARTUP", "true").lower() == "true"
        )

        # ========== Reranker設定 ==========
        # Embeddingモデル設定（E5: A/B のため env で差し替え可能に。
        # 既定は現行の Qwen3-Embedding-8B。query 側(usda_search)と DB 構築
        # (build_index_with_nutrition) の双方が必ず同じモデルを使うこと=index と
        # query の埋め込み空間を一致させるため。dim は埋め込みから自動。）
        # 既定 = light スタック（0.6B）。8B 比で calorie 非劣性（2 draw で wash）かつ
        # 埋め込み ~9× 低レイテンシ・28-31s serverless cold-start 解消（lesson
        # 20260604_e5e6_lightweight_embedding_reranker_ab / 20260605_cross_provider_*）。
        # NOTE: index(data/faiss) も同じ 0.6B(dim1024) でなければ dim mismatch。
        self.DEFAULT_EMBEDDING_MODEL = os.getenv(
            "EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-0.6B"
        )

        # Rerankerモデル設定
        # NOTE: このデフォルト値はFirestore ConfigManagerのフォールバックとして使用
        # 本番環境ではFirestore (Admin Panel) の設定が優先される
        # 既定 = 0.6B（4B 比で p90 tail 一貫改善・calorie 非劣性・安価/高速）。
        self.DEFAULT_RERANKER_MODEL = os.getenv(
            "RERANKER_MODEL", "Qwen/Qwen3-Reranker-0.6B"
        )

        # Reranker instruction (USDA食材マッチング用に最適化)
        self.DEFAULT_RERANKER_INSTRUCTION = os.getenv(
            "RERANKER_INSTRUCTION",
            """Match USDA food database entries that exactly match the query's food name, cooking/preparation method, and form.

Nutritional values (calories, protein, fat, carbs per 100g) vary significantly based on preparation method, so precise matching is essential for accurate nutrition calculation.

Examples:
- 'grilled chicken' → 'Chicken, grilled' NOT 'Chicken, raw'
- 'caesar salad' → 'Caesar salad, with romaine' NOT 'Caesar dressing'
- 'fried rice' → 'Rice, fried' NOT 'Rice, white, cooked'

Prioritize: Complete phrase match > Preparation method match > Ingredient name similarity""",
        )

        # Reranker top_n。**E7 採用(2026-06-05)**: top_n>1 で top-k density mixture
        # (E[kcal/100g] を rerank-softmax で混合) が有効化される。既定 5 は frozen-VLM A/B
        # で calorie MAE を robust に改善（draw#1 −4.0pt p=0.042 / draw#2 −2.1pt 同方向 /
        # k-sweep 単調改善、p90・high30 も改善。lesson 20260605_e7_*）。top_n=1 で従来 top-1。
        self.DEFAULT_RERANKER_TOP_N = (
            int(os.getenv("RERANKER_TOP_N", "0")) if os.getenv("RERANKER_TOP_N") else 5
        )

        # ========== Thinkingモデル推奨設定 ==========
        # Thinkingモデル使用時の推奨パラメータ
        self.THINKING_RECOMMENDED_TEMPERATURE = float(
            os.getenv("THINKING_RECOMMENDED_TEMP", "0.6")
        )
        self.THINKING_TOP_P = float(os.getenv("THINKING_TOP_P", "0.95"))
        self.THINKING_TOP_K = int(os.getenv("THINKING_TOP_K", "20"))

        # 通常モデル使用時のパラメータ
        self.NORMAL_MODEL_TOP_P = float(os.getenv("NORMAL_MODEL_TOP_P", "1.0"))

        # ========== Voice分析設定 ==========
        # Voice用LLM/VLMモデル（テキストモード）
        # デフォルト: OpenRouter GPT-5 Mini
        # VLMモデル（Qwen3-VL等）もテキストモードで使用可能
        self.DEFAULT_VOICE_MODEL_ID = os.getenv(
            "VOICE_MODEL_ID", "openrouter:openai/gpt-5-mini"
        )

        # Voice用プロンプトファイル
        self.DEFAULT_VOICE_PROMPT_FILE = os.getenv(
            "DEFAULT_VOICE_PROMPT_FILE", "freeform_voice_prompt_usda.txt"
        )

        # 音声認識設定
        self.DEFAULT_WHISPER_MODEL = os.getenv(
            "WHISPER_MODEL", "openai/whisper-large-v3-turbo"
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
        if len(prompt_filename) > 200 or "\n" in prompt_filename:
            raise ValueError(
                "Invalid prompt_path: expected a file name, but received text content.\n"
                "Please provide only the file name (e.g., 'freeform_prompt_usda_format_ver_v7_experimental_20251027.txt'),\n"
                "not the full prompt text.\n\n"
                f"Available prompts in {self.PROMPTS_DIR}:\n"
                + "\n".join(f"  - {p.name}" for p in self.PROMPTS_DIR.glob("*.txt"))
            )

        prompt_path = self.PROMPTS_DIR / prompt_filename

        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Prompt file not found: {prompt_path}\n"
                f"Available prompts in {self.PROMPTS_DIR}:\n"
                + "\n".join(f"  - {p.name}" for p in self.PROMPTS_DIR.glob("*.txt"))
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
        if len(prompt_filename) > 200 or "\n" in prompt_filename:
            raise ValueError(
                "Invalid voice prompt_path: expected a file name, but received text content.\n"
                "Please provide only the file name (e.g., 'freeform_voice_prompt_usda.txt'),\n"
                "not the full prompt text.\n\n"
                f"Available voice prompts in {self.PROMPTS_DIR}:\n"
                + "\n".join(
                    f"  - {p.name}" for p in self.PROMPTS_DIR.glob("*voice*.txt")
                )
            )

        prompt_path = self.PROMPTS_DIR / prompt_filename

        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Voice prompt file not found: {prompt_path}\n"
                f"Available prompts in {self.PROMPTS_DIR}:\n"
                + "\n".join(f"  - {p.name}" for p in self.PROMPTS_DIR.glob("*.txt"))
            )

        return str(prompt_path)


@lru_cache()
def get_settings() -> Settings:
    """設定のシングルトンインスタンスを取得"""
    return Settings()
