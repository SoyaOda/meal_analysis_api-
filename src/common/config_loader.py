"""
設定ローダーユーティリティ

YAML設定ファイルと環境変数の統合
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigLoader:
    """設定ローダークラス"""
    
    @staticmethod
    def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        設定ファイルをロードし環境変数と統合
        
        Args:
            config_path: 設定ファイルパス（None の場合はデフォルト）
            
        Returns:
            Dict[str, Any]: 統合された設定
        """
        # デフォルト設定パス
        if not config_path:
            # プロジェクトルートの configs/main_config.yaml を探す
            current_dir = Path(__file__).parent.parent.parent
            config_path = current_dir / "configs" / "main_config.yaml"
        
        config_path = Path(config_path)
        
        # YAML設定ファイルのロード
        try:
            config = ConfigLoader._load_yaml_config(config_path)
            logger.info(f"Configuration loaded from: {config_path}")
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_path}: {e}")
            # デフォルト設定で続行
            config = ConfigLoader._get_default_config()
            logger.info("Using default configuration")
        
        # 環境変数の統合
        config = ConfigLoader._integrate_environment_variables(config)
        
        # 設定の検証
        ConfigLoader._validate_config(config)
        
        return config
    
    @staticmethod
    def _load_yaml_config(config_path: Path) -> Dict[str, Any]:
        """YAML設定ファイルをロード"""
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    @staticmethod
    def _integrate_environment_variables(config: Dict[str, Any]) -> Dict[str, Any]:
        """環境変数を設定に統合"""
        # API Keys
        usda_api_key = os.getenv("USDA_API_KEY")
        if usda_api_key:
            config.setdefault("DB_CONFIG", {}).setdefault("USDA", {})["USDA_API_KEY"] = usda_api_key
        
        # Google Credentials
        google_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if google_creds:
            config.setdefault("GOOGLE", {})["APPLICATION_CREDENTIALS"] = google_creds
        
        # Gemini設定
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if gemini_api_key:
            config.setdefault("GEMINI", {})["API_KEY"] = gemini_api_key
        
        gemini_model = os.getenv("GEMINI_MODEL")
        if gemini_model:
            config.setdefault("GEMINI", {})["MODEL"] = gemini_model
        
        # ログレベル
        log_level = os.getenv("LOG_LEVEL")
        if log_level:
            config["LOGGING_LEVEL"] = log_level
        
        # デバッグモード
        debug_mode = os.getenv("DEBUG_MODE")
        if debug_mode and debug_mode.lower() in ["true", "1", "yes"]:
            config["DEBUG"] = True
        
        logger.info("Environment variables integrated into configuration")
        return config
    
    @staticmethod
    def _validate_config(config: Dict[str, Any]):
        """設定の基本的な検証"""
        required_sections = ["DB_CONFIG", "IMAGE_PROCESSOR_CONFIG", "INTERPRETER_CONFIG", "CALCULATOR_CONFIG"]
        
        for section in required_sections:
            if section not in config:
                logger.warning(f"Required configuration section missing: {section}")
        
        # USDA API Key確認
        usda_config = config.get("DB_CONFIG", {}).get("USDA", {})
        if not usda_config.get("USDA_API_KEY"):
            logger.warning("USDA API Key not configured. Set USDA_API_KEY environment variable.")
        
        logger.info("Configuration validation completed")
    
    @staticmethod
    def _get_default_config() -> Dict[str, Any]:
        """デフォルト設定を返す"""
        return {
            "LOGGING_LEVEL": "INFO",
            "DEBUG": False,
            
            "IMAGE_PROCESSOR_CONFIG": {
                "MAX_IMAGE_SIZE_MB": 10,
                "ALLOWED_EXTENSIONS": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]
            },
            
            "DB_CONFIG": {
                "TYPE": "USDA",
                "DEFAULT_QUERY_STRATEGY": "default_usda_search_v1",
                "USDA": {
                    "USDA_API_BASE_URL": "https://api.nal.usda.gov/fdc/v1",
                    "TIMEOUT_SECONDS": 30
                }
            },
            
            "PROMPTS": {
                "default_usda_search_v1": "{food_name}",
                "usda_raw_food_search": "raw {food_name}",
                "usda_cooked_food_search": "cooked {food_name}"
            },
            
            "INTERPRETER_CONFIG": {
                "STRATEGY_NAME": "DefaultUSDA",
                "STRATEGY_CONFIGS": {
                    "DefaultUSDA": {
                        "NUTRIENT_MAP": {
                            "Protein": "PROTEIN",
                            "Total lipid (fat)": "TOTAL_FAT",
                            "Carbohydrate, by difference": "CARBOHYDRATE_BY_DIFFERENCE",
                            "Energy": "CALORIES"
                        },
                        "TARGET_UNITS": {
                            "PROTEIN": "g",
                            "TOTAL_FAT": "g",
                            "CARBOHYDRATE_BY_DIFFERENCE": "g",
                            "CALORIES": "kcal"
                        }
                    }
                }
            },
            
            "CALCULATOR_CONFIG": {
                "ROUNDING_PRECISION": 2,
                "ENABLE_DAILY_VALUES": False
            }
        }
    
    @staticmethod
    def setup_logging(config: Dict[str, Any]):
        """ログ設定をセットアップ"""
        log_level = config.get("LOGGING_LEVEL", "INFO")
        debug_mode = config.get("DEBUG", False)
        
        # ログレベル設定
        level = getattr(logging, log_level.upper(), logging.INFO)
        
        # フォーマット設定
        if debug_mode:
            log_format = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        else:
            log_format = '%(asctime)s - %(levelname)s - %(message)s'
        
        # ルートロガー設定
        logging.basicConfig(
            level=level,
            format=log_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # HTTPXログを抑制（API呼び出しのノイズを減らす）
        logging.getLogger("httpx").setLevel(logging.WARNING)
        
        logger.info(f"Logging configured: level={log_level}, debug={debug_mode}") 