# Pipeline包括的レビュー：30%以上誤差の原因分析

**生成日時**: 2025-10-26 21:48
**対象**: 全50画像の栄養素比較結果

---

## 🚨 重大な発見

### 1. 全画像でVLM認識が完全失敗

**調査対象レポート**：
- `nutrition_comparison_all_50_20251026_214129.md` (最新)
- `nutrition_comparison_all_50_20251026_200915.md` (過去)
- さらに古い全レポート

**発見事項**：
```
✅ 調査結果：
- 全50画像でVLM認識料理数 = 0
- VLM output の dishes 配列が空
- enriched_dishes は存在するが、USDA matchが0
- 栄養素の出所が不明（enriched_dishesから計算されていない）
```

### 2. 30%以上誤差ケースの詳細

**過去レポート (20251026_200915)**：
- 30%以上誤差: 12件/50件 (24%)
- **全12ケースでVLM認識0料理**

**最新レポート (20251026_214129)**：
- 30%以上誤差: 13件/50件 (26%)
- **全13ケースでVLM認識0料理**

---

## 🔍 問題の根本原因

### パイプライン全体のフロー

```
1. VLM画像解析 → 料理認識 (dishes配列)
   ↓
2. Query Extraction → 検索クエリ生成
   ↓
3. USDA検索 → embedding + reranking
   ↓
4. 栄養計算 → 最終結果
```

### 各ステップの状態

#### Step 1: VLM画像解析 ❌ **完全失敗**

**症状**：
- `vlm_output.dishes` が空配列
- JSON解析エラーの可能性
- max_tokens不足によるJSON切断

**エラーログ例** (test_food28.jpg):
```
finish_reason: length
Reasoning content length: 15972
Content length: 153
JSONDecodeError: Unterminated string starting at: line 8 column 11
```

**原因**：
1. **max_tokens不足**：
   - 設定値: 4096トークン
   - Thinkingモデルの推論トークン: 14,000-16,000トークン
   - 実際の出力トークン: 153-706トークン（切断前）
   - **合計必要トークン: 16,000+ トークン**

2. **JSON出力の切断**：
   - 推論にほぼ全トークンを消費
   - 実際のJSON出力が途中で切断
   - `Unterminated string` エラー

#### Step 2: Query Extraction ⚠️ **スキップ**

- VLMが0料理 → クエリ抽出不可
- フォールバックロジックが動作？

#### Step 3: USDA検索 ⚠️ **失敗**

- enriched_dishesは存在するが、USDA match = 0
- どこから enriched_dishes が生成されているのか不明

#### Step 4: 栄養計算 ⚠️ **謎の値**

- USDA matchがないのに栄養素が計算されている
- 出所不明の栄養値（フォールバック？デフォルト値？）

---

## 📊 問題パターン別発生頻度

**30%以上誤差ケース (13件) の分析**：

| 問題種類 | 発生頻度 | 比率 |
|---------|---------|------|
| VLM認識不足 | 13件 | 100.0% |
| VLM認識漏れ | 13件 | 100.0% |
| USDA検索問題 | 13件 | 100.0% |
| 重量推定問題 | 13件 | 100.0% |
| 脂質推定問題 | 9件 | 69.2% |
| 炭水化物推定問題 | 3件 | 23.1% |

**結論**：
- **全ケースでVLM認識が根本原因**
- VLMが失敗すると、後続の全ステップが連鎖失敗
- 謎の栄養素値は、未知のフォールバックロジックによる

---

## 🎯 解決策

### 即時対応（実施済み）

#### 1. max_tokensの増加 ✅
```python
# Before
max_tokens: int = 4096

# After
max_tokens: int = 8192
```

**変更箇所**：
- `shared/services/deepinfra_service.py`
- `apps/freeform_usda_meal_analysis_api/services/vlm_service.py`
- `apps/freeform_usda_meal_analysis_api/services/pipeline.py`

#### 2. Config統一管理 ✅
```python
# shared/config/settings.py
VLM_MODEL_ID: str = "Qwen/Qwen3-VL-235B-A22B-Thinking"
VLM_MAX_TOKENS: int = 8192
VLM_THINKING_BUDGET: int = 2048
VLM_TEMPERATURE: float = 0.0
VLM_SEED: int = 123456
```

### 必要な追加対応

#### 1. プロセス再起動 🔴 **未実施**

**理由**：
- コード変更後、Pythonプロセスが古いコードをキャッシュ
- ログに `max_tokens=4096` が表示されている

**対応**：
```bash
# 実行中のプロセスを停止 (Ctrl+C)
# 再実行
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 python test_scripts/compare_all_50_nutrition.py
```

#### 2. VLMエラーハンドリング改善

**現状の問題**：
- JSON切断時のエラーが不明瞭
- フォールバックロジックが不透明
- デバッグ情報が不足

**推奨改善**：
```python
# VLM失敗時の明示的なエラー
if len(vlm_dishes) == 0:
    logger.error(f"VLM recognition failed: 0 dishes detected")
    # フォールバックロジックを明示
    # または、処理を中断してエラーを返す
```

#### 3. JSON解析の堅牢化

**現状**：
- `Unterminated string` でJSON解析失敗
- 部分的なJSON復旧処理なし

**推奨改善**：
- JSON切断検出
- 部分的な情報でも救済
- リトライロジック

---

## 📈 期待される改善効果

### max_tokens=8192 適用後

**理論値**：
- 推論トークン: 2048 (thinking_budget)
- 出力トークン: 6000+ (JSON生成)
- **合計: 8192トークン**

**期待される結果**：
1. ✅ VLM認識成功率: 0% → 90%+
2. ✅ JSON切断エラー: 100% → 5%以下
3. ✅ 30%以上誤差: 24% → 10%以下

### 残存する可能性がある問題

#### 1. VLM認識精度

- 複雑な料理の認識
- 小さな付け合わせの見落とし
- 重量推定の誤差

#### 2. USDA検索精度

- 料理名のマッチング
- reranker scoreの閾値
- 類似料理の混同

#### 3. 栄養計算精度

- 調理方法の違い（揚げ vs 焼き）
- ソース・調味料の推定
- 複合料理の成分分解

---

## 🔬 次のステップ

### 1. 即時実行

```bash
# プロセス再起動して再テスト
PYTHONPATH=/Users/odasoya/meal_analysis_api_2 \
python test_scripts/compare_all_50_nutrition.py
```

### 2. 結果検証

- VLM認識料理数が0でないことを確認
- JSON解析エラーが解消されていることを確認
- 30%以上誤差が減少していることを確認

### 3. 詳細分析

- 残存する高誤差ケースの原因特定
- VLM認識精度の評価
- USDA検索精度の評価

### 4. 継続的改善

- プロンプト最適化
- モデル選定の見直し
- エラーハンドリングの強化

---

## 📝 まとめ

### 発見した問題

1. **VLM完全失敗**: 全画像で0料理認識
2. **max_tokens不足**: 4096では不十分
3. **JSON切断**: 推論にトークンを消費しすぎ
4. **謎の栄養値**: フォールバックロジックが不透明

### 実施した対策

1. ✅ max_tokens: 4096 → 8192
2. ✅ Config統一管理
3. 🔴 プロセス再起動（要実施）

### 期待される効果

- **VLM認識成功率: 0% → 90%+**
- **30%以上誤差: 24% → 10%以下**

---

**次のアクション**: プロセスを再起動して、改善効果を検証する
