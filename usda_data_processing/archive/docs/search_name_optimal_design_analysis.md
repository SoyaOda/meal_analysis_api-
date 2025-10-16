# search_name の最適設計 - Word Query API Tier System 分析

## 🎯 結論

**ユーザーの提案は完全に正しい！**

> "search nameはoriginalの名前に囚われすぎず、ユーザーがどのようにqueryするか、色々なパターンを想定してリスト形式で出力してほしい"

この提案は、**Word Query APIのTier Systemと完璧に相性が良い**設計です。

---

## 🔍 Word Query API Tier System の仕組み

### Tier 階層（nutrition_search.py: 251-289行目）

```python
def determine_match_type(query, explanation, original_name,
                        search_name_list, description):
    stemmed_query = stem_query(query)

    # Tier 1: stemmed_search_nameでの完全一致（最優先）
    for name in search_name_list:
        stemmed_name = stem_query(name) if name else ""
        if stemmed_name == stemmed_query:
            return "tier_1_exact"  # Boost: 15

    # Tier 2: stemmed_descriptionでの完全一致
    if description:
        stemmed_desc = stem_query(description)
        if stemmed_desc == stemmed_query:
            return "tier_2_description"  # Boost: 12

    # Tier 3-7: プレフィックス、部分一致、ファジー...
```

### 重要な発見

**search_name_listの各要素が個別に評価される！**

```python
# nutrition_search.py: 253-256行目
for name in search_name_list:
    stemmed_name = stem_query(name) if name else ""
    if stemmed_name == stemmed_query:
        return "tier_1_exact"
```

つまり：
- `search_name: ["Bread", "French bread", "Vienna bread"]` の場合
- ユーザーが `"bread"` で検索すると
  1. "Bread" → stem: "bread" → **Tier 1マッチ！**
  2. "French bread" → stem: "french bread" → 部分一致でTier 5
  3. "Vienna bread" → stem: "vienna bread" → 部分一致でTier 5

→ **最も高いTier（Tier 1）が優先される**

---

## 📊 現状の問題点

### 現在の設計（問題あり）

```json
{
  "description": "Bread, French or Vienna, toasted",
  "search_name": ["French", "Vienna"],
  "ai_description": "toasted"
}
```

**検索シミュレーション**:

| ユーザー入力 | search_name_list | マッチング結果 | Tier |
|-------------|-----------------|--------------|------|
| `"bread"` | `["French", "Vienna"]` | ❌ どの要素もマッチしない | ヒットしない |
| `"french"` | `["French", "Vienna"]` | ✅ "French" がマッチ | Tier 1 |
| `"french bread"` | `["French", "Vienna"]` | ⚠️  "French" のみ部分マッチ | Tier 5（低優先度） |

**問題**:
- ユーザーが最も検索しそうな `"bread"` でヒットしない
- `"french bread"` も低優先度でしかマッチしない

---

## ✅ 推奨設計（ユーザー提案）

### 改善案: 検索パターンを網羅

```json
{
  "description": "Bread, French or Vienna, toasted",
  "search_name": [
    "Bread",
    "French bread",
    "Vienna bread",
    "French",
    "Vienna",
    "Toasted bread"
  ],
  "ai_description": "toasted"
}
```

**検索シミュレーション**:

| ユーザー入力 | マッチした要素 | Tier | スコア | 順位 |
|-------------|--------------|------|--------|------|
| `"bread"` | `"Bread"` | **Tier 1** | 15 | 🥇 最優先 |
| `"french bread"` | `"French bread"` | **Tier 1** | 15 | 🥇 最優先 |
| `"vienna bread"` | `"Vienna bread"` | **Tier 1** | 15 | 🥇 最優先 |
| `"french"` | `"French"` | **Tier 1** | 15 | 🥇 最優先 |
| `"toasted bread"` | `"Toasted bread"` | **Tier 1** | 15 | 🥇 最優先 |

**利点**:
- ✅ あらゆる検索パターンで**Tier 1（最優先）**でヒット
- ✅ ユーザーの検索意図に完璧に対応
- ✅ ai_descriptionは補足情報として機能

---

## 🧪 具体例で検証

### 例1: Topping, chocolate

#### ❌ 現状（問題）

```json
{
  "description": "Topping, chocolate",
  "search_name": "chocolate",
  "ai_description": "topping"
}
```

| ユーザー入力 | 結果 | Tier |
|-------------|------|------|
| `"topping"` | ❌ ヒットしない | - |
| `"chocolate"` | ✅ Tier 1 | 15 |
| `"chocolate topping"` | ⚠️  "chocolate" のみ部分マッチ | Tier 5 |

#### ✅ 改善案

```json
{
  "description": "Topping, chocolate",
  "search_name": [
    "Topping",
    "Chocolate topping",
    "Chocolate"
  ],
  "ai_description": null
}
```

| ユーザー入力 | マッチした要素 | Tier |
|-------------|--------------|------|
| `"topping"` | ✅ `"Topping"` | **Tier 1** |
| `"chocolate"` | ✅ `"Chocolate"` | **Tier 1** |
| `"chocolate topping"` | ✅ `"Chocolate topping"` | **Tier 1** |

---

### 例2: Cheese, Gouda or Edam

#### ❌ 現状（問題）

```json
{
  "description": "Cheese, Gouda or Edam",
  "search_name": ["Gouda", "Edam"],
  "ai_description": null
}
```

| ユーザー入力 | 結果 | Tier |
|-------------|------|------|
| `"cheese"` | ❌ ヒットしない | - |
| `"gouda cheese"` | ⚠️  "Gouda" のみ部分マッチ | Tier 5 |

#### ✅ 改善案

```json
{
  "description": "Cheese, Gouda or Edam",
  "search_name": [
    "Cheese",
    "Gouda cheese",
    "Edam cheese",
    "Gouda",
    "Edam"
  ],
  "ai_description": null
}
```

| ユーザー入力 | マッチした要素 | Tier |
|-------------|--------------|------|
| `"cheese"` | ✅ `"Cheese"` | **Tier 1** |
| `"gouda"` | ✅ `"Gouda"` | **Tier 1** |
| `"gouda cheese"` | ✅ `"Gouda cheese"` | **Tier 1** |
| `"edam cheese"` | ✅ `"Edam cheese"` | **Tier 1** |

---

## 🎨 設計原則

### search_name の役割（変更後）

**ユーザーが検索しそうなあらゆるパターンを網羅**

```
search_name = [
    基本カテゴリ名,
    カテゴリ名 + バリエーション1,
    カテゴリ名 + バリエーション2,
    バリエーション1,
    バリエーション2,
    カテゴリ名 + 状態,
    ...
]
```

### ai_description の役割（変更後）

**search_nameに含まれない補足情報のみ**

```
ai_description = 補足情報、調理法、ブランド、その他の詳細
```

---

## 💡 実装ガイドライン

### パターン1: "A, B or C" 形式

```
元: "Bread, French or Vienna, toasted"
↓
search_name: [
  "Bread",              # 基本カテゴリ
  "French bread",       # カテゴリ + バリエーション1
  "Vienna bread",       # カテゴリ + バリエーション2
  "Toasted bread",      # カテゴリ + 状態
  "French",             # バリエーション1単体
  "Vienna"              # バリエーション2単体
]
ai_description: null  # すべて search_name に含めたので不要
```

### パターン2: "A, B" 形式（状態・フレーバー）

```
元: "Cookie, chocolate chip"
↓
search_name: [
  "Cookie",             # 基本カテゴリ
  "Chocolate chip cookie",  # カテゴリ + フレーバー
  "Chocolate chip"      # フレーバー単体（任意）
]
ai_description: null
```

### パターン3: 修飾語がある場合

```
元: "Cheese flavored corn snacks"
↓
search_name: [
  "Corn snacks",        # 主要カテゴリ（これが正解）
  "Cheese corn snacks", # 修飾語 + カテゴリ
  "Cheese snacks"       # 別名パターン
]
ai_description: "cheese flavored"  # 修飾語は補足情報
```

---

## 📈 期待される効果

### 1. **検索精度の向上**

- ❌ 現状: "bread" で検索しても French/Vienna bread がヒットしない
- ✅ 改善後: すべてTier 1（最優先）でヒット

### 2. **ユーザー体験の改善**

| シナリオ | 現状 | 改善後 |
|---------|------|--------|
| ユーザーが "bread" と入力 | 😡 期待した結果が出ない | 😊 期待通り |
| ユーザーが "french bread" と入力 | ⚠️  低優先度（Tier 5） | 😊 最優先（Tier 1） |
| ユーザーが "topping" と入力 | 😡 chocolate topping が出ない | 😊 期待通り |

### 3. **Tier Systemとの完璧な親和性**

```python
# Word Query APIのTier判定ロジック
for name in search_name_list:  # ← 配列の各要素を個別評価
    if stemmed_name == stemmed_query:
        return "tier_1_exact"  # 最優先
```

→ **search_nameを配列にして、検索パターンを網羅することで、Tier Systemが最大限活用される**

---

## 🔧 実装方針

### AI プロンプトの改善（推奨）

```
【新しいルール】
search_name: ユーザーが検索しそうなあらゆるパターンを配列で列挙
  - 基本カテゴリ名
  - カテゴリ名 + 各バリエーション
  - バリエーション単体
  - カテゴリ名 + 状態・調理法

ai_description: search_nameに含まれない補足情報のみ
  - ブランド名
  - 詳細な説明
  - その他のメタデータ

【例】
"Bread, French or Vienna, toasted"
→
search_name: ["Bread", "French bread", "Vienna bread", "Toasted bread", "French", "Vienna"]
ai_description: null

"Topping, chocolate"
→
search_name: ["Topping", "Chocolate topping", "Chocolate"]
ai_description: null

"Cookie, chocolate chip"
→
search_name: ["Cookie", "Chocolate chip cookie", "Chocolate chip"]
ai_description: null
```

---

## 📋 まとめ

### ✅ ユーザー提案の妥当性

| 項目 | 評価 | 理由 |
|------|------|------|
| **Tier Systemとの親和性** | ⭐⭐⭐⭐⭐ | 配列の各要素が個別評価されるため完璧にマッチ |
| **ユーザー体験** | ⭐⭐⭐⭐⭐ | あらゆる検索パターンでTier 1ヒット |
| **実装の複雑さ** | ⭐⭐⭐⭐☆ | AIプロンプト改善で対応可能 |
| **検索精度** | ⭐⭐⭐⭐⭐ | 現状の問題（16件）をすべて解決 |

### 🎯 推奨アクション

1. **即座に実施**: AIプロンプトを改善して、search_nameを検索パターン配列として生成
2. **既存データの修正**: 16件の問題ケースを手動修正
3. **全データ再生成**: 新しいプロンプトで全1,542件を再生成（推奨）

---

**結論**: 元の名前に囚われず、**ユーザーがどう検索するかを想定してsearch_nameをリスト形式で設計する**ことは、Word Query APIのTier Systemと**完璧に相性が良い**、最適な設計です。
