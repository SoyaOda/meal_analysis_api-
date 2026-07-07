#!/usr/bin/env bash
#
# setup_new_machine.sh — 別Mac移行時のワンショット・セットアップ検証スクリプト
#
# 前提: 先に (1) git clone, (2) 大容量資産の rsync 直接コピー を済ませておくこと。
#       このスクリプトは venv 再生成 / pip install / .env・資産の存在検証 / import スモーク を行う。
# 詳細手順: docs/MACHINE_MIGRATION.md
#
# 使い方:
#   cd <リポジトリroot>
#   bash scripts/setup_new_machine.sh
#
set -euo pipefail

# --- リポジトリ root を解決（このスクリプトの1つ上の階層） ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO"

PY_VERSION="3.9.6"
FREEFORM="apps/freeform_usda_meal_analysis_api"

# --- 出力ヘルパ ---
ok()   { printf "  \033[32m✓\033[0m %s\n" "$1"; }
warn() { printf "  \033[33m!\033[0m %s\n" "$1"; }
err()  { printf "  \033[31m✗\033[0m %s\n" "$1"; }
hdr()  { printf "\n\033[1m== %s ==\033[0m\n" "$1"; }

FAIL=0

hdr "0. リポジトリ確認"
echo "  REPO = $REPO"
if [[ ! -f "$REPO/requirements.txt" || ! -d "$REPO/apps" ]]; then
  err "リポジトリ root で実行されていません（requirements.txt / apps が見つからない）"
  exit 1
fi
ok "リポジトリ root を確認"

hdr "1. 前提ツール"
command -v git  >/dev/null 2>&1 && ok "git 有り" || { err "git が無い"; FAIL=1; }
command -v gcloud >/dev/null 2>&1 && ok "gcloud 有り" || warn "gcloud が無い（GCP操作/デプロイ/Nutrition5k取得に必要）"
command -v jq   >/dev/null 2>&1 && ok "jq 有り"  || warn "jq が無い（一部スクリプトで使用）"

# --- Python 3.9.6 の解決（pyenv 優先） ---
PYBIN=""
if [[ -x "$HOME/.pyenv/versions/$PY_VERSION/bin/python" ]]; then
  PYBIN="$HOME/.pyenv/versions/$PY_VERSION/bin/python"
  ok "pyenv $PY_VERSION を使用: $PYBIN"
elif command -v python3.9 >/dev/null 2>&1; then
  PYBIN="$(command -v python3.9)"
  warn "pyenv $PY_VERSION が無いため system python3.9 を使用: $PYBIN"
else
  err "Python 3.9 が見つからない。'pyenv install $PY_VERSION' を実行してください"
  FAIL=1
fi

hdr "2. venv 再生成 + pip install"
if [[ -n "$PYBIN" ]]; then
  if [[ -d "$REPO/venv" ]]; then
    warn "既存 venv/ が存在します。作り直す場合は削除してから再実行してください（そのまま利用します）"
  else
    "$PYBIN" -m venv "$REPO/venv"
    ok "venv 作成"
  fi
  # shellcheck disable=SC1091
  source "$REPO/venv/bin/activate"
  python -m pip install --upgrade pip >/dev/null
  ok "pip アップグレード"

  echo "  installing root requirements..."
  pip install -r requirements.txt >/dev/null
  ok "requirements.txt"

  if [[ -f "$FREEFORM/requirements.txt" ]]; then
    echo "  installing freeform requirements (torch/faiss 等・時間がかかります)..."
    pip install -r "$FREEFORM/requirements.txt" >/dev/null
    ok "$FREEFORM/requirements.txt"
  fi

  if [[ -f "requirements-barcode.txt" ]]; then
    pip install -r requirements-barcode.txt >/dev/null
    ok "requirements-barcode.txt"
  fi
else
  err "Python が解決できないため pip install をスキップ"
  FAIL=1
fi

hdr "3. import スモークテスト"
if [[ -n "$PYBIN" ]]; then
  if python -c "import faiss, torch, sentence_transformers, fastapi; print('ok')" >/dev/null 2>&1; then
    ok "faiss / torch / sentence_transformers / fastapi の import 成功"
  else
    err "主要ライブラリの import に失敗（freeform が動きません）"
    FAIL=1
  fi
fi

hdr "4. 秘密情報(.env)"
if [[ -f "$REPO/.env" ]]; then
  ok ".env 存在"
  # 主要キーが空でないかを（値を表示せず）確認
  for k in OPENROUTER_API_KEY GOOGLE_CLOUD_PROJECT; do
    if grep -qE "^${k}=.+" "$REPO/.env"; then
      ok "$k が設定済み"
    else
      warn "$k が未設定または空（.env を確認）"
    fi
  done
else
  warn ".env が無い → 'cp .env.example .env' して旧機の値を転記してください"
fi

hdr "5. 大容量ローカル資産（gitに入らない・rsync対象）"
check_path() {
  local p="$1" label="$2" required="$3"
  if [[ -e "$REPO/$p" ]]; then
    ok "$label 存在: $p"
  elif [[ "$required" == "req" ]]; then
    err "$label が無い（freeform に必須）: $p を rsync してください"
    FAIL=1
  else
    warn "$label が無い（任意）: $p"
  fi
}
check_path "$FREEFORM/data/faiss"                  "FAISSインデックス"     req
check_path "$FREEFORM/data/normalized_portions.json" "栄養正規化辞書"     req
check_path "db"                                    "Elasticsearch DB"      opt
check_path "test_images"                           "テスト画像(base)"      opt

hdr "6. Claude Code 設定"
[[ -f "$REPO/.claude/settings.json" ]]        && ok ".claude/settings.json（git管理）"         || warn ".claude/settings.json が無い"
[[ -f "$REPO/.claude/settings.local.json" ]]  && ok ".claude/settings.local.json（旧機からコピー済）" || warn ".claude/settings.local.json が無い → 旧機からコピー＆パス置換が必要（docs/MACHINE_MIGRATION.md §6-2）"
[[ -f "$HOME/.claude/CLAUDE.md" ]]            && ok "~/.claude/CLAUDE.md（グローバル指示）"     || warn "~/.claude/CLAUDE.md が無い → 旧機からコピー（§6-3）"

# settings.local.json に旧機パスが残っていないか
if [[ -f "$REPO/.claude/settings.local.json" ]] && grep -q "/Users/odasoya" "$REPO/.claude/settings.local.json" 2>/dev/null; then
  if [[ "$HOME" != "/Users/odasoya" ]]; then
    warn "settings.local.json に旧機パス '/Users/odasoya' が残存。§6-2 の sed 置換を実施してください"
  fi
fi

hdr "結果"
if [[ "$FAIL" -eq 0 ]]; then
  printf "\033[32mセットアップ検証: すべて必須項目 OK\033[0m（warn は任意/GCP系）\n"
  echo "次: docs/MACHINE_MIGRATION.md §8-9 でサーバ起動スモークを実施してください"
else
  printf "\033[31mセットアップ検証: 必須項目に問題あり（上記 ✗ を解消してください）\033[0m\n"
  exit 1
fi
