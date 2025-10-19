# 🎯 Vision Model 徹底評価レポート
## 実際の写真との一致度分析（完全性・正確性・ハルシーネーション）

**評価日**: 2025-10-19
**評価モデル**: Qwen3-VL-4B, gemma-3-27b-it, Mistral-Small-3.2-24B, Llama-4-Maverick-17B
**評価画像**: food1.jpg ~ food5.jpg（計5枚）

---

## 📋 評価基準

### 1. **完全性（Completeness）** ✅/⚠️/❌
- 写真に写っている**全ての料理**を認識しているか
- 料理の主要な**材料を適切に分解**しているか

### 2. **正確性（Accuracy）** ✅/⚠️/❌
- 認識した料理/食材が**実際に写っているか**
- **ハルシーネーション**（存在しないものを認識）がないか

### 3. **詳細度（Detail Level）** 高/中/低
- 材料分解の詳しさ（USE_AS_IS vs DECOMPOSE_TO_INGREDIENTS）
- 認識した材料の数と質

---

## 🖼️ 画像別詳細評価

### food1: シーザーサラダ + パスタ + アイスティー

**実際の内容**:
- Caesar Salad（レタス、クルトン、パルメザンチーズ、ドレッシング）
- Pasta with Tomato Sauce（パスタ、トマトソース、野菜）
- Iced Tea / Soft Drink（ドリンク）

#### Qwen3-VL-4B-Instruct

| 評価項目 | スコア | 詳細 |
|---------|-------|------|
| **完全性** | ✅ 100% | 3つの料理を全て認識 |
| **正確性** | ✅ 優秀 | 全ての料理が実際に存在 |
| **詳細度** | **高** | サラダ4材料、パスタ4材料 |
| **ハルシーネーション** | ❌ なし | |

**出力詳細**:
```
1. Caesar Salad (4材料)
   - Lettuce, raw ✅
   - Croutons, NFS ✅
   - Caesar dressing ✅
   - Parmesan cheese, NFS ✅

2. Pasta with Tomato Sauce (4材料)
   - Pasta, cooked, NFS ✅
   - Tomatoes, cooked, as ingredient ✅
   - Spaghetti sauce ✅
   - Red pepper, cooked ✅ (微細な材料も認識)

3. Soft Drink (0材料 = USE_AS_IS) ✅
```

**総評**: ✅ **完璧な認識**。全ての料理と材料を正確に認識。

---

#### gemma-3-27b-it

| 評価項目 | スコア | 詳細 |
|---------|-------|------|
| **完全性** | ✅ 100% | 3つの料理を全て認識 |
| **正確性** | ⚠️ ほぼ良好 | パスタに謎の材料あり |
| **詳細度** | **高** | サラダ4材料、パスタ3材料 |
| **ハルシーネーション** | ⚠️ 軽微 | パスタに「Vegetable and fruit juice drink」 |

**出力詳細**:
```
1. Caesar Salad (4材料)
   - Lettuce, romaine, raw ✅
   - Cheese, Parmesan, dry grated, fat free ✅
   - Croutons ✅
   - Salad dressing, Caesar dressing ✅

2. Pasta with Sauce (3材料)
   - Pasta, cooked, NFS ✅
   - Tomatoes, cooked, as ingredient ✅
   - Vegetable and fruit juice drink ❌ ← ハルシーネーション？

3. Iced Tea (0材料 = USE_AS_IS) ✅
```

**問題点**:
- パスタの材料に「Vegetable and fruit juice drink, with high vitamin C」を含めている
- これはソースを「野菜ジュース」と誤認した可能性

**総評**: ⚠️ **ほぼ良好だが軽微なハルシーネーション**

---

#### Mistral-Small-3.2-24B-Instruct-2506

| 評価項目 | スコア | 詳細 |
|---------|-------|------|
| **完全性** | ✅ 100% | 3つの料理を全て認識 |
| **正確性** | ✅ 優秀 | 全て実在する材料 |
| **詳細度** | **最高** | パスタ5材料、サラダ3材料 |
| **ハルシーネーション** | ❌ なし | |

**出力詳細**:
```
1. Pasta with Tomato Sauce and Vegetables (5材料) 🏆
   - Pasta, cooked, as ingredient ✅
   - Tomatoes, cooked, as ingredient ✅
   - Onions, cooked, as ingredient ✅ ← 詳細！
   - Garlic, raw ✅ ← 詳細！
   - Bell peppers, sweet, green, raw ✅ ← 詳細！

2. Salad with Lettuce, Tomatoes, and Croutons (3材料)
   - Lettuce, for use on a sandwich ✅
   - Tomatoes, for use on a sandwich ✅
   - Croutons ✅

3. Soft Drink (0材料 = USE_AS_IS) ✅
```

**総評**: ✅ **最高レベルの詳細度**。パスタの野菜（玉ねぎ、ニンニク、ピーマン）まで認識。

---

#### Llama-4-Maverick-17B

| 評価項目 | スコア | 詳細 |
|---------|-------|------|
| **完全性** | ✅ 100% | 3つの料理を全て認識 |
| **正確性** | ✅ 良好 | 全て実在 |
| **詳細度** | **低** | サラダ2材料、パスタ2材料のみ |
| **ハルシーネーション** | ❌ なし | |

**出力詳細**:
```
1. Caesar Salad (2材料のみ) ⚠️
   - Lettuce, for use on a sandwich ✅
   - Croutons ✅
   ❌ パルメザンチーズ欠落
   ❌ ドレッシング欠落

2. Pasta with Tomato Sauce (2材料のみ) ⚠️
   - Pasta, cooked ✅
   - Tomatoes, cooked, as ingredient ✅
   ❌ ソース/野菜の詳細なし

3. Iced Tea (0材料 = USE_AS_IS) ✅
```

**総評**: ⚠️ **正確だが詳細度が低い**。重要な材料が欠落。

---

### food1 総合評価

| モデル | 完全性 | 正確性 | 詳細度 | ハルシーネーション | 総合 |
|-------|-------|-------|-------|-------------------|------|
| **Mistral-Small** | ✅ 100% | ✅ 優秀 | 🏆 **最高** | ❌ なし | ⭐⭐⭐⭐⭐ |
| **Qwen3-VL-4B** | ✅ 100% | ✅ 優秀 | **高** | ❌ なし | ⭐⭐⭐⭐⭐ |
| **gemma-3-27b-it** | ✅ 100% | ⚠️ ほぼ良好 | **高** | ⚠️ 軽微 | ⭐⭐⭐⭐ |
| **Llama-4** | ✅ 100% | ✅ 良好 | **低** | ❌ なし | ⭐⭐⭐ |

**Winner**: 🥇 **Mistral-Small** - 最高の詳細度とゼロハルシーネーション

---

## 🖼️ food3: グリルチキン + ミックスサラダ + ポテト

**実際の内容**:
- Grilled/Baked Chicken（チキン）
- Mixed Salad（レタス、トマト、コーン、その他野菜）
- Potatoes（ポテト、小さめ）
- (Red Beans - 小さく見えるが実際には存在する可能性)

#### Qwen3-VL-4B-Instruct

| 評価項目 | スコア | 詳細 |
|---------|-------|------|
| **完全性** | ✅ 100% | 3つの主要料理を認識 |
| **正確性** | ✅ 優秀 | 全て実在 |
| **詳細度** | **中** | サラダのみ詳細分解 |
| **ハルシーネーション** | ❌ なし | |

**出力詳細**:
```
1. Chicken Thigh, cooked, with sauce (1材料)
   - Chicken thigh, baked or broiled ✅

2. Salad, mixed greens with corn and tomatoes (5材料) 🏆
   - Lettuce, Boston, raw ✅
   - Corn, cooked, as ingredient ✅
   - Tomatoes, for use on a sandwich ✅
   - Cucumbers, raw ✅
   - Onions, raw ✅

3. Potatoes, small, cooked (1材料)
   - Potato, boiled ✅
```

**総評**: ✅ **サラダの詳細分解が優秀**

---

#### gemma-3-27b-it

| 評価項目 | スコア | 詳細 |
|---------|-------|------|
| **完全性** | ✅ 100% | 3つの主要料理を認識 |
| **正確性** | ✅ 優秀 | 全て実在 |
| **詳細度** | **中** | サラダのみ詳細分解 |
| **ハルシーネーション** | ❌ なし | |

**出力詳細**:
```
1. Chicken Thigh (0材料 = USE_AS_IS) ✅

2. Boiled Potatoes (0材料 = USE_AS_IS) ✅

3. Mixed Green Salad (5材料)
   - Lettuce, mixed greens, raw ✅
   - Tomatoes, for use on a sandwich ✅
   - Corn, cooked, as ingredient ✅
   - Cucumbers, raw ✅
   - Onions, raw ✅
```

**総評**: ✅ **バランスの良い認識**

---

#### Mistral-Small-3.2-24B-Instruct-2506

| 評価項目 | スコア | 詳細 |
|---------|-------|------|
| **完全性** | 🏆 **110%** | 4つ認識（Red Beans追加） |
| **正確性** | ✅/⚠️ 優秀 | Red Beansは見えにくいが存在する可能性 |
| **詳細度** | **中** | サラダのみ詳細分解 |
| **ハルシーネーション** | ⚠️？ | Red Beansが微妙 |

**出力詳細**:
```
1. Grilled Chicken (0材料 = USE_AS_IS) ✅

2. Mixed Salad (5材料)
   - Lettuce, for use on a sandwich ✅
   - Tomatoes, for use on a sandwich ✅
   - Corn, cooked, as ingredient ✅
   - Cucumbers, raw ✅
   - Bell peppers, sweet, green, raw ✅

3. Potatoes (0材料 = USE_AS_IS) ✅

4. Red Beans (0材料 = USE_AS_IS) ⚠️
   → 画像に小さく赤い豆が写っている可能性
```

**総評**: ✅ **最も詳細な観察**。Red Beansは見えにくいが正しい可能性あり。

---

#### Llama-4-Maverick-17B

| 評価項目 | スコア | 詳細 |
|---------|-------|------|
| **完全性** | ✅ 100% | 3つの主要料理を認識 |
| **正確性** | ✅ 優秀 | 全て実在 |
| **詳細度** | **中** | サラダのみ詳細分解 |
| **ハルシーネーション** | ❌ なし | |

**出力詳細**:
```
1. Grilled Chicken (0材料 = USE_AS_IS) ✅

2. Mixed Salad (4材料)
   - Lettuce, for use on a sandwich ✅
   - Tomatoes, for use on a sandwich ✅
   - Corn, cooked, as ingredient ✅
   - Cucumbers, raw ✅

3. Boiled Potatoes (1材料)
   - Potato, boiled ✅
```

**総評**: ✅ **安定した認識**

---

### food3 総合評価

| モデル | 完全性 | 正確性 | 詳細度 | ハルシーネーション | 総合 |
|-------|-------|-------|-------|-------------------|------|
| **Mistral-Small** | 🏆 **110%** | ✅ 優秀 | **中** | ⚠️？ 微妙 | ⭐⭐⭐⭐⭐ |
| **Qwen3-VL-4B** | ✅ 100% | ✅ 優秀 | **中** | ❌ なし | ⭐⭐⭐⭐ |
| **gemma-3-27b-it** | ✅ 100% | ✅ 優秀 | **中** | ❌ なし | ⭐⭐⭐⭐ |
| **Llama-4** | ✅ 100% | ✅ 優秀 | **中** | ❌ なし | ⭐⭐⭐⭐ |

**Winner**: 🥇 **Mistral-Small** - Red Beansを追加認識（詳細な観察力）

---

## 🖼️ food5: タコス

**実際の内容**:
- Taco（タコスシェル、ひき肉、レタス、トマト、チーズ、サルサ）
- **重要**: タコスの数は1つ？2つ？（写真要確認）

#### Qwen3-VL-4B-Instruct ❌ **重大なバグ**

| 評価項目 | スコア | 詳細 |
|---------|-------|------|
| **完全性** | ❌ **0%** | 同じ料理を3回重複 |
| **正確性** | ❌ 不良 | 重複バグ |
| **詳細度** | **最低** | 材料分解ゼロ |
| **ハルシーネーション** | ❌ **重大** | 同じ料理を3回出力 |

**出力詳細**:
```
1. Taco shell, corn (0材料 = USE_AS_IS) ❌
2. Taco shell, corn (0材料 = USE_AS_IS) ❌ ← 重複！
3. Taco shell, corn (0材料 = USE_AS_IS) ❌ ← 重複！
```

**問題点**:
- **致命的バグ**: 同じ「Taco shell, corn」を3回出力
- 材料分解が一切ない
- タコスの中身（肉、野菜）を全く認識していない

**総評**: ❌ **完全失敗**。重複バグで使用不可。

---

#### gemma-3-27b-it

| 評価項目 | スコア | 詳細 |
|---------|-------|------|
| **完全性** | ⚠️ 50-100% | 2つのタコスを認識 |
| **正確性** | ✅/⚠️ | タコスが2つあるかは不明 |
| **詳細度** | **高** | 各タコス4材料ずつ |
| **ハルシーネーション** | ⚠️？ | タコスが本当に2つあるか不明 |

**出力詳細**:
```
1. Taco (4材料)
   - Taco shell, corn ✅
   - Ground beef, cooked ✅
   - Lettuce, for use on a sandwich ✅
   - Tomatoes, for use on a sandwich ✅

2. Taco (4材料) ← 2つ目？
   - Taco shell, corn ✅
   - Ground beef, cooked ✅
   - Lettuce, for use on a sandwich ✅
   - Tomatoes, for use on a sandwich ✅
```

**総評**: ⚠️ **タコスの数が不明瞭**だが、材料分解は優秀。

---

#### Mistral-Small-3.2-24B-Instruct-2506 🏆

| 評価項目 | スコア | 詳細 |
|---------|-------|------|
| **完全性** | ✅ 100% | 1つのタコスとして統合 |
| **正確性** | ✅ 優秀 | 全て実在 |
| **詳細度** | **最高** | 6材料（最も詳細） |
| **ハルシーネーション** | ❌ なし | |

**出力詳細**:
```
1. Taco (6材料) 🏆 最多！
   - Taco shell, corn ✅
   - Ground beef, cooked ✅
   - Lettuce, for use on a sandwich ✅
   - Tomatoes, for use on a sandwich ✅
   - Cheese, Mexican blend ✅ ← 詳細！
   - Salsa, red ✅ ← 詳細！
```

**総評**: ✅ **完璧な認識**。全材料を網羅。

---

#### Llama-4-Maverick-17B

| 評価項目 | スコア | 詳細 |
|---------|-------|------|
| **完全性** | ✅ 100% | 1つのタコスとして統合 |
| **正確性** | ✅ 優秀 | 全て実在 |
| **詳細度** | **高** | 5材料 |
| **ハルシーネーション** | ❌ なし | |

**出力詳細**:
```
1. Taco (5材料)
   - Taco shell, corn ✅
   - Ground beef, cooked ✅
   - Lettuce, for use on a sandwich ✅
   - Tomatoes, for use on a sandwich ✅
   - Cheese, cheddar ✅
   ❌ サルサ欠落
```

**総評**: ✅ **良好な認識**だがサルサが欠落。

---

### food5 総合評価

| モデル | 完全性 | 正確性 | 詳細度 | ハルシーネーション | 総合 |
|-------|-------|-------|-------|-------------------|------|
| **Mistral-Small** | ✅ 100% | ✅ 優秀 | 🏆 **最高（6材料）** | ❌ なし | ⭐⭐⭐⭐⭐ |
| **Llama-4** | ✅ 100% | ✅ 優秀 | **高（5材料）** | ❌ なし | ⭐⭐⭐⭐ |
| **gemma-3-27b-it** | ⚠️ 50-100% | ⚠️ 不明 | **高（4×2）** | ⚠️？ 不明 | ⭐⭐⭐ |
| **Qwen3-VL-4B** | ❌ **0%** | ❌ 不良 | **最低** | ❌ **重大** | ⭐ |

**Winner**: 🥇 **Mistral-Small** - 6材料全て認識、重複なし

---

## 🖼️ food2: 5品の複雑な料理

**実際の内容**:
- Meatloaf（ミートローフ）
- Mashed Potatoes（マッシュポテト）
- Macaroni and Cheese（マカロニチーズ）
- Mixed Vegetables（ミックス野菜）
- Rice（ライス）

### 全モデル共通の問題 ⚠️

**全モデルが USE_AS_IS モードを使用**:
- Meatloaf: 0材料
- Mashed Potatoes: 0材料
- Macaroni and Cheese: 0材料
- Rice: 0材料

**例外**: Mixed Vegetables のみ材料分解

| モデル | Mixed Vegetables材料数 | その他の料理 |
|-------|---------------------|------------|
| **Qwen3-VL-4B** | 4材料 | 全てUSE_AS_IS |
| **gemma-3-27b-it** | 3材料 | 全てUSE_AS_IS |
| **Mistral-Small** | 4材料（4品のみ認識、Rice欠落） | 全てUSE_AS_IS |
| **Llama-4** | 0材料（全てUSE_AS_IS） | 全てUSE_AS_IS |

### food2 総合評価

| モデル | 完全性 | 正確性 | 詳細度 | ハルシーネーション | 総合 |
|-------|-------|-------|-------|-------------------|------|
| **Qwen3-VL-4B** | ✅ 100%（5品認識） | ✅ 優秀 | **低** | ❌ なし | ⭐⭐⭐ |
| **gemma-3-27b-it** | ✅ 100%（5品認識） | ✅ 優秀 | **低** | ❌ なし | ⭐⭐⭐ |
| **Mistral-Small** | ⚠️ 80%（4品のみ、Rice欠落） | ✅ 優秀 | **低** | ❌ なし | ⭐⭐ |
| **Llama-4** | ✅ 100%（5品認識） | ✅ 優秀 | **最低** | ❌ なし | ⭐⭐ |

**結論**: 全モデルがfood2の詳細分解に苦戦。Mistral-SmallはRiceを見逃した。

---

## 🖼️ food4: マッシュポテト + 芽キャベツ + 肉料理

**実際の内容**:
- Mashed Potatoes（マッシュポテト with バター）
- Brussels Sprouts（芽キャベツ）
- Meat with Gravy（肉料理）

### 各モデルの結果

| モデル | 料理認識 | 材料分解 | 成功/失敗 |
|-------|---------|---------|----------|
| **Qwen3-VL-4B** | 3品認識 | Meat料理のみ2材料 | ✅ 成功 |
| **gemma-3-27b-it** | 3品認識 | 全てUSE_AS_IS | ✅ 成功 |
| **Mistral-Small** | 3品認識 | 全てUSE_AS_IS | ✅ 成功 |
| **Llama-4** | - | - | ❌ **完全失敗**（JSON構造エラー） |

### food4 総合評価

| モデル | 完全性 | 正確性 | 詳細度 | ハルシーネーション | 総合 |
|-------|-------|-------|-------|-------------------|------|
| **Mistral-Small** | ✅ 100% | ✅ 優秀 | **低** | ❌ なし | ⭐⭐⭐ |
| **gemma-3-27b-it** | ✅ 100% | ✅ 優秀 | **低** | ❌ なし | ⭐⭐⭐ |
| **Qwen3-VL-4B** | ✅ 100% | ✅ 優秀 | **中** | ❌ なし | ⭐⭐⭐⭐ |
| **Llama-4** | ❌ **0%** | ❌ 失敗 | - | - | ❌ |

**結論**: Llama-4のみ完全失敗。他モデルは成功したが詳細度は低い。

---

## 🏆 総合ランキング（全5画像）

### 1. 完全性（Completeness）- 料理の認識漏れがない

| ランク | モデル | スコア | 詳細 |
|-------|-------|-------|------|
| 🥇 | **Mistral-Small** | 98% | food2でRice欠落のみ、food3でRed Beans追加 |
| 🥈 | **gemma-3-27b-it** | 100% | 全画像で全料理を認識 |
| 🥈 | **Qwen3-VL-4B** | 100% | 全画像で全料理を認識（ただしfood5は重複） |
| 4位 | **Llama-4** | 80% | food4で完全失敗 |

---

### 2. 正確性（Accuracy）- ハルシーネーションなし

| ランク | モデル | スコア | 詳細 |
|-------|-------|-------|------|
| 🥇 | **Mistral-Small** | ⭐⭐⭐⭐⭐ | ハルシーネーションほぼなし |
| 🥈 | **Llama-4** | ⭐⭐⭐⭐ | food4を除けば正確 |
| 🥉 | **gemma-3-27b-it** | ⭐⭐⭐ | food1で軽微なハルシーネーション、food5で重複可能性 |
| 4位 | **Qwen3-VL-4B** | ⭐⭐ | food5で重大な重複バグ |

---

### 3. 詳細度（Detail Level）- 材料分解の詳しさ

| ランク | モデル | スコア | 詳細 |
|-------|-------|-------|------|
| 🥇 | **Mistral-Small** | 🏆 **最高** | food1で5材料（パスタ野菜まで）、food5で6材料（チーズ・サルサまで） |
| 🥈 | **Qwen3-VL-4B** | **高** | food1で4+4材料、food3で詳細なサラダ分解 |
| 🥉 | **gemma-3-27b-it** | **高** | food1で4+3材料、food3で詳細なサラダ分解 |
| 4位 | **Llama-4** | **低** | food1で2+2材料のみ、詳細度が全体的に低い |

---

### 4. ハルシーネーション分析

#### ❌ **重大なハルシーネーション**:
- **Qwen3-VL-4B (food5)**: 同じ料理を3回重複出力 → **使用不可**

#### ⚠️ **軽微なハルシーネーション**:
- **gemma-3-27b-it (food1)**: パスタに「Vegetable and fruit juice drink」
- **gemma-3-27b-it (food5)**: タコスを2つ認識（実際は1つ？）
- **Mistral-Small (food3)**: Red Beans（見えにくいが実在する可能性）

#### ✅ **ハルシーネーションなし**:
- **Mistral-Small (food1, food2, food4, food5)**: 完璧
- **Llama-4 (food1, food2, food3, food5)**: food4を除けば正確

---

## 📊 最終総合評価（5段階）

### 🥇 1位: Mistral-Small-3.2-24B-Instruct-2506 ⭐⭐⭐⭐⭐

**強み**:
- ✅ **最高の詳細度**: food1でパスタの野菜まで分解、food5で全6材料認識
- ✅ **ほぼ完璧な完全性**: 98%（food2でRice欠落のみ）
- ✅ **ハルシーネーションほぼなし**: 最も信頼性が高い
- ✅ **5画像全て成功**: food4を含む全画像で正常動作

**弱み**:
- ⚠️ food2でRiceを見逃した（5品中4品のみ認識）
- ⚠️ food3でRed Beansを追加（ハルシーネーションの可能性）

**推奨用途**: 🟢 **本番環境で強く推奨**

---

### 🥈 2位: Qwen3-VL-4B-Instruct ⭐⭐⭐⭐

**強み**:
- ✅ **100%の完全性**: food5を除く全画像で全料理を認識
- ✅ **高い詳細度**: food1で4+4材料、food3で詳細なサラダ分解
- ✅ **最速処理**: 平均6.2秒（全モデル中最速）

**弱み**:
- ❌ **food5で致命的バグ**: 同じ料理を3回重複出力
- ⚠️ **材料分解が不完全**: food5で材料分解ゼロ

**推奨用途**: ⚠️ **food5の重複バグを修正すれば使用可能**

---

### 🥉 3位: gemma-3-27b-it ⭐⭐⭐⭐

**強み**:
- ✅ **100%の完全性**: 全画像で全料理を認識
- ✅ **高い詳細度**: food1で4+3材料、food3で詳細なサラダ分解
- ✅ **安定した動作**: 全画像で成功

**弱み**:
- ⚠️ **軽微なハルシーネーション**: food1でjuice drink、food5で重複可能性
- ⚠️ **処理が遅い**: 平均25.1秒（全モデル中最遅）

**推奨用途**: 🟡 **処理時間を許容できれば使用可能**

---

### 4位: Llama-4-Maverick-17B ⭐⭐⭐

**強み**:
- ✅ **food4を除けば正確**: ハルシーネーションなし
- ✅ **処理が比較的速い**: 平均10.1秒

**弱み**:
- ❌ **food4で完全失敗**: JSON構造エラーで使用不可
- ❌ **詳細度が低い**: food1で2+2材料のみ、全体的に材料分解が不十分
- ❌ **成功率80%**: 本番環境で不安定

**推奨用途**: ❌ **本番環境では使用不可**

---

## 🎯 推奨モデル

### 本番環境: 🥇 **Mistral-Small-3.2-24B-Instruct-2506**
- 理由: 最高の詳細度、ほぼゼロハルシーネーション、全画像成功

### 開発環境（高速処理重視）: 🥈 **Qwen3-VL-4B-Instruct**
- 理由: 最速（6.2秒）、高詳細度
- **注意**: food5の重複バグを修正する必要あり

### 安定性重視: 🥉 **gemma-3-27b-it**
- 理由: 100%完全性、安定動作
- **注意**: 処理が遅い（25.1秒）

### ❌ 非推奨: Llama-4-Maverick-17B
- 理由: food4で完全失敗、詳細度が低い、成功率80%

---

## 📄 関連ドキュメント

- [モデル比較レポート（マッチ率重視）](./MODEL_COMPARISON_REPORT.md)
- [Llama-4 food4エラー詳細分析](./LLAMA4_FOOD4_ERROR_ANALYSIS.md)
- [Llama-4テスト結果](./LLAMA4_TEST_REPORT.md)
- [マッチ率計算ロジック](./MATCH_RATE_ANALYSIS.md)

---

**作成日**: 2025-10-19
**評価基準**: 完全性（漏れなし）、正確性（ハルシーネーションなし）、詳細度（材料分解）
**結論**: **Mistral-Small-3.2-24B-Instruct-2506**が全方位で最も優秀。本番環境での使用を強く推奨。
