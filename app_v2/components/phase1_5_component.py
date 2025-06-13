#!/usr/bin/env python3
"""
Phase1.5 Component - Alternative Query Generation

exact matchがなかった項目に対してGeminiで代替クエリを生成するコンポーネント
"""

import logging
from typing import Optional

from .base import BaseComponent
from ..models.phase1_5_models import Phase1_5Input, Phase1_5Output, AlternativeQuery
from ..services.gemini_service import GeminiService
from ..config import get_settings
from ..config.prompts.phase1_5_prompts import Phase1_5Prompts

logger = logging.getLogger(__name__)


class Phase1_5Component(BaseComponent[Phase1_5Input, Phase1_5Output]):
    """
    Phase1.5: 代替クエリ生成コンポーネント
    
    Phase1の結果と検索失敗情報を基に、Gemini AIを使用して
    より効果的な代替検索クエリを生成します。
    """
    
    def __init__(self, gemini_service: Optional[GeminiService] = None):
        super().__init__("Phase1_5Component")
        
        # GeminiServiceの初期化（既存のPhase1と同じ方法）
        if gemini_service is None:
            settings = get_settings()
            self.gemini_service = GeminiService(
                project_id=settings.GEMINI_PROJECT_ID,
                location=settings.GEMINI_LOCATION,
                model_name=settings.GEMINI_MODEL_NAME
            )
        else:
            self.gemini_service = gemini_service
    
    async def process(self, input_data: Phase1_5Input) -> Phase1_5Output:
        """
        Phase1.5の主処理: 代替クエリ生成
        
        Args:
            input_data: Phase1_5Input (image_bytes, phase1_result, failed_queries, etc.)
            
        Returns:
            Phase1_5Output: 生成された代替クエリのリスト
        """
        self.logger.info(f"Starting Phase1.5 alternative query generation")
        self.logger.info(f"Failed queries count: {len(input_data.failed_queries)}")
        self.logger.info(f"Iteration: {input_data.iteration}")
        
        # プロンプト生成
        system_prompt = Phase1_5Prompts.get_system_prompt()
        user_prompt = Phase1_5Prompts.get_user_prompt(
            phase1_result=input_data.phase1_result,
            failed_queries=input_data.failed_queries,
            failure_history=input_data.failure_history,
            iteration=input_data.iteration
        )
        
        self.log_prompt("phase1_5_system_prompt", system_prompt)
        self.log_prompt("phase1_5_user_prompt", user_prompt, {
            "failed_queries_count": len(input_data.failed_queries),
            "iteration": input_data.iteration,
            "has_failure_history": len(input_data.failure_history) > 0
        })
        
        # 画像情報のログ記録
        self.log_processing_detail("image_size_bytes", len(input_data.image_bytes))
        self.log_processing_detail("image_mime_type", input_data.image_mime_type)
        self.log_processing_detail("failed_queries", input_data.failed_queries)
        self.log_processing_detail("iteration", input_data.iteration)
        
        try:
            # Vertex AI Gemini APIを使用して代替クエリを生成
            self.log_processing_detail("gemini_phase1_5_api_call_start", "Calling Gemini API for alternative query generation")
            
            # GeminiServiceを使用してVertex AI経由で分析
            gemini_result = await self.gemini_service.analyze_phase1_5(
                image_bytes=input_data.image_bytes,
                image_mime_type=input_data.image_mime_type,
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )
            
            self.log_processing_detail("gemini_phase1_5_response", gemini_result)
            
            # 結果を解析してAlternativeQueryオブジェクトに変換
            alternative_queries = []
            
            if "alternative_queries" in gemini_result:
                for query_data in gemini_result["alternative_queries"]:
                    alternative_query = AlternativeQuery(
                        original_query=query_data.get("original_query", ""),
                        alternative_query=query_data.get("alternative_query", ""),
                        strategy=query_data.get("strategy", "unknown"),
                        reasoning=query_data.get("reasoning", ""),
                        confidence=query_data.get("confidence", 0.5)
                    )
                    alternative_queries.append(alternative_query)
            
            # 統計情報をログ記録
            self.log_processing_detail("generated_alternatives_count", len(alternative_queries))
            
            for i, alt_query in enumerate(alternative_queries):
                self.log_reasoning(
                    f"alternative_query_{i}",
                    f"Original: '{alt_query.original_query}' → Alternative: '{alt_query.alternative_query}' "
                    f"(Strategy: {alt_query.strategy}, Confidence: {alt_query.confidence:.2f})"
                )
            
            # Phase1_5Outputを作成
            output = Phase1_5Output(
                alternative_queries=alternative_queries,
                iteration=input_data.iteration,
                total_alternatives_generated=len(alternative_queries)
            )
            
            self.logger.info(f"Phase1.5 completed: Generated {len(alternative_queries)} alternative queries")
            return output
            
        except Exception as e:
            self.logger.error(f"Phase1.5 processing failed: {str(e)}")
            # エラーの場合は空の結果を返す
            return Phase1_5Output(
                alternative_queries=[],
                iteration=input_data.iteration,
                total_alternatives_generated=0
            )
    
