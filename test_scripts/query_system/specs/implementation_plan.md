# 食品名意味的マッチングシステム 実装計画書

## 1. 概要

本ドキュメントは `spec1.md` に基づき、実際の実装に向けた具体的な技術選定と実装方針を定義します。

### 目的
- VLM出力（search_name + description）からUSDA食品データベースへの高精度マッチング
- 表記揺れ・類義語に対応（例: "fried potato" vs "french fries"）
- リアルタイム処理（1秒以内の応答）

### アーキテクチャ
**2段階ハイブリッド検索**:
1. **Stage 1**: ベクトル検索（FAISS + Sentence-BERT）→ 上位K件の候補取得
2. **Stage 2**: LLM再ランキング（CrossEncoder）→ 最適な1件を選出

---

## 2. 技術選定と根拠

### 2.1 埋め込みモデル（Stage 1）

**選定モデル**: `sentence-transformers/all-MiniLM-L6-v2`

**選定理由**:
- **速度**: mpnet-base-v2の5倍高速（3-6秒 vs 30-50秒）
- **精度**: STS-B 84-85%（mpnetは87-88%だが、5%の精度差より速度を優先）
- **次元数**: 384次元（mpnetの768次元より軽量）
- **実績**: 広く使われており、汎用的な意味表現に優れる
- **将来性**: 精度不足が判明した場合、mpnet-base-v2やRecipeBERT（食品特化）への切り替えが容易

**代替案**（精度向上が必要な場合）:
- `sentence-transformers/all-mpnet-base-v2`: 精度重視
- `RecipeBERT`: 食品ドメイン特化（要ファインチューニング）

### 2.2 再ランキングモデル（Stage 2）

**選定モデル**: `BAAI/bge-reranker-base`

**選定理由**:
- **macOS互換性**: XLM-RoBERTaベースでSDPA依存なし、macOS + PyTorch 2.7.1でNaN問題なし
- **実装の容易性**: CrossEncoderのドロップイン置換、既存コードをそのまま利用可能
- **速度**: 10件の候補で約100-120ms（CPU）、実用的な範囲内
- **精度**: BEIR Avg 54.9%、MS MARCOモデルより高精度
- **リソース効率**: 278Mパラメータ、CPUでも実行可能
- **問題解決**: 従来のms-marco-MiniLM-L-6-v2で発生したNaN問題を完全に解決

**技術詳細**:
- アーキテクチャ: XLM-RoBERTa-base
- 入力形式: `[query, candidate]`ペア
- 出力: スコア（float、-∞〜+∞の範囲）

**代替案**（将来的な精度・速度調整）:
- `BAAI/bge-reranker-v2-m3`: より高精度（BEIR Avg 60.9%）だが遅い（~200ms）
- `BAAI/bge-reranker-large`: 最高精度（BEIR Avg 57.7%）だが最も遅い（~300ms）
- `castorini/monot5-base-msmarco`: T5ベース、約150ms（macOS互換性未確認）

### 2.3 ベクトルインデックス

**選定インデックス**: `faiss.IndexFlatIP`

**選定理由**:
- **正確性**: 100%正確な検索結果（近似なし）
- **データ規模**: 対象は約1,000〜10,000件 → Flat indexで十分高速
- **Web調査結果**: "10K件以下ではIndexFlatIPで問題なし"との情報
- **シンプル性**: 構築・メンテナンスが容易

**代替案**（10万件以上に拡張する場合）:
- `faiss.IndexHNSWFlat`: 近似検索だが大規模データで高速

### 2.4 候補数（K）

**選定値**: `K = 5`

**選定理由**:
- CrossEncoderの処理時間: 5件なら約30-40ms（実用的）
- spec1.mdの推奨範囲（5〜10件）の下限
- 評価後、精度とのトレードオフで調整可能

---

## 3. データソースと前処理

### 3.1 対象データベース

**ファイル**: `test_scripts/mappings/mappings_final/usda_food_mappings_unified.json`

**インデックス対象**:
- `default_usda.name`から"Num. "を除いた部分
- 形式: `"search_name, description1, description2"`
  - 例: `"Chicken, broilers or fryers, breast, meat only, cooked, roasted"`

**追加情報の活用**:
- `display_name`: ユーザー表示用
- `role`: 食品カテゴリ情報（埋め込みに含めるか検討）

### 3.2 テキスト正規化

**方針**: 既存の `test_vlm_usda_matching_full.py` の実装を参考

```python
def normalize_text(text: str) -> str:
    """テキストを正規化"""
    text = text.lower()
    text = re.sub(r'[^a-z\s]', ' ', text)  # アルファベットとスペースのみ
    text = re.sub(r'\s+', ' ', text).strip()  # 複数スペースを単一に
    return text

def parse_usda_name(usda_name: str) -> Tuple[str, str]:
    """USDA名から search_name と description を抽出"""
    # "Num. " を除去
    if '. ' in usda_name:
        name_part = usda_name.split('. ', 1)[1]
    else:
        name_part = usda_name

    # コンマで分割
    components = [c.strip() for c in name_part.split(',')]
    search_name = components[0]
    description = ', '.join(components[1:])

    return search_name, description
```

### 3.3 埋め込みテキストの構成

**方式**: `search_name + " " + description`

例:
- USDA: `"Chicken broiled"` (search_name) + `"skinless"` (description) → `"Chicken broiled skinless"`
- VLM: `"chicken breast"` (search_name) + `"grilled"` (description) → `"chicken breast grilled"`

**代替案**（精度向上が必要な場合）:
- `role`（カテゴリ）を含める: `"Chicken broiled skinless (category: meat)"`

---

## 4. 評価方法

### 4.1 評価データ

**テストデータ**: `test_scripts/output/vlm_test_results_Qwen_Qwen3-VL-235B-A22B-Thinking_freeform_usda_20251025_110445.json`
- 50画像、約300食品アイテム
- 既存のマッチングテスト: 96%成功率（threshold=60）

### 4.2 評価指標

**主要指標**:
1. **Top-1 Accuracy**: 最上位候補が正解である割合
2. **Recall@K**: 上位K件に正解が含まれる割合（K=5）
3. **MRR (Mean Reciprocal Rank)**: 正解の平均ランキング
4. **処理時間**: クエリあたりの応答時間（目標: <1秒）

**ベースライン比較**:
- 既存実装（`test_vlm_usda_matching_full.py`）との精度比較
- Stage 1のみ vs Stage 1+2の精度向上幅

### 4.3 評価プロセス

1. **自動評価**: 全50画像（300アイテム）で指標計測
2. **人手検証**: 失敗ケース20件をマニュアルレビュー
3. **速度評価**: 平均処理時間とP95レイテンシ計測
4. **改善サイクル**: 評価結果に基づきモデル調整

---

## 5. プロジェクト構造

```
test_scripts/query_system/
├── specs/
│   ├── spec1.md                      # 元仕様書
│   └── implementation_plan.md        # 本ドキュメント
├── src/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── embedding.py              # SentenceTransformer埋め込み
│   │   └── reranker.py               # CrossEncoder再ランキング
│   ├── index/
│   │   ├── __init__.py
│   │   ├── builder.py                # FAISSインデックス構築
│   │   └── searcher.py               # ベクトル検索
│   ├── preprocessing/
│   │   ├── __init__.py
│   │   └── text_normalizer.py       # テキスト正規化
│   ├── pipeline.py                   # メインパイプライン
│   └── config.py                     # 設定管理
├── data/
│   ├── usda_embeddings.npy           # 事前計算済み埋め込み
│   ├── usda_index.faiss              # FAISSインデックス
│   └── usda_metadata.json            # メタデータ（ID→名称マッピング）
├── tests/
│   ├── test_embedding.py
│   ├── test_reranker.py
│   ├── test_pipeline.py
│   └── test_evaluation.py
├── scripts/
│   ├── build_index.py                # インデックス構築スクリプト
│   ├── evaluate.py                   # 評価スクリプト
│   └── benchmark.py                  # ベンチマークスクリプト
└── README.md
```

---

## 6. 実装フェーズ

### Phase 1: 基本モジュール実装（1-2日）
- [ ] `models/embedding.py`: SentenceTransformer埋め込み
- [ ] `models/reranker.py`: CrossEncoder再ランキング
- [ ] `preprocessing/text_normalizer.py`: テキスト正規化
- [ ] `config.py`: 設定管理

### Phase 2: インデックス構築（1日）
- [ ] `index/builder.py`: USDA データベース読み込み→埋め込み→FAISS構築
- [ ] `index/searcher.py`: ベクトル検索
- [ ] `scripts/build_index.py`: インデックス構築スクリプト

### Phase 3: パイプライン統合（1日）
- [ ] `pipeline.py`: Stage 1 + Stage 2の統合パイプライン
- [ ] エラーハンドリングとロギング

### Phase 4: 評価とベンチマーク（1-2日）
- [ ] `scripts/evaluate.py`: VLMテストデータでの評価
- [ ] `scripts/benchmark.py`: 速度ベンチマーク
- [ ] ベースライン比較レポート作成

### Phase 5: 最適化と改善（必要に応じて）
- [ ] ハイパーパラメータ調整（K, スコア閾値）
- [ ] モデル切り替え実験（mpnet, RecipeBERT）
- [ ] 多言語対応（必要な場合）

---

## 7. 依存ライブラリ

```txt
sentence-transformers>=2.2.0
faiss-cpu>=1.7.4  # または faiss-gpu
transformers>=4.30.0
torch>=2.0.0
numpy>=1.24.0
```

---

## 8. 設定パラメータ

```python
# config.py の初期設定
CONFIG = {
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "reranker_model": "BAAI/bge-reranker-base",
    "top_k": 5,
    "normalize_embeddings": True,
    "faiss_index_type": "IndexFlatIP",
    "batch_size": 32,
    "device": "cpu",  # または "cuda"
}
```

---

## 9. 成功基準

### 精度
- Top-1 Accuracy ≥ 90%（既存96%をベースライン）
- Recall@5 ≥ 98%

### 速度
- 平均処理時間 < 500ms
- P95レイテンシ < 1秒

### 実装品質
- テストカバレッジ ≥ 80%
- ドキュメント完備
- 再現可能なベンチマーク

---

## 10. リスクと対策

| リスク | 影響 | 対策 |
|--------|------|------|
| 埋め込みモデルの精度不足 | 中 | mpnet-base-v2への切り替え準備 |
| CrossEncoderの速度問題 | 低 | Kを5→3に削減、またはバッチ最適化 |
| USDAデータの表記揺れ | 中 | 同義語辞書の追加、前処理強化 |
| 多言語対応の要求 | 高 | multilingual-MiniLMへの切り替え |

---

## 11. 次のステップ

1. **今すぐ**: プロジェクト構造の作成
2. **Phase 1開始**: 基本モジュールから順次実装
3. **各モジュール完成後**: 単体テストを実施して動作確認
4. **Phase 4**: 評価を行い、精度・速度をベースラインと比較
5. **必要に応じて**: モデル切り替えやハイパーパラメータ調整

---

**作成日**: 2025-10-25
**バージョン**: 1.0
**次回レビュー**: Phase 1完了後
