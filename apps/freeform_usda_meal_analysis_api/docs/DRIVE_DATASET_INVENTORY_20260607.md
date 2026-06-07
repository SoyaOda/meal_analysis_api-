# Google Drive データセット棚卸し（mozu calorie PDCA 向け） — 2026-06-07

## 目的 / 方法
- 目的: **mozu のカロリー精度 PDCA に「マニュアル作業なし」で使える食事画像＋ラベルデータ**を、Google Drive 全域から漏れなく洗い出す。
- 方法: Claude Code の Google Drive MCP（`search_files`/`read_file_content`/`download_file_content`）で My Drive 直下〜各プロジェクトツリーを breadth-first に走査。ラベル形式は実 JSON/HTML を読み、画像ドメインは subagent に隔離して実視（base64 をメイン文脈に入れない）。oishi-kenko は ID 範囲を散らした 8 レシピで**敵対的検証**（栄養 JSON-LD 有無 / 写真=1人前か / ドメイン）。
- 認証注記: Drive MCP は claude.ai 連携（対話認証）。**この棚卸しは認証済みセッションで実行**。headless/cron では Drive ツールが load されない可能性あり。

## 結論（1 行）
- **本命（日本語）= `Scraping_Data` = おいしい健康(oishi-kenko.com) 8,244 レシピ**。per-serving の calories+PFC が schema.org JSON-LD で直接ラベルされ、**マニュアル作業ゼロで `{画像→kcal}` ペアを大量生成可能**。eatthismuch より上位（直接ラベル・和食ドメイン・大規模）。
- **英語版 = allrecipes.com**（recipe-scrapers, per-serving calories+PFC+画像URL）。ただし Drive 上の実体は **cleaned JSON の test バッチのみ（画像未DL）**。bulk は local 中心。
- ⚠️ **いずれも styled 写真 + recipe-intended kcal**（weighed でない・実スマホドメインでない）= `plans/current.md` の確定 lesson（lab/curated は実 JFB ドメインに transfer しない）と同じクラス。**E13/E14（実ドメイン weighed 校正）の代替にはならない**。有用用途は recognition / density-prior / 言語別 calorie サニティに限定。

---

## スコア表（食事画像＋ラベル候補・全件）

| データセット | 場所(Drive) | 規模 | ラベル形式 | calorie GT | per-item grams | 画像ドメイン | mozu calorie 適性 |
|---|---|---|---|---|---|---|---|
| **おいしい健康** (`Scraping_Data`) | My Drive 直下 | **8,244**(log.csv全Success) | schema.org JSON-LD: per-serving kcal+PFC+fiber+sodium、材料+分量、main_img+step画像 | ✅ **直接ラベル** | △(材料分量はあるがper-item grams化は要処理) | styled-pro 完成皿写真・単品1人前・和食 | △ recognition/density-prior/和食calorieサニティ。**E13代替不可**（styled・非weighed） |
| **allrecipes.com** (`cleaned_data/allrecipes`,`/allrecipe`) | llama3.2ツリー | ~11 test バッチ(各 数十〜百, alphabetical, 重複あり) | cleaned JSON: `servings`,`nutrients.calories.kcal`+PFC、材料(単位正規化ml/g)。raw形式は画像URL+`recipe_image.jpg`ペア | ✅ **直接ラベル**(per-serving) | △ | styled-pro 西洋レシピ写真(Drive上は**画像未DL**,URLのみ) | △ 英語calorieサニティ/density。画像は要再DL。**E13代替不可** |
| **eatThisMuch** | local 4583 / Drive=処理WSのみ | 4,583(local) | 材料grams×DB→**導出** kcal | △ 導出 | ✗ | styled stock(西洋) | ❌ calorie-fit不可(domain+portion)/✅ recognition・density prior（既知） |
| **Cookpad** (`All_Recipe_Scraping/Cookpad`) | My Drive 旧ツリー | 多数 | JSON-LD: 材料+分量(**文字化けShift-JIS**)、**栄養なし** | ❌ | ✗ | 実ユーザー投稿写真(画像URL/image) | recognition/実ドメイン写真のみ。calorie 無し |
| **Rakuten Recipe** (`All_Recipe_Scraping/Rakuten`) | My Drive 旧ツリー | 多数 | JSON-LD: 材料+分量(文字化け)、**栄養なし** | ❌ | ✗ | 実ユーザー投稿写真 | 同上 |
| **`レシピjson`** | My Drive 直下 | 多数 | Cookpad parse 済 JSON(2B〜2.8KB) | ❌ | ✗ | 画像なし | テキストのみ |
| **VireoFood172** (共有) | shared-with-me | ~110k(公開DS) | 172カテゴリ認識ラベル | ❌ | ✗ | 中華料理 | recognition のみ・portion/calorie 無し |
| **`画像`/`image_json_*`** (山田さんデータ等) | My Drive 旧ツリー | 多数 | 空 40B json スタブ | ❌ | ✗ | 食事報告の低解像写真(3-13KB, **実食事だが低解像**) | **ラベル無し**＝マニュアル必須・PDCA不適 |

### 除外（食事 calorie と無関係・確認済）
- **`*_101`系**(`train_101`/`valid_101`/`predict_101`): `valid_101_a_1.nii.gz`(156MB, **NIfTI=医療CT/MRI 3D**)。`plate_dicom`/`CT-RATE-v2`/`mesh_data`/`lidar_data_2` と同じ**医療3D画像**プロジェクト。
- **2023-05 `dataset`**(`convert_laion.py`/`download_cc_sbu.sh`/README_1_STAGE)= **MiniGPT-4 / LAION・CC-SBU** 学習scaffold。
- **`食事管理LINE Botトライアル`** = Colab ノートブック（プロンプト/UI 設計）、データセットではない。
- `食サポ素材`/`食サポサービス説明資料` = マーケ資料。

---

## 詳細

### 1. おいしい健康 `Scraping_Data`（本命）
- **場所**: My Drive 直下 `Scraping_Data`(`1Fhmoz3AD8oksCM_kOjyxz4vQ4RH13JVN`)。
- **構造**: recipe-ID 名の folder × 8,244。各 folder = `main_img.jpg`(1-3MB, 完成皿写真) + step画像(106xxx.jpg) + `soup.json`(レシピページ生HTML, 100-140KB)。`log.csv` がマスタ索引（id, main_image, step_images, soup の各 Success/Fail。**全 8,244 行 Success**）。
- **ラベル**: `soup.json` 内の schema.org JSON-LD `Recipe`:
  ```json
  "recipeYield":"1人前",
  "nutrition":{"@type":"NutritionInformation","calories":"218.0 kcal",
    "proteinContent":"15.8 g","fatContent":"13.1 g","carbohydrateContent":"9.7 g",
    "fiberContent":"0.3 g","cholesterolContent":"80.0 mg","sodiumContent":"552.0 mg"}
  ```
  per-serving 値。`recipeCategory`/`recipeCuisine`/材料+分量も取得可能。
- **抽出**: zero-manual。各 soup.json から JSON-LD を正規表現/パースで抜き、`main_img.jpg` と対で `{image, kcal_per_serving, PFC, dish_name, cuisine}` を生成。
- **敵対的検証(8レシピ, ID 散らし)**: **8/8 で栄養JSON-LD あり・8/8 で `{画像,kcal}` ペア成立**。per-serving 11〜395 kcal、全件「単品1人前の完成皿写真」。
  - ⚠️ **データ整合性の注意**: 1/8(folder `10186`)で **folder-id と soup.json 内部ID(10199)が不一致** かつ **写真が料理名と不一致**（料理名=鰆サラダ、写真=焼きキノコ）。→ **使用前に (a) folder名 vs JSON-LD内部id の一致、(b) 画像と料理名の対応 の dedup/整合性チェックが必須**。生ペアは 100% クリーンではない。
  - ⚠️ HTMLは backslash/HTML エスケープされており、抽出時に正規化が必要（HTML-escape 版と double-backslash 版が混在）。
- **ドメイン**: subagent 実視で **プロのスタイリング完成皿写真**（単品・ハイアングル・和食器・小道具あり）。実スマホ食卓写真とは**ドメインギャップ大**。一部 casual な家庭料理風もあり（10186）。

> 📎 **英語圏の web レシピソース全般の実態調査（22 サイト + 公開データセット）は `docs/ENGLISH_RECIPE_SOURCE_SURVEY_20260607.md` に独立 SSOT 化。** 「写真↔材料+分量」用途で Tier1(turnkey)〜Tier3(除外) にランク。最速候補 = Food.com Kaggle(522k 整形済) / 最良 fresh-scrape = Food.com・King Arthur・Budget Bytes・Tasty 等。

### 2. allrecipes.com（英語版・本命の英語対応物）
- **場所**: `…/llama3.2_data_cleaning/cleaned_data/allrecipes`(`1Lvk2P04…`) と `/allrecipe`(`1Xr-F9On…`)。各下に `test_20241223_*` バッチ(計 7+4=~11)。`raw_data/allrecipes`(`1gfkb…`) は .DS_Store のみ＝空。
- **ラベル(cleaned)**: 料理名.json。例「4-Cheese Spinach-Artichoke Dip」: `servings:1`, `nutrients.calories.value:159 kcal` + carb/protein/fat/fiber…、材料は単位正規化(ml/g)。→ **per-serving calorie 直接ラベル**。
- **ラベル(raw, recipe-scrapers `recipe_data/recipe.json`)**: `タイトル/画像URL/材料/手順/分量/栄養成分`。例「Lemon Garlic Butter Chicken Spiedini」: `分量:6 servings`, `calories:636 kcal`, **画像URL(allrecipes.com)** + 同梱 `recipe_image.jpg`。→ pipeline は画像DL可能だが、**cleaned バッチには画像が無く URL のみ**。
- **規模**: Drive 上は "test" バッチのみ（alphabetical で重複再走あり・unique 数は不確定、数百規模）。**full scale は local 中心の可能性が高い**（raw 系フォルダは Drive 上ほぼ空スタブ）。
- **使用**: zero-manual で `{calories, ingredients}` テキストは取得可。画像は URL から自動再DL（manual ではない）。**ドメインは styled-pro 西洋レシピ写真**。

### 3. その他英語
- **eatThisMuch**: Drive(`raw_data/eatThisMuch`)は処理ワークスペース（cleaning スクリプト + log）。`cleaned_recipe_data`/`cleaned_data20241230/food` は **.DS_Store のみ＝空**。実 4583 は local(`raw_nutrition_data/recipe`)。kcal は材料×DB導出、写真は styled stock。
- **recipe-scrapers**: OSS ライブラリ本体 + サンプル1件(image+json)。allrecipes 等多数の英語サイト対応だが、Drive 上に materialize された他サイト(foodnetwork/food.com/seriouseats…)の scrape フォルダは**無し**。

---

## 戦略的含意（mozu PDCA への正直な位置づけ）
`plans/current.md` の確定 lesson との整合:
- mozu の**真の律速 = E13（実スマホ eye-level・weighed per-item grams GT）**。E14 条件付き校正は in-domain なら −18.5pt 効くが、**lab weighed(NVReal/N5k) すら実 JFB ドメインに transfer しない**ことが定量確定済み（`20260606_e14_…`）。frozen-50(curated, ~16%) は実ドメイン bias(JFB 53.8%) を隠していた。
- oishi-kenko / allrecipes は **styled写真 + recipe-intended per-serving kcal**（weighed でない・実スマホでない・「1人前」と実皿量の一致は未保証）。= 既に「transfer しない」と学習済みのクラス。よって **E13/E14 の代替にはならない**。styled curated を calorie 校正/eval に使うと frozen-50 と同じ自己欺瞞リスク。
- **使える用途（zero-manual・価値あり）**:
  1. **Recognition / 食品ID** の大規模学習・評価（和食=oishi-kenko 8244、西洋=allrecipes）。JFB は言語的に和食寄り → oishi-kenko の和食ラベルは in-language 価値。
  2. **density prior**（料理→kcal/100g 分布）の構築・拡充（E7 密度混合の prior 強化候補）。
  3. **言語別 calorie サニティ eval**（実ドメイン eval ではなく、明らかな破綻検出用の補助）。
  4. （探索）和食 conditional-calibration bucket 構造の予備調査（**実ドメインでない前提を明記**して）。

## 次アクション候補（ユーザー判断）
1. oishi-kenko を **recognition/density-prior** 用に取り込むなら: soup.json→JSON-LD パーサ + 整合性フィルタ（folder-id vs 内部id、画像↔料理名）を書き、`{image, kcal/serving, PFC, dish, cuisine}` を harness 形式に変換。**E13(実 weighed) とは別トラックで**。
2. allrecipes を使うなら: cleaned JSON を統合 + 画像URL から再DL。**重複(test 再走)dedup** が必要。
3. **E13(実ドメイン weighed) は引き続き最優先・別物**。本棚卸しは「scraping=実ドメイン校正データではない」を再確認した。

## 主要 folder ID（参照用）
- oishi-kenko: `Scraping_Data`=`1Fhmoz3AD8oksCM_kOjyxz4vQ4RH13JVN`(log.csv=`13xzgrdUr5Qu1vTb7wBAv4_rmzjX7RtUg`)
- allrecipes(cleaned): `1Lvk2P04lGAgjqWQzaFjmBh9XmZAT4HbK` / `1Xr-F9On34NeLmkK5j2ZQwx94YLZR9x_e`
- raw_data(マルチサイトhub: eatThisMuch/allrecipes/cookpad): `1l604rdHb45T0ar1MM8Y4nMv3jLkr8nv3`
- All_Recipe_Scraping(Cookpad/Rakuten): `18_p3ZJr-umZ8Bln18tVrw4pwGdI5il7i`
- VireoFood172(共有): `1MvAurBPvCZuxUJVrRjucWTZoX5rS6TX2`
