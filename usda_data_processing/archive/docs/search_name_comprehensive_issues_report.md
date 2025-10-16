# search_name 徹底分析レポート - 全問題点の特定

## 🎯 質問への回答

**質問**: 「それ以外はbread以外は全て大丈夫そう？徹底的に調べて」

**回答**: ❌ **いいえ、Bread以外にも問題があります。**

---

## 📊 徹底分析の結果サマリー

### 問題件数

| データセット | 問題件数 | 全体件数 | 割合 |
|-------------|---------|---------|------|
| **Raw Ingredients** | 8件 | 1,399件 | 0.57% |
| **Prepared Ingredients** | 8件 | 143件 | 5.59% |
| **合計** | **16件** | 1,542件 | 1.04% |

### 問題の内訳

| カテゴリ | 件数 | データセット |
|---------|------|-------------|
| **Bread** | 8件 | Prepared |
| **Topping** | 5件 | Raw |
| **Icing** | 2件 | Raw |
| **Cheese** | 1件 | Raw |

---

## 🔴 問題の詳細リスト

### Raw Ingredients (8件)

#### 1. Cheese カテゴリ (1件)

| Code | Description | search_name | ai_description | 問題 |
|------|------------|-------------|----------------|------|
| 14105010 | Cheese, Gouda or Edam | `['Gouda', 'Edam']` | `null` | ❌ "Cheese" で検索できない |

**推奨修正**:
```json
{
  "search_name": "Cheese",
  "ai_description": "Gouda, Edam"
}
```

#### 2. Topping カテゴリ (5件)

| Code | Description | search_name | ai_description | 問題 |
|------|------------|-------------|----------------|------|
| 91304010 | Topping, butterscotch or caramel | `['butterscotch', 'caramel']` | `null` | ❌ "Topping" で検索できない |
| 91304060 | Topping, nuts and syrup | `['nuts', 'syrup']` | `null` | ❌ "Topping" で検索できない |
| 91304020 | Topping, chocolate | `"chocolate"` | `"topping"` | ❌ "Topping" で検索できない |
| 91304030 | Topping, fruit | `"fruit"` | `"topping"` | ❌ "Topping" で検索できない |
| 91304040 | Topping, marshmallow | `"marshmallow"` | `"topping"` | ❌ "Topping" で検索できない |

**推奨修正** (例: Topping, chocolate):
```json
{
  "search_name": "Topping",
  "ai_description": "chocolate"
}
```

#### 3. Icing カテゴリ (2件)

| Code | Description | search_name | ai_description | 問題 |
|------|------------|-------------|----------------|------|
| 91305010 | Icing, chocolate | `"chocolate"` | `"icing"` | ❌ "Icing" で検索できない |
| 91305020 | Icing, white | `"white"` | `"icing"` | ❌ "Icing" で検索できない |

**推奨修正** (例: Icing, chocolate):
```json
{
  "search_name": "Icing",
  "ai_description": "chocolate"
}
```

---

### Prepared Ingredients (8件)

#### Bread カテゴリ (8件) - **すべて Yeast breads カテゴリ**

| Code | Description | search_name | ai_description | 問題 |
|------|------------|-------------|----------------|------|
| 51107040 | Bread, French or Vienna, toasted | `['French', 'Vienna']` | `"toasted"` | ❌ "Bread" で検索できない |
| 51109040 | Bread, Italian, Grecian, Armenian, toasted | `['Italian', 'Grecian', 'Armenian']` | `"toasted"` | ❌ "Bread" で検索できない |
| 51301020 | Bread, wheat or cracked wheat, toasted | `['Wheat', 'cracked wheat']` | `"toasted"` | ❌ "Bread" で検索できない |
| 51301050 | Bread, wheat or cracked wheat, from home recipe, toasted | `['Wheat', 'cracked wheat']` | `"toasted, from home recipe, from bakery"` | ❌ "Bread" で検索できない |
| 51301130 | Bread, wheat or cracked wheat, with raisins, toasted | `['Wheat', 'cracked wheat']` | `"toasted, with raisins"` | ❌ "Bread" で検索できない |
| 51301520 | Bread, wheat or cracked wheat, reduced calorie/high fiber, toasted | `['Wheat', 'cracked wheat']` | `"toasted, reduced calorie, high fiber"` | ❌ "Bread" で検索できない |
| 51301550 | Bread, French or Vienna, whole wheat, toasted | `['French', 'Vienna']` | `"toasted, whole wheat"` | ❌ "Bread" で検索できない |
| 51401040 | Bread, marble rye and pumpernickel, toasted | `['Marble rye', 'Pumpernickel']` | `"toasted"` | ❌ "Bread" で検索できない |

**推奨修正** (例: Bread, French or Vienna, toasted):
```json
{
  "search_name": "Bread",
  "ai_description": "French, Vienna, toasted"
}
```

---

## 🔍 問題のパターン分析

### 共通パターン

すべての問題は以下のパターンに該当します：

```
元の description: "A, B"
                    ↓
現状（問題）:
  search_name: B（または [B1, B2]）
  ai_description: (その他の情報)
                    ↓
問題: ユーザーが "A" で検索してもヒットしない
```

### 具体例

| description | 現状 search_name | 主要単語 | 問題 |
|------------|-----------------|---------|------|
| **Bread**, French or Vienna | `['French', 'Vienna']` | Bread | ❌ Bread で検索不可 |
| **Cheese**, Gouda or Edam | `['Gouda', 'Edam']` | Cheese | ❌ Cheese で検索不可 |
| **Topping**, chocolate | `"chocolate"` | Topping | ❌ Topping で検索不可 |
| **Icing**, white | `"white"` | Icing | ❌ Icing で検索不可 |

---

## ✅ 問題ないケース（参考）

以下のケースは**意図的な設計**で、問題ありません：

### パターン1: "形容詞 + 名詞" で名詞が主要単語

| description | search_name | ai_description | 評価 |
|------------|-------------|----------------|------|
| Cheese flavored **corn snacks** | `"Corn snacks"` | `"cheese flavored"` | ✅ 適切 |
| Baby Toddler **beef** | `"beef"` | `"Baby, Toddler"` | ✅ 適切 |
| Mayonnaise-type **salad dressing** | `"Mayonnaise"` | `"type salad dressing"` | ✅ 適切 |
| Vegan **mayonnaise** | `"Mayonnaise"` | `"vegan"` | ✅ 適切 |

**理由**:
- "Cheese flavored corn snacks" の場合、ユーザーは「corn snacks」で検索するのが自然
- "cheese" は ai_description に含まれているため、tier system で処理可能
- 主要な食品カテゴリ（Corn snacks, Beef, Mayonnaise）が search_name に入っている

### パターン2: "or" を含むが主要単語も含む

| description | search_name | ai_description | 評価 |
|------------|-------------|----------------|------|
| Cookie, chocolate or fudge | `['Cookie', 'fudge']` | `"chocolate"` | ✅ 適切 |
| Cookie, butter or sugar | `['Cookie', 'sugar']` | `"butter"` | ✅ 適切 |
| Cheese, Blue or Roquefort | `['Blue cheese', 'Roquefort']` | `null` | ✅ 適切 |

**理由**: 主要単語 "Cookie" または "Cheese" が search_name の配列に含まれている

---

## 📈 統計情報

### search_name のデータ型分布

| データセット | 文字列 | 配列 | 合計 |
|-------------|--------|------|------|
| **Raw Ingredients** | 1,214件 (86.8%) | 185件 (13.2%) | 1,399件 |
| **Prepared Ingredients** | 128件 (89.5%) | 15件 (10.5%) | 143件 |

### 配列の内訳（Raw Ingredients）

| 種類 | 件数 | 説明 |
|------|------|------|
| ✅ 問題なし（"or" パターンで主要単語含む） | 95件 | Cookie, chocolate or fudge など |
| ✅ 問題なし（配列だが主要単語含む） | 87件 | Crackers, multigrain など |
| ❌ **問題あり（主要単語欠如）** | **3件** | Cheese, Topping 配列 |
| **合計** | 185件 | |

---

## 💡 修正方針

### 基本ルール

```
search_name: 常に元の description の最初の主要単語（カンマの前）
ai_description: それ以降のすべての詳細情報

例外:
- "形容詞 + 名詞" の場合、名詞が主要単語
  例: "Cheese flavored corn snacks" → search_name: "Corn snacks"
```

### 修正スクリプト（疑似コード）

```python
# パターン1: "A, B" → search_name に "B" が入っている場合
if description.startswith("Bread,") and "Bread" not in search_name:
    search_name = "Bread"
    ai_description = [元の search_name の内容] + [元の ai_description]

# パターン2: "A, B or C" → search_name が [B, C] の場合
if description.startswith("Cheese,") and "Cheese" not in search_name:
    search_name = "Cheese"
    ai_description = [元の search_name の内容]

# パターン3: 同様に Topping, Icing にも適用
```

---

## 🎯 まとめ

### ❌ 問題のあるケース

- **合計 16件** (全体の1.04%)
- **Bread**: 8件（Prepared Ingredients）
- **Topping**: 5件（Raw Ingredients）
- **Icing**: 2件（Raw Ingredients）
- **Cheese**: 1件（Raw Ingredients）

### ✅ 問題ないケース

- **約98.96%** は適切に生成されている
- "Cheese flavored corn snacks", "Baby Toddler beef" など、意図的な設計

### 🔧 推奨アクション

1. **即座に修正**: 16件の foodCode を特定して修正
2. **根本対策**: AI プロンプトの改善（今後の再生成時に防ぐ）
3. **検証**: 修正後、Word Query API でテスト

---

## 📋 修正用チェックリスト

### Raw Ingredients (8件)

- [ ] 14105010 - Cheese, Gouda or Edam
- [ ] 91304010 - Topping, butterscotch or caramel
- [ ] 91304060 - Topping, nuts and syrup
- [ ] 91304020 - Topping, chocolate
- [ ] 91304030 - Topping, fruit
- [ ] 91304040 - Topping, marshmallow
- [ ] 91305010 - Icing, chocolate
- [ ] 91305020 - Icing, white

### Prepared Ingredients (8件)

- [ ] 51107040 - Bread, French or Vienna, toasted
- [ ] 51109040 - Bread, Italian, Grecian, Armenian, toasted
- [ ] 51301020 - Bread, wheat or cracked wheat, toasted
- [ ] 51301050 - Bread, wheat or cracked wheat, from home recipe, toasted
- [ ] 51301130 - Bread, wheat or cracked wheat, with raisins, toasted
- [ ] 51301520 - Bread, wheat or cracked wheat, reduced calorie/high fiber, toasted
- [ ] 51301550 - Bread, French or Vienna, whole wheat, toasted
- [ ] 51401040 - Bread, marble rye and pumpernickel, toasted

---

**作成日**: 2025-10-14
**分析対象**: 全1,542件のUSDA食材データ
**分析手法**: 徹底的な全件チェック
