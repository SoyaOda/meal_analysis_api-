"""
AI-powered Fallback Ingredient Matcher Component

AIを使用して、exact matchに失敗した食材名をデータベース候補にマッチングする
再利用可能なコンポーネントとして実装
"""

import httpx
import json
import re
from typing import List, Dict, Any
from pydantic import BaseModel

from shared.components.base import BaseComponent


class AIFallbackMatcherInput(BaseModel):
    """AIフォールバックマッチャーの入力"""
    failed_ingredients: List[str]  # 失敗した食材名のリスト
    database_candidates: List[str]  # データベースの候補名リスト


class AIFallbackMatcherOutput(BaseModel):
    """AIフォールバックマッチャーの出力"""
    matches: Dict[str, str]  # {失敗した食材名: マッチしたDB名}
    metadata: Dict[str, Any]  # 処理メタデータ


# フォールバックマッチング用のプロンプトテンプレート
FALLBACK_MATCHING_PROMPT = """あなたは食材名のマッチング専門家です。

AIが出力した食材名がデータベースで見つからなかったため、最も適切なデータベース内の食材名を見つける必要があります。

## 失敗した食材名
{failed_ingredients}

## データベース内の全食材名候補
{database_names}

## タスク
各失敗した食材名について、データベース内の食材名リストから**最も意味的に近い食材名を1つだけ**選んでください。

## 重要なルール
1. **必ずデータベースリストから選ぶこと** - 候補リスト以外の名前は絶対に使用不可
2. **完全一致を探すこと** - 失敗した名前と意味が完全に一致するものを優先
3. **文字列の差異を許容** - "or hamburger patty"などの追加説明がある場合、それを含む候補を選ぶ
4. **正確にコピーすること** - 選んだ食材名を1文字たりとも変更せずにそのままコピー

## 出力形式
以下のJSON形式で出力してください：

```json
{{
  "matches": [
    {{
      "failed_name": "失敗した食材名1",
      "matched_name": "データベース内の正確な食材名1",
      "reasoning": "マッチングの理由（1文で簡潔に）"
    }},
    {{
      "failed_name": "失敗した食材名2",
      "matched_name": "データベース内の正確な食材名2",
      "reasoning": "マッチングの理由（1文で簡潔に）"
    }}
  ]
}}
```

**重要**: matched_nameはデータベースリストから文字通り完全にコピーしてください。一切の変更を加えないこと。
"""


class AIFallbackMatcherComponent(BaseComponent[AIFallbackMatcherInput, AIFallbackMatcherOutput]):
    """
    AI-powered Fallback Ingredient Matcher

    DeepInfra APIを使用して、失敗した食材名をデータベース候補にマッチング
    他のフォールバック戦略と簡単に入れ替え可能な設計
    """

    def __init__(
        self,
        model: str = "google/gemma-3-27b-it",
        temperature: float = 0.5,
        timeout: float = 60.0,
        max_tokens: int = 4000
    ):
        """
        Args:
            model: 使用するAIモデル
            temperature: 生成の多様性（0.0-1.0）
            timeout: APIタイムアウト（秒）
            max_tokens: 最大トークン数
        """
        super().__init__("AIFallbackMatcherComponent")
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.logger.info(
            f"✅ AIFallbackMatcherComponent initialized "
            f"(model={model}, temperature={temperature})"
        )

    async def process(self, input_data: AIFallbackMatcherInput) -> AIFallbackMatcherOutput:
        """
        失敗した食材名をAIでマッチング

        Args:
            input_data: 失敗した食材名とDB候補のリスト

        Returns:
            マッチング結果
        """
        failed_ingredients = input_data.failed_ingredients
        database_candidates = input_data.database_candidates

        self.logger.info(
            f"Starting AI fallback matching for {len(failed_ingredients)} failed ingredients "
            f"against {len(database_candidates)} database candidates"
        )

        # 失敗した食材名をフォーマット
        failed_list = '\n'.join([f"{i+1}. {name}" for i, name in enumerate(failed_ingredients)])

        # データベース名をフォーマット
        db_list = '\n'.join([f"{i+1}. {name}" for i, name in enumerate(database_candidates)])

        # プロンプトを構築
        prompt = FALLBACK_MATCHING_PROMPT.format(
            failed_ingredients=failed_list,
            database_names=db_list
        )

        # DeepInfra APIを使用してマッチング
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    "https://api.deepinfra.com/v1/openai/chat/completions",
                    headers={"Content-Type": "application/json"},
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": self.temperature,
                        "max_tokens": self.max_tokens
                    }
                )
                response.raise_for_status()
                result = response.json()

                # レスポンスからテキストを抽出
                ai_response = result["choices"][0]["message"]["content"]
                self.logger.info(f"AI fallback response received: {ai_response[:500]}...")

                # JSONを抽出
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', ai_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = ai_response

                # JSONをパース
                matches_data = json.loads(json_str)

                # データベース名をセットに変換（高速検索用）
                database_names_set = set(database_candidates)

                # 結果を辞書に変換 + 検証
                result_dict = {}
                validated_count = 0
                partial_match_count = 0

                for match in matches_data.get("matches", []):
                    failed_name = match.get("failed_name")
                    matched_name = match.get("matched_name")
                    reasoning = match.get("reasoning", "")

                    if not failed_name or not matched_name:
                        continue

                    # 重要: AIが返したmatched_nameが実際にデータベースに存在するか検証
                    if matched_name in database_names_set:
                        result_dict[failed_name] = matched_name
                        validated_count += 1
                        self.logger.info(
                            f"  ✅ Matched '{failed_name}' -> '{matched_name}' (reason: {reasoning})"
                        )
                    else:
                        self.logger.warning(
                            f"  ❌ AI returned '{matched_name}' for '{failed_name}', "
                            f"but it does NOT exist in database!"
                        )
                        self.logger.warning(f"     Reason given: {reasoning}")

                        # DBに存在しない場合は部分一致で検索
                        partial_matches = [
                            name for name in database_candidates
                            if matched_name.lower() in name.lower() or name.lower() in matched_name.lower()
                        ]

                        if partial_matches:
                            best_match = partial_matches[0]
                            result_dict[failed_name] = best_match
                            partial_match_count += 1
                            self.logger.info(f"  🔍 Found partial match instead: '{best_match}'")
                        else:
                            self.logger.error(
                                f"  ⚠️  No similar match found for '{failed_name}', skipping..."
                            )

                self.logger.info(
                    f"AI fallback matching completed: {len(result_dict)}/{len(failed_ingredients)} matches found "
                    f"(validated={validated_count}, partial={partial_match_count})"
                )

                return AIFallbackMatcherOutput(
                    matches=result_dict,
                    metadata={
                        "total_failed": len(failed_ingredients),
                        "total_matched": len(result_dict),
                        "validated_matches": validated_count,
                        "partial_matches": partial_match_count,
                        "model_used": self.model,
                        "temperature": self.temperature
                    }
                )

        except Exception as e:
            error_msg = f"AI fallback matching failed: {str(e)}"
            self.logger.error(error_msg)
            # フォールバックが失敗した場合は空の結果を返す
            return AIFallbackMatcherOutput(
                matches={},
                metadata={
                    "total_failed": len(failed_ingredients),
                    "total_matched": 0,
                    "error": str(e),
                    "model_used": self.model
                }
            )
