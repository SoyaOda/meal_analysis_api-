#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BM25Sインデックス構築スクリプト

USDA食品データからBM25Sインデックスを構築します。
"""

import json
import logging
from pathlib import Path
from typing import List, Dict
import bm25s
import Stemmer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_metadata(metadata_path: Path) -> List[Dict]:
    """メタデータをロード"""
    logger.info(f"Loading metadata from: {metadata_path}")

    with open(metadata_path, 'r', encoding='utf-8') as f:
        items = json.load(f)

    logger.info(f"✅ Loaded {len(items)} items")
    return items


def build_bm25_index(
    items: List[Dict],
    output_dir: Path,
    k1: float = 1.2,
    b: float = 0.75
):
    """
    BM25Sインデックスを構築

    Args:
        items: 食品アイテムのリスト
        output_dir: 出力ディレクトリ
        k1: BM25 k1パラメータ（term frequency saturation）
        b: BM25 bパラメータ（document length normalization）
    """
    logger.info(f"Building BM25S index...")
    logger.info(f"Parameters: k1={k1}, b={b}")

    # コーパスの準備
    corpus = []
    for item in items:
        # main_nameとdescriptorsを結合
        text = f"{item.get('main_name', '')} {item.get('descriptors', '')}"
        corpus.append(text.strip())

    logger.info(f"Corpus size: {len(corpus)} documents")

    # ステマーの初期化
    stemmer = Stemmer.Stemmer("english")
    logger.info("✅ Stemmer initialized")

    # トークナイズ（ストップワード除去 + ステミング）
    logger.info("Tokenizing corpus...")
    corpus_tokens = bm25s.tokenize(
        corpus,
        stopwords="en",
        stemmer=stemmer
    )
    logger.info("✅ Tokenization completed")

    # BM25モデルの構築
    logger.info("Building BM25S model...")
    bm25_model = bm25s.BM25(k1=k1, b=b)
    bm25_model.index(corpus_tokens)
    logger.info("✅ BM25S model built successfully")

    # インデックスの保存
    output_dir.mkdir(parents=True, exist_ok=True)
    index_path = output_dir / "usda_bm25_index"

    logger.info(f"Saving BM25S index to: {index_path}")
    bm25_model.save(str(index_path))
    logger.info("✅ BM25S index saved successfully")

    # 統計情報の保存
    stats = {
        "num_documents": len(corpus),
        "k1": k1,
        "b": b,
        "index_path": str(index_path),
        "stemmer": "english"
    }

    stats_path = output_dir / "bm25_stats.json"
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)

    logger.info(f"✅ Statistics saved to: {stats_path}")
    logger.info(f"\n📊 BM25S Index Statistics:")
    logger.info(f"  Documents: {stats['num_documents']}")
    logger.info(f"  k1: {stats['k1']}")
    logger.info(f"  b: {stats['b']}")


def main():
    """メイン処理"""
    # パスの設定
    base_dir = Path(__file__).parent.parent / "data" / "faiss"
    metadata_path = base_dir / "usda_metadata.json"
    output_dir = base_dir

    if not metadata_path.exists():
        logger.error(f"Metadata file not found: {metadata_path}")
        return

    # メタデータのロード
    items = load_metadata(metadata_path)

    # BM25インデックスの構築
    build_bm25_index(
        items=items,
        output_dir=output_dir,
        k1=1.2,  # デフォルト値（2025年ベストプラクティス）
        b=0.75   # デフォルト値（2025年ベストプラクティス）
    )

    logger.info("\n🎉 BM25S index building completed successfully!")


if __name__ == "__main__":
    main()
