# 別PC移行ガイド（macOS）— meal_analysis_api_2

このリポジトリ（6つのAPIアプリを含む monorepo）と **Claude Code 開発環境一式** を別の Mac に丸ごと引き継ぐための完全手順。
対象OS: **macOS**（Apple Silicon / Intel）。大容量資産は **旧機からの直接コピー（rsync / 外付けSSD）** を前提とする。

> 一言まとめ: **①コードは git clone、②Python環境は venv 再生成、③Claude Code 設定は `~/.claude` を手動コピー、④秘密情報(.env)は手動転記、⑤gitに入らない大容量資産(~2GB)は rsync 直接コピー**。この5つが揃えば旧機と同じ状態になる。

---

## 0. 移行対象の全体像（何を移すか）

| 区分 | 対象 | 移行方法 | 必須 |
|------|------|----------|------|
| コード本体 | GitHub `SoyaOda/meal_analysis_api-` | `git clone` | ✅ |
| Python 依存 | `venv/`（約1.3GB） | **再生成**（`pip install`） | ✅ |
| 秘密情報 | リポジトリ root `.env` | **手動転記**（値はコピペ） | ✅ |
| Claude Code プロジェクト設定 | `.claude/settings.local.json` 等 | git clone + パス置換 | ✅ |
| Claude Code グローバル設定 | `~/.claude/`（CLAUDE.md, commands, agents, memory） | **手動コピー** | ✅ |
| FAISS インデックス | `apps/freeform_usda_meal_analysis_api/data/faiss/`(274MB) | **rsync 直接コピー** | ✅(freeform) |
| 栄養正規化辞書 | `.../data/normalized_portions.json`(8MB) | rsync | ✅(freeform) |
| Elasticsearch DB | `db/`（498MB） | rsync（または再構築） | ✅(ES系アプリ) |
| テスト画像セット | `test_images*/`（~450MB） | rsync | 評価する場合 |
| PDCA 実行履歴 | `.../evals/`（92MB） | git clone で入るもの＋ローカル run | 履歴が必要なら |
| gcloud SDK / 認証 | `~/google-cloud-sdk` + ADC | **新規インストール＆再ログイン** | GCP操作する場合 |

---

## 1. 前提ツールのインストール（新Mac側）

```bash
# Homebrew（未導入なら）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 基本ツール
brew install git jq

# Python 3.9.6（pyenv 経由推奨。旧機は pyenv 3.9.6 を使用）
brew install pyenv
pyenv install 3.9.6

# Google Cloud SDK（GCP操作/デプロイ/Nutrition5k取得に必要）
brew install --cask google-cloud-sdk
# → 旧機は ~/google-cloud-sdk/bin/gcloud に配置。settings.local.json がこのパスを参照するため
#   新機でパスが異なる場合は後述「§6 パス置換」で修正すること。

# Claude Code CLI（本開発環境の中核）
npm install -g @anthropic-ai/claude-code   # または公式手順に従う
```

> **Elasticsearch** はローカルで ES 系アプリ（word_query / meal_analysis / usda_*）を動かす場合のみ必要。freeform_usda（mozu）は FAISS ベースで ES 不要。必要なら `brew install elasticsearch` 等で用意し `http://localhost:9200` で起動する。

---

## 2. コードの取得

```bash
git clone https://github.com/SoyaOda/meal_analysis_api-.git ~/meal_analysis_api_2
cd ~/meal_analysis_api_2

# 旧機の作業ブランチに合わせる（例）
git checkout main   # または旧機で作業中のブランチ
```

> **パス方針**: 旧機は `/Users/odasoya/meal_analysis_api_2`。新機のユーザー名が異なる場合、`$HOME/meal_analysis_api_2` に置き、後述の `PYTHONPATH` とスクリプト内絶対パスを新パスに合わせる。**ディレクトリ名にスペースを含めないこと**（旧機に残る `meal_analysis_api /venv` スペース入りパスは旧チェックアウトの遺物で、本移行では使わない）。

---

## 3. Python 仮想環境の再生成

```bash
cd ~/meal_analysis_api_2

# pyenv の 3.9.6 で venv を作る
~/.pyenv/versions/3.9.6/bin/python -m venv venv
source venv/bin/activate
python -V   # Python 3.9.6 を確認

pip install --upgrade pip

# ルート依存（FastAPI / Elasticsearch / google-cloud 系 / OpenAI 等 23パッケージ）
pip install -r requirements.txt

# freeform_usda（mozu）依存（torch 2.1.2 / faiss-cpu / sentence-transformers / FlagEmbedding 等 49パッケージ）
pip install -r apps/freeform_usda_meal_analysis_api/requirements.txt

# barcode 専用（使う場合）
pip install -r requirements-barcode.txt

# 動作確認: freeform の要となる faiss が入っているか
python -c "import faiss, sentence_transformers, torch; print('faiss/st/torch OK')"
```

> Apple Silicon で `torch==2.1.2` / `faiss-cpu==1.7.4` は pip で導入可能。万一ビルド失敗する場合はエラーを確認し、該当バージョンの wheel 有無を調べる（**勝手に別バージョンへ上げない** — 依存追加・変更はオーナー確認事項）。

---

## 4. 秘密情報（.env）の転記

`.env` は **git 管理外**。

> ⚠️ **重要**: 追跡されているテンプレート `.env.example` は現行 `.env` より**キーが不足している**（`GEMINI_API_KEY`/`GOOGLE_API_KEY`/`OPENAI_API_KEY`/`DEEPINFRA_TOKEN`/`ELASTICSEARCH_URL`/`VLM_CACHE_DIR`/`USDA_INDEX_DIR` 等が雛形に無い）。**`.env.example` を鵜呑みにせず、旧機の実 `.env` を丸ごと安全転送するのが最も確実**。大容量資産を外付けSSD/rsyncで移すのと同じ経路で `.env` も運ぶ。

```bash
# 【推奨】旧機の実 .env を直接コピー（値ごと移る・キー漏れが無い）
#   外付けSSD経由、または安全な手段で:
scp "$OLD:/Users/odasoya/meal_analysis_api_2/.env" "$DST/.env"   # OLD/DST は §5 参照
# パス系キー（VLM_CACHE_DIR / USDA_INDEX_DIR / BM25_INDEX_PATH 等）だけ新機の絶対パスに直す

# 【フォールバック】実.env が手に入らない場合のみ雛形から再構成
cp .env.example .env
# → 下表を見ながら各サービスでキーを再発行して埋める（雛形に無いキーも下表で補う）
```

**必要なキー一覧（`.env.example` に無いものも含む完全版・これが正）:**

| キー | 用途 | 入手元 |
|------|------|--------|
| `OPENROUTER_API_KEY` | 採用モデル `openrouter:google/gemini-3-flash-preview`（必須） | openrouter.ai |
| `GEMINI_API_KEY` / `GOOGLE_API_KEY` | Google native Gemini | Google AI Studio / GCP Console |
| `DEEPINFRA_API_KEY` / `DEEPINFRA_TOKEN` | DeepInfra / Whisper 系 | deepinfra.com |
| `OPENAI_API_KEY` | OpenAI Whisper 等（任意） | platform.openai.com |
| `ALIBABA_API_KEY` / `NOVITA_API_KEY` / `SILICONFLOW_API_KEY` / `JINA_API_KEY` | 代替LLM/embeddingプロバイダ（任意） | 各サービス |
| `GOOGLE_CLOUD_PROJECT` | GCPプロジェクト = `new-snap-calorie`（固定） | 既定値 |
| `ELASTICSEARCH_URL` | ローカルES（`http://localhost:9200`） | ローカル |
| `USDA_INDEX_DIR` / `VLM_CACHE_DIR` / `BM25_INDEX_PATH` | ローカルパス系 | 新機パスに調整 |

> ⚠️ `.env` は **絶対にコミットしない**（`.gitignore` 済み）。`.claude/settings.json` の `permissions.deny` により Claude Code からの `.env` 読み取りも禁止されている。

---

## 5. gitに入らない大容量ローカル資産の直接コピー（rsync）

旧機と新機を同一LAN上に置くか、外付けSSD経由で以下を丸ごとコピーする。**FAISSインデックスと `normalized_portions.json` は freeform 起動に必須**（再構築はembedding再計算で長時間）。

> 💡 **旧機側で1コマンド書き出し**: `scripts/export_migration_bundle.sh` を使うと、必須資産（＋フラグ指定で任意資産）を移行先へ repo 相対構造を保って rsync し、受け取り側の展開コマンドまで表示する。
> ```bash
> # 旧機で: 外付けSSDへ必須＋任意資産を書き出し
> bash scripts/export_migration_bundle.sh /Volumes/EXTSSD/meal_migration --all
> # 新機で: git clone 後に展開
> rsync -ah --info=progress2 /Volumes/EXTSSD/meal_migration/repo/ ~/meal_analysis_api_2/
> ```
> 秘密情報 `.env`（`--with-env` で任意同梱）と `~/.claude` は対象外＝安全経路で別途運ぶ。

以下は手動 rsync の個別コマンド（上記スクリプトを使わない場合）。

```bash
# 旧機 → 新機（LAN経由 rsync の例。OLD=旧機ホスト, DST=新機の配置先）
OLD=odasoya@OLD-MAC.local
DST=~/meal_analysis_api_2

# ① FAISS インデックス（必須, 274MB） — freeform の検索コア
rsync -avh --progress \
  "$OLD:/Users/odasoya/meal_analysis_api_2/apps/freeform_usda_meal_analysis_api/data/faiss/" \
  "$DST/apps/freeform_usda_meal_analysis_api/data/faiss/"

# ② 栄養正規化辞書（必須, 8MB）
rsync -avh --progress \
  "$OLD:/Users/odasoya/meal_analysis_api_2/apps/freeform_usda_meal_analysis_api/data/normalized_portions.json" \
  "$DST/apps/freeform_usda_meal_analysis_api/data/"

# ③ Elasticsearch DB（ES系アプリを使うなら, 498MB）
rsync -avh --progress \
  "$OLD:/Users/odasoya/meal_analysis_api_2/db/" \
  "$DST/db/"

# ④ テスト画像セット（PDCA評価をするなら, ~450MB）
rsync -avh --progress \
  "$OLD:/Users/odasoya/meal_analysis_api_2/test_images/" \
  "$DST/test_images/"
# JFB / NVReal / N5K の外部評価セットも使うなら test_images_jfb/ test_images_nvreal/ test_images_n5k/ を同様に

# ⑤（任意）実験用A/B FAISS 739MB, PDCA履歴 evals/ 92MB, 分析結果 analysis_results/ 38MB
#   必要な場合のみ同様に rsync。faiss.zip(114MB) はバックアップなので通常不要。
```

**外付けSSD経由の場合**は、上記の各 `$OLD:...` パスから SSD へ `cp -R` し、新機で `$DST/...` へ展開する。

**再構築フォールバック**（直接コピーできない資産のみ）:
- FAISS: `python -m apps.freeform_usda_meal_analysis_api.scripts.build_index_with_nutrition`（embedding再計算あり・長時間）
- Nutrition5k 評価画像: `python -m apps.freeform_usda_meal_analysis_api.scripts.build_nutrition5k_evalset`（`gsutil` で `gs://nutrition5k_dataset` から取得）
- Elasticsearch DB: `scripts/` 配下のインデックス構築スクリプトで再構築可能

---

## 6. Claude Code 開発環境の移行

### 6-1. プロジェクト内設定（git clone で入る＝追跡済み）
git 追跡されているのは **以下4つのみ**（`git ls-files .claude/` で確認）:
- `CLAUDE.md` / `AGENTS.md`（ルート＋各アプリ）※`.claude/`外だが追跡
- `.claude/hooks/format-python.sh`（Write|Edit 後に `ruff format` + `py_compile`）
- `.claude/agents/pdca-runner.md`（PDCA隔離実行subagent）
- `.claude/skills/handoff/SKILL.md`（`/handoff` スキル）
- `.claude/scheduled_tasks.lock`

> ⚠️ これら追跡ファイルは、移行ガイドを含むブランチ（`docs/mozu-dataset-inventory-e13-uiux-handoff` 等）には存在するが、**古い作業ブランチ（例: `feature/admin-config-panel`）には無い**場合がある。その場合は取り込む:
> ```bash
> git checkout docs/mozu-dataset-inventory-e13-uiux-handoff -- .claude/agents .claude/hooks .claude/skills
> ```

### 6-2. プロジェクト内ローカル設定（git管理外・旧機から手動コピー必須）
**`.claude/settings.json` と `.claude/settings.local.json` はどちらも git 未追跡**（ローカル専用）。旧機から両方を手動コピーする。

- `settings.json`: PostToolUse フック定義（`ruff format`+`py_compile`）＋`.env` 読取禁止ルール。`$CLAUDE_PROJECT_DIR` 変数使用でパス非依存 → **コピーのみでOK（パス置換不要）**
- `settings.local.json`: 許可リスト約300行。旧機固有の絶対パスが埋まっているため **コピー後にパス置換が必要**

```bash
# 旧機から両ファイルをコピー（例）
scp "$OLD:/Users/odasoya/meal_analysis_api_2/.claude/settings.json"       .claude/
scp "$OLD:/Users/odasoya/meal_analysis_api_2/.claude/settings.local.json" .claude/

# settings.local.json のパスを新機に合わせる
#   /Users/odasoya                 → $HOME（新機ユーザー名が違う場合）
#   /Users/odasoya/google-cloud-sdk → 新機の gcloud SDK パス
#   /Users/odasoya/meal_analysis_api_2 → 新機のリポジトリパス
sed -i '' "s#/Users/odasoya#$HOME#g" .claude/settings.local.json
# gcloud パスが異なる場合は追加で置換
```

> `serena` MCP は settings.local.json の許可リスト定義のみで動く（別途の設定ファイル不要・Claude Code が自動認識）。

### 6-3. Claude Code グローバル設定（`~/.claude`・手動コピー）
プロジェクト外だが本開発環境の中核。旧機の以下を新機の `~/.claude/` へコピーする:

| パス | 内容 | 移行 |
|------|------|------|
| `~/.claude/CLAUDE.md` | グローバル指示（日本語応答/モデル委譲ポリシー等） | コピー |
| `~/.claude/commands/` | グローバルスキル（/analyze /commit /pr 等） | コピー |
| `~/.claude/agents/` | Explore / implementer / verifier | コピー |
| `~/.claude/projects/-Users-odasoya-meal-analysis-api-2/memory/` | プロジェクトメモリ（`freeform-local-eval-env.md` = ローカル実行の非自明設定） | コピー |

```bash
# 旧機から（rsync 例）。ただし ~/.claude 配下の認証トークン類は再ログインが安全
rsync -avh "$OLD:~/.claude/CLAUDE.md"   ~/.claude/
rsync -avh "$OLD:~/.claude/commands/"   ~/.claude/commands/
rsync -avh "$OLD:~/.claude/agents/"     ~/.claude/agents/
rsync -avh "$OLD:~/.claude/projects/-Users-odasoya-meal-analysis-api-2/memory/" \
          ~/.claude/projects/-Users-odasoya-meal-analysis-api-2/memory/
```

> Claude Code 本体のログイン（Anthropicアカウント）は新機で `claude` 起動時に再認証する。認証トークンはコピーせず再ログインが安全。
> メモリのプロジェクトキー `-Users-odasoya-meal-analysis-api-2` は旧ユーザー名 `odasoya` に紐づく。新機のユーザー名が異なると Claude Code が別キーで新規メモリディレクトリを作るため、その場合は新キー配下にコピーし直すこと。

---

## 7. GCP 認証（GCP操作/デプロイをする場合のみ）

```bash
gcloud auth login
gcloud config set project new-snap-calorie
gcloud auth application-default login   # ADC（ローカルからFirestore/GCS等にアクセスする場合）
```

- プロジェクト: `new-snap-calorie`（番号 `1077966746907`）
- Cloud Run SA: `meal-analysis-api@new-snap-calorie.iam.gserviceaccount.com`
- 本番 freeform サービス: `https://freeform-usda-meal-analysis-api-1077966746907.us-central1.run.app`
- サービスアカウント鍵JSONを使う場合のみ `.env` の `GOOGLE_APPLICATION_CREDENTIALS` にパス指定（通常は ADC 優先）

---

## 8. 起動確認（スモークテスト）

各アプリは `PYTHONPATH=<リポジトリ絶対パス>` 前提。以下は新機パスを `$HOME/meal_analysis_api_2` とした例。

```bash
export REPO=$HOME/meal_analysis_api_2
source $REPO/venv/bin/activate
```

| App | Port | 起動コマンド |
|-----|------|-------------|
| meal_analysis_api | 8001 | `PYTHONPATH=$REPO GOOGLE_CLOUD_PROJECT=new-snap-calorie PORT=8001 python -m apps.meal_analysis_api.main` |
| word_query_api | 8002 | `PYTHONPATH=$REPO PORT=8002 python -m apps.word_query_api.main` |
| barcode_api | 8003 | `PYTHONPATH=$REPO PORT=8003 python -m apps.barcode_api.main` |
| usda_word_query_api | 8004 | `PYTHONPATH=$REPO PORT=8004 python -m apps.usda_word_query_api.main` |
| usda_meal_analysis_api | 8005 | `PYTHONPATH=$REPO WORD_QUERY_API_URL=http://localhost:8004 INGREDIENT_ELASTICSEARCH_INDEX=usda_unified_nutrition_db NUTRITION_DATA_SOURCE=usda_api GOOGLE_CLOUD_PROJECT=new-snap-calorie PORT=8005 python -m apps.usda_meal_analysis_api.main` |
| freeform_usda_meal_analysis_api | 8006 | 下記「§9 freeform ローカル運用」参照 |

（出典: `docs/API_QUICKSTART.md`）

---

## 9. freeform_usda（mozu）ローカル運用の非自明ルール【重要】

freeform のサーバ/eval をローカルで動かす際は、以下を守らないと 401 や本番Firestore誤接続が起きる（プロジェクトメモリ `freeform-local-eval-env.md` 由来）。

**サーバ/eval/build 起動は必ず `env -u` で古い環境変数を落とす:**

```bash
export REPO=$HOME/meal_analysis_api_2
env -u OPENROUTER_API_KEY -u DEEPINFRA_API_KEY -u DEEPINFRA_TOKEN -u GOOGLE_CLOUD_PROJECT \
  PYTHONPATH=$REPO PORT=8006 \
  $REPO/venv/bin/python -m apps.freeform_usda_meal_analysis_api.main
```

理由:
- `OPENROUTER_API_KEY` / `DEEPINFRA_API_KEY` / `DEEPINFRA_TOKEN`: shell に古い無効キーが残ると `load_dotenv(override=False)` で `.env` の新キーが上書きされず **401**。
- `GOOGLE_CLOUD_PROJECT` を **unset 必須**: set のままだと ConfigManager が **本番 Firestore** へ接続を試み、本番config漏れ/ハングの原因。unset で in-memory 既定になる。
- **venv の python をフルパスで呼ぶ**（pyenv shim には faiss が無くサーバ/build が動かない）。

**PDCA セッション開始（毎回・精度改善に着手する前）:**

```bash
python -m apps.freeform_usda_meal_analysis_api.scripts.pdca_session_bootstrap \
  --api-url https://freeform-usda-meal-analysis-api-1077966746907.us-central1.run.app
# → evals/knowledge/session_bootstrap_latest.md を確認
```

**バッチ評価（原則50例フル・cache無効）:**

```bash
env -u OPENROUTER_API_KEY -u DEEPINFRA_API_KEY -u DEEPINFRA_TOKEN -u GOOGLE_CLOUD_PROJECT \
  PYTHONPATH=$REPO $REPO/venv/bin/python \
  -m apps.freeform_usda_meal_analysis_api.scripts.run_pdca_batch_eval \
  --config apps/freeform_usda_meal_analysis_api/evals/configs/pdca_gemini_prompt_sweep_v9_20260224.json \
  --api-url http://localhost:8006 --limit 50 --no-use-vlm-cache
```

- 採用モデル: **`openrouter:google/gemini-3-flash-preview`**（code既定・本番とも flash。pro は撤回済）
- 過学習防止: prompt に評価データ固有情報（画像id/label/GT）を埋め込まない
- 並列eval注意: run dir は秒単位timestamp → 同一秒に並列起動すると衝突。逐次 or 時間をずらす
- 引き継ぎSSOT: `apps/freeform_usda_meal_analysis_api/plans/current.md`（最初に読む）

詳細は各ドキュメント参照:
- `apps/freeform_usda_meal_analysis_api/docs/PDCA_SESSION_START_CHECKLIST.md`
- `apps/freeform_usda_meal_analysis_api/docs/MOZU_MODEL_DECISION_20260603.md`
- `apps/freeform_usda_meal_analysis_api/docs/MOZU_PDCA_COMPLETE_20260606.md`（最も詳しい総括）

---

## 10. 検証チェックリスト（新機セットアップ完了判定）

- [ ] `git clone` 済み・作業ブランチに切替済み
- [ ] `python3.9.6` で venv 作成、`pip install` 3ファイル完了
- [ ] `python -c "import faiss, torch, sentence_transformers"` が成功
- [ ] `.env` に全キー転記済み（最低 `OPENROUTER_API_KEY` / `GOOGLE_CLOUD_PROJECT`）
- [ ] `data/faiss/` と `data/normalized_portions.json` が存在（rsync 済み）
- [ ] ES系アプリを使うなら `db/` が存在 or ES 起動可能
- [ ] `.claude/settings.local.json` を旧機からコピー＆パス置換済み
- [ ] `~/.claude/`（CLAUDE.md/commands/agents/memory）をコピー済み
- [ ] freeform サーバが `§9` の起動コマンドで立ち上がり `/docs` が開く
- [ ] （GCP使うなら）`gcloud auth` / ADC 済み
- [ ] `scripts/setup_new_machine.sh` を実行し全チェックがgreen

---

## 付録: 自動セットアップスクリプト

`scripts/setup_new_machine.sh` を用意した。git clone と大容量資産の rsync **後** に実行すると、venv再生成・pip install・.env/資産の存在検証・import スモークまでを一括で行う。

```bash
cd ~/meal_analysis_api_2
bash scripts/setup_new_machine.sh
```
