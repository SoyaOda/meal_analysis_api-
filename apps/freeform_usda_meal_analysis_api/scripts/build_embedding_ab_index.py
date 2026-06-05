#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build a USDA FAISS index for an E5 embedding A/B candidate.

既存の `usda_metadata.json`（13,564件）の `description` を、指定した embedding モデルで
**再埋め込み**して FAISS index のみを作り直す。metadata と BM25 index は元のものを
そのままコピーするため、A/B では **embedding ベクトルだけ**が変わる（clean isolation）。

document はモデル規約に合わせて整形する（format_embedding_document; EmbeddingGemma のみ
doc プロンプトが付く）。query 側は serve 時に format_embedding_query が同じ規約で整形する。

使い方（DeepInfra キーは .env を使うため env -u で shell の古いキーを外す）:
    env -u DEEPINFRA_API_KEY -u DEEPINFRA_TOKEN -u OPENROUTER_API_KEY \
      PYTHONPATH=<repo> python -m apps.freeform_usda_meal_analysis_api.scripts.build_embedding_ab_index \
      --model Qwen/Qwen3-Embedding-0.6B \
      --output-dir apps/freeform_usda_meal_analysis_api/data/faiss_ab/qwen3_0_6b
"""

import argparse
import asyncio
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import faiss

_REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO_ROOT))

from apps.freeform_usda_meal_analysis_api.services.deepinfra_service import (  # noqa: E402
    DeepInfraService,
    format_embedding_document,
)
from apps.freeform_usda_meal_analysis_api.services.extra_providers import (  # noqa: E402
    embed_texts,
    is_external,
)

# DeepInfra embedding API は 1 リクエスト最大 1024 入力
BATCH_SIZE = 1024
DEFAULT_SOURCE_DIR = str(_REPO_ROOT / "apps/freeform_usda_meal_analysis_api/data/faiss")


async def build(model: str, source_dir: str, output_dir: str) -> None:
    # 相対パスは repo root 基準で解決する（cwd に依存して二重ネストするのを防ぐ）
    src = Path(source_dir)
    if not src.is_absolute():
        src = _REPO_ROOT / src
    out = Path(output_dir)
    if not out.is_absolute():
        out = _REPO_ROOT / out

    metadata_path = src / "usda_metadata.json"
    bm25_path = src / "usda_bm25_index"
    if not metadata_path.exists():
        raise FileNotFoundError(f"metadata not found: {metadata_path}")
    if not bm25_path.exists():
        raise FileNotFoundError(f"bm25 index not found: {bm25_path}")

    items = json.loads(metadata_path.read_text(encoding="utf-8"))
    print(f"📂 loaded {len(items)} items from {metadata_path}")

    if is_external(model):
        # F-PROV: 非 DeepInfra provider は document 規約（input_type/taskType）を内包。
        # gemma 用 doc プロンプトは付与しない（生の description を渡す）。
        raw_docs = [it["description"] for it in items]
        print(f"🔨 embedding {len(raw_docs)} docs via external provider: {model}")
        all_vecs = await asyncio.to_thread(embed_texts, model, raw_docs, False)
    else:
        # DeepInfra 経路: document をモデル規約で整形（EmbeddingGemma のみ doc プロンプト付与）
        documents = [
            format_embedding_document(it["description"], model) for it in items
        ]
        service = DeepInfraService(model_id=model)
        print(f"🔨 embedding {len(documents)} docs with model: {model}")
        all_vecs = []
        total_batches = (len(documents) + BATCH_SIZE - 1) // BATCH_SIZE
        for i in range(0, len(documents), BATCH_SIZE):
            batch = documents[i : i + BATCH_SIZE]
            vecs = await service._call_embeddings_api(batch, model)
            all_vecs.extend(vecs)
            print(
                f"  batch {i // BATCH_SIZE + 1}/{total_batches}: "
                f"{i + len(batch)}/{len(documents)} embedded"
            )

    embeddings = np.array(all_vecs, dtype="float32")
    if embeddings.shape[0] != len(items):
        raise ValueError(
            f"embedding count {embeddings.shape[0]} != item count {len(items)}"
        )
    dim = embeddings.shape[1]
    print(f"✅ embeddings shape: {embeddings.shape}")

    # cosine 類似度用に L2 正規化（serve 側も l2_normalize_rows で正規化）→ IndexFlatIP
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    embeddings = embeddings / norms

    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    out.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(out / "usda_index_full.faiss"))
    shutil.copy2(metadata_path, out / "usda_metadata.json")
    shutil.copytree(bm25_path, out / "usda_bm25_index", dirs_exist_ok=True)
    bm25_stats = src / "bm25_stats.json"
    if bm25_stats.exists():
        shutil.copy2(bm25_stats, out / "bm25_stats.json")

    print(
        f"✅ wrote index ({index.ntotal} vectors, dim {dim}) + metadata + bm25 to {out}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="DeepInfra embedding model id")
    parser.add_argument("--source-dir", default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    asyncio.run(build(args.model, args.source_dir, args.output_dir))


if __name__ == "__main__":
    main()
