# 英語圏レシピ／料理写真ソース 実態調査 — 2026-06-07

`docs/DRIVE_DATASET_INVENTORY_20260607.md` の続き。**目的 = 「料理の完成写真 ↔ 材料+分量（数量+単位）」の対応が zero-manual で取れる英語圏ソース**を、Allrecipes を基準に網羅棚卸し。栄養は「あれば尚良いが必須でない」（材料+分量 → カロリーは DB 導出可）。

## 方法
- 24 エージェント並列（22 サイト個別調査 + recipe-scrapers ロスター列挙 + 公開データセット調査）。各サイトは **実レシピページを WebFetch して①完成写真 ②材料の分量(数量+単位) ③栄養 ④schema.org Recipe JSON-LD を直接確認**し、recipe-scrapers 対応（turnkey 可否）・写真ドメイン・規模・ライセンス・技術障壁(anti-bot/paywall)を評価。
- 結果: 22 サイト中 **high 15 / medium 6 / low 1**。

## 重要な技術的事実
- **recipe-scrapers (hhursev/recipe-scrapers)** は **~643 サイト**対応・統一 API（`title/image/ingredients/yields/nutrients`）。**`.nutrients()` は計算せず、サイトの schema.org JSON-LD の nutrition を抽出するだけ** → 栄養の有無は「サイトが schema.org に栄養を埋めているか」次第（US 食ブログは WP Recipe Maker 系で yes が多い）。ユーザーは既に allrecipes でこの pipeline を使用済。
- **分量の形式**: 大半は `recipeIngredient` 内の **free-text「数量+単位+材料名」**（例 `"0.25 cup olive oil"`）→ 数量/単位/材料を分離する **ingredient-phrase パーサが必要**。King Arthur / Budget Bytes / Tasty は**構造化・グラム重量併記**でフィデリティが高い。
- **scrapeable な main photo** = schema.org `image`/og:image の **styled hero（単品1皿）**。Allrecipes/Food.com はユーザー "Made It" 写真もあるが、それは main image ではない。

---

## Tier 1 — turnkey scrape・アクセス容易・{写真+分量+(栄養)}完備（**最優先**）
JSON-LD あり・recipe-scrapers 対応・通常UAで取得可（anti-bot 障壁が低い）。

| サイト | 規模 | 栄養 | 分量形式 | 写真ドメイン | メモ |
|---|---|---|---|---|---|
| **Food.com** | **~500k** | ✅ | qty+unit text | 実ユーザー写真(単品) | 大規模 + **Kaggle 整形済ミラーあり**(後述)。最有力 |
| **Simply Recipes** | 数千 | ✅ | qty+unit text | styled-pro | Dotdash 編集・栄養充実 |
| **King Arthur Baking** | ~2k | ✅ | **構造化+グラム重量** | styled-pro studio | 分量フィデリティ最高(`2 cups (240g)`) |
| **Budget Bytes** | ~1.2k | ✅ | **構造化** | styled-pro | WPRM・材料コスト+栄養 |
| **Tasty (BuzzFeed)** | ~7.5k | ✅ | **構造化+メトリック** | styled-pro studio | img.buzzfeed.com・単品hero |
| **Skinnytaste** | ~1-2k | ✅ | qty+unit text | styled-pro | カロリー管理特化(栄養が常に詳細) |
| **Minimalist Baker** | ~1.7k | ✅ | qty+unit text | styled-pro | ヴィーガン・単著・静的HTML |
| **RecipeTin Eats** | ~0.5-1.5k | ✅ | qty+unit text(+g併記) | styled-pro | WP Recipe Card・クリーン |
| **Pinch of Yum** | ~1k | ❌(分量✅) | qty+unit text | styled-pro | Tasty Recipes plugin |
| **Epicurious** | **~50k** | ❌(分量✅) | qty+unit text | styled-pro editorial | Condé Nast・大規模・栄養は無し |

## Tier 2 — データ良好だがアクセス摩擦（要 適切UA/proxy/rate-limit・robots 順守）
| サイト | 規模 | 栄養 | 障壁 | メモ |
|---|---|---|---|---|
| **Allrecipes** | 数万+ | ✅ | anti-bot(medium) | **基準**。混在写真(hero=styled)・JSON-LD最クリーン |
| **Taste of Home** | **~250k** | ✅ | 403 anti-bot(headers で可) | 規模大・styled |
| **BBC Good Food** | ~17k | ✅ | medium | 英・専用 scraper・写真高品質 |
| **Serious Eats** | 数千 | △(不安定) | medium | 写真/材料は確実 |
| **Delish** | ~10k | ✅ | anti-bot | styled・専用 scraper |
| **Bon Appétit** | ~10k | ❌ | anti-bot | styled editorial |
| **EatingWell** | ~13k | ✅ | crawler ブロック | 健康系・栄養充実 |
| **The Kitchn** | 数千 | ✅ | anti-bot(403) | styled |
| **Food Network** | 数万 | ❌ | **403 + robots が ClaudeBot/GPTBot/CCBot を明示禁止** | **robots 順守必須**・要注意 |

## Tier 3 — 除外 / 要注意
| サイト | 判定 |
|---|---|
| **NYT Cooking** | ❌ **ペイウォール**(`isAccessibleForFree:false`・有料購読必須) → 除外 |
| **Yummly** | ❌ **2024-12-20 閉鎖**(kitchenaid.com へ 301) → ライブ無し |
| **EatThisMuch** | △ JSON-LD 無し・recipe-scrapers 非対応(要 custom scraper)。構造化分量+グラム+栄養・実ユーザー写真。既に local に保有 |

## 調査外だが有望（recipe-scrapers 対応・追加候補）
ロスター agent が指摘した未調査の有力候補（いずれも栄養・写真・分量が揃いやすい）:
**Love and Lemons / Well Plated / Sally's Baking Addiction / Cookie and Kate / The Mediterranean Dish / Gimme Some Oven**。recipe-scrapers ~643 サイトから英語圏 food-blog を追加抽出可能。

---

## 公開データセット（スクレイプ不要・ダウンロード型）
| データセット | 画像 | 分量 | 栄養 | 規模 | 入手 | 有望度 |
|---|---|---|---|---|---|---|
| ★ **Food.com Kaggle (irkaal)** | URL列 | ✅ **構造化**(`RecipeIngredientParts`/`Quantities`別列) | ✅ `Calories`等 | **522,517** | **公開(Kaggle)** | **high — 最も turnkey**(整形済・画像はURL再DL) |
| **Recipe1M / Recipe1M+** (MIT) | ✅ 88.8万/**1374万枚** | △(数量揃いは~103k) | △(栄養付き~50k) | 100万 recipe | 申請制(研究用) | high(規模最大・但し分量/栄養は部分) |
| **Epicurious Kaggle (images)** | ✅ 同梱 | △ 生テキスト | ❌ | ~13.5k | 公開(CC BY-SA?) | med(画像↔材料 1:1で扱い易) |
| **Eight Portions / RecipeBox** | ✅ ~70k | △ free-text | ❌ | ~125k | 公開 | med(栄養なし・ライセンス不明) |
| **Yummly-28K (ISIA)** | ✅ 1:1 | ❌ **分量なし** | ❌ | 27.6k | 申請制 | low(分量欠落=本用途不足) |
| 参考: **PITA / Picture-to-Amount** | — | — | — | Recipe1M利用 | 論文 | **手法参照**(画像→材料相対分量＝本用途と同方向) |

### 本用途外（認識のみ・材料分量なし）= 列挙
Food-101 / UEC FOOD-100,256 / ISIA Food-500 / Nutrition5k / FoodSeg103 / VireoFood-172,251 — 画像分類・セグメンテーション・栄養回帰用で**材料+分量の構造化対応なし**。

---

## 推奨（zero-manual 優先度）
1. **最速 = Food.com Kaggle (irkaal, 522k)**: 構造化 材料+分量+カロリー+画像URL が既に整形済 → **スクレイプ不要**、DL + 画像URL 再取得のみ。
2. **新規 turnkey scrape = Tier 1**（Food.com / Simply Recipes / King Arthur / Budget Bytes / Tasty / Skinnytaste / Minimalist Baker）。既存 recipe-scrapers + allrecipes pipeline をサイト名追加するだけで拡張可。**King Arthur / Budget Bytes / Tasty は分量がグラム/構造化**で最良。
3. **大規模画像 = Recipe1M+**（研究ライセンス・申請）。
4. **大規模 scrape = Taste of Home(~250k) / Food.com(~500k)**（要 header/proxy/robots 順守）。
5. **回避**: NYT(paywall) / Yummly(閉鎖) / Food Network(robots が AI bot 明示禁止)。

## 戦略的位置づけ（再掲・重要）
これら全ては **styled/ユーザー レシピ写真 + recipe-intended 分量** ＝ oishi-kenko/allrecipes と同じクラス。
- ✅ **zero-manual で「写真↔材料+分量」を大規模生成**でき、**recognition / density-prior / 材料-分量 supervision / 西洋 calorie サニティ**に有用。
- 🔴 ただし **weighed でない・実スマホ食卓ドメインでない** → `plans/current.md` の `20260606_e14_*`（lab/curated は実 JFB に transfer せず）どおり、**mozu の本命律速 E13/E14（実ドメイン weighed 校正）の代替にはならない**。別トラックとして扱うこと。

## ★ 写真↔分量(ポーション)一致度の実証（最重要軸・2026-06-07 追検証）
「写真に写る量」と「ラベルが表す量」が一意対応するか、を 4 サイト×実レシピ2件で実証（hero画像のalt/caption/本文 + per-serving 栄養 + servings を WebFetch 取得）。

| 順位 | サイト | nutrition基準 | hero が写すもの | 対応度 | 要点 |
|---|---|---|---|---|---|
| 1 | **Skinnytaste** | per-serving(1 piece等) | 単品1人前を皿盛り | **tight** | カロリー管理特化・単品料理を per-serving で撮る運用＝最も一致。料理タイプ依存 |
| 2 | **Budget Bytes** | per-serving(1 cup) | 1ボウル(≈1人前風) | loose | ボウル実量≠"1 cup"・トッピングで要正規化 |
| 3 | **King Arthur** | per-serving(**g明示**) | 丸ごとケーキ/演出 | loose | 分量(g)は最厳密だが hero=全yield(16人前)で量が一意でない |
| 4 | **Food.com** | per-serving(投稿者申告) | 丸ごと料理+UGC混在 | **unreliable** | servings 自己申告でブレ・複数ユーザー写真が非統制・情報源で栄養が食い違う |

**構造的結論**: schema.org `nutrition` は慣例 **per-serving**、一方 hero は SEO/CTR 目的の **beauty shot（丸ごとの鍋/天板/ケーキ or 演出された一部）**＝ 写真の物理量とラベル単位(1 serving)が**設計上ずれる**。加えて `recipeYield` は人数表記で **1 serving の実グラム量が不定**（King Arthur の g 明示が例外）。よって **recipe-scrape は写真↔分量が構造的に loose**。UGC(Food.com/Recipe1M+) では unreliable まで劣化。
- **この軸で真に tight なのは「写真＝実際に計量した皿」のデータ**＝ **Nutrition5k(N5k) / NutritionVerse-Real(NVReal) / 計画中の E13**（実スケール由来で対応は構造的に保証）。→ ユーザーの「写真↔分量一致が最重要」という観点は、**PDCA が既に出した E13 結論を独立に再導出**している。
- **scrape を使うなら tight サブセット抽出**: `servings=1`（or per-serving g 明示）× `単品1皿 hero`（VLMで「1人前か」判定）× UGC 複数写真除外。**Skinnytaste / おいしい健康（per-serving写真+per-serving栄養, 検証8/8）** がこのサブセットを最も多く生む。

## ライセンス/法務メモ
- レシピの「材料リスト＝事実」は米国で著作権不可だが、**写真と説明文は著作権あり**。大手publisher の ToS は一般に自動収集を禁止。**bulk 利用前に各サイト ToS/robots.txt の確認必須**。recipe-scrapers(MIT) はコードのライセンスであり、対象サイトのコンテンツ権は付与しない。
