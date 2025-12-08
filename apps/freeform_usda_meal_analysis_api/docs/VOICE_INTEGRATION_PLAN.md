# 音声入力機能統合実装プラン

## 概要

`meal_analysis_api--apps-usda_meal_analysis_api` リポジトリの音声機能を、現在の `meal_analysis_api_2` の `freeform_usda_meal_analysis_api` に統合する詳細プラン。

## 差分分析サマリー

### 移植元 (meal_analysis_api--apps-usda_meal_analysis_api) に存在し、現在のリポジトリにないファイル

| ファイル | 役割 |
|---------|------|
| `routers/voice.py` | `/api/v1/meal-analyses/voice` エンドポイント |
| `services/speech_service.py` | DeepInfra Whisper API による音声認識 (STT) |
| `services/text_analysis_service.py` | テキストからLLMで食事情報を抽出 |
| `prompts/freeform_voice_prompt_usda.txt` | 音声用プロンプト |

### 既存ファイルの差分

| ファイル | 移植元の追加機能 |
|---------|----------------|
| `config/settings.py` | Voice関連設定（`DEFAULT_VOICE_MODEL_ID`, `DEFAULT_VOICE_PROMPT_FILE`, `DEFAULT_WHISPER_MODEL`, `get_voice_prompt_path()`） |
| `models/response_models.py` | `VoiceMetadata` クラス, `AnalysisResponse.voice_metadata` フィールド |
| `services/providers/base_provider.py` | `analyze_text()` 抽象メソッド（テキストモード用） |
| `services/pipeline.py` | `analyze_meal_from_voice()` メソッド |
| `main.py` | Voice routerの登録、OpenAPI tagsの追加 |

---

## 実装フェーズ

### フェーズ 1: 設定ファイルの更新 (`config/settings.py`)

**変更内容:**
1. Voice用環境変数と設定を追加:
   - `DEFAULT_VOICE_MODEL_ID` (デフォルト: `google/gemma-3-27b-it`)
   - `DEFAULT_VOICE_PROMPT_FILE` (デフォルト: `freeform_voice_prompt_usda.txt`)
   - `DEFAULT_WHISPER_MODEL` (デフォルト: `openai/whisper-large-v3-turbo`)
   - `DEFAULT_VOICE_MAX_TOKENS` (デフォルト: `4096`)
   - `DEFAULT_VOICE_TEMPERATURE` (デフォルト: `0.3`)

2. `get_voice_prompt_path()` メソッドを追加

**追加するコード (lines 151-176 相当):**
```python
# ========== Voice分析設定 ==========
# Voice用LLM/VLMモデル（テキストモード）
# デフォルト: gemma-3-27b-it（軽量で高速なLLM）
# VLMモデル（Qwen3-VL等）もテキストモードで使用可能
self.DEFAULT_VOICE_MODEL_ID = os.getenv(
    "VOICE_MODEL_ID",
    "google/gemma-3-27b-it"
)

# Voice用プロンプトファイル
self.DEFAULT_VOICE_PROMPT_FILE = os.getenv(
    "DEFAULT_VOICE_PROMPT_FILE",
    "freeform_voice_prompt_usda.txt"
)

# 音声認識設定
self.DEFAULT_WHISPER_MODEL = os.getenv(
    "WHISPER_MODEL",
    "openai/whisper-large-v3-turbo"
)

# Voice用LLMパラメータ
self.DEFAULT_VOICE_MAX_TOKENS = int(os.getenv("VOICE_MAX_TOKENS", "4096"))
self.DEFAULT_VOICE_TEMPERATURE = float(os.getenv("VOICE_TEMPERATURE", "0.3"))
```

**追加するメソッド:**
```python
def get_voice_prompt_path(self, prompt_filename: Optional[str] = None) -> str:
    """Voice用プロンプトファイルの絶対パスを取得"""
    if prompt_filename is None:
        prompt_filename = self.DEFAULT_VOICE_PROMPT_FILE

    # バリデーション
    if len(prompt_filename) > 200 or '\n' in prompt_filename:
        raise ValueError(...)

    prompt_path = self.PROMPTS_DIR / prompt_filename

    if not prompt_path.exists():
        raise FileNotFoundError(...)

    return str(prompt_path)
```

---

### フェーズ 2: レスポンスモデルの更新 (`models/response_models.py`)

**変更内容:**
1. `VoiceMetadata` クラスを追加
2. `AnalysisResponse` に `voice_metadata` フィールドを追加

**追加するコード:**
```python
class VoiceMetadata(BaseModel):
    """音声入力メタデータ"""
    model_config = {"protected_namespaces": ()}

    whisper_model: str = Field(..., description="使用したWhisperモデル", example="openai/whisper-large-v3-turbo")
    audio_duration_seconds: Optional[float] = Field(None, description="音声の長さ（秒）", example=5.3)
    audio_size_bytes: int = Field(..., description="音声ファイルサイズ（バイト）", example=84736)
    language_detected: Optional[str] = Field(None, description="検出された言語", example="en")
    stt_processing_time_seconds: Optional[float] = Field(None, description="STT処理時間（秒）", example=1.2)
```

**AnalysisResponseへの追加:**
```python
# 音声入力特有（transcriptは既に存在）
voice_metadata: Optional[VoiceMetadata] = Field(None, description="音声入力メタデータ（音声入力時のみ）")
```

---

### フェーズ 3: プロバイダーの更新 (`services/providers/`)

**変更内容:**
1. `base_provider.py` に `analyze_text()` 抽象メソッドを追加
2. 各プロバイダー（DeepInfra, Alibaba, OpenRouter）に `analyze_text()` を実装

**base_provider.py への追加:**
```python
@abstractmethod
async def analyze_text(
    self,
    text: str,
    prompt: str,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    seed: Optional[int] = None,
    return_usage: bool = False
) -> Union[str, Tuple[str, Dict[str, Any]]]:
    """
    テキスト入力を分析してLLM/VLMの応答を取得（Voice入力用）

    画像なしでテキストのみを処理する。音声入力から変換されたテキストの
    分析に使用される。
    """
    pass
```

**DeepInfraProvider への実装例:**
```python
async def analyze_text(
    self,
    text: str,
    prompt: str,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    seed: Optional[int] = None,
    return_usage: bool = False
) -> Union[str, Tuple[str, Dict[str, Any]]]:
    """テキストモードでLLM/VLM呼び出し"""
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": text}
    ]

    # OpenAI互換APIを使用してテキストのみのリクエストを送信
    # 画像なしのシンプルなChat Completion形式
    ...
```

---

### フェーズ 4: 新規サービスファイルの追加

#### 4.1 `services/speech_service.py` (新規)

**機能:**
- DeepInfra Whisper API を使用した音声認識 (STT)
- 対応フォーマット: WAV, MP3, FLAC, OGG
- Whisperモデル: `whisper-large-v3`, `whisper-large-v3-turbo`, `whisper-base`

**主要クラス/メソッド:**
```python
class WhisperModel(Enum):
    LARGE_V3 = "openai/whisper-large-v3"
    LARGE_V3_TURBO = "openai/whisper-large-v3-turbo"
    BASE = "openai/whisper-base"

class SpeechService:
    def __init__(self, api_key: Optional[str] = None): ...

    async def transcribe_audio(
        self,
        audio_data: bytes,
        language: str = "en",
        model: Optional[str] = None,
        temperature: float = 0.0,
        prompt: Optional[str] = None
    ) -> str: ...

    @staticmethod
    def detect_audio_format(audio_data: bytes) -> tuple[str, int]: ...

    @staticmethod
    def get_available_models() -> list[str]: ...
```

#### 4.2 `services/text_analysis_service.py` (新規)

**機能:**
- LLM/VLM を使用してテキストから食事情報を抽出
- VLMServiceと同じインターフェースパターン
- JSON形式で出力

**主要クラス/メソッド:**
```python
class TextAnalysisService:
    def __init__(
        self,
        model_id: Optional[str] = None,
        prompt_file: Optional[str] = None
    ): ...

    async def analyze_text(
        self,
        text: str,
        temperature: Optional[float] = None,
        seed: Optional[int] = None,
        max_tokens: Optional[int] = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]: ...

    def get_prompt(self) -> str: ...
    def set_prompt(self, prompt: str) -> None: ...
    def reload_prompt(self, prompt_file: Optional[str] = None) -> None: ...
```

---

### フェーズ 5: パイプラインの更新 (`services/pipeline.py`)

**変更内容:**
1. `SpeechService` と `TextAnalysisService` のインポートを追加
2. `analyze_meal_from_voice()` メソッドを追加

**追加するメソッド (約300行):**
```python
async def analyze_meal_from_voice(
    self,
    audio_bytes: bytes,
    user_context: Optional[str] = None,
    model_config_override: Optional[Any] = None,
    search_config_override: Optional[Any] = None,
    voice_model_id: Optional[str] = None,
    voice_prompt_file: Optional[str] = None,
    whisper_model: Optional[str] = None,
    language: str = "en",
) -> Dict[str, Any]:
    """
    API用の音声分析エンドポイント

    処理フロー:
    1. 音声 → Whisper STT → テキスト変換
    2. テキスト → LLM → 食事情報抽出（USDA形式JSON）
    3. USDA検索 → 栄養価計算

    Returns:
        - dishes: 検出された料理リスト
        - total_nutrition: 総栄養価
        - transcript: 音声認識テキスト
        - voice_metadata: 音声メタデータ
        - usage: Token使用量
    """
    ...
```

---

### フェーズ 6: Voiceルーターの追加 (`routers/voice.py`)

**新規作成:**
```python
"""Voice analysis router for voice-based meal analysis endpoints"""

router = APIRouter(prefix="/api/v1/meal-analyses", tags=["Voice Analysis"])

@router.post("/voice", response_model=AnalysisResponse)
async def analyze_meal_from_voice(
    audio_file: UploadFile = File(..., description="音声ファイル（WAV, MP3, FLAC等）"),
    user_context: Optional[str] = Form(None, description="ユーザーコンテキスト"),
    language: Optional[str] = Form("en", description="言語コード（en, ja等）"),
    # Voice model config
    voice_model_id: Optional[str] = Form(None, description="Voice解析用LLM/VLMモデルID"),
    voice_prompt_file: Optional[str] = Form(None, description="Voice解析用プロンプトファイル"),
    whisper_model: Optional[str] = Form(None, description="Whisperモデル（STT用）"),
    # Model config overrides
    temperature: Optional[float] = Form(None, description="生成温度"),
    max_tokens: Optional[int] = Form(None, description="最大トークン数"),
    # Search config overrides
    stage1_top_k: Optional[int] = Form(None),
    bm25_weight: Optional[float] = Form(None),
    vector_weight: Optional[float] = Form(None),
    rrf_k: Optional[int] = Form(None),
    reranker_model: Optional[str] = Form(None),
    reranker_instruction: Optional[str] = Form(None),
    reranker_top_n: Optional[int] = Form(None),
):
    """
    音声から食事を分析して栄養価を計算

    ## 処理フロー
    1. 音声ファイル → Whisper STT → テキスト変換
    2. テキスト → LLM → 食事情報抽出（USDA形式JSON）
    3. USDA検索 → 栄養価計算
    """
    ...
```

---

### フェーズ 7: メインアプリケーションの更新 (`main.py`)

**変更内容:**
1. `voice` ルーターのインポートを追加
2. OpenAPI tagsに "Voice Analysis" を追加
3. ルーター登録
4. ルートエンドポイントのレスポンスに `voice` エンドポイントを追加

**変更箇所:**
```python
# Import追加
from .routers import health, analysis, retrieval, metadata, voice

# OpenAPI tags追加
{
    "name": "Voice Analysis",
    "description": "音声入力分析 - 音声から食事を分析し栄養価を計算。Whisper STT + LLM + USDA検索"
}

# ルーター登録追加
app.include_router(voice.router)

# ルートレスポンス追加
"endpoints": {
    ...
    "voice": "/api/v1/meal-analyses/voice",
}
```

---

### フェーズ 8: プロンプトファイルの追加

**ファイル:** `prompts/freeform_voice_prompt_usda.txt`

移植元からコピー。内容:
- 入力解釈ルール
- 重量推定ガイドライン
- USDA形式の命名規則（カテゴリファースト）
- 出力フォーマット定義
- サンプル例

---

## 統合時の注意点

### 1. 現在のリポジトリとの差分への対応

| 項目 | 現在のリポジトリ | 移植元 | 対応方針 |
|-----|----------------|-------|---------|
| `AnalysisResponse.meal_title` | 存在 | 存在しない | 維持（現在のまま） |
| `AnalysisResponse.voice_metadata` | 存在しない | 存在 | 追加 |
| `debug_info`構造 | 新しい形式 | 旧形式 | 現在の形式を維持、Voice用にも適用 |

### 2. プロバイダーのanalyze_text実装

各プロバイダーで `analyze_text()` メソッドを実装する必要がある:

- **DeepInfraProvider**: OpenAI互換API（Chat Completion形式）を使用
- **AlibabaProvider**: DashScope APIのテキストモード
- **OpenRouterProvider**: OpenAI互換API

### 3. エラーハンドリング

Voice特有のエラーケース:
- 音声ファイル形式が無効
- STT（音声認識）失敗
- LLMテキスト解析失敗
- 空の音声ファイル
- 長すぎる音声ファイル

---

## テスト計画

### 単体テスト

1. **SpeechService**
   - 各音声フォーマットの認識テスト
   - エラーハンドリングテスト

2. **TextAnalysisService**
   - テキスト解析結果の検証
   - プロンプトロードテスト

3. **各プロバイダーのanalyze_text()**
   - DeepInfra
   - Alibaba
   - OpenRouter

### 統合テスト

1. **End-to-End Voice分析**
   ```bash
   curl -X POST "http://localhost:8006/api/v1/meal-analyses/voice" \
     -F "audio_file=@test-audio/lunch.wav" \
     -F "language=en"
   ```

2. **異なるモデルでのテスト**
   - voice_model_id指定
   - whisper_model指定

---

## ファイル一覧

### 新規作成ファイル

| ファイルパス | サイズ(行) |
|------------|----------|
| `routers/voice.py` | ~200 |
| `services/speech_service.py` | ~200 |
| `services/text_analysis_service.py` | ~160 |
| `prompts/freeform_voice_prompt_usda.txt` | ~210 |

### 変更ファイル

| ファイルパス | 変更内容 |
|------------|---------|
| `config/settings.py` | Voice設定追加 (~60行) |
| `models/response_models.py` | VoiceMetadata追加 (~15行) |
| `services/providers/base_provider.py` | analyze_text抽象メソッド追加 (~25行) |
| `services/providers/deepinfra_provider.py` | analyze_text実装 (~50行) |
| `services/providers/alibaba_provider.py` | analyze_text実装 (~50行) |
| `services/providers/openrouter_provider.py` | analyze_text実装 (~50行) |
| `services/pipeline.py` | analyze_meal_from_voice追加 (~300行) |
| `main.py` | Voiceルーター登録 (~15行) |
| `models/__init__.py` | VoiceMetadataエクスポート |

---

## 実装順序

1. **Phase 1**: `config/settings.py` - Voice設定追加
2. **Phase 2**: `models/response_models.py` - VoiceMetadata追加
3. **Phase 3**: `services/providers/base_provider.py` - analyze_text抽象メソッド
4. **Phase 4a**: `services/speech_service.py` - 新規作成
5. **Phase 4b**: `services/text_analysis_service.py` - 新規作成
6. **Phase 5**: 各プロバイダーに `analyze_text()` 実装
7. **Phase 6**: `services/pipeline.py` - analyze_meal_from_voice追加
8. **Phase 7**: `routers/voice.py` - 新規作成
9. **Phase 8**: `main.py` - Voiceルーター登録
10. **Phase 9**: `prompts/freeform_voice_prompt_usda.txt` - プロンプト追加
11. **Phase 10**: テスト実行と動作確認

---

## 依存関係

### 必要なPythonパッケージ

既存の依存関係で対応可能:
- `aiohttp` - 非同期HTTPクライアント（SpeechServiceで使用）
- `fastapi` - APIフレームワーク
- `pydantic` - データバリデーション

### 環境変数

| 変数名 | 必須 | デフォルト |
|-------|-----|---------|
| `DEEPINFRA_API_KEY` | Yes | - |
| `VOICE_MODEL_ID` | No | `google/gemma-3-27b-it` |
| `DEFAULT_VOICE_PROMPT_FILE` | No | `freeform_voice_prompt_usda.txt` |
| `WHISPER_MODEL` | No | `openai/whisper-large-v3-turbo` |
| `VOICE_MAX_TOKENS` | No | `4096` |
| `VOICE_TEMPERATURE` | No | `0.3` |

---

## API仕様

### POST /api/v1/meal-analyses/voice

**リクエスト (multipart/form-data):**

| パラメータ | 型 | 必須 | 説明 |
|----------|---|-----|-----|
| `audio_file` | File | Yes | 音声ファイル（WAV, MP3, FLAC等） |
| `user_context` | string | No | ユーザーコンテキスト |
| `language` | string | No | 言語コード（デフォルト: "en"） |
| `voice_model_id` | string | No | Voice解析用LLM/VLMモデルID |
| `voice_prompt_file` | string | No | Voice解析用プロンプトファイル |
| `whisper_model` | string | No | Whisperモデル（STT用） |
| `temperature` | float | No | 生成温度 |
| `max_tokens` | int | No | 最大トークン数 |
| `stage1_top_k` | int | No | Stage1候補数 |
| `bm25_weight` | float | No | BM25検索の重み |
| `vector_weight` | float | No | Vector検索の重み |
| `rrf_k` | int | No | RRFのkパラメータ |
| `reranker_model` | string | No | Rerankerモデル名 |

**レスポンス:**

`AnalysisResponse` と同じ形式に加えて:
- `transcript`: 音声認識結果テキスト
- `voice_metadata`: 音声メタデータ

```json
{
  "analysis_id": "abc12345",
  "input_type": "voice",
  "total_dishes": 2,
  "total_ingredients": 5,
  "processing_time_seconds": 8.5,
  "dishes": [...],
  "total_nutrition": {...},
  "ai_model_used": "google/gemma-3-27b-it",
  "prompt_file_used": "freeform_voice_prompt_usda.txt",
  "match_rate_percent": 100.0,
  "usage": {...},
  "transcript": "I had grilled chicken with rice and broccoli",
  "voice_metadata": {
    "whisper_model": "openai/whisper-large-v3-turbo",
    "audio_duration_seconds": 3.2,
    "audio_size_bytes": 51200,
    "language_detected": "en",
    "stt_processing_time_seconds": 1.2
  },
  "warnings": []
}
```
