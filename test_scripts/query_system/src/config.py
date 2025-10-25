"""
設定管理モジュール

モデル、検索、前処理などの設定を一元管理します。
"""

from pathlib import Path
from typing import Dict, Any

# プロジェクトパス設定
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
USDA_DB_PATH = PROJECT_ROOT.parent.parent / "mappings/mappings_final/usda_food_mappings_unified.json"

# モデル設定
MODEL_CONFIG: Dict[str, Any] = {
    # 埋め込みモデル（Stage 1）
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "embedding_dim": 384,
    "normalize_embeddings": True,

    # 再ランキングモデル（Stage 2）
    "reranker_model": "BAAI/bge-reranker-base",

    # デバイス設定
    "device": "cpu",  # "cuda" for GPU
}

# 検索設定
SEARCH_CONFIG: Dict[str, Any] = {
    # 第1段階（Stage 1）で取得する候補数（上位K件）
    "top_k": 5,

    # FAISSインデックスタイプ
    "faiss_index_type": "IndexFlatIP",

    # スコア閾値（オプション: None の場合は閾値なし）
    "score_threshold": None,
}

# 前処理設定
PREPROCESSING_CONFIG: Dict[str, Any] = {
    # テキスト正規化設定
    "lowercase": True,
    "remove_special_chars": True,
    "normalize_spaces": True,
}

# インデックス構築設定
INDEX_BUILD_CONFIG: Dict[str, Any] = {
    # バッチサイズ
    "batch_size": 32,

    # 保存先パス
    "embeddings_path": DATA_DIR / "usda_embeddings.npy",
    "index_path": DATA_DIR / "usda_index.faiss",
    "metadata_path": DATA_DIR / "usda_metadata.json",
}

# 評価設定
EVALUATION_CONFIG: Dict[str, Any] = {
    # テストデータパス
    "vlm_test_data": PROJECT_ROOT.parent / "output/vlm_test_results_Qwen_Qwen3-VL-235B-A22B-Thinking_freeform_usda_20251025_110445.json",

    # 評価指標
    "metrics": ["top1_accuracy", "recall@k", "mrr", "processing_time"],

    # ベースラインスクリプト（比較用）
    "baseline_script": PROJECT_ROOT.parent / "test_vlm_usda_matching_full.py",
}


def get_config(section: str = "all") -> Dict[str, Any]:
    """
    設定を取得

    Args:
        section: 取得する設定セクション
                 "model", "search", "preprocessing", "index", "evaluation", "all"

    Returns:
        設定辞書
    """
    configs = {
        "model": MODEL_CONFIG,
        "search": SEARCH_CONFIG,
        "preprocessing": PREPROCESSING_CONFIG,
        "index": INDEX_BUILD_CONFIG,
        "evaluation": EVALUATION_CONFIG,
    }

    if section == "all":
        return {
            **MODEL_CONFIG,
            **SEARCH_CONFIG,
            **PREPROCESSING_CONFIG,
            **INDEX_BUILD_CONFIG,
            **EVALUATION_CONFIG,
        }

    return configs.get(section, {})