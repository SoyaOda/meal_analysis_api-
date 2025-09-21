音声入力対応の実装戦略 (Meal Analysis API 拡張計画)
背景・目的

既存の Meal Analysis API は FastAPI ベースで動作し、画像から料理・食材を認識し、栄養データベース（Word Query API）と連携して栄養価を計算するシステムです
GitHub
GitHub
。この既存構造を踏襲しつつ、Flutter アプリから送信される音声データを入力として受け取り、Google Cloud Speech-to-Text v2 で文字起こしし、得られたテキストから料理名・食材名およびその量を抽出して、既存の Word Query API（栄養データベース）に照会する機能を追加実装します。これにより、ユーザーが食事内容を音声で記録するだけで、自動的に栄養分析を行えるようになり、UX が向上します。

本計画では、音声入力処理のための新規 API エンドポイントの設計、音声処理モジュールの追加、NLU（自然言語理解）による食品名・量の抽出、DeepInfra 経由の LLM（大規模言語モデル）活用による解析、既存の Word Query API 連携、および段階的テスト戦略について詳細に示します。特に、現状の実装を踏まえて最小限の変更で拡張する方針とし、米国ユーザー（英語話者）を想定した設定で計画を策定します。
全体アーキテクチャ方針

音声入力機能は、既存の画像分析パイプラインと並列する新たなパイプラインとして設計します。ただし可能な限り既存コンポーネントを再利用し、一貫した結果フォーマット・栄養計算ロジックを共有します。具体的には、以下のフローで処理を行います。

    音声ファイル受信 (Flutterクライアント -> API): Flutterアプリからアップロードされた音声データをFastAPIで受け取ります。

    音声認識 (Google Cloud Speech-to-Text v2): 受信音声をGoogle CloudのSpeech-to-Text APIに送り、音声から英語テキストに変換します。

    NLU処理 (DeepInfra LLM): 認識テキスト（英語）をDeepInfraの生成系AIモデル（LLM）に入力し、料理名・食材名・推定量を抽出します。LLMには現行デフォルトのgemma-3-27b-itモデルを用いますが、APIパラメータでモデルを選択できる柔軟性を持たせます（他のモデルも試用可能な設計）。

    栄養データベース検索 (Word Query API): LLMが抽出した各食材名とその量を、既存のWord Query APIに照会します。これにより各食材の100gあたり栄養情報を取得し、指定量に応じたカロリー等を算出します（この処理は既存実装のPhase2以降のコンポーネントをそのまま利用します）。

    栄養価計算と結果生成: 取得した栄養データをもとに、各料理や全体の栄養価を計算します（これも既存のNutritionCalculationComponentを再利用）。最終的に画像分析時と同じレスポンスJSON構造で結果をクライアントに返します
    GitHub
    GitHub
    。例えば、料理名、推定量（例:"1人前（約300g）"）、食材リスト（各食材名と重量）、各料理の総カロリー、全体の合計栄養価などを含むJSON形式です。

この新規音声パイプラインをコンポーネント指向で実装し、例えば「Phase1SpeechComponent」を新設して音声 → テキスト → 食品抽出までを担当させ、以降は既存の AdvancedNutritionSearchComponent や NutritionCalculationComponent に処理を委ねる構成とします。これにより、画像入力と音声入力で前段の処理は異なりますが、後段の栄養情報検索・計算ロジックは共通化できます。
音声データアップロード方式の設計

Flutter クライアントからサーバーへの音声データ送信は、multipart/form-data を用いたバイナリファイルアップロード形式を採用します。これは既存の画像アップロードと同様の方式であり、サーバー側での受け取り・パースが容易で、モバイルからの実装もシンプルだからです。具体的には、Flutter の http クライアント等で Content-Type: multipart/form-data の POST リクエストを構築し、音声ファイル（例: audio.wav あるいは audio.m4a など）をファイルフィールドとして添付します。既存 API が-F "image=@food.jpg"のように画像を受け取っているのと同様に、音声では例えば -F "audio=@voice.m4a" のようなリクエストになります。

音声ファイル形式については、ユーザーの UX および公式推奨を踏まえ、できるだけロスレスな形式を用いる方針です。Google Cloud Speech-to-Text では FLAC や LINEAR16 (無圧縮 WAV)といったロスレスコーデックが推奨されており、MP3 や M4A（AAC）などの有損圧縮は認識精度を下げる可能性があるとされています
cloud.google.com
。そのため、理想的には Flutter 側で録音を WAV (PCM 16bit)等で行い、そのままアップロードすることが望ましいです。WAV の場合ファイルサイズは増えますが、音声データ圧縮による劣化がなく高精度な認識が期待できます
cloud.google.com
cloud.google.com
。もしモバイル側の制約で AAC(M4A)等になる場合でも、サーバー側で受け取った後に必要なら FFmpeg や pydub 等で LINEAR16 に変換し、Google API に送る対応も検討します（もっとも短い音声であればそのままでも大きな問題は起こりにくい想定です）。ユーザー体験上は、録音ボタンを押して話す → ボタンを離すと自動アップロード、というフローを想定しており、ファイル形式の違いは裏側で処理されます。

まとめると、multipart/form-data + バイナリ音声アップロードにより、余計なエンコード処理（例: Base64 エンコードによるテキスト化とサイズ増大）を避け、シンプルかつ効率的に音声データを送信します。この方式は Flutter の実装例も多く、公式にも推奨される一般的な手法です。
Google Cloud Speech-to-Text v2 の音声認識実装

Google Cloud Speech-to-Text API v2 を用いて、アップロードされた音声ファイルをテキストに変換します。サーバー側では Google の Python クライアントライブラリ（google-cloud-speech）を使用し、非同期ではなく同期認識 API を呼び出します（想定する音声入力が比較的短いフレーズ～数十秒程度であり、リアルタイム性を重視するため）。認識対象言語は**英語（米国）**を想定し、language_code="en-US"を指定します。認識結果も英語の文章で出力されます。

実装方針: 新規に speech_service.py（仮称）モジュールを作成し、以下のような関数を実装します。

import os
from google.cloud import speech

# 環境変数や設定から Google 認証情報を読み込む（例: GOOGLE_APPLICATION_CREDENTIALS）

client = speech.SpeechClient() # Google Speech-to-Text クライアントの初期化

def transcribe_audio(data: bytes, sample_rate: int = 16000) -> str:
"""音声バイナリデータをテキストに変換する"""
audio = speech.RecognitionAudio(content=data)
config = speech.RecognitionConfig(
encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
sample_rate_hertz=sample_rate,
language_code="en-US",
enable_automatic_punctuation=True # 句読点も自動付与
)
response = client.recognize(config=config, audio=audio) # 結果からテキストを抽出（複数文ある可能性もあるがシンプルに連結）
transcript = ""
for result in response.results:
transcript += result.alternatives[0].transcript
return transcript.strip()

上記では、RecognitionConfig でエンコーディングやサンプリングレート、言語コードを指定しています。Flutter 側で 16kHz PCM(WAV)を送る場合は sample_rate_hertz=16000 で設定し、仮に別形式なら適宜合わせます。enable_automatic_punctuation=True を有効にしており、これにより STT が出力するテキストに句点やコンマを自動付与します。これらの句読点は後段の LLM が文を理解する助けになります（例えば「I ate two eggs, a slice of toast and a glass of orange juice.」のように区切りが明確になる）。

UX 観点では、音声認識はサーバー到達後に行うためネットワーク遅延+認識処理時間がかかります。Google STT は数秒程度の短い音声であれば 1 秒前後で結果が返ることが多いですが、長い発話では処理時間が線形に伸びます。本システムでは Cloud Run 上で並行度 1（シングルスレッド）の設定
GitHub
で動作しているため、一度に一リクエストを順次処理します。この制約下でも音声認識自体は Google 側で非同期に行われるため、サーバー負荷は軽微ですが、長時間の音声は扱わない運用（おおむね 1 分以内）とすることで応答時間とコストのバランスを取ります。

エラーハンドリングとして、音声ファイルが空だった場合や認識結果が得られなかった場合には適切なエラーレスポンスを返します。例えば、Google STT が音声内に明瞭な発話を検出できなかったときは、API レスポンスとして 400 Bad Request と共に"error": {"code": "NO_SPEECH", "message": "音声から有効なテキストを取得できませんでした"}のようなメッセージを返す設計とします（既存エラーレスポンス形式に倣い、コードとメッセージを含む JSON）。
LLM（DeepInfra）による食品名・量の抽出処理

音声認識で得られた英語テキストから、食事内容（料理名・食材名）とその量を抽出するために、DeepInfra が提供する生成 AI（LLM）を活用します。具体的には、認識テキストを入力として、大規模言語モデルに自然言語理解 (NLU) のタスクを実行させます。ユーザが自由な言葉で述べた食事内容から、構造化された情報（料理や食材のリストと数量）を引き出す役割です。
モデル選定と柔軟性

現行システムでは DeepInfra 上に Gemma 3-27B という Vision 対応のモデルを利用しています
GitHub
。このモデルは画像から料理・食材・重量を推定する指示調整済みモデルとして機能していますが、テキスト入力のみの NLU にも応用可能と考えられます。デフォルトでは**google/gemma-3-27b-it を引き続き使用しつつ、API 入力でモデルを選択可能な仕組みを導入します。例えば、リクエストパラメータに llm_model_id（あるいは既存の model_id を拡張）を追加し、値として DeepInfra 上の別モデル ID を指定できるようにします。これにより、将来的に別の生成モデル**（例えばテキスト専用の LLM や、Gemma の上位モデル、GPT 系モデル等）が試せる余地を確保します。モデル ID のデフォルトは Gemma 3-27B とし、指定がなければこれを使用します（環境変数 DEEPINFRA_MODEL_ID で既定値を管理
GitHub
）。
プロンプト設計と出力形式

LLM への入力（プロンプト）として、音声認識テキストをそのまま渡します（特別な前処理は行いません）。ユーザー発話は既に英語テキストになっており、冗長な修正は不要です。前処理を敢えて行わないことで、元の文脈やニュアンスを損なわずモデルに渡せます（ユーザーから確認済みの方針）。ただし、プロンプト内ではシステムメッセージや指示を加えて、モデルが望むフォーマットで出力するよう誘導します。

具体的には、「料理名・食材・量」の構造化出力を得るために、以下のような指示を与えます。

    出力フォーマット: 既存APIのレスポンスと統一するため、JSON形式での出力を指示します。例えば、dishesというトップレベルキーの下に、料理の配列を格納し、各料理にdish_name, quantity_on_plate, ingredientsのフィールドを持たせます
    GitHub
    GitHub
    。各ingredientはingredient_nameとweight_gを含むようにします
    GitHub
    GitHub
    。モデルにはこのJSONスキーマに従って回答させるよう促します。

    料理と食材の抽出: ユーザーの発話が一品以上の料理を含む場合、それぞれを別の料理エントリとしてリストします。例えば「I had toast and coffee for breakfast.」という発話なら、「Toast」と「Coffee」を別々のdishオブジェクトとして出力します。それぞれにingredients配列がありますが、シンプルな食品（単一素材）であればingredientsに一つの要素（例えばToastならパン1枚、Coffeeならコーヒー液）を入れる形になります。

    分量・重量の推定: ユーザーが量を明言している場合（例: "two eggs", "a glass of orange juice"）、その情報をモデル出力に反映させます。例えばquantity_on_plateフィールドに「2個」や「1グラス（約240ml）」等の記述、weight_gにはモデルが知識や常識に基づきグラム換算した推定重量を出力します（Gemma 3-27Bは画像からも重量を推定していたため、テキストからもある程度推定できる想定）。ユーザーが量を言及していない場合は、モデルに典型的なポーションを推測させます。例えば「I ate Caesar salad.」だけなら、一人前のシーザーサラダの典型的重量を100-200g程度と見積もり、主要食材（レタス、クルトン、ドレッシング等）に適切な配分で重量を割り振ることが期待されます。

    食材展開: ユーザーが料理名だけ述べた場合でも、可能なら典型的な材料を列挙させます。これも画像分析時と同様に、LLMの持つ知識を活用します。例えば「I had a Caesar Salad.」に対し、シーザーサラダの材料（ロメインレタス、クルトン、チーズ、ドレッシング等）をモデルが補完し、それぞれに重量を割り当てて出力します。これによって、画像入力時と遜色ない詳細な分析結果を得られます。

上記を実現するためのプロンプト例:

System: あなたは食事の内容を理解し栄養分析のための情報を抽出するアシスタントです。ユーザーの発話から料理名、料理の量、含まれる食材と各食材のおおよその重量(g)を特定し、JSON 形式で出力してください。

User: "I had two eggs and a slice of toast with butter for breakfast."

Assistant:
{
"dishes": [
{
"dish_name": "Scrambled Eggs",
"quantity_on_plate": "2 個 (2 eggs)",
"ingredients": [
{ "ingredient_name": "egg", "weight_g": 100.0 }
]
},
{
"dish_name": "Butter Toast",
"quantity_on_plate": "1 枚 (1 slice)",
"ingredients": [
{ "ingredient_name": "bread", "weight_g": 30.0 },
{ "ingredient_name": "butter", "weight_g": 5.0 }
]
}
]
}

（※上記は形式説明のための擬似例です）

このように、LLM にはシステムメッセージで役割と出力フォーマットを厳密に指示し、ユーザーテキストを与えて回答させます。DeepInfra の API 経由でモデルを呼び出す際、プロンプトを組み立てて HTTP リクエストします。例えば Python で実装する場合、新規 llm_service.py モジュールに以下のような関数を用意します。

import os
import requests

DEEPINFRA_API_KEY = os.getenv("DEEPINFRA_API_KEY")
DEFAULT_MODEL_ID = os.getenv("DEEPINFRA_LLM_MODEL_ID", "google/gemma-3-27b-it")

def extract_foods_from_text(text: str, model_id: str = None) -> dict:
"""テキストから料理・食材・量を抽出して JSON 構造を返す"""
model = model_id or DEFAULT_MODEL_ID # DeepInfra 推論 API のエンドポイント URL（モデル ID を URL パスに含める想定）
url = f"https://api.deepinfra.com/v1/inference/{model}"
headers = {"Authorization": f"Bearer {DEEPINFRA_API_KEY}"} # プロンプト構築
system_prompt = "You are an AI assistant for nutrition analysis..." # (← 上記日本語指示を英語で記述)
user_prompt = text
payload = {
"prompt": f"{system_prompt}\nUser: {user_prompt}\nAssistant:",
"max_tokens": 512,
"temperature": 0.0 # 決定論的出力
}
response = requests.post(url, json=payload, headers=headers)
response.raise_for_status()
result_text = response.json().get("result") # モデルの生テキスト出力 # JSON パース（フォーマット不整合時の例外処理も必要）
try:
result_json = json.loads(result_text)
except Exception as e: # 必要に応じて整形や再試行
raise RuntimeError(f"LLM 出力の JSON 変換に失敗: {e}")
return result_json

上記では DeepInfra の REST API を想定し、model_id で指定したモデルを使って推論を行っています。prompt にはシステムメッセージ＋ユーザー発話＋アシスタントの出力枠を与え、temperature=0.0 で出力のブレを無くす設定にしています（栄養分析は決定性が求められるため
GitHub
、ランダム性は不要）。モデルの応答を JSON としてパースし返しています。実運用では、モデル出力が厳密な JSON でない可能性もあるため、例えば終了ブラケットの欠落など軽微な不整合は補正する処理を入れるか、もしくは再度プロンプトでフォーマット遵守を促すなどの工夫も検討します。基本的には、Gemma 3-27B など指示対応モデルで temperature0 ならかなり厳密に指示通りの JSON を返すと期待しています。

他モデル活用: model_id 引数で例えば小規模なモデルに切り替えれば、応答速度を上げることもできます（Gemma3-27B は応答に~15 秒程度かかるケースもあるため
GitHub
GitHub
、シンプルな食事文の解析ならより小さい LLM でも十分可能性があります）。実際にどのモデルが適切かは試行が必要ですが、本設計ではその柔軟性を持たせる拡張性を確保します。
新規 API エンドポイント設計

音声入力を処理するための FastAPI エンドポイントを新規追加します。エンドポイントの定義は以下の通りです。

    パス: POST /api/v1/meal-analyses/voice （既存の/meal-analyses/completeに倣い、機能別にvoiceエンドポイントを用意）

    機能: 音声データを入力として受け取り、完全な食事分析（料理特定＋栄養計算）結果を返す。

    リクエスト形式: multipart/form-data

        フィールド:

            audio: 音声ファイル（必須）。サポート形式: WAV (推奨), M4A等（対応可能にする）。最大サイズは画像同様~10MB程度を想定しバリデーション。

            （オプション）llm_model_id: 使用するLLMモデルのID文字列（例: "google/gemma-3-27b-it"）。指定なき場合はデフォルトモデルを使用。

            （オプション）test_execution: ブール値。テストモードフラグ。既存実装同様、Trueの場合は外部API呼び出しのモックや短絡処理を行う等、テスト用の動作に切り替える。デフォルトFalse。

            その他、画像エンドポイントで存在したsave_detailed_logs等は、音声でも必要なら追加可能ですが、ひとまずコア機能に関係ないため省略可。

    レスポンス形式: HTTP 200 + JSONボディ。構造はMealAnalysisResponseスキーマと同様
    GitHub
    で、トップレベルにdishes: [...]のリストを含みます。各dish要素はdish_name, quantity_on_plate, ingredients（その中にingredient_name, weight_g）などを持ちます
    GitHub
    GitHub
    。さらに必要に応じ、各料理ごとのtotal_caloriesや全体合計栄養total_nutritionを含める場合は、画像エンドポイントに倣って計算します
    GitHub
    GitHub
    。

    エラーレスポンス: 不正リクエストや処理失敗時には、HTTP 400/500系コードとともに、{"error": { "code": "...", "message": "..." }}形式のJSONを返します
    GitHub
    GitHub
    。例えば音声未添付の場合は400 + INVALID_AUDIO_FILEコード、サポート外フォーマットの場合はUNSUPPORTED_AUDIO_FORMATコード、内部処理中の例外は500 + INTERNAL_ERROR等、既存に倣い定義します。

エンドポイント実装（擬似コード）: FastAPI のメインアプリケーション（例:app_v2/main/app.py）にルーターを追加します。

from fastapi import APIRouter, File, UploadFile, HTTPException
from app_v2.services import speech_service, llm_service, nutrition_service

router = APIRouter()

@router.post("/api/v1/meal-analyses/voice", summary="音声からの食事分析")
async def analyze_meal_from_voice(
audio: UploadFile = File(...),
llm_model_id: str = None,
test_execution: bool = False
): # 1. 入力音声の検証
filename = audio.filename or "audio"
content = await audio.read()
if not content:
raise HTTPException(status_code=400, detail={
"code": "EMPTY_FILE", "message": "音声ファイルが空です。"
}) # 簡易フォーマットチェック（拡張子や MIME タイプ）
if not filename.lower().endswith((".wav", ".m4a", ".flac", ".mp3", ".ogg")): # 拡張子ベースで判定、詳細にはファイルヘッダで判定可能
raise HTTPException(status_code=400, detail={
"code": "UNSUPPORTED_AUDIO_FORMAT",
"message": "サポートされていない音声形式です。wav や flac をご利用ください。"
})
try: # 2. Google STT で音声 → テキスト
transcript = speech_service.transcribe_audio(content)
except Exception as e: # STT 失敗時
raise HTTPException(status_code=500, detail={
"code": "SPEECH_TO_TEXT_FAILED",
"message": f"音声認識に失敗しました: {str(e)}"
})
if not transcript:
raise HTTPException(status_code=400, detail={
"code": "NO_SPEECH",
"message": "音声から有効なテキストを取得できませんでした。"
}) # 3. LLM でテキスト解析（食品名・量の抽出）
try:
analysis_result = llm_service.extract_foods_from_text(transcript, model_id=llm_model_id)
except Exception as e:
raise HTTPException(status_code=500, detail={
"code": "LLM_EXTRACTION_FAILED",
"message": f"食品情報の抽出に失敗しました: {str(e)}"
}) # 4. 栄養データ検索・計算（既存サービス再利用）
try:
nutrition_result = nutrition_service.query_and_calculate(analysis_result)
except Exception as e:
raise HTTPException(status_code=500, detail={
"code": "NUTRITION_CALCULATION_FAILED",
"message": f"栄養計算処理に失敗しました: {str(e)}"
}) # 5. 結果 JSON を構築して返す
return nutrition_result

上記の擬似コードフローにより、音声ファイルを受け取ってから結果を返すまでの一連の処理が行われます。nutrition_service.query_and_calculate は既存の栄養検索コンポーネントに対応する処理で、LLM が抽出した analysis_result（JSON 構造で料理・食材・重量が入っている）を受け取り、食材名ごとに Word Query API/Elasticsearch で栄養データを検索、weight_g に応じたカロリーや栄養素を計算し、analysis_result にカロリー情報や料理合計カロリー、全体合計を付加して nutrition_result として返すイメージです。既に画像用パイプラインで確立済みの処理を呼び出すだけなので、新規実装部分は最小限に留められます。

モデル ID パラメータ: 上記では関数引数 llm_model_id として取得しています。FastAPI ではクエリパラメータまたはフォームフィールドとして扱うことになります。音声ファイルと一緒に送る場合、multipart の他フィールドとして文字列を付与できます。例えば curl でテストするなら:

curl -X POST "http://localhost:8000/api/v1/meal-analyses/voice" \
 -F "audio=@test_voice.wav" \
 -F "llm_model_id=google/gptj-6b"

のように送信可能です。モデル指定がなければ None が渡り、サービス側でデフォルト ID を補完します。
既存モジュールへの組み込みと修正点

プロジェクト構成: Meal Analysis API v2 はコンポーネント化された構造を持っています
GitHub
。既存コードではおそらく app_v2/components/phase1_component.py（画像分析）、advanced_nutrition_search_component.py、nutrition_calculation_component.py 等が存在し、app_v2/main/app.py からエンドポイントがそれらを呼ぶ形になっていると推測します。今回の実装では以下の追加・修正を行います。

    新規コンポーネント: Phase1SpeechComponent（仮称）のクラスまたはサービス関数群を追加します。役割は音声認識→テキスト→食品抽出まで。内部的には前述のspeech_service.transcribe_audioとllm_service.extract_foods_from_textを呼び出し、結果のJSON（料理・食材リスト）を生成します。画像のPhase1Componentに相当。

        実装上、Phase1Component（画像）のメソッドを参考にします。例えばPhase1ComponentではDeepInfra Visionモデルに画像を送り、返ってきたテキストをJSON化していたかもしれません。Phase1SpeechComponentではGoogle STT + DeepInfra LLMという二段構えになりますが、インターフェースは揃えておくと良いでしょう（例えばrun(input) -> analysis_jsonのような共通メソッド）。

        Phase1SpeechComponentを既存Pipelineに統合する場合、Pipeline Orchestratorに「if input_type == audioならPhase1Speechを使う」など条件を入れる方法もあります。ただ、今回別エンドポイントで実装するため、各エンドポイント関数内で直接サービス関数を呼ぶ形でも問題ありません。シンプルさを優先し、まずはルーター内に直接処理を書く実装（前述の擬似コードのような）が考えられます。その後必要ならクリーンアップとして共通処理をコンポーネントクラスにまとめるでも良いでしょう。

    設定ファイルの拡張: .env.exampleにGoogle Cloud認証情報やDeepInfraテキストモデルIDの設定項目を追加します。例えば:

        GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json （GCP認証キーファイルのパス）

        DEEPINFRA_LLM_MODEL_ID=google/gemma-3-27b-it （LLMのデフォルトモデルID、初期値はGemma3）

        （DeepInfra APIキーは既にDEEPINFRA_API_KEYが利用されています
        GitHub
        ので共用）

    要件ライブラリ: requirementsにgoogle-cloud-speechを追加します。また音声処理にffmpeg等使う場合はffmpeg-pythonやpydubも検討しましたが、基本は不要なので追加しません（クライアント側で対応する前提）。

    Word Query API連携: こちらは既存コードでElasticsearch検索部分として実装済みです
    GitHub
    。音声による抽出結果も最終的には食材名のリストと重量なので、そのままAdvancedNutritionSearchComponentに渡せば動作するはずです。もし既存のAdvancedNutritionSearchComponentがPhase1Componentからの出力を想定しているなら、形式を合わせてやる必要があります。例えばPhase1Componentからの出力JSONキー名（dish_nameやingredient_nameなど）が決まっているので、それに準拠することが重要です。前述したLLM出力を整形する際、そのキー名を既存と同一にしています（ingredient_name, weight_g等
    GitHub
    ）。こうすることで、AdvancedNutritionSearchComponentが受け取ったデータを違和感なく処理できます。

        実装的には、例えばnutrition_service.query_and_calculate(analysis_result)の中で、各ingredient_nameについてElasticsearchにクエリを投げ、ヒットした食品データから100gあたりカロリー等を取得、weight_gを掛けて栄養値を算出する処理が行われるでしょう
        GitHub
        GitHub
        。音声由来でもそれは同じです。

        既存実装でoptional_text（補助テキスト情報）の仕組みがありました
        GitHub
        GitHub
        が、音声パイプラインでは基本利用しません。ただ、LLMにはユーザー発話テキストしか与えていないので、例えば「このユーザーは減塩食が必要」などコンテキストを付加したい場合、optional_text相当をLLMプロンプトに含める応用も可能です。現段階では要件にないため考慮しません。

    ログ・モニタリング: 新規処理のログを適切に出力します。音声入力エンドポイントが呼ばれた際には、ログに「音声分析開始」「音声長XX秒、STT結果: '...'」「LLMモデルID: ..., 抽出結果: ...」等をINFOレベルで記録し、デバッグ容易性を高めます。既存システムは包括的なログを特徴としているため
    GitHub
    、その流れに沿います。

    エラーメッセージ: 追加したエラーコード（INVALID_AUDIO_FORMAT, NO_SPEECH等）は、必要に応じてErrorResponseスキーマ
    GitHub
    GitHub
    やドキュメントに追記します。

    OpenAPIドキュメント更新: openapi.yamlに新エンドポイント/api/v1/meal-analyses/voiceの定義を追記し、リクエスト（multipartでaudio受け取り等）とレスポンス例を記載します。例として、audioフィールドがbinaryで必須、llm_model_idがstring任意、といった記述を追加します。またタグはMeal Analysisに属させます。これにより、/docsの自動APIドキュメントにも反映されます。

段階的テスト戦略

新機能実装後、以下の段階でテストを行い、不具合の早期発見と機能の信頼性確保を図ります。

1. ユニットテスト

各モジュール・関数単位でテストを作成します（Python の unittest または pytest を使用）。特に以下を重点的にテストします。

    音声認識モジュールテスト: speech_service.transcribe_audio関数に対し、短いテスト用音声ファイルを入力し、期待する文字列が返るか確認します。例えば、人間が「apple」一語だけ話したWAVファイルを用意し、それを読み込んで関数を呼び出し、結果が"apple"という文字列になることをアサートします。実際にGoogle STT APIを呼ぶと課金が発生するため、自動テストではモックを使用します。speech.SpeechClient().recognizeメソッドをモック化し、決まったTranscript結果を返すように設定、関数内部でそれを呼んだとき期待通りパースされるかを検証します。APIキーなど機密情報を使わずにテストできるよう、環境変数の切り替えやモンキーパッチを活用します。

    LLM抽出モジュールテスト: llm_service.extract_foods_from_text関数に対し、モックを使ったテストを行います。DeepInfraへの実際のHTTP呼び出しは避け、requests.postをモックして、予め用意したモデル出力例（JSON文字列）を返すようにします。例えば、入力テキスト"I ate two eggs."に対して、モックが

    { "result": "{\"dishes\":[{\"dish_name\":\"Eggs\",\"quantity_on_plate\":\"2個\",\"ingredients\":[{\"ingredient_name\":\"egg\",\"weight_g\":100.0}]}]}" }

    を返すようセットし、関数実行後の戻り値の辞書構造が期待通りであること（dish_nameが"Eggs"である等）を確認します。また、不正なJSONが返ってきた場合に例外を投げる処理もテストし、例外ハンドリングの網羅性を高めます。

    エンドポイントのロジックテスト: FastAPIのTestClientを用いて、新エンドポイント/api/v1/meal-analyses/voiceに対するリクエストテストを実施します。ここでも外部依存を避けるため、speech_service.transcribe_audio及びllm_service.extract_foods_from_text, nutrition_service.query_and_calculateをテスト用にモックまたはスタブに差し替えます。例えばpytestではmonkeypatch機能でこれら関数をテスト用ダミー関数に置き換え、決め打ちの結果を返させます。その上で、実際にテスト用音声ファイルデータ（バイナリ。中身はdummyでもよい）をmultipartで送り、レスポンスJSONが期待構造になっているかを検証します。期待構造はスタブが返す値に依存しますが、例えばスタブで「卵2個」の結果を返すようにしておけば、レスポンスのJSONに"dish_name": "Eggs"等が含まれることをassertします。

2. 統合テスト（ローカル環境）

ユニットテストで各コンポーネントが正しく動作することを確認した後、実際に Google STT および DeepInfra API に接続した統合テストを行います。課金や API コールの都合上、自動化というより手動に近いテストとなりますが、以下のステップで検証します。

    短文音声で通しテスト: 例えば「I ate an apple.」程度の3秒程度の音声ファイル（明瞭に収録されたもの）を用意し、ローカル実行中のAPIに対してcurlまたはFlutterクライアントからPOSTします。レスポンスが返り、JSON内に"apple"が食材として出現しカロリー情報が付与されていることを確認します。

    複数食品音声でテスト: 「I had bacon and eggs with toast and orange juice.」のように複数食品を含むやや長めの音声をテストします。期待としては、レスポンスJSON内に"Bacon and Eggs"および"Toast with Orange Juice"のように複数のdishエントリが生成され、それぞれに材料とカロリーが算出されていることを確認します。分量も、おおよそ適切な値（例えばオレンジジュース1杯=240ml→カロリー計算される等）になっているかチェックします。

    異常系テスト: 音声でないファイル（例えば.txtファイル）を送ってみて400エラーになるか、極端にノイズの多い音声や無音のファイルでNO_SPEECHエラーハンドリングが機能するか確認します。また、LLMの応答時間が極端に遅い場合（例えば非常に長文の入力を与える）にどうなるか、タイムアウト設定が必要かなども検討します。DeepInfra APIの応答待ち時間が長すぎる場合は、サーバー側でタイムアウト（requests.postのtimeout指定など）を設定し、TimeoutExceptionをキャッチして適切なエラーを返すようにします。この挙動もテストします。

    性能テスト: 可能であれば本番相当環境で音声入力処理の処理時間を計測します。画像分析が1リクエスト10〜30秒程度だったのに対し、音声分析は音声長＋αで処理されます。例えば10秒の音声ではSTT~2秒＋LLM推論~5秒の計7秒程度で結果が返る、といった具合に、実時間内に収まることを確認します。並行リクエスト試験はCloud Runの設定上直列処理になるため、主として単発性能を見ます。

3. Flutter クライアントとの結合テスト

バックエンド API 単体で正しく動作することを確認した後、Flutter アプリ側から実際に音声録音〜アップロード〜結果表示までシームレスに動くかをテストします。想定手順:

    Flutterアプリで音声録音（開発用にデバッグモードで実施）。録音フォーマットやエンコード方式がサーバーと齟齬なく伝わるか確認します。例えばiOSデバイスではデフォルトでm4a(AAC)になる場合がありますが、そのまま送信してサーバー側で正しく処理できるか（Google STTが対応していればOK、エラーならFlutter側で変換を検討）。

    録音後、用意したAPIクライアントコード（例えばMealAnalysisApiRepositoryの新メソッド）で/voiceエンドポイントにmultipartリクエストを送り、レスポンスをパースします。Flutterのリポジトリ実装にも、画像時と同様のレスポンスモデル(MealAnalysisApiResponseModel)があるはずなので、それが流用できるか確認します。おそらく共通のOpenAPI仕様から生成していれば同じモデルで受け取れるはずです。

    アプリUI上で結果（料理名・カロリー等）が期待通り表示されることを確認します。必要に応じて「音声分析中...」のインジケータ表示や、エラー時のトースト表示など、UX面の確認も行います。

4. リファクタリングとコードレビュー

テストで確認された問題を修正し、コードの重複や構造を改善します。例えば、画像と音声で共通化できる部分（栄養計算部分やレスポンス組み立て部分）は関数化・モジュール化し直すなど、メンテナンス性を高めます。また、第三者によるコードレビューを行い、見落としがないかチェックします。
まとめと展望

以上、Flutter 音声入力から栄養分析結果を得るまでの実装戦略を詳細に示しました。本計画に沿って開発を進めることで、ユーザーは食事内容を話すだけで記録・分析できるようになり、Meal Analysis API の UX は飛躍的に向上します。設計上は現行システムを拡張する形で進めており、画像分析機能との共存もスムーズです。デフォルトでは Gemma-3-27B モデルによる安定した解析を行いつつ、将来的にモデル変更や精度向上も設定一つで対応可能な柔軟性を持っています。

今後の展望として、例えばリアルタイム音声ストリーミング認識への対応（長い発話を逐次結果表示する）や、LLM を用いた対話的な栄養アドバイスへの拡張も考えられます。しかしまずは本計画のとおり確実に音声->栄養分析という一連の機能を実装・安定化させ、ユーザーに提供することが第一目です。そのための具体的な道筋は本ドキュメントで明確になりましたので、これに従い実装を進めます。各ステップでの検証を着実に行い、曖昧さのない堅牢なシステムを完成させましょう。
