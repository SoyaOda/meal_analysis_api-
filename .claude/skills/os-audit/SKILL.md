---
name: os-audit
description: Self-check for the repo's development OS (ssot/DEVELOPMENT_OS.md). Run monthly, at wave boundaries, or whenever an SSOT pointer (branch, lessons INDEX, docs INDEX, dataset registry) looks stale or broken. Runs scripts/os_audit.py and proposes fixes; never applies changes on its own (propose-then-ratify).
when_to_use: Monthly cadence, wave/session boundaries, or when the user suspects a broken SSOT pointer (e.g. plans/current.md branch mismatch, missing lessons INDEX entry, dataset not found on this machine).
argument-hint: "[optional: --repo-root <path>]"
allowed-tools: Read, Edit, Bash
---

# os-audit — Development OS self-check

Runs the repo's self-check script and turns FAIL/WARN findings into a
Japanese summary plus concrete, user-approved fix proposals. Never edits
`ssot/`, gate values, or `.claude/` files on its own — those changes are
propose-then-ratify (`ssot/DEVELOPMENT_OS.md` §9).

## Steps

1. Run `python3 scripts/os_audit.py` (add `--repo-root <path>` only if not
   run from the repo root).
2. Summarize the full result in Japanese: for each check (a–h), state its
   PASS/WARN/FAIL status and a one-line plain-language explanation.
3. For every WARN/FAIL, propose a concrete fix:
   - **Mechanical regeneration only** (e.g. lessons INDEX stale — check b)
     may be applied automatically by running the regeneration command the
     script prints (e.g.
     `python -m apps.freeform_usda_meal_analysis_api.scripts.build_lessons_index`).
   - Anything touching `ssot/`, adoption-gate values, or `.claude/`
     (settings / hooks / skills / agents) is **propose-only**: describe the
     exact diff you would make and wait for the user to ratify it before
     touching the file.
4. After handling the findings, tell the user to record the outcome (what
   was auto-fixed, what is still pending owner approval) in the Session Log
   of the relevant app's `plans/current.md`.

## Principles

- This skill reports and proposes; it does not silently "fix" governance
  files.
- Never weaken an adoption gate or edit `ssot/*` as a side effect of running
  this skill.
- If `scripts/os_audit.py` exits non-zero (a FAIL is present), say so
  explicitly — do not downplay it as only a WARN.
