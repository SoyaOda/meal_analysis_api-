"""
Settings and configuration for Freeform USDA Meal Analysis API
"""
import os
from pathlib import Path
from functools import lru_cache
from typing import Optional


class Settings:
    """API設定クラス（Fullインデックスのみ使用）"""

    def __init__(self):
        # プロジェクトルート
        self.PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

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
        - モデル: Qwen3-VL-30B-A3B-Thinking (30Bパラメータ)
        - プロンプト: v7_experimental
        - 検索: Fullインデックスのみ使用
        """

        # ========== VLMモデル設定 ==========
        # デフォルト: 30B Thinking モデル
        self.DEFAULT_VLM_MODEL_ID = os.getenv(
            "VLM_MODEL_ID",
            "Qwen/Qwen3-VL-30B-A3B-Thinking"
        )

        # デフォルト: v7_experimental プロンプト
        self.DEFAULT_PROMPT_FILE = os.getenv(
            "DEFAULT_PROMPT_FILE",
            "freeform_prompt_usda_format_ver_v7_experimental_20251027.txt"
        )

        # プロンプトディレクトリ
        self.PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

        # VLMトークン設定
        # Qwen3-VL-30B-A3B-Thinking推奨設定
        # - コンテキストウィンドウ: 256K (最大1Mまで拡張可能)
        # - 出力トークン数: 16384 (実際の上限はDeepInfra APIにより動的に制限される)
        # - Thinking Budget: 8192 (max_tokensの約半分を推論に使用)
        # - Temperature: 0.6 (Qwen公式推奨値。0.0は性能劣化と無限ループの原因となるため非推奨)
        self.DEFAULT_MAX_TOKENS = int(os.getenv("VLM_MAX_TOKENS", "16384"))
        self.DEFAULT_THINKING_BUDGET = int(os.getenv("VLM_THINKING_BUDGET", "8192"))  # max_tokensの約半分
        self.DEFAULT_TEMPERATURE = float(os.getenv("VLM_TEMPERATURE", "0.6"))  # Qwen公式推奨値
        self.DEFAULT_SEED = int(os.getenv("VLM_SEED", "123456"))

        # ========== DeepInfra API設定 ==========
        self.DEEPINFRA_API_KEY = os.getenv("DEEPINFRA_API_KEY")
        if not self.DEEPINFRA_API_KEY:
            raise ValueError("DEEPINFRA_API_KEY environment variable is required")

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

        # 検索結果数の設定
        self.DEFAULT_SEARCH_TOP_K = int(os.getenv("SEARCH_TOP_K", "100"))
        self.DEFAULT_SEARCH_STAGE1_TOP_K = int(os.getenv("SEARCH_STAGE1_TOP_K", "100"))

        # ========== Thinkingモデル推奨設定 ==========
        # Thinkingモデル使用時の推奨パラメータ
        self.THINKING_RECOMMENDED_TEMPERATURE = float(os.getenv("THINKING_RECOMMENDED_TEMP", "0.6"))
        self.THINKING_TOP_P = float(os.getenv("THINKING_TOP_P", "0.95"))
        self.THINKING_TOP_K = int(os.getenv("THINKING_TOP_K", "20"))

        # 通常モデル使用時のパラメータ
        self.NORMAL_MODEL_TOP_P = float(os.getenv("NORMAL_MODEL_TOP_P", "1.0"))

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
            FileNotFoundError: プロンプトファイルが存在しない場合
        """
        if prompt_filename is None:
            prompt_filename = self.DEFAULT_PROMPT_FILE

        prompt_path = self.PROMPTS_DIR / prompt_filename

        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Prompt file not found: {prompt_path}\n"
                f"Available prompts in {self.PROMPTS_DIR}:\n" +
                "\n".join(f"  - {p.name}" for p in self.PROMPTS_DIR.glob("*.txt"))
            )

        return str(prompt_path)

@lru_cache()
def get_settings() -> Settings:
    """設定のシングルトンインスタンスを取得"""
    return Settings()
