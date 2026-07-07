#!/usr/bin/env bash
#
# export_migration_bundle.sh — 【旧Mac側で実行】gitに乗らない資産を移行先へ書き出す
#
# git clone では移らない資産（FAISS/栄養辞書/ES DB/テスト画像/任意で.env）を、
# 外付けSSDや別Macの受け取りディレクトリへ repo 相対構造を保ったまま rsync する。
# 受け取り側は import コマンド（最後に表示）を実行すれば同じ配置に展開できる。
#
# 使い方:
#   bash scripts/export_migration_bundle.sh <DEST>            # 必須資産のみ
#   bash scripts/export_migration_bundle.sh <DEST> --with-db --with-images
#   bash scripts/export_migration_bundle.sh <DEST> --all      # 任意資産も全部
#   例: bash scripts/export_migration_bundle.sh /Volumes/EXTSSD/meal_migration --all
#
# フラグ:
#   --with-db       Elasticsearch DB (db/, ~498MB)
#   --with-images   テスト画像 (test_images*/, ~450MB)
#   --with-ab       実験用A/B FAISS (data/faiss_ab/, 739MB)
#   --with-evals    PDCA実行履歴 (evals/, 92MB)
#   --with-env      .env を含める【秘密情報】。外付けSSD等の安全経路のみで使うこと
#   --all           上記(env除く)を全部含める
#
# 注意: ~/.claude（グローバル設定/認証）と .env はデフォルトで含めない。
#       秘密・認証は安全な手段で別途運ぶ（docs/MACHINE_MIGRATION.md §4/§6-3）。
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
FREEFORM="apps/freeform_usda_meal_analysis_api"

ok()   { printf "  \033[32m✓\033[0m %s\n" "$1"; }
warn() { printf "  \033[33m!\033[0m %s\n" "$1"; }
err()  { printf "  \033[31m✗\033[0m %s\n" "$1"; }
hdr()  { printf "\n\033[1m== %s ==\033[0m\n" "$1"; }

if [[ $# -lt 1 ]]; then
  err "移行先ディレクトリを指定してください（例: /Volumes/EXTSSD/meal_migration）"
  echo "  使い方: bash scripts/export_migration_bundle.sh <DEST> [--all|--with-db --with-images --with-ab --with-evals --with-env]"
  exit 1
fi

DEST="$1"; shift
WITH_DB=0; WITH_IMAGES=0; WITH_AB=0; WITH_EVALS=0; WITH_ENV=0
for arg in "$@"; do
  case "$arg" in
    --with-db) WITH_DB=1 ;;
    --with-images) WITH_IMAGES=1 ;;
    --with-ab) WITH_AB=1 ;;
    --with-evals) WITH_EVALS=1 ;;
    --with-env) WITH_ENV=1 ;;
    --all) WITH_DB=1; WITH_IMAGES=1; WITH_AB=1; WITH_EVALS=1 ;;
    *) err "不明なフラグ: $arg"; exit 1 ;;
  esac
done

STAGE="$DEST/repo"
mkdir -p "$STAGE"

# rsync 1件: repo相対パス src を STAGE配下の同一相対位置へ
copy_rel() {
  local rel="$1" label="$2" required="$3"
  local src="$REPO/$rel"
  if [[ ! -e "$src" ]]; then
    if [[ "$required" == "req" ]]; then
      err "$label が旧機に無い（必須）: $rel"; return 1
    else
      warn "$label が旧機に無い（スキップ）: $rel"; return 0
    fi
  fi
  local dstdir="$STAGE/$(dirname "$rel")"
  mkdir -p "$dstdir"
  if [[ -d "$src" ]]; then
    rsync -ah --info=progress2 "$src/" "$STAGE/$rel/"
  else
    rsync -ah --info=progress2 "$src" "$STAGE/$rel"
  fi
  ok "$label → $rel"
}

hdr "0. 前提"
echo "  REPO = $REPO"
echo "  DEST = $DEST"
if [[ ! -f "$REPO/requirements.txt" ]]; then err "リポジトリ root で実行してください"; exit 1; fi
if [[ ! -d "$DEST" ]]; then err "移行先 $DEST が存在しません（外付けSSDがマウントされているか確認）"; exit 1; fi
ok "移行先を確認"

FAIL=0
hdr "1. 必須資産（freeform 起動に不可欠）"
copy_rel "$FREEFORM/data/faiss"                  "FAISSインデックス(274MB)" req || FAIL=1
copy_rel "$FREEFORM/data/normalized_portions.json" "栄養正規化辞書(8MB)"     req || FAIL=1

hdr "2. 任意資産（フラグ指定分のみ）"
[[ "$WITH_DB" == 1 ]]     && copy_rel "db"                      "Elasticsearch DB(498MB)" opt || [[ "$WITH_DB" == 1 ]] || warn "db/ 未指定（--with-db で含める）"
[[ "$WITH_IMAGES" == 1 ]] && { copy_rel "test_images" "テスト画像base" opt; \
   for d in test_images_jfb test_images_nvreal test_images_n5k; do [[ -e "$REPO/$d" ]] && copy_rel "$d" "テスト画像($d)" opt; done; } \
   || [[ "$WITH_IMAGES" == 1 ]] || warn "test_images*/ 未指定（--with-images で含める）"
[[ "$WITH_AB" == 1 ]]     && copy_rel "$FREEFORM/data/faiss_ab" "実験用A/B FAISS(739MB)" opt || [[ "$WITH_AB" == 1 ]] || warn "faiss_ab/ 未指定（--with-ab で含める）"
[[ "$WITH_EVALS" == 1 ]]  && copy_rel "$FREEFORM/evals" "PDCA履歴(92MB)" opt || [[ "$WITH_EVALS" == 1 ]] || warn "evals/ 未指定（--with-evals で含める）"

hdr "3. 秘密情報(.env)"
if [[ "$WITH_ENV" == 1 ]]; then
  if [[ -f "$REPO/.env" ]]; then
    rsync -ah "$REPO/.env" "$STAGE/.env"
    warn ".env を含めました【秘密情報】。この媒体は安全に扱い、転送後は媒体から削除すること"
  else
    warn ".env が旧機に無い"
  fi
else
  warn ".env は含めていません（--with-env で含められるが、原則は安全経路で別途転送）"
fi
warn "~/.claude（グローバル設定/認証）はこのスクリプト対象外 → docs §6-3 で別途コピー"

hdr "4. マニフェスト出力"
MANIFEST="$DEST/MIGRATION_MANIFEST.txt"
{
  echo "meal_analysis_api_2 移行バンドル"
  echo "生成元REPO: $REPO"
  echo "内容(du):"
  du -sh "$STAGE"/* 2>/dev/null || true
} > "$MANIFEST"
ok "マニフェスト: $MANIFEST"

hdr "完了 — 受け取り側(新Mac)での展開コマンド"
cat <<EOF
新Mac側で、先に git clone を済ませてから以下を実行（DEST を新Mac視点のパスに読み替え）:

  REPO=\$HOME/meal_analysis_api_2
  DEST="$DEST"          # 外付けSSDを新Macにマウントしたパス
  rsync -ah --info=progress2 "\$DEST/repo/" "\$REPO/"

その後:
  cd \$REPO && bash scripts/setup_new_machine.sh

.env と ~/.claude は §4 / §6-3 に従い別途安全に転送してください。
EOF

if [[ "$FAIL" -ne 0 ]]; then
  err "必須資産のコピーに失敗があります（上記 ✗ を確認）"; exit 1
fi
