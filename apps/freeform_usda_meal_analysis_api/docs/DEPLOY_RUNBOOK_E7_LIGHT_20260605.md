# Production Deploy Runbook — E7 (reranker.top_n=5) + Light Retrieval Stack (0.6B emb / 0.6B rerank)

- 作成: 2026-06-05（mozu phase, branch `feature/mozu-api` @ `0d30625`）
- 検証: deploy 機構を 4 観点で read-only マッピング → runbook 草案 → コードに対する敵対的検証（評決「yes-with-corrections」、修正4件を本書に反映済み）。
- **Service:** `freeform-usda-meal-analysis-api` · **Project:** `new-snap-calorie` (1077966746907) · **Region:** `us-central1`
- **Prod URL:** `https://freeform-usda-meal-analysis-api-1077966746907.us-central1.run.app`

> 凡例: **[SAFE local prep]** = ローカル読み取り/準備のみ。 **[PROD WRITE — 要 go]** = 本番への書き込み（ユーザー明示指示が必要）。 **[PAID]** = 課金 API 呼び出しを伴う。

---

## 0. 要点（なぜ 2 面が必要か）

採用済みコード既定は 3 つとも整合済み（`settings.py`）:
- E7: `DEFAULT_RERANKER_TOP_N=5`（`settings.py:199-201`、`top_n=1` で旧 top-1 に即 revert）
- light embedding: `DEFAULT_EMBEDDING_MODEL=Qwen/Qwen3-Embedding-0.6B`（`settings.py:168-170`）
- light reranker: `DEFAULT_RERANKER_MODEL=Qwen/Qwen3-Reranker-0.6B`（`settings.py:176-178`）

ただし**本番の実効値は 2 つの別系統**で決まる:

| 変更 | 反映系統 | 理由 |
|---|---|---|
| **embedding モデル（0.6B）** | **image rebuild + Cloud Run deploy** | embedding モデルは Firestore に項目が存在しない。serve 時は `settings.DEFAULT_EMBEDDING_MODEL`（`usda_search.py:96`）。さらに FAISS index は image に baked（`Dockerfile.optimized:42`）= **embedding と index は 1 image で一緒に動く**。 |
| **reranker.top_n=5（E7）** | **Firestore write** | serve 時は `config.reranker.top_n`（`pipeline.py:927-929,982`）。既存 prod doc は**verbatim**で読まれる（`config_manager.py:314-317`）ため、再deploy だけでは変わらない。 |
| **reranker.model（0.6B）** | **Firestore write** | serve 時は `config.reranker.model`（`usda_search.py:190-192`, `pipeline.py:919-921`）。reranker は call 時に再スコアするだけで index 依存なし。 |

**順序が重要**: ① 0.6B image を先に deploy（embedding↔index↔reranker-model を相互整合）→ ② **実クエリで dim 整合を確認**（D3）→ ③ Firestore の 2 値を flip。

---

## (A) ビルド成果物の準備 — 0.6B index

deploy される index は build 時にローカル作業ツリーにある `usda_index_full.faiss` のバイト列そのもの。これは **gitignore**（`.gitignore:106 *.faiss`）で git/GCS provenance が無いため、**最初に必ず実体を確認**する。

**A1. [SAFE local prep] serving index が 1024-dim 0.6B か確認（最重要ゲート・唯一の安全網）**
```
ls -l apps/freeform_usda_meal_analysis_api/data/faiss/usda_index_full.faiss \
      apps/freeform_usda_meal_analysis_api/data/faiss/usda_index_full.8b.faiss \
      apps/freeform_usda_meal_analysis_api/data/faiss/usda_metadata.json
```
期待: `usda_index_full.faiss` ≈ **55,558,189 B（dim=1024 / ntotal=13564）**、`usda_index_full.8b.faiss` ≈ 222,232,621 B（dim=4096・8B backup・**serve では読まれない**: `usda_search.py:67` は `usda_index_full.faiss` のみ）、`usda_metadata.json` ≈ 8.4 MB。

> **2026-06-05 確認済み**: serving = magic `IxFI` / **dim=1024 / ntotal=13564 / 55.5 MB** ✅、8b backup = dim=4096。→ **A1 PASS。A2 はスキップ。**

**A1 GATE**: もし serving が 222 MB（8B 4096-dim）なら **STOP**。0.6B の `EMBEDDING_MODEL` × 4096-dim index は `faiss.index.search()`（`usda_search.py:152`/`hybrid_search.py:172`）内で**ハードクラッシュ**（app 側に dim ガード無し・`grep` で assertion 0 件）。

**A2. [PAID — network] ※A1 が失敗した場合のみ（本deployでは不要）** 既存 13,564-doc metadata を 0.6B で再埋め込みし serving dir へ直接出力。**13.5k docs の DeepInfra 課金ジョブ**（「SAFE」ではない）:
```
env -u DEEPINFRA_API_KEY -u DEEPINFRA_TOKEN -u OPENROUTER_API_KEY -u GOOGLE_CLOUD_PROJECT \
  PYTHONPATH=/Users/odasoya/meal_analysis_api_2 \
  "/Users/odasoya/meal_analysis_api /venv/bin/python" \
  -m apps.freeform_usda_meal_analysis_api.scripts.build_embedding_ab_index \
  --model Qwen/Qwen3-Embedding-0.6B \
  --output-dir apps/freeform_usda_meal_analysis_api/data/faiss
```
（`build_embedding_ab_index.py:62-115` は metadata + `usda_bm25_index/` を変更なしコピーし FAISS ベクトルのみ差替。実行後 A1 を再確認。**本deployでは A1 PASS のため実行しない**。）

**A3. [SAFE local prep] metadata/BM25 の同梱整合** `usda_metadata.json`（13,564-doc）が 0.6B ベクトルと対応していること。BM25 は `data/faiss/usda_bm25_index/` にあり同じ `data/faiss/` COPY で同梱（`Dockerfile.optimized:42`）。`Dockerfile.optimized` は別 `data/bm25/` を COPY しない（正しい）。

---

## (B) image build & Cloud Run deploy

**B1. [SAFE local prep] build context プリフライト** `deploy.sh:170-213` が一時 `.gcloudignore` を書くが `data/` は除外しない → ローカル `data/faiss/`（両 `.faiss` 含む）が Cloud Build に上がり image に COPY（`Dockerfile.optimized:42`）。**submit 直前に A1 サイズを再確認**（誤った embedding 空間を出荷しない最後のゲート）。
- 任意: 222 MB の `usda_index_full.8b.faiss` は image 内で**読まれない死荷重**。残しても安全、削れば image が縮むだけ。

**B2. [PROD WRITE — 要 go] build + deploy** `deploy.sh` が `Dockerfile.optimized` を採用（`:158-159`）し Cloud Build → 本番 deploy（`min-instances=2`, `PRELOAD_INDEXES_ON_STARTUP=true`）。`EMBEDDING_MODEL`/`RERANKER_MODEL`/`RERANKER_TOP_N` は**未設定**（grep 0）→ embedding は code 既定 0.6B。
```
ENVIRONMENT=production /Users/odasoya/meal_analysis_api_2/apps/freeform_usda_meal_analysis_api/deploy.sh
```
内部実行（`deploy.sh:215-220, 273-288`）:
```
gcloud builds submit --tag gcr.io/new-snap-calorie/freeform-usda-meal-analysis-api:optimized \
  --timeout=900 --machine-type=E2_HIGHCPU_32 --project=new-snap-calorie .
gcloud run deploy freeform-usda-meal-analysis-api \
  --image gcr.io/new-snap-calorie/freeform-usda-meal-analysis-api:optimized \
  --region us-central1 --platform managed --allow-unauthenticated \
  --port 8006 --memory=4Gi --cpu=2 --cpu-boost --execution-environment=gen2 \
  --concurrency=80 --max-instances=10 --min-instances=2 \
  --set-env-vars="${ENV_VARS}" --project=new-snap-calorie
```
- `deploy.sh:74-114` が `DEEPINFRA_API_KEY`/`OPENROUTER_API_KEY` を live service から自動取得。**`DEEPINFRA_API_KEY` 必須**（embedding/reranker は serve 時 DeepInfra リモート呼び出し: `usda_search.py:7,93-97`; `deepinfra_service.py:106-107`; 未設定なら `settings.py:96-100` が raise）。
- light 化は「要求する DeepInfra model ID と同梱 FAISS index」を変えるだけで、**container にモデル重みは入らない**（image サイズ不変）。

**B3. [PROD WRITE — 検証のみ] rollback 用に新 revision 名を控える。** ⚠️ **dim mismatch は preload でも `/health` でも検出されない**: preload（`usda_search.py:72`）は `faiss.read_index()` がどの dim でも成功し、embedding は**リモート client を作るだけで dim チェック無し**（`usda_search.py:96-98`）。**最初の実クエリ**で 1024-dim query が wrong-dim index に当たって初めて 500（本番経路 `food_search_service.py:155`→`hybrid_search.py:172`）。→ **green health を dim 整合の証拠と見なさない**。必ず (D3) を実施してから Firestore を flip。

---

## (C) Firestore config 変更

対象 doc `api_configs/freeform_usda_meal_analysis`（`config_manager.py:187-188`）。書き込みは**認証なし**の `PUT /admin/api/config`（`router.py:106-132`）。prod doc は **2026-02-26（E7 前）**更新なので、`reranker.top_n` / `reranker.model` が古い可能性あり → **両 write は no-op でなく必須として実行**（冪等なので既に正しくても無害）。

**C1. [PROD WRITE — read first] 書き込み前に現 doc をスナップショット（rollback 記録用）**
```
curl -s 'https://freeform-usda-meal-analysis-api-1077966746907.us-central1.run.app/admin/api/config?refresh=true'
```
既存 `reranker.top_n` / `reranker.model` を記録。`vlm.prompt_text`（len 2841）/ `vlm.model_id`（flash）が存在することも確認（**両方 out of scope・触らない**）。

> 注: doc に `top_n` キーが**欠落**している場合、Pydantic は code 既定 **5** を backfill する（= E7 が既に ON の可能性）。明示的に `null` の時のみ `None`→`or 1`→top-1（`pipeline.py:982`）。いずれにせよ C2 の `top_n:5` は冪等で安全。

**C2. [PROD WRITE — 要 go] E7 を有効化（top_n=5）**
```
curl -s -X PUT 'https://freeform-usda-meal-analysis-api-1077966746907.us-central1.run.app/admin/api/config?updated_by=deploy_e7_lightstack' \
  -H 'Content-Type: application/json' \
  -d '{"updates":{"reranker.top_n":5}}'
```
mixture は `top_n>1` のときのみ発火（`pipeline.py:1222-1228`）。**`detect_config_drift` は top_n を見ない**（`config_manager.py:353-377`）→ `/health` では正否が分からないので D2/D4 で明示確認。

**C3. [PROD WRITE — 要 go] light reranker モデル**
```
curl -s -X PUT 'https://freeform-usda-meal-analysis-api-1077966746907.us-central1.run.app/admin/api/config?updated_by=deploy_e7_lightstack' \
  -H 'Content-Type: application/json' \
  -d '{"updates":{"reranker.model":"Qwen/Qwen3-Reranker-0.6B"}}'
```
code 既定と一致 → 既存の `reranker.model` drift フラグが解消。index 依存なしで安全に flip 可。

**C4. [注意] Firestore TTL cache は 5s（`config_manager.py:198`）。Admin UI の `Local` タブは `baseUrl:''`＝same-origin**（`admin/templates/dashboard.html:724-725`）= prod ドメインで開いて保存すると「Local」表記でも **prod に書く**。→ UI でなく上記 `curl` を使う。`vlm.prompt_text` / `vlm.model_id` / `search.stage1_top_k`(50) / `self_consistency_k`(1) は**触らない**。

---

## (D) deploy 後の検証

**D1. health** `curl -s '.../health'` → healthy。C3 後に `config_drift_fields`（`routers/health.py:41-54`）が `reranker.model` を flag していないこと（まだ 4B を flag するなら write 未反映）。

**D2. admin config refresh** `curl -s '.../admin/api/config?refresh=true'` → `reranker.top_n==5` / `reranker.model=="Qwen/Qwen3-Reranker-0.6B"` / `updated_at` が新しい / **`vlm.prompt_text` len=2841・`vlm.model_id`=flash が不変**。

**D3. embedding/index 整合（dim mismatch トラップ）** 実画像で 1 回 analyze/retrieve。**dim 不一致はここで初めて 500**（preload/health は素通り）。200 + food マッチが返れば embedding↔index 整合 OK。

**D4. calorie サニティ** 既知画像を少数 prod に通し総 kcal を GT と目視比較。`top_n=5` で rerank-softmax density mixture（`pipeline.py:1222-1228`）が効き、非退化の総 kcal なら E7 engaged。**本 deploy の一環で 50枚 paid フル eval は行わない**（要明示指示）。

---

## (E) rollback

**E1. [PROD WRITE] E7 即 revert（top_n→1, 再deploy 不要・~5s）**
```
curl -s -X PUT '.../admin/api/config?updated_by=rollback_e7' \
  -H 'Content-Type: application/json' -d '{"updates":{"reranker.top_n":1}}'
```

**E2. [PROD WRITE] reranker モデル revert**（C1 で記録した旧値へ）
```
curl -s -X PUT '.../admin/api/config?updated_by=rollback_reranker' \
  -H 'Content-Type: application/json' -d '{"updates":{"reranker.model":"<C1の旧値>"}}'
```

**E3. [PROD WRITE] image/embedding revert（旧 revision へ即トラフィック切替, B3 で控えた名前）**
```
gcloud run services update-traffic freeform-usda-meal-analysis-api \
  --region us-central1 --project new-snap-calorie --to-revisions <PRIOR_REVISION>=100
```
⚠️ **embedding（image）と index は必ず一緒に動かす**。0.6B `EMBEDDING_MODEL` revision を 8B index に当てる（逆も）と dim crash。旧 revision は自分の index と整合済みなのでトラフィック切替単体で coherent。

---

## 決定が必要な項目

1. **本番 deploy を実行するか**（要明示 go）。準備（runbook + A1 PASS）は完了。
2. **`EMBEDDING_MODEL` を明示 pin するか**: 現状は code 既定（`settings.py:169`）依存。`deploy.sh` の `ENV_VARS` に `EMBEDDING_MODEL=Qwen/Qwen3-Embedding-0.6B` を足すと embedding↔index coupling が明示化され部分 rollback 事故が減る。今回の正否には不要だが将来の安全マージン。
3. **8B backup（222 MB）を image から除外するか**: 読まれない死荷重。残して安全・削れば image 縮小のみ。
4. **prompt は触らない（決定済み）**: prod の `vlm.prompt_text`（len 2841）は code 既定 v13（`...prodcapture_20260226.txt`, 2841B, prod 由来）と**バイト一致**（`settings.py:68-74`）。E7+light の scope 外。`prompt_file` ラベルの v7→v13 修正は deploy 後に延期（text override が勝つため cosmetic）。

## 既知の留意（deploy ブロッカーではない）
- VLM 既定は **flash**（pro でない・`settings.py:64-66`）。app-dir `CLAUDE.md` は "pro (default)" のままで stale だが code は flash に revert 済（2026-06-04）。prod も flash で整合。
- index は gitignore で**このマシンの作業ツリーにのみ存在**。build host が別マシンなら A1 が出荷物の唯一の保証。
- `/admin/*` は app 層に認証なし（Cloud Run ingress 任せ）。
