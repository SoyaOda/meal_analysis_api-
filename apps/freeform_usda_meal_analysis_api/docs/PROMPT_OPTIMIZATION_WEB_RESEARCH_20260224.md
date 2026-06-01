# Prompt Optimization Web Research (Gemini 3 Flash)

- Date: 2026-02-24
- Scope: `openrouter:google/gemini-3-flash-preview` 用の画像解析プロンプト最適化

## Sources (primary docs)
- Google AI for Developers: Prompt design strategies  
  https://ai.google.dev/gemini-api/docs/prompting-strategies
- Google AI for Developers: Structured output  
  https://ai.google.dev/gemini-api/docs/structured-output
- Google AI for Developers: Image understanding  
  https://ai.google.dev/gemini-api/docs/image-understanding
- Google AI for Developers: Thinking  
  https://ai.google.dev/gemini-api/docs/thinking
- OpenRouter: Reasoning tokens  
  https://openrouter.ai/docs/use-cases/reasoning-tokens
- OpenRouter: Structured outputs  
  https://openrouter.ai/docs/features/structured-outputs

## Extracted best practices
1. 指示は具体的かつ明確にし、出力形式を厳密に指定する。  
2. 構造化出力では、キー順序や必須キーを安定させる。  
3. 画像解析では「何を見るか」を段階的に指示する（主成分→小物）。  
4. thinkingは品質向上に有効だが、推論量はレイテンシ/コストに影響するため制御する。  
5. JSONモードや構造化出力の制約は、可能ならAPI側でも適用する。

## How we mapped this to prompts
- `v9a`: compact + schema-first。最重要制約（JSON、キー順、必須項目）を先頭に集約。
- `v9b`: two-pass recall + weight guardrails。見落とし防止と過大重量の両方を抑える。
- 両者共通:
  - 「内部推論は可、出力はJSONのみ」を明示
  - USDA検索名を comma format で固定
  - weight現実性チェックを明示

## Initial experiment config
- `evals/configs/pdca_gemini_prompt_sweep_v9_20260224.json`
  - baseline: `v7`
  - candidates: `v9a`, `v9b`
  - model: Gemini 3 Flash only
