食事管理アプリ向け栄養価計算精度向上 API（フェーズ 2）開発方針 1. はじめに本レポートは、食事管理アプリケーション（以下、本アプリ）における栄養価計算機能の精度向上を目的とした API（フェーズ 2）の包括的な開発方針を提示するものです。フェーズ 1 で開発された AI 画像解析 API（以下、フェーズ 1API）は、食事画像から料理・食材名とその量を推定します。本フェーズ 2API は、その初期推定結果を米国農務省（USDA）の FoodData Central データベースと照合し、マルチモーダル AI（Google Gemini）を再度活用することで、より正確で信頼性の高い栄養価情報へと精緻化することを目的とします。ユーザーが直面している問題点、すなわち「生成 AI が USDA 栄養データベースを参照せずに自由に栄養計算してしまう信頼性の欠如」、「全データベース情報をプロンプトに含めることによるトークン数超過」、「キーワード検索だけでは不適切な食材や量が選択される可能性」を解決するため、本方針では USDA データベースとの連携、効果的な情報抽出、そして AI への適切なコンテキスト提供を核とします。本方針は、フェーズ 1API の設計思想を継承し、OpenAPI 仕様への準拠、RESTful な設計原則の適用、そして Google Gemini との連携を維持しつつ、USDA データベースの情報を効果的に組み込むための戦略と具体的な実装案を提示します。これにより、本アプリの栄養価計算機能の信頼性とユーザー体験の向上を目指します。2. コア要件と API 設計原則フェーズ 2API の設計は、フェーズ 1API で確立されたコア要件と設計原則を踏襲し、拡張します。これらの原則は、API の品質、保守性、および将来の拡張性を確保するための基盤となります。2.A. ユーザー（エンジニア）要件の確認（再掲と拡張）フェーズ 1API と同様の技術要件が適用されます。
OpenAPI 仕様準拠: API 定義は OpenAPI Specification (OAS) v3.0.x に準拠します [既存資料]。
RESTful API 設計: リソースベースの URL 設計、HTTP メソッドの適切な使用、ステートレスな通信を基本とします [既存資料]。
可読性と拡張性: 将来的な機能追加や変更に柔軟に対応できる設計を目指します [既存資料]。
システム間連携: Flutter クライアントとの円滑な連携のため、OpenAPI Generator を用いたクライアントコード生成を前提とします [既存資料]。
汎用性: 特定のアプリケーション仕様に依存しない、一般的かつシンプルなエンドポイント構成を目指します [既存資料]。
単一責任のエンドポイント: 各エンドポイントは明確に定義された単一の責務を持ちます [既存資料]。
AI 連携のモジュール化: Google Gemini との連携部分はモジュール化し、将来的なモデル変更を容易にします [既存資料]。
これらに加え、フェーズ 2 特有の要件として以下が挙げられます。
USDA データベース連携: USDA FoodData Central データベースの情報を活用し、栄養価計算の精度を向上させます。
二段階 AI 処理: フェーズ 1 の AI 出力を初期情報とし、USDA 検索結果をコンテキストとして再度 AI 処理を行うことで、情報の精緻化を図ります。
信頼性と再現性の向上: 標準化されたデータベースに基づくことで、栄養価計算の信頼性と再現性を高めます。
2.B. API 設計の基本方針（再掲と拡張）フェーズ 1API の基本方針を継承し、フェーズ 2 の特性に合わせて拡張します。
デザインファースト・アプローチ: 実装に先立ち、OpenAPI 仕様を用いて API コントラクトを定義します [既存資料]。
リソース指向アーキテクチャ: API 機能を「リソース」としてモデル化します [既存資料]。本フェーズでは、「食事分析結果の精緻化」が主要なリソースとなります。
汎用性と再利用性: フェーズ 1API の構造を可能な限り再利用しつつ、USDA 連携という新たな要件に対応します。
単一責任の原則: /v1/meal-analyses/refine のような新しいエンドポイントを設け、既存の /v1/meal-analyses エンドポイントの責務を明確に分離します。
データベース構造の非公開: USDA データベースの構造を直接クライアントに公開せず、API が抽象化レイヤーとして機能します [既存資料]。
明確なエラーレスポンス: 成功レスポンスだけでなく、USDA API 連携時のエラーなども含め、明確なエラーレスポンスを定義します [既存資料]。
この方針に基づき、「アプリケーションが API に合わせる」という考え方を主軸に、堅牢かつ柔軟な API を構築します。3. USDA データベース連携戦略本 API の核心機能の一つは、USDA FoodData Central データベースとの効果的な連携です。これにより、栄養価計算の信頼性と精度を大幅に向上させることを目指します。3.A. USDA FoodData Central 概要 USDA FoodData Central は、米国農務省（USDA）が提供する包括的な食品成分データベースです 1。研究者、政策立案者、栄養士、食品開発者など、幅広いユーザーに利用されています 1。このデータベースは、食品の栄養成分に関する詳細な情報を提供し、複数のデータタイプで構成されています。主要なデータタイプには以下のようなものがあります。
Foundation Foods: 詳細な分析データとメタデータ（サンプリング情報など）を含む、基本的な加工度の低い食品に関するデータ。年に 2 回（4 月と 10 月）更新されます 2。
SR Legacy (Standard Reference Legacy): 長年にわたり米国の食品成分データベースの標準とされてきたデータ。分析、計算、文献に基づいており、2018 年 4 月が最終リリースです 2。
Branded Foods: ラベル情報を基にした市販食品のデータ。公的機関と民間企業のパートナーシップにより収集され、月次で更新されることがあります 1。
FNDDS (Food and Nutrient Database for Dietary Studies): 米国の国民健康栄養調査（NHANES）の食事摂取量調査「What We Eat in America」で報告される食品および飲料の栄養素と分量に関するデータ。2 年ごとに更新されます 2。
本 API では、これらのデータタイプの中から、特にアプリケーションの目的に合致するもの（例：一般的な食材には Foundation Foods や SR Legacy、加工食品には Branded Foods）を選択的に利用することを想定します。3.B. アクセス方法の検討：API 利用とデータダウンロード USDA FoodData Central のデータを利用する方法として、主に公式 API の利用とデータセットのダウンロードの二つが考えられます。

API 利用:

利点:

リアルタイムに近いデータアクセス（特に Branded Foods は月次更新されるため） 3。
特定の食品や食材をキーワードで検索し、必要な情報のみを効率的に取得可能。
データベース全体をローカルに保持する必要がないため、ストレージや管理の負担が少ない。

欠点:

API リクエスト数には制限（レートリミット）が存在する（通常 1 時間あたり 1,000 リクエスト/IP アドレス） 5。大量のリクエストが必要な場合、制限に達する可能性がある。
ネットワーク接続が必須であり、外部 API の可用性に依存する。
API の応答速度が全体のパフォーマンスに影響する可能性がある。

データセットダウンロード:

利点:

ローカルデータベースにインポートすることで、API のレートリミットやネットワーク遅延の影響を受けずに高速アクセスが可能。
オフラインでの利用や、複雑なクエリ処理をローカルで実行可能。

欠点:

データの鮮度が問題となる可能性がある。Foundation Foods は年 2 回、Branded Foods のダウンロードファイルは半年ごとの更新に対し、API では月次更新の情報が得られる場合がある 2。
データベースのサイズが大きく（全データタイプ CSV で数 GB 9）、ローカルストレージを圧迫する可能性がある。
定期的なデータ更新とローカルデータベースへの同期メカニズムを自前で構築・維持する必要がある。

アクセス方法の決定:本 API のユースケース（ユーザーがアップロードした画像ごとに食材を検索し、候補を AI に提示する）を考慮すると、USDA FoodData Central API の利用を主軸とし、パフォーマンス向上のためにキャッシュ戦略を組み合わせるのが最も現実的かつ効果的です。API を利用することで、比較的最新のデータにアクセスでき、必要な情報のみをオンデマンドで取得できます。レートリミットへの対策として、後述するキャッシュ戦略（セクション 3.I）や、ユーザーごとのリクエスト頻度のコントロールが重要となります。将来的に非常に高いスループットが求められる場合は、ダウンロードしたデータを活用したローカルデータベースの構築も検討の余地がありますが、初期段階では API ベースで進めるのが適切です。3.C. USDA API キーの取得と管理 USDA FoodData Central API を利用するには、data.gov から API キーを取得する必要があります 6。
取得方法: data.gov の API キーサインアップページ（例: https://api.data.gov/signup/ や https://fdc.nal.usda.gov/api-key-signup.html 11）から必要な情報を登録することで取得できます。
利用方法: 取得した API キーは、各 API リクエストに含める必要があります。通常、クエリパラメータ api_key=YOUR_API_KEY または HTTP ヘッダー X-Api-Key: YOUR_API_KEY として送信します 7。
管理: API キーは機密情報として扱い、ソースコードにハードコーディングせず、環境変数（例: USDA_API_KEY）を通じてアプリケーションに供給します。これにより、セキュリティを確保し、異なる環境（開発、ステージング、本番）でのキーの管理が容易になります。
3.D. USDA API エンドポイントとレスポンス構造の理解 FoodData Central API は、主に食品検索と食品詳細取得のための RESTful エンドポイントを提供します 6。

食品検索エンドポイント: GET /v1/foods/search または POST /v1/foods/search

目的: キーワードに基づいて食品を検索します 6。
主要パラメータ 13:

query (必須): 検索キーワード（例: "Cheddar Cheese"）。
dataType: データタイプ（例: "Foundation", "SR Legacy", "Branded"）。複数指定可能（API ドキュメントでは配列として記述されているが、GET リクエストではカンマ区切り文字列または繰り返しパラメータとして渡すことが多い）。
pageSize: 1 ページあたりの結果数（デフォルト 50）。
pageNumber: 取得するページ番号。
sortBy: ソートキー（例: "description.keyword", "fdcId"）。
sortOrder: ソート順（"asc", "desc"）。
brandOwner: ブランド所有者（Branded Foods のみ）。

レスポンス構造: 検索結果の食品リストを含む JSON オブジェクト。各食品オブジェクトには、fdcId（食品 ID）、description（食品名）、dataType（データタイプ）、brandOwner（ブランド所有者、Branded Foods の場合）、ingredients（原材料、Branded Foods の場合）、foodNutrients（栄養素リストの要約）、score（検索適合度スコア）などが含まれます 15。

食品詳細取得エンドポイント: GET /v1/food/{fdcId}

目的: 指定された fdcId の食品に関する詳細情報を取得します 6。
主要パラメータ 6:

fdcId (パスパラメータ, 必須): 食品 ID。
format: レスポンス形式（"abridged" または "full"、デフォルトは "full"）。
nutrients: 特定の栄養素番号のリスト（最大 25 件、カンマ区切り）。指定した場合、その栄養素情報のみが返されます。

レスポンス構造: 指定された食品の詳細情報を含む JSON オブジェクト。fdcId、description、dataType、publicationDate、foodCategory、そして最も重要な foodNutrients の完全なリストが含まれます。foodNutrients の各要素には、nutrient.id（栄養素の内部 ID）、nutrient.name（栄養素名、例: "Protein"）、nutrient.number（栄養素番号、例: "203"）、nutrient.unitName（単位、例: "G", "MG", "KCAL"）、amount（100g または 100ml あたりの量）などが含まれます 16。servingSize や servingSizeUnit、householdServingFullText といった分量に関する情報も含まれる場合があります。

抽出対象とする主要フィールド:本 API の目的（Gemini へのコンテキスト提供と最終的な栄養計算）のため、以下のフィールドを重点的に抽出・利用します。
fdcId: データベース内のユニークな識別子。Gemini が選択した食品を特定するために必須。
description: 食品の名称。ユーザーや Gemini が理解しやすいように。
dataType: データの種類。情報の特性を理解する上で有用。
brandOwner: ブランド食品の場合、その所有者情報。
ingredients: ブランド食品の場合、原材料リスト。Gemini が食品を特定する際の追加情報となり得る。
foodNutrients:

nutrient.name / nutrient.number / nutrient.id: 栄養素の識別。
amount: 100g（または 100ml）あたりの栄養素量。これが栄養価計算の基礎となる。
nutrient.unitName: 栄養素の単位。

servingSize, servingSizeUnit: 一部の食品では参考情報として有用。
これらのフィールドを適切にパースし、Pydantic モデル（後述）にマッピングします。3.E. データタイプの選定 USDA FoodData Central は複数のデータタイプを提供しており、それぞれ特性が異なります 1。本アプリの目的（一般的な食事写真からの栄養推定）を考慮し、以下の優先順位でデータタイプを選定・利用します。
Foundation Foods: 分析に基づいた信頼性の高いデータが多く、基本的な食材（野菜、果物、肉類など）に適しています。可能な限り最新の情報（年 2 回更新）を利用します 2。
SR Legacy (Standard Reference Legacy): 長年の実績があり、広範な食品をカバーしています。Foundation Foods で適切な情報が見つからない場合のフォールバックとして有用です 2。2018 年が最終更新である点に留意します。
Branded Foods: 市販の加工食品やブランド製品（例: 特定のシリアル、ソース、冷凍食品など）を特定する際に重要です。ユーザーが摂取したものが市販品である可能性が高い場合に役立ちます。月次更新の可能性があるため、API 経由での利用が望ましいです 1。
FNDDS は食事調査研究向けであり、Experimental Foods は研究目的の特殊なデータが多いため 1、本アプリの一般的な栄養推定の主目的からは優先度を下げます。検索時には、これらの優先順位の高いデータタイプを組み合わせて（例: dataType=Foundation,SR Legacy,Branded）検索するか、あるいは段階的に検索することが考えられます。3.F. 検索クエリ戦略フェーズ 1API で AI（Gemini）が推定した料理・食材名 (dish_name, ingredient_name) を主な検索クエリとして使用します。
食材名ベースの検索: initial_analysis_data 内の各 ingredients の ingredient_name を直接クエリとして使用します。これが最も基本的な検索アプローチです。

例: フェーズ 1 で「Chicken breast 150g」と推定された場合、「Chicken breast」で USDA を検索。

料理名ベースの検索（補助的）: dish_name も検索クエリとして利用することを検討します。特に、一般的な料理名（例: "Caesar Salad", "Spaghetti Bolognese"）で検索することで、その料理全体としての栄養価情報が見つかる可能性があります（特に FNDDS や一部の Branded Foods）。ただし、料理名は構成要素が多様であるため、食材名ベースの検索と組み合わせて慎重に扱う必要があります。
クエリの最適化:

具体性: できるだけ具体的な食材名を使用します（例: "Apple"よりも"Fuji Apple"）。フェーズ 1 の AI 出力が具体的であれば、それを活用します。
表記揺れへの対応: USDA データベースの表記と AI の出力表記が異なる場合（例: "ground beef" vs "beef, ground"）を考慮し、必要であれば簡単な正規化や複数パターンの検索を検討します。ただし、これは複雑になりすぎる可能性があるため、初期は AI 出力の直接利用を優先します。

3.G. 検索結果の絞り込みとランキング USDA API の/foods/search エンドポイントは、多数の検索結果を返す可能性があります。Gemini に提示する候補を適切に絞り込むため、以下の戦略を採用します。
取得件数: pageSize パラメータを利用し、各クエリに対して上位 5 件程度の候補を取得します 13。これにより、プロンプトに含める情報量を適切に管理します。
データタイプの優先順位付け: dataType パラメータで優先するデータタイプ（Foundation, SR Legacy, Branded など）を指定します。
USDA スコアの利用: /foods/search レスポンスには score フィールドが含まれる場合があり、これは検索クエリとの適合度を示唆します 16。このスコアを参考に、より関連性の高い候補を優先することができます。
完全一致・部分一致: 検索結果の description と元のクエリ文字列との類似度（例: Levenshtein 距離など）を計算し、より近いものを優先することも考えられますが、実装の複雑さを考慮し、初期は USDA の返す順序やスコアに依存します。
最終的に Gemini に提示する情報は、これらの絞り込み戦略によって選ばれた、最も関連性が高いと考えられる少数の候補となります。3.H. 必要な栄養素情報の特定 USDA データベースには非常に多くの栄養素情報が含まれています 18。Gemini へのプロンプトに含める情報量と、栄養計算の有用性のバランスを考慮し、主要な栄養素を選択して提示します。
主要栄養素 (Key Nutrients):

エネルギー (Energy / Calories,例: kcal)
タンパク質 (Protein, 例: g)
総脂質 (Total lipid (fat), 例: g)
炭水化物 (Carbohydrate, by difference, 例: g)
食物繊維 (Fiber, total dietary, 例: g)
総糖類 (Sugars, total including NLEA, 例: g)
ナトリウム (Sodium, Na, 例: mg)

その他重要な微量栄養素（選択的）:

飽和脂肪酸 (Fatty acids, total saturated, 例: g)
カルシウム (Calcium, Ca, 例: mg)
鉄 (Iron, Fe, 例: mg)
カリウム (Potassium, K, 例: mg)
ビタミン D (Vitamin D (D2 + D3), 例: IU or µg)
ビタミン C (Vitamin C, total ascorbic acid, 例: mg)

これらの栄養素情報を、各 USDA 検索候補について「100g あたり」の数値として整形し、Gemini へのプロンプトに含めます。/food/{fdcId}エンドポイントの nutrients パラメータや、/foods/search レスポンスの foodNutrients 配列からこれらの情報を抽出します 13。3.I. キャッシュ戦略 USDA API の利用にはレートリミット（1 時間あたり 1,000 リクエスト/IP 5）が存在するため、また、API 応答のレイテンシを削減するために、キャッシュ戦略を導入します。
キャッシュ対象: USDA API の/foods/search エンドポイントからのレスポンス。
キャッシュキー: 検索クエリ文字列、dataType、pageSize などの主要なリクエストパラメータを組み合わせたもの。
キャッシュストア: Redis や Memcached のようなインメモリキャッシュ、またはサーバーのファイルシステムキャッシュを利用します。FastAPI のミドルウェアや専用ライブラリ（例: fastapi-cache）の活用を検討します。
TTL (Time To Live): USDA データの更新頻度を考慮して設定します。例えば、Branded Foods は月次更新の可能性があるため 3、キャッシュの TTL は数時間〜1 日程度が適切と考えられます。SR Legacy は更新されないため、長めの TTL を設定できます。Foundation Foods は年 2 回更新です 2。
効果: 同じ食材名での検索が繰り返された場合、キャッシュから迅速に応答を返すことで、USDA API への負荷軽減とユーザー体験の向上に繋がります。
このキャッシュ戦略により、API の利用効率を高め、レートリミットに達するリスクを低減します。4. AI 再連携戦略（Google Gemini - フェーズ 2）フェーズ 1 で特定された食事内容と USDA データベースから取得した食品候補情報を組み合わせ、再度 Google Gemini を利用して分析結果を精緻化します。この二段階目の AI 処理が、本 API の精度向上の中核を担います。4.A. モデル選定フェーズ 1API と同様に、Google Cloud の最新マルチモーダル AI モデルである Gemini ファミリーの中から、画像とテキストの複合的な理解能力に優れ、かつ構造化データ（JSON）出力に対応している最新のモデル（例: gemini-1.5-pro-latest または gemini-1.5-flash-latest）を選定します [既存資料]。特に、複数の情報源（画像、初期 AI 分析結果、USDA 候補リスト）を統合して判断を下す能力が求められるため、推論能力の高いモデルの利用を検討します。モデル名は設定ファイルで管理し、容易に変更可能とします。4.B. SDK と認証・初期化フェーズ 1API と同様に、Python 向け SDK である google-generativeai ライブラリ（Vertex AI 経由での利用を推奨）を使用します [既存資料]。認証も Google Cloud のサービスアカウントを通じて行い、Application Default Credentials (ADC) の利用を基本とします [既存資料]。4.C. フェーズ 2 プロンプト設計 Gemini に送信するプロンプトは、フェーズ 1 よりも多くの情報を含み、より高度な判断を促すものとなります。

入力要素:

食事画像: ユーザーからアップロードされた画像データ（バイト列）。
フェーズ 1AI 分析結果: フェーズ 1API が出力した JSON 文字列。これには、初期推定された料理・食材名、量、材料が含まれます。
USDA 食品候補情報: フェーズ 1 の各食材名（または料理名）に対して USDA FoodData Central API で検索し、取得した上位候補の食品情報（食品名、FDC ID、主要栄養素（100g あたり）など）を整形したテキスト。
システムインストラクション: AI の役割、タスク、出力形式を厳密に指示するテキスト。

システムインストラクション（例）:「あなたは経験豊富な栄養士であり、食事分析の専門家です。提供された食事画像、初期 AI 分析結果、および USDA 食品データベースからの候補情報を総合的に評価し、初期 AI 分析結果を精緻化してください。あなたのタスクは以下の通りです：

初期 AI 分析結果に含まれる各料理および食材について、提示された USDA 食品候補の中から最も適切と思われるものを一つ選択してください。選択の際には、画像の内容、食材の一般的な使われ方、栄養価の妥当性を考慮してください。
選択した USDA 食品の FDC ID を特定してください。
最終的な料理・食材名、その種類、皿の上の量、そして各材料（選択した USDA 食品に対応する）の名称、推定重量（グラム）、および FDC ID を、指定された JSON スキーマに厳密に従って出力してください。
もし初期 AI 分析結果の食材が USDA 候補に適切なものがない場合、または画像と著しく異なる場合は、その旨を考慮し、最も妥当な判断を下してください。
あなたの出力は、正確な栄養価計算の基礎となります。」

ユーザープロンプト構造（概念）:contents パラメータには、画像パートに加え、以下のようなテキストパートを組み合わせて渡します。

このプロンプト設計により、Gemini は複数の情報源を比較検討し、より根拠のある判断を下すことが期待されます。特に、USDA 候補の提示は、AI が信頼性の低い情報を生成するリスクを低減し、標準化されたデータベースへの紐付けを促進します。4.D. JSON レスポンススキーマ定義（フェーズ 2）Gemini の構造化出力機能（Controlled Generation）を活用するため、期待する JSON 出力形式をスキーマとして定義します [既存資料]。フェーズ 2 のレスポンススキーマは、フェーズ 1 のスキーマを拡張し、USDA データベースとの連携結果を反映するフィールドを追加します。
主要な追加・変更フィールド:

各 ingredients オブジェクト内に以下を追加:

fdc_id (integer, optional): 選択された USDA 食品の FDC ID。該当なしの場合は null または省略。
usda_source_description (string, optional): 選択された USDA 食品の description。
key_nutrients_per_100g (object, optional): 選択された USDA 食品の主要栄養素情報（100g あたり）。例: {"calories_kcal": 150, "protein_g": 20,...}。これは、後続の栄養計算や表示に直接利用できる形式が望ましい。

dish_name, type, quantity_on_plate, ingredient_name, weight_g はフェーズ 1 と同様に維持、または Gemini による精緻化の結果を反映。

以下は、このレスポンス構造に対応する Gemini 向けの JSON スキーマの概念的な例です（Python 辞書形式）。Python# app/services/gemini_service.py 内で定義想定
REFINED_MEAL_ANALYSIS_GEMINI_SCHEMA = {
"type": "object",
"properties": {
"dishes": {
"type": "array",
"description": "画像から特定・精緻化された料理のリスト。",
"items": {
"type": "object",
"properties": {
"dish_name": {"type": "string", "description": "特定された料理の名称。"},
"type": {"type": "string", "description": "料理の種類（例: 主菜, 副菜）。"},
"quantity_on_plate": {"type": "string", "description": "皿の上の量。"},
"ingredients": {
"type": "array",
"description": "この料理に含まれると推定される材料のリスト（USDA 情報で精緻化）。",
"items": {
"type": "object",
"properties": {
"ingredient_name": {"type": "string", "description": "材料の名称（USDA 情報に基づき精緻化される可能性あり）。"},
"weight_g": {"type": "number", "description": "その材料の推定重量（グラム単位）。"},
"fdc_id": {"type": ["integer", "null"], "description": "選択された USDA 食品の FDC ID。該当なしの場合は null。"},
"usda_source_description": {"type": ["string", "null"], "description": "選択された USDA 食品の公式名称。"},
"key_nutrients_per_100g": { # この部分は Gemini に直接生成させるか、fdc_id を元にバックエンドで付与するか検討
"type": ["object", "null"],
"description": "選択された USDA 食品の主要栄養素（100g あたり）。例: {'calories_kcal': 150,...}",
"properties": { # 具体的な栄養素はアプリ要件に応じて定義
"calories_kcal": {"type": ["number", "null"]},
"protein_g": {"type": ["number", "null"]},
"fat_g": {"type": ["number", "null"]},
"carbohydrate_g": {"type": ["number", "null"]}
#... 他の主要栄養素
}
}
},
"required": ["ingredient_name", "weight_g"]
}
}
},
"required": ["dish_name", "type", "quantity_on_plate", "ingredients"]
}
}
},
"required": ["dishes"]
}
key_nutrients_per_100g を Gemini に直接生成させるか、Gemini には fdc_id のみを選択させ、バックエンドで USDA サービスから詳細な栄養情報を再取得してこのフィールドを埋めるかは、プロンプトの複雑性と Gemini の能力、API の応答速度のバランスを考慮して決定します。後者のアプローチ（バックエンドでの付与）の方が、Gemini への負荷を減らし、一貫性のある正確な栄養情報を保証しやすい可能性があります。本方針では、Gemini には fdc_id の選択に注力させ、key_nutrients_per_100g はバックエンドで付与するアプローチを推奨します。その場合、Gemini へのスキーマからは key_nutrients_per_100g を削除またはオプショナルとして簡略化します。4.E. USDA 検索結果のプロンプトへの整形 USDA API から取得した検索結果（各食材候補のリスト）を、Gemini が理解しやすく、かつトークン数を効率的に使用できる形式のテキストに整形する必要があります。
情報選択: 各 USDA 候補について、以下の情報をプロンプトに含めます。

description (食品名)
fdcId (FDC ID)
dataType (データタイプ)
主要栄養素（100g あたり、セクション 3.H で特定したもの。例: エネルギー、タンパク質、脂質、炭水化物）
brandOwner や ingredients (Branded Foods の場合、参考情報として)

フォーマット例:
食材「鶏むね肉」に対する USDA 候補:

FDC ID: 12345, 名称: Chicken, breast, raw (SR Legacy), 栄養素(100g あたり): エネルギー 165kcal, タンパク質 31g, 脂質 3.6g, 炭水化物 0g
FDC ID: 67890, 名称: Chicken Breast, grilled (Foundation), 栄養素(100g あたり): エネルギー 180kcal, タンパク質 35g, 脂質 4g, 炭水化物 0g
FDC ID: 11223, 名称: Organic Chicken Breast Tenderloins, (Branded), 原材料: Organic Chicken Breast, Water, Sea Salt. 栄養素(100g あたり): エネルギー 110kcal, タンパク質 23g, 脂質 1.5g, 炭水化物 0g

食材「ブロッコリー」に対する USDA 候補:

FDC ID:...

この整形されたテキストを、セクション 4.C で示したユーザープロンプト構造内の{usda_candidates_formatted_text}部分に挿入します。各食材ごとに候補を区切ることで、Gemini がどの候補がどの初期推定食材に対応するのかを理解しやすくなります。5. API 仕様 (OpenAPI - フェーズ 2)フェーズ 2API は、フェーズ 1API の出力を基に USDA データベース情報を活用して食事分析結果を精緻化する新しいエンドポイントを提供します。5.A. エンドポイント定義
パス: /v1/meal-analyses/refine
HTTP メソッド: POST
説明: ユーザーから送信された食事の画像とフェーズ 1API による初期分析結果（JSON 文字列形式）を基に、USDA FoodData Central データベースの情報を参照し、Gemini AI が食事内容を再分析・精緻化し、その結果を JSON 形式で返却します。
バージョニング: フェーズ 1API 同様、URL パスにバージョン情報 (/v1/) を含めます。
このエンドポイントは、既存の /v1/meal-analyses とは独立しており、明確に異なる責務（初期分析結果の精緻化）を持ちます。5.B. リクエストフォーマット POST /v1/meal-analyses/refine エンドポイントは、multipart/form-data コンテンツタイプのリクエストボディを受け付けます。
image (必須):

タイプ: ファイル (バイナリデータ)
説明: 分析対象の食事の画像ファイル。

initial_analysis_data (必須):

タイプ: 文字列 (JSON 文字列)
説明: フェーズ 1API (/v1/meal-analyses) が出力した JSON レスポンスの文字列。これには、初期推定された料理、食材、量などが含まれます。この文字列をバックエンドでパースして利用します。

この形式により、画像データと構造化されたテキストデータ（初期分析結果）を効率的に同一リクエストで送信できます。5.C. レスポンスフォーマット API からの成功レスポンス (200 OK) は、application/json コンテンツタイプで、セクション 4.D で定義した REFINED_MEAL_ANALYSIS_GEMINI_SCHEMA（またはそれに対応する Pydantic モデル）に基づく構造の JSON オブジェクトを返却します。JSON レスポンス構造（概念）:JSON{
"dishes":
}
//... 他の料理
]
}
このレスポンス構造は、栄養価計算の精度向上に必要な FDC ID や、選択された USDA 食品の信頼できる名称を提供します。key_nutrients_per_100g フィールドは、クライアント側での迅速な栄養価表示や、より詳細な栄養計算の入力として利用できます。5.D. エラーハンドリングフェーズ 1API と同様の標準的な HTTP ステータスコードに加え、フェーズ 2 特有のエラーケースも考慮します。
400 Bad Request:

必須パラメータ（image, initial_analysis_data）の欠如。
initial_analysis_data が不正な JSON 文字列である場合。
画像ファイル形式が無効な場合。

422 Unprocessable Entity:

initial_analysis_data の JSON 構造が期待する形式でない場合（Pydantic モデルでのバリデーションエラー）。

429 Too Many Requests:

USDA API のレートリミットを超過した場合（USDA API からの 429 エラーをクライアントに伝播する場合）。
本 API 自体のレートリミットを超過した場合（将来的な導入を考慮）。

500 Internal Server Error:

Gemini AI サービス（フェーズ 2 処理）との通信障害や内部処理エラー。
USDA API 連携中の予期せぬサーバー側エラー（USDA API が 5xx 系エラーを返した場合）。

503 Service Unavailable:

USDA API サービスが一時的に利用不可能な場合。

エラーレスポンスの JSON 形式はフェーズ 1API と一貫性を保ち、error.code と error.message を含めます。6. バックエンド実装戦略 (Python with FastAPI - フェーズ 2)フェーズ 2API のバックエンドも、Python の FastAPI フレームワークを使用して構築します。フェーズ 1API のプロジェクト構成を基盤とし、必要なコンポーネントを追加・拡張します。6.A. プロジェクト構成の再利用と拡張フェーズ 1API のプロジェクト構成 (meal_analysis_api/) をベースに、以下の変更・追加を行います。meal_analysis_api/
├── app/
│ ├── **init**.py
│ ├── main.py # FastAPI アプリケーションインスタンス、ルーター集約
│ ├── api/
│ │ ├── **init**.py
│ │ └── v1/
│ │ ├── **init**.py
│ │ ├── endpoints/
│ │ │ ├── **init**.py
│ │ │ ├── meal_analyses.py # フェーズ 1 エンドポイント (/meal-analyses)
│ │ │ └── meal_analyses_refine.py # ★ フェーズ 2 エンドポイント (/meal-analyses/refine)
│ │ └── schemas/
│ │ ├── **init**.py
│ │ └── meal.py # ★ フェーズ 1・フェーズ 2 共通の Pydantic モデル群
│ ├── core/
│ │ ├── **init**.py
│ │ └── config.py # 設定（環境変数など）
│ └── services/
│ ├── **init**.py
│ ├── gemini_service.py # ★Gemini 連携サービス (フェーズ 2 メソッド追加)
│ └── usda_service.py # ★USDA API 連携サービス (新規)
├── tests/
│ └──... # テストコード (フェーズ 2 用テスト追加)
├──.env.example
├──.gitignore
├── openapi.yaml # ★OpenAPI 仕様ファイル (フェーズ 2 エンドポイント追加)
├── Pipfile / requirements.txt
└── README.md
主な変更点：
app/api/v1/endpoints/meal_analyses_refine.py: フェーズ 2 の/refine エンドポイントのロジックを実装する新しいファイル。
app/services/usda_service.py: USDA FoodData Central API との通信を担当する新しいサービスクラスを定義。
app/services/gemini_service.py: 既存の Gemini 連携サービスに、フェーズ 2 用の新しいメソッド（USDA 情報をコンテキストとして利用）を追加。
app/api/v1/schemas/meal.py: フェーズ 2 のリクエスト・レスポンスに対応する新しい Pydantic モデルを追加。
openapi.yaml: フェーズ 2 のエンドポイント定義とスキーマ定義を追記。
6.B. Pydantic モデル（フェーズ 2）app/api/v1/schemas/meal.py に、フェーズ 2API で送受信するデータ構造を定義する Pydantic モデルを追加します。
InitialAnalysisDishPydantic / InitialAnalysisIngredientPydantic / InitialAnalysisDataPydantic:

フェーズ 1API のレスポンス JSON (initial_analysis_data 文字列) をパースして構造化データとして扱うためのモデル。フェーズ 1 のレスポンススキーマと一致させます。

USDANutrientPydantic:

USDA API から取得する栄養素情報を表すモデル。
フィールド例: name: str, amount: float, unit_name: str, nutrient_id: Optional[int] = None, nutrient_number: Optional[str] = None。

USDASearchResultItemPydantic:

USDA /foods/search API の各検索結果アイテムを表すモデル。
フィールド例: fdc_id: int, description: str, data_type: Optional[str] = None, brand_owner: Optional[str] = None, ingredients_text: Optional[str] = None (USDA の ingredients フィールドに対応), food_nutrients: List =, score: Optional[float] = None。

RefinedIngredientPydantic:

フェーズ 2API のレスポンスに含まれる、精緻化された材料情報を表すモデル。
フィールド例: ingredient_name: str, weight_g: float, fdc_id: Optional[int] = None, usda_source_description: Optional[str] = None, key_nutrients_per_100g: Optional]] = None。

RefinedDishPydantic:

フェーズ 2API のレスポンスに含まれる、精緻化された料理情報を表すモデル。
フィールド例: dish_name: str, type: str, quantity_on_plate: str, ingredients: List。

MealAnalysisRefinementResponsePydantic:

フェーズ 2API (/refine) の成功レスポンス全体を表すモデル。
フィールド例: dishes: List。

これらの Pydantic モデルは、リクエストデータのバリデーション、レスポンスデータのシリアライゼーション、そして OpenAPI スキーマの自動生成に利用されます。6.C. /meal-analyses/refine エンドポイントのコアロジック app/api/v1/endpoints/meal_analyses_refine.py に実装します。Pythonfrom fastapi import APIRouter, File, Form, UploadFile, HTTPException, Depends
from typing import Annotated, List, Optional, Dict
import json

# Pydantic モデル (app.api.v1.schemas.meal からインポート)

from..schemas.meal import (
InitialAnalysisDataPydantic,
MealAnalysisRefinementResponsePydantic,
USDASearchResultItemPydantic
)

# サービス (app.services からインポート)

from...services.usda_service import USDAService, get_usda_service
from...services.gemini_service import GeminiMealAnalyzer, get_gemini_analyzer # フェーズ 1 と同じ依存関係を使用可能
from...core.config import Settings, get_settings

router = APIRouter()

@router.post(
"/refine",
response_model=MealAnalysisRefinementResponsePydantic,
summary="食事分析結果を USDA データで精緻化 (Refine Meal Analysis with USDA Data)",
description="画像と初期 AI 分析結果を基に、USDA 食品データベースの情報を参照し、Gemini AI で再分析・精緻化します。"
)
async def refine_meal_analysis(
settings: Annotated,
image: Annotated[UploadFile, File(description="食事の画像ファイル。")],
initial_analysis_data_str: Annotated,
usda_service: Annotated,
gemini_service: Annotated # 既存の Gemini サービスを拡張して利用
): # 1. 画像バリデーション
if not image.content_type or not image.content_type.startswith("image/"):
raise HTTPException(status_code=400, detail="無効な画像ファイル形式です。")
image_bytes = await image.read() # TODO: 最大ファイルサイズチェック

    # 2. initial_analysis_data_str をパース
    try:
        initial_analysis_dict = json.loads(initial_analysis_data_str)
        initial_analysis = InitialAnalysisDataPydantic(**initial_analysis_dict)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="initial_analysis_dataが不正なJSON形式です。")
    except Exception as e: # Pydanticバリデーションエラーなど
        raise HTTPException(status_code=422, detail=f"initial_analysis_dataの形式エラー: {str(e)}")

    # 3. USDA候補情報を収集し、プロンプト用テキストを生成
    usda_candidates_prompt_segments =
    # 各料理・材料についてUSDA検索結果を格納する辞書（後でkey_nutrients_per_100gを付与するため）
    all_usda_search_results_map: Dict = {}


    for dish in initial_analysis.dishes:
        for ingredient in dish.ingredients:
            search_query = ingredient.ingredient_name
            try:
                # 検索するデータタイプをconfigから取得できるようにするのも良い
                # 例: settings.USDA_PREFERRED_DATA_TYPES or
                usda_results: List = await usda_service.search_foods(
                    query=search_query,
                    page_size=settings.USDA_SEARCH_CANDIDATES_LIMIT  # 例: 5件
                )
                if usda_results:
                    segment = f"食材「{search_query}」に対するUSDA候補:\n"
                    for i, item in enumerate(usda_results):
                        all_usda_search_results_map[item.fdc_id] = item # 後で参照するために保存
                        # プロンプトに含める栄養素情報を整形
                        nutrients_str_parts =
                        for nutr in item.food_nutrients: # USDASearchResultItemPydantic には主要栄養素のみ含める想定
                            if nutr.name and nutr.amount is not None and nutr.unit_name:
                                nutrients_str_parts.append(f"{nutr.name}: {nutr.amount}{nutr.unit_name}")
                        nutrients_str = ", ".join(nutrients_str_parts) if nutrients_str_parts else "栄養素情報なし"

                        segment += (
                            f"{i+1}. FDC ID: {item.fdc_id}, 名称: {item.description} ({item.data_type or 'N/A'}), "
                            f"栄養素(100gあたり): {nutrients_str}"
                        )
                        if item.brand_owner:
                            segment += f", ブランド: {item.brand_owner}"
                        if item.ingredients_text: # Branded Foods の原材料情報
                             segment += f", 原材料: {item.ingredients_text[:100]}..." # 長すぎる場合は省略
                        segment += "\n"
                    usda_candidates_prompt_segments.append(segment)
            except RuntimeError as e: # USDAService内でのエラー
                # ログ記録推奨
                # ここでは処理を継続し、Geminiには取得できた情報のみを渡すか、エラーを返すか選択
                # 今回は一部のUSDA検索が失敗しても、他の情報でGeminiに判断させる方針
                usda_candidates_prompt_segments.append(f"食材「{search_query}」のUSDA候補検索中にエラーが発生しました: {str(e)}\n")
            except Exception as e:
                # 予期せぬエラー
                usda_candidates_prompt_segments.append(f"食材「{search_query}」のUSDA候補検索中に予期せぬエラー: {str(e)}\n")


    usda_candidates_prompt_text = "\n---\n".join(usda_candidates_prompt_segments) if usda_candidates_prompt_segments else "USDA候補情報はありませんでした。"

    # 4. Geminiサービス（フェーズ2用メソッド）を呼び出し
    try:
        # Geminiに渡すスキーマは MealAnalysisRefinementResponsePydantic に対応するもの
        # REFINED_MEAL_ANALYSIS_GEMINI_SCHEMA を gemini_service 内で定義・利用
        refined_gemini_output_dict = await gemini_service.analyze_image_with_usda_context(
            image_bytes=image_bytes,
            image_mime_type=image.content_type,
            usda_candidates_text=usda_candidates_prompt_text,
            initial_ai_output_text=initial_analysis_data_str # フェーズ1の出力をそのまま渡す
        )

        # 5. Gemini出力をパースし、必要に応じてkey_nutrients_per_100gを付与
        # Pydanticモデルでパースすることで、スキーマ通りの構造になっているか検証
        refined_analysis_response = MealAnalysisRefinementResponsePydantic(**refined_gemini_output_dict)

        # バックエンドで key_nutrients_per_100g を付与する場合のロジック
        for dish_resp in refined_analysis_response.dishes:
            for ing_resp in dish_resp.ingredients:
                if ing_resp.fdc_id and ing_resp.fdc_id in all_usda_search_results_map:
                    usda_item = all_usda_search_results_map[ing_resp.fdc_id]
                    key_nutrients = {}
                    # USDASearchResultItemPydantic.food_nutrients から必要なものを抽出
                    for nutr in usda_item.food_nutrients:
                         # 栄養素名をキーとして整形（例: "Protein" -> "protein_g"）
                        if nutr.name and nutr.amount is not None:
                            # このキー名はレスポンススキーマと一致させる
                            if "energy" in nutr.name.lower() and "kcal" in nutr.unit_name.lower():
                                key_nutrients["calories_kcal"] = nutr.amount
                            elif "protein" in nutr.name.lower():
                                key_nutrients["protein_g"] = nutr.amount
                            elif "total lipid (fat)" in nutr.name.lower():
                                key_nutrients["fat_g"] = nutr.amount
                            elif "carbohydrate, by difference" in nutr.name.lower():
                                key_nutrients["carbohydrate_g"] = nutr.amount
                            #... 他の主要栄養素も同様にマッピング
                    ing_resp.key_nutrients_per_100g = key_nutrients
                elif ing_resp.fdc_id:
                    # Geminiがfdc_idを選択したが、元の検索結果にない場合（通常は起こらないはず）
                    # または、Geminiにkey_nutrients_per_100gの生成を任せる場合はこの処理は不要
                    pass


        return refined_analysis_response # FastAPIがJSONにシリアライズ

    except RuntimeError as e: # GeminiサービスまたはUSDAサービスからのエラー
        # ログ記録
        raise HTTPException(status_code=503, detail=f"外部サービス連携エラー: {str(e)}")
    except ValueError as e: # JSONパースエラーなど
        # ログ記録
        raise HTTPException(status_code=500, detail=f"処理エラー: {str(e)}")
    except Exception as e: # その他の予期せぬエラー
        # ログ記録
        raise HTTPException(status_code=500, detail=f"予期せぬ内部エラーが発生しました: {str(e)}")

処理ステップの解説:
リクエストから画像と初期分析データ（JSON 文字列）を取得し、基本的なバリデーションを行います。
初期分析データ文字列を InitialAnalysisDataPydantic モデルにパースします。これにより、構造化されたデータとして扱えるようになります。
初期分析データの各食材について、usda_service.search_foods を呼び出し、USDA データベースから候補食品を検索します。取得した候補情報は、Gemini へのプロンプト用に整形されたテキスト（usda_candidates_prompt_text）に集約されます。この際、後で栄養情報を参照できるように、取得した USDA 検索結果（USDASearchResultItemPydantic オブジェクト）を fdc_id をキーとする辞書 all_usda_search_results_map にも保存しておきます。
整形された USDA 候補情報テキスト、元の画像、初期分析データ文字列を gemini_service.analyze_image_with_usda_context メソッドに渡し、Gemini による再分析を依頼します。
Gemini からのレスポンス（JSON 形式を期待）を MealAnalysisRefinementResponsePydantic モデルにパースします。
栄養情報の付与: Gemini が各材料に対して fdc_id を選択して返してきた場合、その fdc_id を元に all_usda_search_results_map から対応する USDA 食品の完全な栄養素情報を参照し、レスポンスの key_nutrients_per_100g フィールドをバックエンドで構築・設定します。これにより、Gemini のプロンプトやレスポンススキーマを複雑にしすぎることなく、正確な栄養情報をクライアントに提供できます。
最終的な Pydantic レスポンスオブジェクトを返却します（FastAPI が JSON に自動シリアライズ）。
USDA サービスや Gemini サービスとの通信エラー、データパースエラーなど、各ステップで発生しうる例外を捕捉し、適切な HTTP エラーレスポンスを返します。
このロジックにより、フェーズ 1 の AI 分析結果を USDA データベースの情報で補強し、より信頼性の高い最終結果を生成することを目指します。特に、バックエンドで key_nutrients_per_100g を付与するステップは、Gemini のタスクを「最適な USDA エントリの選択」に集中させ、栄養データの正確性を担保する上で重要です。6.D. USDA サービス実装 (app/services/usda_service.py)USDA FoodData Central API との通信をカプセル化するサービスクラス。Python# app/services/usda_service.py
import httpx
from typing import List, Optional, Dict, Any
from..core.config import settings # 環境変数から API キーなどをロード
from..api.v1.schemas.meal import USDASearchResultItemPydantic, USDANutrientPydantic # Pydantic モデル

class USDAService:
def **init**(self, api_key: str = settings.USDA_API_KEY,
base_url: str = settings.USDA_API_BASE_URL):
if not api_key: # アプリケーション起動時にチェックされるべきだが、念のため # logging.error("USDA_API_KEY is not configured.")
raise ValueError("USDA API key not configured.")
self.api_key = api_key
self.base_url = base_url # httpx.AsyncClient は **aenter**/**aexit** を持つため、 # Depends でインスタンスを生成・破棄するのが望ましい # ここでは簡略化のため、コンストラクタで初期化する例を示すが、 # get_usda_service のような依存性注入関数内で管理することを推奨
self.client = httpx.AsyncClient(timeout=settings.USDA_API_TIMEOUT) # 例: 10.0 秒

    async def search_foods(
        self,
        query: str,
        data_types: Optional[List[str]] = None, # 例:
        page_size: int = 5,
        page_number: int = 1,
        sort_by: str = "score", # USDA APIのデフォルトは relevance (score) だったはず
        sort_order: str = "desc" # 関連度高い順
    ) -> List:

        params = {
            "query": query,
            "api_key": self.api_key,
            "pageSize": page_size,
            "pageNumber": page_number,
            "sortBy": sort_by,
            "sortOrder": sort_order
        }
        if data_types:
            # USDA APIのGET /foods/search は dataType をカンマ区切り文字列で受け付けるか、
            # または繰り返しパラメータ (dataType=A&dataType=B) で受け付けるか要確認。
            # Postmanのドキュメント[13]では <string> とあり "specify one or more values in an array" と注釈。
            # API Guide [6] の POST 例ではJSON配列。GETでの複数指定はカンマ区切りが一般的。
            params = ",".join(data_types)

        # 特定の栄養素IDリスト (例: エネルギー、タンパク質、脂質、炭水化物)
        # これらを指定すると、レスポンスの foodNutrients がフィルタリングされる
        # settings.USDA_TARGET_NUTRIENT_IDS (例: )
        # target_nutrient_ids = settings.USDA_TARGET_NUTRIENT_IDS
        # if target_nutrient_ids:
        #    params["nutrients"] = ",".join(map(str, target_nutrient_ids))


        try:
            response = await self.client.get(f"{self.base_url}/foods/search", params=params)
            # レートリミットヘッダーのログ記録を検討 (X-RateLimit-Remaining) [7, 8]
            # logger.info(f"USDA API Rate Limit Remaining: {response.headers.get('X-RateLimit-Remaining')}")
            response.raise_for_status()  # 4xx/5xxエラーで例外発生

            data = response.json()
            results =

            # FoodData Central API /foods/search のレスポンス構造に基づくパース
            # data は {"totalHits":..., "currentPage":..., "totalPages":..., "foods": [...]} のような形
            for food_data in data.get("foods",)[:page_size]: # pageSizeを超えたデータは無視
                nutrients_extracted =
                # foodNutrients 配列から主要栄養素を抽出
                for nutrient_entry in food_data.get("foodNutrients",):
                    # nutrient_entry は {"nutrientId":..., "nutrientName":..., "nutrientNumber":...,
                    #                   "unitName":..., "value":..., "derivationDescription":...} のような形 (AbridgedFoodItem)
                    # または {"nutrient": {"id":..., "number":..., "name":..., "rank":..., "unitName":...},
                    #        "type":..., "id":..., "amount":...} (SearchResultFood)
                    # [16] の例では後者の構造に近い (FoodNutrient object in Food object)

                    # [16]の構造を優先的に想定 (amount, nutrient.id, nutrient.name, nutrient.unitName)
                    nutrient_detail = nutrient_entry.get("nutrient", {}) # SR Legacy, Foundation
                    amount = nutrient_entry.get("amount") # SR Legacy, Foundation

                    # Branded Foods の abridged format では nutrient_entry が直接栄養素情報を持つ場合がある
                    # 例: {"nutrientId": 1008, "nutrientName": "Energy", "nutrientNumber": "208", "unitName": "KCAL", "value": 200}
                    if not nutrient_detail and "nutrientId" in nutrient_entry: # Branded abridged
                        nutrient_id = nutrient_entry.get("nutrientId")
                        name = nutrient_entry.get("nutrientName")
                        number = nutrient_entry.get("nutrientNumber")
                        unit_name = nutrient_entry.get("unitName")
                        amount = nutrient_entry.get("value") # Branded abridged では "value"
                    else: # SR Legacy, Foundation, or full Branded
                        nutrient_id = nutrient_detail.get("id")
                        name = nutrient_detail.get("name")
                        number = nutrient_detail.get("number")
                        unit_name = nutrient_detail.get("unitName")

                    # 主要栄養素のみを抽出するロジック（設定ファイルでIDリストを管理推奨）
                    # settings.USDA_KEY_NUTRIENT_NUMBERS (例: ["208", "203", "204", "205", "291", "269"])
                    if number in settings.USDA_KEY_NUTRIENT_NUMBERS:
                         if name and amount is not None and unit_name:
                            nutrients_extracted.append(
                                USDANutrientPydantic(
                                    name=name,
                                    amount=float(amount),
                                    unit_name=unit_name,
                                    nutrient_id=int(nutrient_id) if nutrient_id else None,
                                    nutrient_number=str(number) if number else None
                                )
                            )

                results.append(
                    USDASearchResultItemPydantic(
                        fdc_id=food_data.get("fdcId"),
                        description=food_data.get("description"),
                        data_type=food_data.get("dataType"),
                        brand_owner=food_data.get("brandOwner"), # Branded Foods
                        ingredients_text=food_data.get("ingredients"), # Branded Foods
                        food_nutrients=nutrients_extracted,
                        score=food_data.get("score") # 検索スコア
                    )
                )
            return results
        except httpx.HTTPStatusError as e:
            # logger.error(f"USDA API HTTP error: {e.response.status_code} - {e.response.text}")
            if e.response.status_code == 429:
                raise RuntimeError(f"USDA API rate limit exceeded. Detail: {e.response.text}") from e
            raise RuntimeError(f"USDA API error: {e.response.status_code} - {e.response.text}") from e
        except httpx.RequestError as e: # Timeout, ConnectionErrorなど
            # logger.error(f"USDA API request failed: {str(e)}")
            raise RuntimeError(f"USDA API request failed: {str(e)}") from e
        except (json.JSONDecodeError, TypeError, KeyError) as e: # レスポンスのパースエラー
            # logger.error(f"USDA API response parsing error: {str(e)}")
            raise RuntimeError(f"USDA API response parsing error: {str(e)}") from e
        except Exception as e:
            # logger.error(f"Unexpected error in USDAService.search_foods: {str(e)}")
            raise RuntimeError(f"Unexpected error in USDA service: {str(e)}") from e

    async def get_food_details(self, fdc_id: int, format: str = "full",
                               target_nutrient_numbers: Optional[List[str]] = None) -> Optional: # 返り値は詳細情報を含むモデルでも良い
        # `/v1/food/{fdcId}` エンドポイントを呼び出すロジック
        # search_foods と同様のエラーハンドリングとパース処理
        # target_nutrient_numbers を `nutrients` パラメータとして渡す (カンマ区切り文字列)
        # 返り値は USDASearchResultItemPydantic またはより詳細な USDAFoodDetailsPydanticModel
        # (このメソッドは現状の /refine エンドポイントでは直接使用されていないが、将来的な拡張のため)
        params = {
            "api_key": self.api_key,
            "format": format
        }
        if target_nutrient_numbers:
            params["nutrients"] = ",".join(target_nutrient_numbers)

        try:
            response = await self.client.get(f"{self.base_url}/food/{fdc_id}", params=params)
            response.raise_for_status()
            food_data = response.json() # Food オブジェクトが返る

            # food_data から USDASearchResultItemPydantic を構築するロジック (search_foods と同様)
            # foodNutrients の構造は /foods/search のものとほぼ同じはず [16]
            nutrients_extracted =
            for nutrient_entry in food_data.get("foodNutrients",):
                nutrient_detail = nutrient_entry.get("nutrient", {})
                amount = nutrient_entry.get("amount")

                nutrient_id = nutrient_detail.get("id")
                name = nutrient_detail.get("name")
                number = nutrient_detail.get("number")
                unit_name = nutrient_detail.get("unitName")

                if name and amount is not None and unit_name: # ターゲット栄養素のフィルタリングは省略 (全栄養素取得想定)
                    nutrients_extracted.append(
                        USDANutrientPydantic(
                            name=name,
                            amount=float(amount),
                            unit_name=unit_name,
                            nutrient_id=int(nutrient_id) if nutrient_id else None,
                            nutrient_number=str(number) if number else None
                        )
                    )

            return USDASearchResultItemPydantic(
                fdc_id=food_data.get("fdcId"),
                description=food_data.get("description"),
                data_type=food_data.get("dataType"),
                brand_owner=food_data.get("brandOwner"),
                ingredients_text=food_data.get("ingredients"),
                food_nutrients=nutrients_extracted,
                # score は /food/{fdcId} には無い
            )

        except Exception as e:
            # logger.error(f"Error fetching food details for FDC ID {fdc_id}: {str(e)}")
            # エラー処理は search_foods と同様
            return None # または例外をraise

    async def close_client(self):
        await self.client.aclose()

# FastAPI の依存性注入用関数

async def get_usda_service(): # settings は main.py や endpoint で Depends(get_settings) 経由で取得し、 # ここに渡すか、USDAService 内で直接 settings をインポートする。 # ここでは USDAService が直接 settings をインポートする想定。
service = USDAService()
try:
yield service
finally:
await service.close_client()

実装のポイント:
httpx.AsyncClient を使用して非同期 HTTP リクエストを実行します。クライアントのライフサイクル管理（初期化とクローズ）は、FastAPI の依存性注入システム (Depends) を利用して行うのが適切です。
API キーは設定 (settings.USDA_API_KEY) から取得します。
search_foods メソッド:

必須パラメータ (query, api_key) とオプションパラメータ (dataType, pageSize など) を組み立てて /foods/search エンドポイントに GET リクエストを送信します。
レスポンス JSON をパースし、各食品アイテムを USDASearchResultItemPydantic モデルのインスタンスに変換します。この際、foodNutrients からは事前に定義された主要栄養素（例: settings.USDA_KEY_NUTRIENT_NUMBERS で ID リストを管理）のみを抽出して USDANutrientPydantic オブジェクトのリストとして格納します。これにより、後続処理で扱うデータ量を最適化します。
USDA API のレスポンス構造はデータタイプ（SR Legacy, Branded など）やフォーマット（abridged, full）によって微妙に異なる可能性があるため 16、パースロジックは頑健性を持たせる必要があります。特に foodNutrients 内の栄養素量を示すキーが amount なのか value なのかは注意が必要です（16 では amount が新しい形式と示唆）。

get_food_details メソッド: 特定の fdcId の詳細情報を取得します。/refine エンドポイントの現在のロジックでは直接使用されませんが、将来的な機能拡張（例: ユーザーが特定の USDA 候補の詳細を見たい場合など）のために実装しておく価値があります。
エラーハンドリング: ネットワークエラー (httpx.RequestError)、HTTP エラーステータスコード (httpx.HTTPStatusError、特に 429 Rate Limit Exceeded)、JSON パースエラーなどを適切に捕捉し、カスタム例外または RuntimeError を送出して上位の呼び出し元（エンドポイントロジック）に伝えます。
dataType パラメータの扱い: USDA API の GET リクエストで複数の dataType を指定する方法（カンマ区切りか、パラメータの繰り返し&dataType=A&dataType=B か）は、公式ドキュメントや実際の API 挙動で最終確認が必要です。Postman のドキュメント 13 では<string>型で「配列で一つ以上の値を指定」とあり曖昧ですが、一般的にはカンマ区切りが用いられることが多いです。コード例ではカンマ区切りを採用しています。
主要栄養素の抽出: USDASearchResultItemPydantic に含める food_nutrients は、アプリケーションにとって重要な栄養素（設定ファイル settings.USDA_KEY_NUTRIENT_NUMBERS で管理する栄養素番号リストに基づいてフィルタリング）に限定することが推奨されます。これにより、Gemini へのプロンプトに含める情報量を制御し、レスポンスサイズを最適化します。
この USDAService は、USDA データベースとの連携における複雑さを抽象化し、API エンドポイントのロジックをクリーンに保つ役割を果たします。6.E. Gemini サービス更新 (app/services/gemini_service.py)既存の GeminiMealAnalyzer クラスに、フェーズ 2 処理のための新しい非同期メソッドを追加します。Python# app/services/gemini_service.py (既存のクラスに追加)

# from vertexai.generative_models import Part # 既存の import に追記または確認

# from..api.v1.schemas.meal import REFINED_MEAL_ANALYSIS_GEMINI_SCHEMA # スキーマ定義をインポート

class GeminiMealAnalyzer:
#... (既存の **init**, analyze_image_and_text メソッド)...

    async def analyze_image_with_usda_context(
        self,
        image_bytes: bytes,
        image_mime_type: str,
        usda_candidates_text: str,
        initial_ai_output_text: Optional[str] = None,
        # refined_schema: Optional = None # スキーマは __init__ で設定済みのものを使うか、引数で渡すか
    ) -> Dict:
        # refined_schema が None の場合は、クラスのデフォルトスキーマ (REFINED_MEAL_ANALYSIS_GEMINI_SCHEMA) を使用
        # current_schema = refined_schema if refined_schema else self.default_refined_schema
        # (self.default_refined_schema は __init__ で REFINED_MEAL_ANALYSIS_GEMINI_SCHEMA をロードしておく)

        image_part = Part.from_data(data=image_bytes, mime_type=image_mime_type)

        prompt_text_parts =
        # システムインストラクションは self.model の system_instruction で設定済みと仮定
        # または、ここで明示的に追加も可能

        if initial_ai_output_text:
            prompt_text_parts.append(f"初期AI分析結果:\n{initial_ai_output_text}\n")

        prompt_text_parts.append(f"上記分析結果と画像に関するUSDA食品データベースの候補情報:\n{usda_candidates_text}\n")
        prompt_text_parts.append("これらの情報を踏まえ、システムインストラクションに従って最終的な分析結果をJSON形式で生成してください。")

        full_prompt_text = "\n".join(prompt_text_parts)

        # contents リストを作成
        contents_for_gemini = [image_part, Part.from_text(full_prompt_text)]

        try:
            # generation_config は __init__ で設定したものをベースに、
            # response_schema をフェーズ2用に差し替えるか、専用のconfigを用意
            current_generation_config = self.generation_config.copy() # 既存のconfigをコピー
            current_generation_config.response_schema = REFINED_MEAL_ANALYSIS_GEMINI_SCHEMA # フェーズ2用スキーマ
            current_generation_config.response_mime_type = "application/json"


            response = await self.model.generate_content_async(
                contents_for_gemini,
                generation_config=current_generation_config, # フェーズ2用スキーマを含むconfig
                safety_settings=self.safety_settings
            )

            # レスポンスのパース (フェーズ1と同様のロジック)
            if not response.candidates or not response.candidates.content.parts:
                # logger.error("Gemini (Phase 2) returned no valid candidates or parts.")
                raise ValueError("Geminiからレスポンス候補またはパートが返されませんでした。")

            json_string = response.candidates.content.parts.text
            # logger.debug(f"Gemini (Phase 2) raw JSON response: {json_string}")
            return json.loads(json_string)

        except ValueError as ve: # JSONパースエラーやレスポンス構造の問題
            # logger.error(f"Gemini (Phase 2) response processing error: {ve}. Raw response: {getattr(response, 'text', 'N/A')}")
            raise RuntimeError(f"Gemini(フェーズ2)からの応答処理中にエラー: {ve}") from ve
        except Exception as e: # その他のGemini API関連エラー
            # logger.error(f"Gemini (Phase 2) API request failed: {e}")
            raise RuntimeError(f"Gemini(フェーズ2) APIリクエスト失敗: {e}") from e

実装のポイント:
メソッドシグネチャ: 画像バイト列、MIME タイプ、整形された USDA 候補テキスト、そしてオプションでフェーズ 1 の AI 出力テキスト（JSON 文字列）を受け取ります。
プロンプト構築:

画像パート (Part.from_data)。
テキストパート (Part.from_text) には、システムインストラクション（セクション 4.C で定義したもの、モデル初期化時に設定されていれば不要）、フェーズ 1AI 出力、および整形された USDA 候補情報を結合して含めます。

GenerationConfig: response_mime_type="application/json" と、フェーズ 2API のレスポンス構造に対応する JSON スキーマ（REFINED_MEAL_ANALYSIS_GEMINI_SCHEMA、セクション 4.D で定義）を指定します。
generate_content_async 呼び出し: 構築したプロンプトパートと GenerationConfig を使用して Gemini API を非同期に呼び出します。
レスポンス処理: Gemini からの JSON 文字列レスポンスをパースして Python 辞書として返します。エラーハンドリングはフェーズ 1 と同様に堅牢に行います。
このメソッドにより、GeminiMealAnalyzer はフェーズ 2 のより複雑な推論タスク（画像、初期分析、USDA 候補の統合評価）を実行できるようになります。プロンプトの文言や情報の提示順序は、最適な結果を得るために実験と調整が必要になる場合があります。7. OpenAPI Specification (openapi.yaml - フェーズ 2 スニペット)フェーズ 2API のコントラクトを定義するため、既存の openapi.yaml ファイルに新しいエンドポイントと関連スキーマを追加します。YAML# openapi.yaml (既存ファイルに追記・変更)

#... (既存の info, servers, paths./v1/meal-analyses など)...

paths:
#... (既存の /v1/meal-analyses)...
/v1/meal-analyses/refine:
post:
summary: 食事分析結果を USDA データで精緻化 (Refine Meal Analysis with USDA Data)
operationId: refineMealAnalysisWithUSDA
description: >
送信された食事画像と初期 AI 分析結果（フェーズ 1 の出力）を基に、
USDA 食品データベースの情報を参照し、AI（Gemini）が食事内容を再分析・精緻化します。
特定された料理、種類、量、材料（USDA の FDC ID を含む）を含む構造化 JSON を返します。
tags: - Meal Analysis
requestBody:
required: true
content:
multipart/form-data:
schema:
type: object
properties:
image:
type: string
format: binary
description: 食事の画像ファイル。
initial_analysis_data: # alias="initial_analysis_data" に対応
type: string
description: >
フェーズ 1API (/v1/meal-analyses) が出力した JSON レスポンスの文字列。
例: {"dishes":}
required: - image - initial_analysis_data
encoding: # initial_analysis_data が application/json であることを明示 (任意)
initial_analysis_data:
contentType: application/json # この指定はツールによっては解釈されない場合もあるが、意図を明確にする
responses:
'200':
description: 食事分析の精緻化成功。
content:
application/json:
schema:
$ref: '#/components/schemas/MealAnalysisRefinementResponseObject'
'400':
description: 不正なリクエスト (例: 必須パラメータ欠如、不正な JSON 文字列)。
content:
application/json:
schema:
$ref: '#/components/schemas/ErrorResponseObject'
'422':
description: 処理不可能なエンティティ (例: initial_analysis_data の JSON 構造が不正)。
content:
application/json:
schema:
$ref: '#/components/schemas/ErrorResponseObject'
'429':
description: リクエストが多すぎます (例: USDA API レートリミット超過)。
content:
application/json:
schema:
$ref: '#/components/schemas/ErrorResponseObject'
'500':
description: 内部サーバーエラー。
content:
application/json:
schema:
$ref: '#/components/schemas/ErrorResponseObject'
'503':
description: サービス利用不可 (例: 外部 AI または USDA サービスの問題)。
content:
application/json:
schema:
$ref: '#/components/schemas/ErrorResponseObject'

components:
schemas:
#... (既存の IngredientObject, DishObject, MealAnalysisResponseObject, ErrorResponseObject)...

    # --- フェーズ1の出力を表すスキーマ (initial_analysis_data用) ---
    InitialAnalysisIngredientObject:
      type: object
      description: フェーズ1で推定された材料オブジェクト。
      properties:
        ingredient_name:
          type: string
          description: 材料の名称。
        weight_g:
          type: number
          format: float
          description: 材料の推定重量（グラム単位）。
      required:
        - ingredient_name
        - weight_g

    InitialAnalysisDishObject:
      type: object
      description: フェーズ1で推定された料理オブジェクト。
      properties:
        dish_name:
          type: string
        type:
          type: string
        quantity_on_plate:
          type: string
        ingredients:
          type: array
          items:
            $ref: '#/components/schemas/InitialAnalysisIngredientObject'
      required:
        - dish_name
        - type
        - quantity_on_plate
        - ingredients

    InitialAnalysisDataObject: # initial_analysis_data のJSON文字列がパースされた後の構造
      type: object
      properties:
        dishes:
          type: array
          items:
            $ref: '#/components/schemas/InitialAnalysisDishObject'
      required:
        - dishes

    # --- USDA検索結果を表すスキーマ ---
    USDANutrientObject:
      type: object
      description: USDA食品の栄養素情報。
      properties:
        name:
          type: string
          description: 栄養素名。
        amount:
          type: number
          format: float
          description: 100gまたは100mlあたりの量。
        unit_name:
          type: string
          description: 単位名 (例: "g", "mg", "kcal")。
        nutrient_id: # USDA nutrient.id
          type: integer
          nullable: true
          description: USDA栄養素ID。
        nutrient_number: # USDA nutrient.number
          type: string
          nullable: true
          description: USDA栄養素番号。
      required:
        - name
        - amount
        - unit_name

    USDASearchResultItemObject:
      type: object
      description: USDA食品検索結果の単一アイテム。
      properties:
        fdc_id:
          type: integer
          description: USDA FoodData Central ID。
        description:
          type: string
          description: 食品の公式名称。
        data_type:
          type: string
          nullable: true
          description: USDAデータタイプ (例: "SR Legacy", "Branded")。
        brand_owner:
          type: string
          nullable: true
          description: ブランド所有者 (Branded Foodsの場合)。
        ingredients_text:
          type: string
          nullable: true
          description: 原材料リスト文字列 (Branded Foodsの場合)。
        food_nutrients:
          type: array
          items:
            $ref: '#/components/schemas/USDANutrientObject'
          description: 主要な栄養素情報のリスト。
        score:
          type: number
          format: float
          nullable: true
          description: 検索結果の関連度スコア。
      required:
        - fdc_id
        - description

    # --- フェーズ2のレスポンススキーマ ---
    KeyNutrientsObject: # key_nutrients_per_100g のためのスキーマ
      type: object
      nullable: true
      description: 選択されたUSDA食品の主要栄養素（100gあたり）。キーは栄養素名（例: "calories_kcal"）、値は量。
      additionalProperties: # 任意の栄養素キーを許可 (または具体的に定義)
        type: number
        nullable: true
      example:
        calories_kcal: 165
        protein_g: 31.0
        fat_g: 3.6
        carbohydrate_g: 0.0

    RefinedIngredientObject:
      type: object
      description: USDA情報で精緻化された材料オブジェクト。
      properties:
        ingredient_name:
          type: string
          description: 材料の名称（精緻化後）。
        weight_g:
          type: number
          format: float
          description: 材料の推定重量（グラム単位）。
        fdc_id:
          type: integer
          nullable: true
          description: 対応するUSDA食品のFDC ID。
        usda_source_description:
          type: string
          nullable: true
          description: 選択されたUSDA食品の公式名称。
        key_nutrients_per_100g: # バックエンドで付与する場合
          $ref: '#/components/schemas/KeyNutrientsObject'
      required:
        - ingredient_name
        - weight_g

    RefinedDishObject:
      type: object
      description: USDA情報で精緻化された料理オブジェクト。
      properties:
        dish_name:
          type: string
        type:
          type: string
        quantity_on_plate:
          type: string
        ingredients:
          type: array
          items:
            $ref: '#/components/schemas/RefinedIngredientObject'
      required:
        - dish_name
        - type
        - quantity_on_plate
        - ingredients

    MealAnalysisRefinementResponseObject: # /refine エンドポイントのメインレスポンス
      type: object
      properties:
        dishes:
          type: array
          items:
            $ref: '#/components/schemas/RefinedDishObject'
      required:
        - dishes

この OpenAPI 仕様は、フェーズ 2API のコントラクトを明確に定義し、クライアント（Flutter アプリ）開発者が OpenAPI Generator を使用して型安全なクライアントコードを生成するための基礎となります。initial_analysis_data を文字列として受け取り、バックエンドで JSON パースおよび Pydantic モデルへの変換を行うアプローチは、multipart/form-data で複雑な JSON オブジェクトを直接送信する際の曖昧さを回避し、リクエストの構造をシンプルに保つのに役立ちます。KeyNutrientsObject の additionalProperties: true は柔軟性を提供しますが、クライアント側での取り扱いを考慮し、期待される主要な栄養素キーを明示的に properties として定義することも検討できます。8. デプロイメントと運用上の注意点フェーズ 2API の本番運用に向けて、フェーズ 1 で考慮された点に加え、USDA API 連携に伴う新たな注意点が生じます。8.A. 環境変数の更新アプリケーションの動作に必要な設定値は、引き続き環境変数を通じて管理します。フェーズ 2 では USDA API 関連の変数が追加されます。表 8.1: 主要な設定変数（フェーズ 2 更新版）変数名説明例ソース GEMINI_PROJECT_IDVertex AI 用の Google Cloud プロジェクト IDmy-gcp-project-12345 環境変数 GEMINI_LOCATIONVertex AI のリージョン/ロケーション us-central1 環境変数 GEMINI_MODEL_NAME 使用する特定の Gemini モデル名 gemini-1.5-flash-latest 環境変数 USDA_API_KEYUSDA FoodData Central API キー YOUR_USDA_API_KEY_HERE 環境変数 USDA_API_BASE_URLUSDA FoodData Central API のベース URLhttps://api.nal.usda.gov/fdc/v1環境変数USDA_API_TIMEOUTUSDA API 呼び出しのタイムアウト秒数 10.0 環境変数 USDA_SEARCH_CANDIDATES_LIMIT1 回の USDA 検索で取得する最大候補数 5 環境変数 USDA_KEY_NUTRIENT_NUMBERSUSDAService で抽出する主要栄養素の番号リスト（カンマ区切り文字列）"208,203,204,205,291,269"環境変数 API_LOG_LEVELAPI のロギングレベル INFO 環境変数 FASTAPI_ENVFastAPI の実行環境 (例: development, production)production 環境変数 CORS_ALLOWED_ORIGINSCORS を許可するオリジンのリスト（カンマ区切り）http://localhost:3000,https://app.example.com環境変数CACHE_TYPEキャッシュの種類 (例: "redis", "memcached", "simple")simple (インメモリ) / redis 環境変数 CACHE_REDIS_URLRedis キャッシュを使用する場合の URLredis://localhost:6379/0 環境変数 USDA_CACHE_TTL_SECONDSUSDA API レスポンスのキャッシュ有効期間（秒）3600 (1 時間)環境変数これらの変数を一元的に管理し、ドキュメント化することで、デプロイメント、ローカルでの開発セットアップ、トラブルシューティングが円滑に行え、設定ミスによるエラーを低減できます。特に、USDA_API_KEY のような機密情報は安全に管理する必要があります。8.B. 拡張ロギングフェーズ 2API の動作状況を詳細に把握し、問題発生時の原因究明を迅速に行うため、以下のロギングポイントを追加します。
USDA API 連携:

USDAService が USDA API に送信するリクエスト（URL、主要パラメータ。API キーはマスクする）。
USDA API から受信したレスポンスのステータスコード、ヘッダー（特に X-RateLimit-Limit, X-RateLimit-Remaining 7）、およびエラー時のレスポンスボディ。
キャッシュのヒット/ミス状況、キャッシュキー。

Gemini（フェーズ 2）連携:

GeminiMealAnalyzer の analyze_image_with_usda_context メソッドに渡される整形済み usda_candidates_text と initial_ai_output_text（機密情報や個人情報を含まない範囲で、デバッグ用にログレベル制御）。
Gemini（フェーズ 2）から返却された JSON レスポンス（構造化出力が期待通りか確認するため）。

エンドポイント処理:

/refine エンドポイントへのリクエスト受信時（主要な入力パラメータの概要）。
処理中の主要なステップ（例: USDA 検索開始/終了、Gemini 呼び出し開始/終了）。
最終的なレスポンス送信時（ステータスコード）。

構造化ロギング（例: JSON 形式）を引き続き採用し、ログ管理システムでの検索・分析を容易にします。8.C. モニタリング API のパフォーマンスと信頼性を維持するため、以下のメトリクスを監視します。
USDA API:

USDAService からの API 呼び出しの平均レイテンシおよびパーセンタイルレイテンシ。
USDA API からのエラーレート（特に 429 Too Many Requests、5xx 系エラー）。
X-RateLimit-Remaining ヘッダーの値を監視し、レートリミット枯渇を事前に警告するアラートを設定。

Gemini（フェーズ 2）:

analyze_image_with_usda_context メソッドの呼び出しレイテンシ。
Gemini からのエラーレート。

/refine エンドポイント全体:

リクエストレート。
平均およびパーセンタイルレイテンシ。
エラーレート（4xx, 5xx）。

キャッシュ:

キャッシュヒット率。

これらのメトリクスを Google Cloud Monitoring などの監視ツールで収集・可視化し、パフォーマンスのボトルネックや信頼性の問題を早期に特定できるようにします。8.D. USDA API キーのローテーション/セキュリティ USDA_API_KEY は重要な認証情報であり、その管理には細心の注意が必要です。
安全な保管: 環境変数として供給し、バージョン管理システムには含めません。デプロイメントプラットフォームのシークレット管理機能（例: Google Secret Manager, HashiCorp Vault）の利用を検討します。
ローテーション: 定期的なキーのローテーション手順を確立し、キーが漏洩した場合や組織のポリシー変更があった場合に迅速に対応できるようにします。
アクセス制御: API キーへのアクセス権限を最小限に抑えます。
これらの運用上の考慮事項を適切に実施することで、フェーズ 2API の安定稼働とセキュリティを確保します。特に外部 API への依存が増えるため、その可用性やパフォーマンス変動に対する耐性（タイムアウト設定、リトライ戦略、サーキットブレーカーパターンの検討など）も重要になります。9. まとめと結論本レポートでは、食事管理アプリの栄養価計算精度を向上させるためのフェーズ 2API の開発方針について、USDA FoodData Central データベースとの連携と、Google Gemini AI の再活用を中心に詳述しました。9.A. フェーズ 2API 設計の概要提案されたフェーズ 2API は、フェーズ 1 で AI が初期推定した食事内容（料理・食材名、量）を入力として受け取ります。次に、これらの食材名をクエリとして USDA FoodData Central API を検索し、関連性の高い食品候補（FDC ID、公式名称、主要栄養素情報を含む）を取得します。これらの USDA 候補情報と元の食事画像、初期 AI 分析結果を統合し、再度 Gemini AI に入力することで、より文脈に即し、かつ標準データベースに紐づけられた精緻な食事分析結果を生成します。この結果には、各食材に対応する FDC ID が含まれ、信頼性の高い栄養価計算の基礎となります。API は FastAPI で構築され、OpenAPI 仕様に準拠し、フェーズ 1 の設計思想を継承・拡張します。9.B. 精緻化分析アプローチの利点この二段階の分析アプローチは、以下の主要な利点をもたらします。
栄養価情報の精度と信頼性向上: AI の自由な推定だけでなく、USDA という標準化された大規模栄養データベースを参照することで、栄養価計算の根拠が明確になり、精度と信頼性が大幅に向上します。
食品の曖昧性への対応改善: 「鶏肉」のような一般的な食材名に対しても、USDA データベースから具体的な種類（例: 「鶏むね肉、皮なし、生」）の候補を提示し、AI が画像コンテキストと照合して選択することで、より適切な食品特定が可能になります。
データベースへの正規化: 食材情報が FDC ID に紐づけられることで、データの標準化が図られ、後続の栄養計算処理の一貫性と再現性が保証されます。
ユーザーへの信頼感醸成: 栄養情報が信頼できるソースに基づいていることを示すことで、アプリケーション全体の信頼性とユーザー満足度の向上に繋がります。
9.C. 潜在的な課題と将来の考慮事項本アプローチにはいくつかの潜在的な課題と、将来的に検討すべき事項が存在します。
USDA API レートリミット管理: アプリケーションの利用規模が拡大した場合、USDA API のレートリミット（1 時間あたり 1,000 リクエスト/IP） 5 がボトルネックとなる可能性があります。効果的なキャッシュ戦略、リクエストの集約、必要に応じたレートリミット緩和申請などの対策が求められます。
プロンプトエンジニアリングの複雑性: フェーズ 2 の Gemini へのプロンプトは、画像、初期分析結果、多数の USDA 候補情報を含むため、複雑になります。AI がこれらの情報を最適に解釈し、意図通りの判断を下すためには、継続的なプロンプトの調整と評価が不可欠です。
処理レイテンシ: USDA API 呼び出しと二段階目の AI 処理が追加されるため、全体のレスポンスタイムが増加する可能性があります。パフォーマンスモニタリングと、必要に応じたキャッシュ戦略の強化や処理の非同期化（例: 結果を後で通知する）などの最適化が検討課題となります。
USDA 候補のマッチング: 初期 AI 分析結果の食材名に対して、USDA データベース内に適切な候補が見つからない、あるいは多数の候補が存在して選択が困難なケースへの対応が必要です。AI が「該当なし」と判断できるような指示や、ユーザーによる候補選択インターフェースの導入も将来的には考えられます。
key_nutrients_per_100g の拡充: 現在想定している主要栄養素リストは限定的です。アプリケーションのニーズに応じて、このリストを拡張したり、ユーザーが関心のある栄養素を選択できるようにしたりする機能が求められる可能性があります。
9.D. 今後の開発ステップ本方針に基づき、以下のステップで開発を進めることを推奨します。
USDAService の実装とテスト: USDA API との通信、データパース、エラーハンドリング、キャッシュ機能を備えた usda_service.py を開発し、単体テストを徹底します。
GeminiMealAnalyzer の更新: フェーズ 2 用の analyze_image_with_usda_context メソッドを gemini_service.py に追加し、プロンプト構築とレスポンス処理を実装します。
Pydantic モデルとエンドポイントロジックの開発: フェーズ 2 用の Pydantic モデル群を定義し、/v1/meal-analyses/refine エンドポイントのコアロジックを実装します。
OpenAPI 仕様の更新: openapi.yaml にフェーズ 2 のエンドポイントとスキーマ定義を記述し、ドキュメントを整備します。
統合テスト: 画像入力から USDA 連携、Gemini 再分析、最終レスポンス生成までの一連の流れを検証する統合テストを実施します。
プロンプトエンジニアリングの反復: 様々な食事画像と初期分析結果のパターンを用いて、フェーズ 2 の Gemini プロンプトを継続的に評価し、改善します。
運用準備: ロギング、モニタリング、アラート設定など、運用に必要な仕組みを整備します。
本開発方針に従うことで、技術的要件を満たし、信頼性が高く、スケーラブルで、保守しやすい API（フェーズ 2）を構築し、食事管理アプリの栄養価計算機能の大幅な品質向上に貢献できると期待されます。特に、Gemini の高度な推論能力と USDA データベースの網羅性を組み合わせることで、ユーザーにとって価値の高い、正確な栄養情報提供が実現できるでしょう。
