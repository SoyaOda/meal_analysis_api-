#!/usr/bin/env python3
"""
音声分析APIのテストスクリプト

test-audio/breakfast_detailed.mp3 を使用して音声分析機能をテストします。
"""
import asyncio
import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 環境変数の設定（必要に応じて）
if not os.getenv("DEEPINFRA_API_KEY"):
    print("❌ DEEPINFRA_API_KEY環境変数が設定されていません")
    print("   export DEEPINFRA_API_KEY=your_api_key_here")
    sys.exit(1)

if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    print("⚠️ GOOGLE_APPLICATION_CREDENTIALS環境変数が設定されていません")
    print("   Google Cloud Speech-to-Textの認証に必要です")


async def test_voice_analysis_components():
    """音声分析コンポーネントの単体テスト"""
    print("🎤 音声分析コンポーネントのテスト開始")

    # テスト音声ファイル
    test_audio_path = project_root / "test-audio" / "breakfast_detailed.mp3"

    if not test_audio_path.exists():
        print(f"❌ テスト音声ファイルが見つかりません: {test_audio_path}")
        return False

    try:
        # 音声データ読み込み
        with open(test_audio_path, "rb") as f:
            audio_data = f.read()

        print(f"✅ 音声ファイル読み込み成功: {len(audio_data)} bytes")

        # Step 1: SpeechServiceのテスト
        try:
            from app_v2.services.speech_service import SpeechService

            print("🔊 Step 1: 音声認識テスト")
            speech_service = SpeechService()

            # 音声フォーマット検出
            encoding, sample_rate = speech_service.detect_audio_format(audio_data)
            print(f"   検出フォーマット: {encoding}, サンプリングレート: {sample_rate}Hz")

            # 音声認識実行
            transcript = await speech_service.transcribe_audio(
                audio_data=audio_data,
                sample_rate=sample_rate,
                encoding="MP3",  # MP3として処理
                language_code="en-US"
            )

            print(f"✅ 音声認識成功: '{transcript}'")

        except Exception as e:
            print(f"❌ 音声認識失敗: {e}")
            return False

        # Step 2: NLUServiceのテスト
        try:
            from app_v2.services.nlu_service import NLUService

            print("🧠 Step 2: NLU処理テスト")
            nlu_service = NLUService()

            # サンプルテキストでテスト（実際の音声認識結果を使用）
            test_text = transcript
            nlu_result = await nlu_service.extract_foods_from_text(test_text)

            print(f"✅ NLU処理成功:")
            print(f"   検出料理数: {len(nlu_result.get('dishes', []))}")
            for dish in nlu_result.get('dishes', []):
                print(f"   - {dish['dish_name']} (信頼度: {dish.get('confidence', 'N/A')})")
                for ingredient in dish.get('ingredients', []):
                    print(f"     * {ingredient['ingredient_name']}: {ingredient['weight_g']}g")

        except Exception as e:
            print(f"❌ NLU処理失敗: {e}")
            return False

        # Step 3: Phase1SpeechComponentのテスト
        try:
            from app_v2.components.phase1_speech_component import Phase1SpeechComponent
            from app_v2.models.voice_analysis_models import VoiceAnalysisInput

            print("🎯 Step 3: Phase1Speech統合テスト")

            phase1_speech = Phase1SpeechComponent()
            voice_input = VoiceAnalysisInput(
                audio_bytes=audio_data,
                audio_mime_type="audio/mp3",
                language_code="en-US"
            )

            phase1_result = await phase1_speech.execute(voice_input)

            print(f"✅ Phase1Speech成功:")
            print(f"   検出料理数: {len(phase1_result.dishes)}")
            print(f"   総食材数: {sum(len(dish.ingredients) for dish in phase1_result.dishes)}")
            print(f"   分析信頼度: {phase1_result.analysis_confidence:.2f}")

            for dish in phase1_result.dishes:
                print(f"   - {dish.dish_name} (信頼度: {dish.confidence:.2f})")
                for ingredient in dish.ingredients:
                    print(f"     * {ingredient.ingredient_name}: {ingredient.weight_g}g")

        except Exception as e:
            print(f"❌ Phase1Speech失敗: {e}")
            return False

        print("🎉 音声分析コンポーネントテスト完了！")
        return True

    except Exception as e:
        print(f"❌ テスト中にエラーが発生: {e}")
        return False


async def test_voice_api_endpoint():
    """音声分析APIエンドポイントのテスト"""
    print("\n🌐 音声分析APIエンドポイントのテスト開始")

    try:
        import httpx
        from fastapi.testclient import TestClient
        from app_v2.main.app import app

        # TestClientを使用したテスト
        client = TestClient(app)

        # テスト音声ファイル
        test_audio_path = project_root / "test-audio" / "breakfast_detailed.mp3"

        if not test_audio_path.exists():
            print(f"❌ テスト音声ファイルが見つかりません: {test_audio_path}")
            return False

        # APIエンドポイントテスト
        with open(test_audio_path, "rb") as f:
            files = {"audio": ("breakfast_detailed.mp3", f, "audio/mp3")}
            data = {
                "language_code": "en-US",
                "save_detailed_logs": "false",  # テスト用にログ保存無効
                "test_execution": "true"
            }

            print("📡 /api/v1/meal-analyses/voice エンドポイントをテスト中...")
            response = client.post("/api/v1/meal-analyses/voice", files=files, data=data)

        if response.status_code == 200:
            result = response.json()
            print(f"✅ API呼び出し成功:")
            print(f"   分析ID: {result.get('analysis_id')}")
            print(f"   料理数: {result.get('total_dishes')}")
            print(f"   食材数: {result.get('total_ingredients')}")
            print(f"   処理時間: {result.get('processing_time_seconds'):.2f}秒")
            print(f"   総カロリー: {result.get('total_nutrition', {}).get('calories', 'N/A')} kcal")

            return True
        else:
            print(f"❌ API呼び出し失敗: {response.status_code}")
            print(f"   エラー詳細: {response.text}")
            return False

    except Exception as e:
        print(f"❌ APIテスト中にエラーが発生: {e}")
        return False


async def main():
    """メインテスト実行"""
    print("🎵 音声分析機能のテスト開始")
    print("=" * 50)

    # コンポーネントテスト
    component_success = await test_voice_analysis_components()

    if component_success:
        # APIエンドポイントテスト
        api_success = await test_voice_api_endpoint()

        if api_success:
            print("\n🎊 すべてのテストが成功しました！")
            print("\n次のステップ:")
            print("1. ローカルサーバーを起動: python -m uvicorn app_v2.main.app:app --host 0.0.0.0 --port 8001 --reload")
            print("2. 音声分析API実行:")
            print("   curl -X POST 'http://localhost:8001/api/v1/meal-analyses/voice' \\")
            print("     -F 'audio=@test-audio/breakfast_detailed.mp3' \\")
            print("     -F 'language_code=en-US'")
        else:
            print("\n❌ APIエンドポイントテストに失敗しました")
    else:
        print("\n❌ コンポーネントテストに失敗しました")


if __name__ == "__main__":
    asyncio.run(main())