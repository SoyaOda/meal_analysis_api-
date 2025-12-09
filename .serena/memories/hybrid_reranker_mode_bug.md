# hybrid_reranker モードのバグ

## 発見日
2024-12-08

## 問題
`/api/v1/retrieve` エンドポイントで `mode=hybrid_reranker` を指定すると、以下のエラーが発生する：

```
{"detail": "Search failed: 'str' object has no attribute 'get'"}
```

## 再現方法
```bash
curl -s "http://localhost:8006/api/v1/retrieve?q=cola&top_k=20&mode=hybrid_reranker&debug=true"
```

## 関連ファイル
- `apps/freeform_usda_meal_analysis_api/routers/retrieval.py` - `_search_hybrid_reranker_mode` 関数
- `apps/freeform_usda_meal_analysis_api/services/hybrid_search.py` - `search_hybrid_with_reranker` メソッド

## 推定原因
`_search_hybrid_reranker_mode` 関数内で、reranker の結果を処理する際に、文字列を辞書として扱おうとしている可能性がある。
`search_hybrid_with_reranker` メソッドの戻り値の形式と、`_search_hybrid_reranker_mode` での期待する形式が一致していない。

## 優先度
中（hybrid モードは動作しているため、主要機能には影響なし）

## 修正予定
cola検索問題の修正後に対応
