# Lesson: Self-verification 2nd pass IMPLEMENTED (opt-in, works mechanically) but a SAME-TIER verifier is ineffective — net conviction flat

- Date: 2026-06-02
- Built (opt-in, default OFF): a self-verification 2nd VLM pass. `vlm_service.verify_items` re-shows the image with the candidate food list and returns present/not_present/unsure per item; `apply_verification` drops items marked not_present (keeps unsure -> recall-safe; name mismatch keeps the item -> fail-safe). Wired through `pipeline.analyze_image` (Step 1.5, gated by `enable_self_verification`), the `/complete` router (`enable_self_verification` form field), and the eval harness (candidate/`build_candidate_list` flag). Verify prompt: `prompts/freeform_verify_pass_20260602.txt` (anti-overfit, generic). Tests: `test_self_verification.py` (4). NOT cached (verify is the experimental variable).
- Also fixed a harness whitelist bug: `build_candidate_list` dropped any config key not in its explicit allow-list, so the first A/B run silently never fired verify (0 firings). Added `enable_self_verification` to the allow-list.

## A/B (dev40, v13 single-pass vs v13+verify, SHARED generate via cache so verify is the only variable; judge sonnet-4.6 rubric v2, advisory)
| metric | v13_baseline | v13_verify |
|---|---|---|
| conviction | 32.08 | 32.11 |
| recognition | 2.175 | 2.237 |
| naming_db_match | 1.725 | 1.658 |
| hallucinated_items/img | 1.82 | 1.74 |
| missed_gt_items/img | 1.98 | 2.11 |
| per-dish hallucinated | 58 | 51 |
| n predicted dishes | 245 | 230 |
- Server log: the verify pass dropped only **7 items over 40 images (0.17/img)**.

## Findings
- **The mechanism works**: verify removed ~7 phantom dishes (per-dish hallucinated 58 -> 51, recognition 2.175 -> 2.237). But it is TINY.
- **A same-tier verifier (gemini-3-flash verifying gemini-3-flash) is too lenient**: it drops only 0.17 items/img while the generator invents ~1.5/img, because the verifier SHARES the generator's default-presence bias and rubber-stamps most phantoms (e.g. it removes an obvious phantom dressing but confirms phantom apples).
- **Net conviction is FLAT (32.08 vs 32.11)**, with a tiny hallucination drop offset by a tiny recall cost (missed 1.98 -> 2.11). The research's top precision lever is neutralized when the verifier is the same cheap model.

## Meta-finding (now very robust)
Across reranker-instruction, v16/v17 prompts, AND self-verification, **user-conviction sits at a ~32/100 ceiling for gemini-3-flash and NO inference-time lever using the same model moves it beyond n=40 judge noise.** The ceiling is recognition-capability-bound.

## Action / next
- **Keep the self-verification feature** (opt-in, default OFF, tested) — it is correct infrastructure and the substrate for the only promising variant: a STRONGER / more-skeptical verifier.
- The next experiment worth running: verify with a stronger model (e.g. gemini-3.1-pro) OR a harsher abstention prompt / drop_unsure=True, to see if a more skeptical verifier catches the phantoms the same-tier one rubber-stamps. (Needs a verify-model override; small addition.)
- Strategic: a non-marginal conviction gain likely requires a stronger GENERATOR model (gemini-3.1-pro, already shown to have a higher portion slope), not another inference-time patch on flash.

## Related
- [[20260602_v16_grounding_mixed_identity_helps_evidence_field_backfires]] / [[20260602_v17_describe_shape_identity_mild_win_near_noise]]
- [[20260602_reranker_instruction_was_inert_bug_fixed]]
- [[20260602_broad_vlm_sweep_thinking_helps_slope]] (gemini-3.1-pro has the best portion slope)
