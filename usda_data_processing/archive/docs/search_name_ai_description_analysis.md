# search_name と ai_description の妥当性分析レポート

## 📊 概要

`usda_raw_ingredients_split_cleaned.json` と `usda_prepared_ingredients_split_cleaned.json` の全カテゴリから、**search_name** と **ai_description** の生成品質を分析しました。

**使用用途**:
- **search_name**: Word Query API で、ユーザーが料理や食材を登録する際の予測候補を優先順位とともに表示
- **ai_description**: Word Query API の tier system で使用予定

---

## ✅ 良好なケース（大多数）

### 典型的な良い例

```json
{
  "description": "Cookie, chocolate chip",
  "search_name": "Cookie",
  "ai_description": "chocolate chip"
}
```

✓ **主要な食品名** (`Cookie`) が `search_name` に適切に設定
✓ **詳細情報** (`chocolate chip`) が `ai_description` に分離
✓ ユーザーが「cookie」で検索すれば確実にヒット

### 他の良い例

| description | search_name | ai_description | 評価 |
|------------|-------------|----------------|------|
| Cookie, almond | Cookie | almond | ✅ 適切 |
| Butter, light | Butter | light | ✅ 適切 |
| Coffee, espresso | Coffee | espresso | ✅ 適切 |
| Blueberries, raw | Blueberries | raw | ✅ 適切 |
| Beer, light | Beer | light | ✅ 適切 |

**全体の約99%**は適切に生成されています。

---

## ❌ 問題のあるケース（11件）

### 問題の内訳

| データセット | 問題件数 | 全体件数 | 割合 |
|-------------|---------|---------|------|
| **Raw Ingredients** | 3件 | 1,399件 | 0.21% |
| **Prepared Ingredients** | 8件 | 143件 | 5.59% |
| **合計** | **11件** | 1,542件 | 0.71% |

### 問題パターン

**問題**: `search_name` が配列で、元の description の**主要な単語が欠けている**

#### 例1: Bread 関連（最も深刻）

```json
{
  "description": "Bread, French or Vienna, toasted",
  "search_name": ["French", "Vienna"],  // ❌ "Bread" が欠けている！
  "ai_description": "toasted"
}
```

**影響**:
- ❌ ユーザーが「**bread**」で検索しても**ヒットしない**
- ⚠️  「French」や「Vienna」でしかマッチしない
- 🔍 Word Query API の基本機能が機能しない

#### 例2: Cheese 関連

```json
{
  "description": "Cheese, Gouda or Edam",
  "search_name": ["Gouda", "Edam"],  // ❌ "Cheese" が欠けている！
  "ai_description": null
}
```

**影響**:
- ❌ ユーザーが「**cheese**」で検索しても**ヒットしない**
- ⚠️  チーズの種類（Gouda, Edam）でしかマッチしない

#### 例3: Topping 関連

```json
{
  "description": "Topping, butterscotch or caramel",
  "search_name": ["butterscotch", "caramel"],  // ❌ "Topping" が欠けている！
  "ai_description": null
}
```

---

### 🔴 深刻な問題例（完全リスト）

#### Raw Ingredients (3件)

| Code | Description | search_name | 問題 |
|------|------------|-------------|------|
| 14105010 | Cheese, Gouda or Edam | `['Gouda', 'Edam']` | ❌ 'Cheese' が欠如 |
| 91304010 | Topping, butterscotch or caramel | `['butterscotch', 'caramel']` | ❌ 'Topping' が欠如 |
| 91304060 | Topping, nuts and syrup | `['nuts', 'syrup']` | ❌ 'Topping' が欠如 |

#### Prepared Ingredients (8件) - すべて Bread 関連

| Code | Description | search_name | 問題 |
|------|------------|-------------|------|
| 51107040 | Bread, French or Vienna, toasted | `['French', 'Vienna']` | ❌ 'Bread' が欠如 |
| 51109040 | Bread, Italian, Grecian, Armenian, toasted | `['Italian', 'Grecian', 'Armenian']` | ❌ 'Bread' が欠如 |
| 51301020 | Bread, wheat or cracked wheat, toasted | `['Wheat', 'cracked wheat']` | ❌ 'Bread' が欠如 |
| 51301050 | Bread, wheat or cracked wheat, from home recipe, toasted | `['Wheat', 'cracked wheat']` | ❌ 'Bread' が欠如 |
| 51301130 | Bread, wheat or cracked wheat, with raisins, toasted | `['Wheat', 'cracked wheat']` | ❌ 'Bread' が欠如 |
| 51301520 | Bread, wheat or cracked wheat, reduced calorie/high fiber, toasted | `['Wheat', 'cracked wheat']` | ❌ 'Bread' が欠如 |
| 51301550 | Bread, French or Vienna, whole wheat, toasted | `['French', 'Vienna']` | ❌ 'Bread' が欠如 |
| 51401040 | Bread, marble rye and pumpernickel, toasted | `['Marble rye', 'Pumpernickel']` | ❌ 'Bread' が欠如 |

---

## 💡 改善提案

### 基本方針

**search_name は常に主要な食品名を含めるべき**

| 要素 | 役割 | 内容 |
|------|------|------|
| **search_name** | 検索マッチング | **主要な食品カテゴリ**（Bread, Cheese, Cookie など） |
| **ai_description** | Tier system | **詳細情報・バリエーション**（種類、調理法、フレーバーなど） |

### 具体的な改善案

#### 改善案 1: Bread, French or Vienna, toasted

```json
// ❌ 現状
{
  "search_name": ["French", "Vienna"],
  "ai_description": "toasted"
}

// ✅ 改善案
{
  "search_name": "Bread",
  "ai_description": "French, Vienna, toasted"
}
```

**理由**:
- 主要な食品名 "Bread" を `search_name` に
- バリエーション（French, Vienna）と状態（toasted）を `ai_description` に統合

#### 改善案 2: Cheese, Gouda or Edam

```json
// ❌ 現状
{
  "search_name": ["Gouda", "Edam"],
  "ai_description": null
}

// ✅ 改善案
{
  "search_name": "Cheese",
  "ai_description": "Gouda, Edam"
}
```

**理由**:
- 主要な食品名 "Cheese" を `search_name` に
- チーズの種類（Gouda, Edam）を `ai_description` に

#### 改善案 3: Muffin, English, oat bran

```json
// ❌ 現状（部分的に問題）
{
  "search_name": ["Muffin", "oat bran"],
  "ai_description": "English"
}

// ✅ 改善案
{
  "search_name": "Muffin",
  "ai_description": "English, oat bran"
}
```

**理由**:
- `search_name` はシンプルに "Muffin" のみ
- 詳細情報（English, oat bran）をすべて `ai_description` に統合

---

## 🎯 Word Query API での使用シーンへの影響

### シナリオ 1: ユーザーが「bread」と入力

| 状況 | 現状 | 改善後 |
|------|------|--------|
| **検索結果** | ❌ "Bread, French or Vienna" がヒットしない | ✅ すべての Bread がヒット |
| **ユーザー体験** | 😡 期待した結果が出ない | 😊 期待通り |

### シナリオ 2: ユーザーが「french bread」と入力

| 状況 | 現状 | 改善後 |
|------|------|--------|
| **マッチング** | ⚠️  "French" のみでマッチ（不完全） | ✅ "Bread" でマッチ |
| **ランキング** | - | ✅ Tier system で "French, Vienna" を考慮して上位表示 |

### シナリオ 3: ユーザーが「cheese」と入力

| 状況 | 現状 | 改善後 |
|------|------|--------|
| **検索結果** | ❌ "Cheese, Gouda or Edam" がヒットしない | ✅ すべての Cheese がヒット |
| **ユーザー体験** | 😡 Gouda や Edam と直接入力しないとダメ | 😊 期待通り |

---

## 📝 推奨される修正アプローチ

### オプション 1: AI プロンプトの改善（推奨）

元の AI 処理（split 処理）のプロンプトを修正：

```
【修正前のルール推測】
- "X or Y" のパターンがある場合、[X, Y] を search_name に抽出

【修正後のルール】
- search_name: 常に元の description の最初の主要単語（カンマの前）
- ai_description: それ以降の詳細情報（バリエーション、調理法、状態など）

特別ルール:
- "X or Y" パターンは ai_description に含める
- search_name は配列ではなく文字列にする
```

### オプション 2: ポスト処理での修正

既存のデータに対して、以下のロジックで修正：

```python
if isinstance(search_name, list):
    # 元の description の最初の単語を抽出
    main_word = description.split(',')[0].strip()

    # search_name を主要単語に置き換え
    search_name = main_word

    # ai_description に元の search_name の内容を統合
    if ai_description:
        ai_description = ', '.join(search_name_list) + ', ' + ai_description
    else:
        ai_description = ', '.join(search_name_list)
```

---

## 📊 まとめ

### 現状評価

| 評価項目 | 評価 | 詳細 |
|---------|------|------|
| **全体品質** | ⭐⭐⭐⭐☆ (4/5) | 99%以上は適切に生成 |
| **Raw Ingredients** | ⭐⭐⭐⭐⭐ (5/5) | 0.21%のみ問題 |
| **Prepared Ingredients** | ⭐⭐⭐⭐☆ (4/5) | 5.59%に問題（主に Bread 関連） |

### 重要性

| 側面 | 影響度 | 説明 |
|------|--------|------|
| **ユーザー体験** | 🔴 **高** | 基本的な検索（"bread", "cheese"）が機能しない |
| **Word Query API の信頼性** | 🔴 **高** | コア機能の検索精度に直結 |
| **修正の緊急度** | 🟡 **中** | 件数は少ない（11件）が、影響は大きい |

### 推奨アクション

1. ✅ **即座に修正すべき**: Bread 関連 8件（Prepared Ingredients）
2. ✅ **優先修正**: Cheese, Topping 関連 3件（Raw Ingredients）
3. 🔧 **根本対策**: AI プロンプトの改善（今後の再生成時に同じ問題を防ぐ）

---

## 🔍 検証方法

修正後、以下のテストケースで検証：

```python
# テストケース
test_cases = [
    {"input": "bread", "expected": "Bread, French or Vienna"},
    {"input": "french bread", "expected": "Bread, French or Vienna (高ランク)"},
    {"input": "cheese", "expected": "Cheese, Gouda or Edam"},
    {"input": "gouda", "expected": "Cheese, Gouda or Edam (tier system で検知)"},
]
```

---

**作成日**: 2025-10-14
**分析対象**:
- `usda_raw_ingredients_split_cleaned.json` (1,399件)
- `usda_prepared_ingredients_split_cleaned.json` (143件)
