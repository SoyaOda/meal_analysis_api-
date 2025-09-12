Firebase プロジェクトへの FastAPI デプロイ手順

現在の「new-snap-calorie」Firebase プロジェクトに、GitHub リポジトリで提供された食事分析 API（FastAPI アプリ）をデプロイする方法を解説します。ここでは Cloud Run を利用する方法を紹介します（Cloud Run は Docker コンテナで FastAPI アプリを手軽にデプロイでき、Firebase Hosting からのリダイレクトで統合可能です）。手順を初心者向けに分かりやすく説明します。

1. 前提準備とプロジェクト設定
   • Google Cloud SDK のインストール・初期化: ご自身の PC に gcloud CLI がインストールされていない場合はインストールしてください ￼。インストール後、以下のコマンドで Google アカウントにログインし、Firebase の GCP プロジェクトを選択します（new-snap-calorie が Firebase プロジェクトに対応する Google Cloud プロジェクト ID だと仮定します）。

gcloud auth login # アカウントログイン
gcloud auth application-default login # アプリケーションデフォルト認証情報を設定
gcloud config set project new-snap-calorie # プロジェクトを Firebase プロジェクト ID に設定 [oai_citation:1‡GitHub](https://github.com/SoyaOda/meal_analysis_api-/blob/32a17976b19ff3c7cb10990ebe3c91e2525e462b/README.md#L92-L99)

    •	必要なAPIの有効化: FirebaseプロジェクトでCloud RunやVertex AIを使うため、必要なAPIを有効化します（すでにFirebaseで有効になっている場合もありますが念のため実行します）。

gcloud services enable run.googleapis.com # Cloud Run API を有効化
gcloud services enable cloudbuild.googleapis.com # Cloud Build API を有効化（コンテナビルド用）
gcloud services enable aiplatform.googleapis.com # Vertex AI API を有効化 [oai_citation:2‡GitHub](https://github.com/SoyaOda/meal_analysis_api-/blob/32a17976b19ff3c7cb10990ebe3c91e2525e462b/README.md#L107-L114)

    •	アプリケーションコードの取得: GitHubリポジトリ SoyaOda/meal_analysis_api- のコードをローカルに用意します（Git cloneするか、ZIPをダウンロードして展開してください）。以降はそのディレクトリ内で作業します。

2. 環境変数とコードの調整

GitHub の README によれば、この API はいくつかの環境変数を必要とします ￼。Cloud Run では環境変数はデプロイ時に設定できますので、.env ファイルは使わず Cloud Run の設定に直接登録します。必要な主な環境変数は以下です：
• USDA_API_KEY : USDA フードデータ API のキー（栄養データ取得用） ￼
• Vertex AI 関連（Google Gemini モデル使用） ￼:
• GEMINI_PROJECT_ID : GCP プロジェクト ID（例: new-snap-calorie）
• GEMINI_LOCATION : Vertex AI のリージョン（例: us-central1）
• GEMINI_MODEL_NAME : 利用するモデル名（例: gemini-2.5-flash-preview-05-20）

💡 メモ: GOOGLE_APPLICATION_CREDENTIALS という環境変数も README に記載されています ￼ が、Cloud Run 上ではサービスアカウントを使った自動認証（アプリケーションデフォルト認証）が利用可能です。今回はサービスアカウントに必要権限（Vertex AI のユーザ権限など）を付与することで、この変数を設定せずに安全に認証させる方法がおすすめです。もしどうしてもサービスアカウント JSON キーを直接指定する場合は、Secret Manager にキーを登録して Cloud Run にマウントする方法がありますが、初心者には難易度が高いためここでは割愛します。

    •	Elasticsearchの接続: このAPIはElasticsearchデータベースに接続し、栄養データ検索を行う機能を持ちます ￼。Firebase/Cloud Run環境にはElasticsearchを直接デプロイできないため、外部にElasticsearchサーバを用意する必要があります（例: GCPのVMでElasticsearchを立てるか、Elastic社のマネージドサービスを利用）。用意できたら、そのホストURLとポート（例: http://<Elasticのホスト>:9200）を環境変数としてCloud Runに設定し、コードで参照できるようにしましょう。リポジトリのコードではデフォルトでlocalhost:9200に接続する実装になっている可能性が高いです。その場合、デプロイ前にコードを1箇所修正しておきます：Elasticsearchクライアントを生成する箇所で、ハードコードされた"localhost:9200"を、環境変数からホストを読むように変更します（例えばELASTIC_HOSTという環境変数を作り、os.environ.get("ELASTIC_HOST", "http://localhost:9200")のように記述）。この修正により、本番環境では外部Elasticsearchを利用し、ローカル実行時は従来通りlocalhostを使う形にできます。
    •	FastAPIアプリの起動方法: コード構造を見ると、FastAPIアプリはapp_v2/main/app.pyに定義されています ￼。起動コマンドはREADMEにある通り python -m app_v2.main.app を使います ￼。これはモジュール形式で実行するためで、相対インポートエラーを回避するための注意点です ￼。Cloud Run用のコンテナでも、この形式で起動することを守る必要があります。

3. Docker コンテナの作成

Cloud Run にデプロイするには、アプリケーションをコンテナ化する必要があります。ここでは Dockerfile を作成し、FastAPI アプリ用のコンテナイメージをビルドします。

プロジェクトのルートディレクトリ（meal_analysis_api_2 ディレクトリがある場所）に、新規ファイル Dockerfile を作成し、以下の内容を記述してください：

# ベースイメージとして軽量な Python ランタイムを使用

FROM python:3.9-slim

# 作業ディレクトリを設定

WORKDIR /app

# Python の依存関係をコピーしてインストール

COPY requirements.txt .
RUN pip install -r requirements.txt

# アプリケーションコードをコピー

COPY . .

# 環境変数で UVicorn のポートを受け取る設定（Cloud Run は PORT 環境変数を使用）

ENV PORT=8000

# コンテナ起動時に FastAPI(Uvicorn)を起動

# "-m app_v2.main.app" を指定してモジュールとして実行 [oai_citation:11‡GitHub](https://github.com/SoyaOda/meal_analysis_api-/blob/32a17976b19ff3c7cb10990ebe3c91e2525e462b/README.md#L133-L138)

CMD ["python", "-m", "app_v2.main.app"]

解説:
• python:3.9-slim は軽量な Python 3.9 イメージです。リポジトリ README で「Python 3.9+」とあるので 3.9 で問題ありません。
• requirements.txt から依存パッケージをインストールします ￼。
• コード一式をコンテナにコピーし、最後に FastAPI アプリを実行する CMD を定義しています。ここでは README に従いモジュール起動しています ￼。なお、FastAPI は Uvicorn サーバで起動されますが、Cloud Run では環境変数 PORT でポート番号が指定されるため、Uvicorn がデフォルトで使う 8000 番を ENV で指定しました（Cloud Run 実行時には自動的に PORT 環境変数が例えば 8080 に設定されますが、今回の構成では app.py 内で明示していない限り Uvicorn は 8000 番を使います。このため、Cloud Run 側でポートを 8000 にマッピングする形となります）。
• Uvicorn のホスト設定: （もし app_v2/main/app.py 内で Uvicorn を起動するコードがあれば、host='0.0.0.0'になっていることを確認してください。Cloud Run 上ではコンテナ内の全てのネットワークインターフェイスでリクエストを受け付ける必要があるためです。多くの場合、Uvicorn のデフォルトが 127.0.0.1 なので、0.0.0.0 に変更が必要ですが、FastAPI の場合は uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000))) のように起動するのが一般的です。今回 README の起動方法では-m で実行しているので、app.py 内で適切に設定されていると推測しますが、念のため確認してください。）

4. コンテナイメージのビルドと Cloud Run デプロイ

Dockerfile の準備ができたら、Cloud Run にデプロイするためコンテナイメージをビルドし、リポジトリ（コンテナレジストリ）にプッシュします。ここでは Google 提供の Cloud Build サービスを使い、ローカルで Docker を使わず直接ビルド＆デプロイする手順をとります。

ターミナルでプロジェクトのルートディレクトリに移動し、次のコマンドを実行してください：

# 1. Cloud Build でコンテナイメージをビルドして Artifact Registry にアップロード

gcloud builds submit --tag gcr.io/new-snap-calorie/meal-analysis-api:latest .

# 2. Cloud Run にデプロイ（--image には上でビルドしたイメージを指定）

gcloud run deploy meal-analysis-api \
 --image gcr.io/new-snap-calorie/meal-analysis-api:latest \
 --platform managed --region us-central1 \
 --allow-unauthenticated \
 --update-env-vars USDA_API_KEY=あなたの USDA_API キー,GEMINI_PROJECT_ID=new-snap-calorie,GEMINI_LOCATION=us-central1,GEMINI_MODEL_NAME=gemini-2.5-flash-preview-05-20,ELASTIC_HOST=<Elasticsearch の URL>

上記では、イメージ名に gcr.io/プロジェクト ID/...を用いています。new-snap-calorie がプロジェクト ID であることを確認してください。

コマンド解説:
• gcloud builds submit は現在ディレクトリの Dockerfile を使ってビルドし、--tag で指定したレジストリ（ここでは Google Container Registry の gcr.io）にプッシュします。
• gcloud run deploy は Cloud Run サービスを作成/更新するコマンドです。meal-analysis-api はサービス名で任意に決められます。--region us-central1 はリージョンを指定しています（Firebase Hosting からのデフォルトも us-central1 なのでここでは揃えています ￼）。--allow-unauthenticated は認証無しアクセス（公開 URL アクセス）を許可するオプションです。API を Firebase 経由で呼び出す場合、外部からのアクセスを許可するためこれをオンにしています。
• --update-env-vars で環境変数を同時に設定しています。上で準備した USDA や GEMINI 関連、そして Elastic のホスト URL をカンマ区切りで指定してください（値内の=や,は含めないよう注意）。例えば、USDA_API_KEY の値に特殊文字が含まれる場合はシェルエスケープも検討してください。

デプロイコマンドが成功すると、Cloud Run サービスの URL が表示されます ￼。例えば:

https://meal-analysis-api-<ランダム ID>-us-central1.a.run.app

この URL が API エンドポイントのベース URL となります。ブラウザで<その URL>/docs にアクセスすると、FastAPI のインタラクティブなドキュメント（Swagger UI）が表示されるはずです ￼。また<その URL>/health でヘルスチェックエンドポイントにアクセスして、稼働確認もできます ￼。

⏱ 参考: 初回デプロイ後、Cloud Run の管理画面（Firebase コンソールの「ビルド」→「Cloud Run」から該当サービスを選択）で、設定の確認や変更が可能です。環境変数を追加・変更したい場合や、メモリ/CPU などリソース設定を調整したい場合は、コンソール画面から編集して再デプロイできます。

5. Firebase Hosting から Cloud Run へのリダイレクト設定（オプション）

上記の手順で Cloud Run 上に API はデプロイされました。このままでも Cloud Run の URL で API を利用できますが、Firebase Hosting のドメイン（例: new-snap-calorie.web.app）から API を呼び出したい場合は、Hosting のリライトルールを設定すると便利です。Firebase Hosting のリライト機能を使うと、指定したパスへのリクエストを Cloud Run のサービスに転送できます ￼ ￼。

例えば、Firebase Hosting 配下の /api/\*\* パスをすべて先ほどデプロイした Cloud Run サービスに転送するには、プロジェクトの firebase.json に以下のような設定を追加します：

{
"hosting": {
// ...（他の Hosting 設定）...
"rewrites": [
{
"source": "/api/**",
"run": {
"serviceId": "meal-analysis-api", // Cloud Run サービス名（デプロイ時の名前）
"region": "us-central1"
}
}
]
}
}

上記の rewrites ルールでは、/api/で始まるあらゆるリクエストを、Cloud Run の meal-analysis-api サービスにルーティングしています ￼。設定後、以下のコマンドで Firebase Hosting にデプロイします：

firebase deploy --only hosting

デプロイが成功すれば、Firebase のプロジェクト用ドメイン（new-snap-calorie.web.app など）で https://new-snap-calorie.web.app/api/v1/meal-analyses/complete のようにアクセスすることで、Cloud Run 上の FastAPI エンドポイントに到達できるようになります。 ￼

💡 メモ: Firebase Hosting 経由で Cloud Run コンテナにアクセスする場合、60 秒のタイムアウト制限があります ￼。もし画像分析 API の応答に時間がかかりすぎる場合、Hosting 経由ではタイムアウトする可能性があります。その場合は、直接 Cloud Run のエンドポイントを使うか、Cloud Run の最大インスタンス数やタイムアウト設定を調整することも検討してください（ただし Hosting 経由の 60 秒制限は変更できません）。

6. デプロイ後の動作確認

Firebase Hosting のリライト設定まで行った場合は、Firebase Hosting のドメインから API が使えるか確認しましょう。先ほどの例では /api/ 以下が転送されるため、ブラウザで https://PROJECT_ID.web.app/api/docs にアクセスすると Swagger UI が表示されるはずです。あるいは、以下のように curl コマンドでエンドポイントを叩いてみます：

# 料理画像を使った完全分析 API エンドポイントにリクエスト

curl -X POST "https://new-snap-calorie.web.app/api/v1/meal-analyses/complete" \
 -H "Content-Type: multipart/form-data" \
 -F "image=@test_images/food3.jpg"

上記は README で紹介されている完全分析エンドポイントへのリクエスト例（ローカルホスト向け）を Firebase ドメイン経由に書き換えたものです ￼ ￼。適切なレスポンス（JSON データ）が返ってくれば、デプロイは成功です 🎉。

また、Elasticsearch 連携部分が正しく動作しているかも確認しましょう。環境変数 ELASTIC_HOST で指定した先の Elasticsearch が稼働中で、API からアクセスできていれば、栄養検索機能も動作するはずです（例えば test_local_nutrition_search_v2.py でテストしていた機能） ￼ ￼。

7. 付録: そのほかのポイント
   • 永続データについて: この API は分析結果を自動で JSON/Markdown ファイルに保存する機能があります ￼。ただし Cloud Run コンテナのファイルシステムは一時的であり、コンテナ停止で消えてしまいます。重要なデータはクラウドストレージやデータベースに保存するよう変更する必要があります。今回のデプロイではファイル保存は長期保持されない点に注意してください。
   • Cloud Functions を使う場合: （参考情報）Firebase プロジェクトでは、Python 製バックエンドを Cloud Functions（第 2 世代）としてデプロイすることも可能ですが、FastAPI アプリ全体を Functions として動かすにはカスタムランタイムの設定が必要で難易度が高いです。Cloud Run を使う方法は、Docker コンテナに包んでそのまま動作させられるため比較的簡単で、今回はこちらを採用しました。

以上、GitHub の README 情報を踏まえて Firebase へのデプロイ手順を説明しました。これらの手順に沿って進めれば、Firebase プロジェクト「new-snap-calorie」で FastAPI ベースの食事分析 API を利用できるようになるでしょう。頑張ってください！🚀

引用情報: GitHub リポジトリ README【11】および Firebase 公式ドキュメント【21】より、設定手順やコード例を参照しました。

Sources:
• GitHub: SoyaOda/meal_analysis_api- README ￼ ￼
• Firebase 公式: Cloud Run と Firebase Hosting の統合ガイド ￼ ￼
