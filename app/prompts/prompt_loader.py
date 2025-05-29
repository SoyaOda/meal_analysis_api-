"""
プロンプトファイルを読み込んで管理するモジュール
"""
import os
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class PromptLoader:
    """プロンプトファイルを読み込んで管理するクラス"""
    
    def __init__(self, prompts_dir: Optional[str] = None):
        """
        初期化
        
        Args:
            prompts_dir: プロンプトファイルが格納されているディレクトリパス
                        Noneの場合は現在のファイルと同じディレクトリを使用
        """
        if prompts_dir is None:
            self.prompts_dir = Path(__file__).parent
        else:
            self.prompts_dir = Path(prompts_dir)
        
        # プロンプトをキャッシュ
        self._prompt_cache = {}
    
    def _load_prompt_file(self, filename: str) -> str:
        """
        プロンプトファイルを読み込む
        
        Args:
            filename: プロンプトファイル名
            
        Returns:
            プロンプトの内容
            
        Raises:
            FileNotFoundError: ファイルが見つからない場合
            IOError: ファイル読み込みエラー
        """
        if filename in self._prompt_cache:
            return self._prompt_cache[filename]
        
        file_path = self.prompts_dir / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            self._prompt_cache[filename] = content
            logger.debug(f"Loaded prompt file: {filename}")
            return content
        
        except Exception as e:
            logger.error(f"Error loading prompt file {filename}: {e}")
            raise IOError(f"Failed to load prompt file {filename}: {e}") from e
    
    def get_phase1_system_prompt(self) -> str:
        """フェーズ1のシステムプロンプトを取得"""
        return self._load_prompt_file("phase1_system_prompt.txt")
    
    def get_phase1_user_prompt(self, optional_text: Optional[str] = None) -> str:
        """
        フェーズ1のユーザープロンプトを取得
        
        Args:
            optional_text: オプションのテキスト
            
        Returns:
            フォーマット済みのユーザープロンプト
        """
        template = self._load_prompt_file("phase1_user_prompt_template.txt")
        
        if optional_text and optional_text.strip():
            optional_text_section = f" Additional information from user: {optional_text}"
        else:
            optional_text_section = ""
        
        return template.format(optional_text_section=optional_text_section)
    
    def get_phase2_system_prompt(self) -> str:
        """フェーズ2のシステムプロンプトを取得"""
        return self._load_prompt_file("phase2_system_prompt.txt")
    
    def get_phase2_user_prompt(
        self, 
        initial_ai_output: str,
        usda_candidates: str
    ) -> str:
        """
        フェーズ2のユーザープロンプトを取得
        
        Args:
            initial_ai_output: フェーズ1のAI出力（JSON文字列）
            usda_candidates: USDA候補情報
            
        Returns:
            フォーマット済みのユーザープロンプト
        """
        template = self._load_prompt_file("phase2_user_prompt_template.txt")
        
        return template.format(
            initial_ai_output=initial_ai_output,
            usda_candidates=usda_candidates
        )
    
    def reload_prompts(self):
        """プロンプトキャッシュをクリアして再読み込みを促す"""
        self._prompt_cache.clear()
        logger.info("Prompt cache cleared. Prompts will be reloaded on next access.") 