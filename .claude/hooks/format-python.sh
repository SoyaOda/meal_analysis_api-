#!/bin/bash
# PostToolUse hook (Write|Edit): 編集された Python ファイルを ruff で整形し、
# py_compile で構文チェックする（Boris式 検証ループの自動化）。
#
# - stdin から JSON を受け取り tool_input.file_path を取得する
# - 対象が *.py のときのみ実行する
# - 整形・構文チェックの失敗で編集をブロックはしない（PostToolUse は編集後に走るため）
# - 構文エラー時のみ additionalContext で Claude に警告を返す
set -u

input="$(cat)"

file_path="$(printf '%s' "$input" | python3 -c "import sys, json
try:
    data = json.load(sys.stdin)
    print((data.get('tool_input') or {}).get('file_path', ''))
except Exception:
    print('')" 2>/dev/null)"

case "$file_path" in
  *.py)
    [ -f "$file_path" ] || exit 0
    # 整形（ruff が無ければ黙ってスキップ）
    if command -v ruff >/dev/null 2>&1; then
      ruff format "$file_path" >/dev/null 2>&1 || true
    fi
    # 構文チェック（失敗時のみ JSON で警告を返す。json.dumps で安全にエスケープ）
    err="$(python3 -m py_compile "$file_path" 2>&1)"
    if [ -n "$err" ]; then
      FP="$file_path" ERR="$err" python3 -c "import os, json
msg = '⚠️ py_compile failed for %s: %s' % (os.environ['FP'], ' '.join(os.environ['ERR'].split())[:400])
print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PostToolUse', 'additionalContext': msg}}))"
    fi
    ;;
esac

exit 0
