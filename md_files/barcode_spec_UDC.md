0. 「バーコード情報はどこにあるか？」

FDC の「Branded Foods」（USDA Global Branded Food Products Database）に、バーコードを示す**gtin_upc**が入っています（重複する gtin_upc は=製品更新。最新を選ぶには food テーブルの publication_date を見る）。
fdc.nal.usda.gov

栄養値は**food_nutrient テーブルにあり、amount は 100 g あたり**の量で入っています。
fdc.nal.usda.gov

つまり、**branded_food.gtin_upc → food.fdc_id で製品を特定し、food_nutrient**から必要栄養（Energy, Fat, Carbohydrate, Protein）を取るのが基本です。

1. どのように FDC にアクセスするか？（API？事前 DB インストール？）
   おすすめ構成（商用・高トラフィック想定）

A. FDC の「一括ダウンロード（CSV/JSON）」をローカル DB へ取り込み、API は使わない（または補助的に）

FDC は公式に全データの一括ダウンロードを提供しています（CSV/JSON）。ローカル DB 化すれば外部 API コール不要でスケールできます（ゼロ課金）。
fdc.nal.usda.gov

「Branded Foods」は毎月更新。月次で差分/全量を再取り込みしてください。
fdc.nal.usda.gov

メリット：外部レート制限・ダウン・仕様変更の影響を受けにくい／レスポンス高速化。

デメリット：初期セットアップ＆定期更新の運用が必要（後述の自動化で解消）。

代替：API 直叩き（補助／バックアップ用途）

FDC は REST API（検索・詳細）を提供、API キー（api.data.gov）が必要。レート制限あり（デフォルト 1,000 リクエスト/時/キー。必要に応じて増枠相談）。
Postman
+1

注意：/foods/search で GTIN を直接フィルタするパラメータは公表されていないため、query にバーコード数字を入れて dataType=Branded で検索 →fdcId 取得 →/food/{fdcId} で詳細、という実装が現実的です（Web のヘルプ上は GTIN 検索可能と明記）。
fdc.nal.usda.gov

本設計では API は未ヒット時の補助として提案します（ローカル DB が主）。

2. 導入手順（コマンドベース or Web ブラウザ）
   2-1. データ取得

方法 1（推奨／自動化向け）：コマンドでダウンロード（実運用は CI で最新アーカイブ URL を取得して curl -L -O→unzip）。
最新のダウンロードページ（リリースごとの ZIP リンクあり）から URL を取得してスクリプトに渡してください。
fdc.nal.usda.gov

方法 2（手動）：ブラウザでダウンロードページにアクセス → 最新の**“Full Download of All Data Types (CSV or JSON)”**を取得。
fdc.nal.usda.gov

必要ファイル（CSV 想定）

food.csv（fdc_id, publication_date ほか）

branded_food.csv（fdc_id, gtin_upc, serving_size, serving_size_unit ほか）
fdc.nal.usda.gov

food_nutrient.csv（100 g あたり各栄養の amount、fdc_id, nutrient_id）
fdc.nal.usda.gov

nutrient.csv（nutrient_id と名称/単位のマスタ）

栄養 ID（FDC 標準）：Energy=1008, Fat=1004, Carbohydrate=1005, Protein=1003（新体系）。※Energy=1008 については FDC 公式の仕様文書にも記載があります。
fdc.nal.usda.gov
+2
Nelson Gonzabato
+2

2-2. ローカル DB 作成（SQLite 例）

運用は PostgreSQL/SQLite/DuckDB のいずれでも OK。まずは SQLite で最小構成 → 必要に応じて Postgres へ移行が実装コスト低。

インポート時に主キー・インデックスを設定（branded_food.gtin_upc, food.fdc_id, food_nutrient(fdc_id, nutrient_id)）。

3. データモデリング／同一 GTIN の重複対策

同一 gtin_upc の複数行は「製品更新（改定版）」を意味するため、food.publication_date で最新（最大）を採用。
fdc.nal.usda.gov

マップの流れ：

gtin_upc → fdc_id（最新版に解決）

fdc_id → food_nutrient（Energy, Fat, Carbs, Protein を抽出）

単位：Energy は kcal、他は g（FDC 標準）。

サービング（1 食分）が必要な場合は、branded_food.serving_size が g のときだけ、100 g あたり値 ×(serving_size/100)で近似の 1 食分値を算出。serving_size_unit が ml 等なら 100 g あたり値を返す（密度情報がないため）。
fdc.nal.usda.gov

（注）FDC API の**labelNutrients（1 食分ラベル値）は API 詳細で取得できますが、CSV 一括では 100 g 基準が基本です。必要なら API で補完**する設計を用意。
Postman

4. 実装（サンプルコード：DB 作成 & FastAPI）
   4-1. 取り込みスクリプト（SQLite, pandas, 分割読み込み）
