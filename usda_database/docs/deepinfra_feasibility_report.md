# DeepInfra APIを使用したsearch_name/description生成の実現可能性レポート

## 📋 調査日時
2025-10-12

## ✅ 結論: **完全に実現可能**

DeepInfra APIを使用してFNDDSデータ（5,432件）からsearch_nameとdescriptionを生成することは技術的に完全に実現可能です。

---

## 🔍 技術的調査結果

### 1. 既存インフラストラクチャ

#### `shared/services/deepinfra_service.py`
- ✅ **DeepInfraServiceクラスが既に実装済み**
- ✅ AsyncOpenAIクライアントを使用
- ✅ JSON形式の出力をサポート (`response_format={"type": "json_object"}`)
- ✅ 非同期処理に完全対応

#### 利用可能なモデル（`shared/config/settings.py`）

| モデル | 期待応答時間 | 特性 | 推奨用途 |
|--------|------------|------|---------|
| **Qwen/Qwen2.5-VL-32B-Instruct** | 12.5秒 | 高速・高精度 | ✅ **推奨** |
| google/gemma-3-27b-it | 30秒 | 多様性重視 | - |
| meta-llama/Llama-3.2-90B-Vision-Instruct | 45秒 | 最高精度 | - |

**推奨**: Qwen2.5-VL-32B（速度と精度のバランスが最良）

### 2. API仕様

```python
# 既存のDeepInfraServiceの使用例
from shared.services.deepinfra_service import DeepInfraService

service = DeepInfraService(model_id="Qwen/Qwen2.5-VL-32B-Instruct")

# テキストのみのタスクも可能（画像なし）
response = await service.client.chat.completions.create(
    model=service.model_id,
    messages=[{"role": "user", "content": prompt}],
    max_tokens=512,
    temperature=0.0,
    response_format={"type": "json_object"}
)
```

---

## 📊 実装計画

### Phase 1: プロトタイプ作成（10件テスト）

```python
# 必要な機能
1. DeepInfraServiceに新メソッド追加: generate_food_metadata()
2. プロンプトエンジニアリング（Few-shot learning）
3. 10件のFNDDSデータでテスト
```

**プロンプト設計**:
```
You are a food database expert. Given a food name, generate:
1. search_name: A concise, searchable name (remove cooking methods, modifiers)
2. description: A comma-separated list of key attributes

Examples from MyNetDiary database:
- Input: "Beef ground 93% lean 7% fat raw"
  Output: {"search_name": "Ground beef", "description": "93% lean, 7% fat, raw"}

- Input: "Corn sweet yellow boiled without salt"
  Output: {"search_name": "corn", "description": "sweet, yellow, boiled, without salt"}

Now process: "{fndds_food_name}"
```

### Phase 2: バッチ処理（全5,432件）

#### パフォーマンス試算

**シングルスレッド処理**:
- 1件あたり: 12.5秒（Qwen2.5-VL）
- 全5,432件: **18.9時間**

**10並列処理**:
- 全5,432件: **約2時間** ✅

**実装方法**:
```python
import asyncio

async def process_batch(foods_batch):
    tasks = [generate_food_metadata(food) for food in foods_batch]
    return await asyncio.gather(*tasks)

# 10並列で処理
batch_size = 10
for i in range(0, len(fndds_foods), batch_size):
    batch = fndds_foods[i:i+batch_size]
    results = await process_batch(batch)
```

---

## 💰 コスト試算

### トークン使用量の見積もり

#### 1件あたりのトークン数:
- **入力**: プロンプト（200トークン） + FNDDSの食品名（20トークン） = 220トークン
- **出力**: JSON（80トークン）
- **合計**: 約300トークン/件

#### 全体:
- 5,432件 × 300トークン = **1,629,600トークン** （約1.6Mトークン）

### DeepInfra価格（要確認）
- 推定: $0.20-0.50 / 1M入力トークン
- 推定: $0.50-1.00 / 1M出力トークン
- **総コスト**: $0.50 - $2.00 程度 ✅ **非常に安価**

※正確な価格はhttps://deepinfra.com/pricing で確認してください

---

## 📈 品質予測

### 期待される品質向上

| 項目 | ルールベース（v2） | LLMベース（予測） |
|------|------------------|-----------------|
| リスト型の比率 | 18% ❌ | 6-8% ✅ |
| 調理法の誤分割 | 多数発生 ❌ | ほぼなし ✅ |
| 複雑な料理名の処理 | 不適切 ❌ | 適切 ✅ |
| 全体的な品質 | MyNetDiaryより劣る | MyNetDiaryと同等以上 ✅ |

### 根拠:
- Few-shot learningでMyNetDiaryのパターンを学習
- 文脈理解による適切な"or"の処理
- 調理法・修飾語の自動識別

---

## 🚀 実装ロードマップ

### ステップ1: プロトタイプ（1時間）
1. ✅ DeepInfraService確認（完了）
2. ⏳ 新メソッド `generate_food_metadata()` 追加
3. ⏳ プロンプト作成
4. ⏳ 10件テスト実行

### ステップ2: 評価（30分）
1. ⏳ 生成結果をMyNetDiaryと比較
2. ⏳ 品質レポート作成
3. ⏳ プロンプト改善（必要に応じて）

### ステップ3: フル実行（2-3時間）
1. ⏳ 全5,432件を並列処理
2. ⏳ 結果をJSON形式で保存
3. ⏳ 品質検証

### ステップ4: データベース統合（1時間）
1. ⏳ MyNetDiary形式のJSONを生成
2. ⏳ 栄養データとマージ
3. ⏳ Elasticsearchへのインデックス作成

**総所要時間**: 約5-6時間

---

## ⚠️ リスク・制約事項

### 1. API制限
- **Rate Limit**: DeepInfraのAPIレート制限を確認する必要あり
- **対策**: 並列数を調整（10 → 5に減らすなど）

### 2. ネットワーク障害
- **リスク**: 処理中にネットワーク断が発生する可能性
- **対策**: チェックポイント機能（N件ごとに中間保存）

### 3. コスト超過
- **リスク**: 想定より高額になる可能性
- **対策**: 最初に100件テストしてコストを確認

### 4. 品質不足
- **リスク**: LLM生成結果が期待を下回る可能性
- **対策**: Few-shot examplesを増やす、プロンプト改善

---

## 🎯 最終推奨事項

### ✅ 推奨アプローチ

**LLMベースのsearch_name/description生成を採用すべき理由**:

1. **技術的実現可能性**: 100%（既存インフラが完備）
2. **コスト**: 非常に低い（$1-2程度）
3. **品質**: ルールベースより大幅に向上が期待できる
4. **メンテナンス性**: ルール追加不要、プロンプト調整のみ
5. **拡張性**: 新しいデータセットにも簡単に適用可能

### 🔄 実装優先順位

**Priority 1** (今すぐ実行):
- プロトタイプ作成（10件テスト）
- 品質評価

**Priority 2** (品質OK後):
- フルバッチ処理（5,432件）
- データベース統合

**Priority 3** (運用後):
- 定期的な品質モニタリング
- プロンプト最適化

---

## 📝 次のアクション

1. **immediate**: 10件のプロトタイプスクリプトを作成して実行
2. **コスト確認**: DeepInfraの正確な価格を確認
3. **品質評価**: 生成結果がMyNetDiaryと同等以上か判定
4. **Go/No-Go判断**: 品質が十分なら全件処理を実行

---

## 📚 参考情報

- **DeepInfraService**: `/Users/odasoya/meal_analysis_api_2/shared/services/deepinfra_service.py`
- **設定ファイル**: `/Users/odasoya/meal_analysis_api_2/shared/config/settings.py`
- **MyNetDiaryデータ**: `/Users/odasoya/meal_analysis_api_2/db/mynetdiary_converted_tool_calls_list_stemmed_with_nutrition.json`
- **FNDDSデータ**: `/Users/odasoya/meal_analysis_api_2/usda_database/surveyDownload.json`
- **ルールベース結果**: `/tmp/test_fndds_search_name_generation.py`
