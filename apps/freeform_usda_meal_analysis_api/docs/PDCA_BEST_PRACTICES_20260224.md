# Prompt/Model PDCA Best Practices (as of 2026-02-24)

このドキュメントは、`apps/freeform_usda_meal_analysis_api` で
VLMモデル・プロンプトを継続改善するための実運用ガイド。

## 1. Latest External References
- OpenRouter Models API: https://openrouter.ai/api/v1/models
- OpenRouter Docs (Models): https://openrouter.ai/docs/api-reference/models/get-a-list-of-models
- OpenRouter Docs (Reasoning): https://openrouter.ai/docs/use-cases/reasoning-tokens
- OpenRouter Docs (Prompt Caching): https://openrouter.ai/docs/features/prompt-caching
- OpenAI Evals design guide: https://platform.openai.com/docs/guides/evals-design
- OpenAI Prompting guide: https://platform.openai.com/docs/guides/text
- OpenAI Reasoning best practices: https://platform.openai.com/docs/guides/reasoning-best-practices
- OpenAI Image understanding: https://platform.openai.com/docs/guides/images-vision
- Anthropic Claude prompting overview: https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview
- Anthropic Evaluate Claude's performance: https://docs.anthropic.com/en/docs/test-and-evaluate/evaluate-your-prompts
- Anthropic Reduce hallucinations: https://docs.anthropic.com/en/docs/test-and-evaluate/strengthen-guardrails/reduce-hallucinations
- Gemini Prompt guide: https://ai.google.dev/gemini-api/docs/prompting-intro
- Gemini Prompt gallery (multimodal examples): https://ai.google.dev/gemini-api/prompts

## 2. Principles to Apply Here
1. Eval-first development
- 先に評価指標と採用条件を固定してから、プロンプト/モデルを変更する。
- 単発の成功例ではなく、固定50画像セットで判定する。
- 採用ゲートは `required_image_count` を満たす run のみ対象（部分runは hold）。
- `failure_count == 0` / `coverage_complete == true` を採用の前提条件にする。

2. Structured output discipline
- モデル出力は厳密JSONを要求し、パース失敗を明示的にエラー化する。
- JSON cleanupは最小限にとどめ、異常系を必ず記録する。

3. Reasoning control for stability
- thinking可能モデルは `reasoning_effort` を固定（default: `medium`）し、run間ぶれを減らす。
- 温度・トークン上限をrun内で固定し、比較軸を1つずつ変える。

4. Cost and latency as first-class metrics
- 精度だけでなく `avg_cost_usd`, `avg_latency_sec` を必須指標にする。
- 高価モデルは「改善幅が十分なときのみ採用」のゲートを適用する。

5. Prompt caching and reproducibility
- 同一長文プロンプトを多用する検証では、キャッシュ可能な経路を優先する。
- 実験設定JSON・結果JSON・失敗学習メモを同じrunディレクトリで紐づける。
- ただし精度比較runは `use_vlm_cache=false` を原則とし、キャッシュ混入を防ぐ。

6. Anti-overfitting discipline
- promptに評価データ固有情報（`test_foodXX`, label値, ground truth）を含めない。
- チューニング中は `dev` split で探索し、昇格判定は full50 で実施する。
- holdout split を定期ローテーションして、固定subsetへの過適合を抑える。

## 3. Recommended Model Selection Policy
1. Discovery
- `sync_openrouter_candidates.py` で最新モデル一覧から候補抽出。
- 条件: `image` 対応、価格上限内、必要なら `thinking-only`。

2. Candidate tiers
- Tier A (accuracy): 高精度候補（例: GPT-5.1, Gemini 3.1 Proなど）
- Tier B (balanced): 価格と精度のバランス（例: Gemini 3 Flash, Qwen3-VL-30B Thinking）
- Tier C (budget): 低コスト候補（例: GPT-5 miniなど）

3. Promotion gate
- MAE 1.0pt以上改善
- 30%超誤差率が悪化しない
- レイテンシ +20%以内
- 画像あたり平均コストが予算内

## 4. Repo-level Workflow
1. `evals/configs/*.json` を更新
2. `python -m apps.freeform_usda_meal_analysis_api.scripts.run_pdca_batch_eval ...`
3. 分割runの場合は `python -m ...scripts.merge_pdca_runs --runs ...` で正式統合
4. `evals/runs/<timestamp>/summary.md` を確認
5. 採用時のみ baseline を更新
6. `evals/lessons/` に知見記録
7. `python -m ...scripts.export_pdca_knowledge` で構造化ログを更新

## 4.1 Suggested Splits
- `evals/splits/dev_40_v1.txt`
- `evals/splits/holdout_10_v1.txt`
- 探索は dev を主に使い、採用判定は full50 + stability を必須にする。

## 5. Notes
- OpenRouter model catalogは頻繁に更新されるため、候補は固定リストでなく定期同期する。
- 2026-02-24 時点の方針として、価格上限を設けた thinking 対応モデル群を母集団にする。
