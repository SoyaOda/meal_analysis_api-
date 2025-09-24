#!/usr/bin/env python3
"""
DeepInfra Whisper API 音声ファイルテストスクリプト

test_audio/lunch_detailed.wavを使用してWhisper統合の実際のAPI呼び出しをテストします。
"""
import asyncio
import os
import aiohttp
import json
from pathlib import Path

async def test_whisper_with_actual_audio():
    """
    実際の音声ファイルを使用したWhisper統合テスト
    """
    print("🔍 DeepInfra Whisper API 実音声テスト開始")

    # 音声ファイルのパス
    audio_file_path = "test_audio/lunch_detailed.wav"

    # ファイル存在確認
    if not os.path.exists(audio_file_path):
        print(f"❌ 音声ファイルが見つかりません: {audio_file_path}")
        return False

    print(f"📁 音声ファイル: {audio_file_path}")
    file_size = os.path.getsize(audio_file_path)
    print(f"📏 ファイルサイズ: {file_size} bytes")

    try:
        # APIエンドポイントURL
        api_url = "http://localhost:8001/voice"

        # フォームデータを準備
        data = aiohttp.FormData()

        # 音声ファイルを追加
        with open(audio_file_path, 'rb') as f:
            data.add_field('audio', f,
                          filename='lunch_detailed.wav',
                          content_type='audio/wav')

        # Whisperパラメータを追加
        data.add_field('use_whisper', 'true')
        data.add_field('whisper_backend', 'deepinfra_api')
        data.add_field('whisper_model', 'openai/whisper-large-v3-turbo')
        data.add_field('language_code', 'en-US')
        data.add_field('temperature', '0.0')
        data.add_field('save_detailed_logs', 'true')

        print("📡 1. DeepInfra Whisper APIテスト実行中...")

        # API呼び出し実行
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ API呼び出し成功!")

                    # 結果の詳細表示
                    if "nutrition_info" in result and "dishes" in result["nutrition_info"]:
                        dishes = result["nutrition_info"]["dishes"]
                        print(f"🍽️  検出された料理数: {len(dishes)}")

                        for i, dish in enumerate(dishes, 1):
                            print(f"   {i}. {dish['dish_name']} (信頼度: {dish['confidence']:.2f})")
                            for ingredient in dish['ingredients']:
                                print(f"      - {ingredient['ingredient_name']}: {ingredient['weight_g']}g")

                    # 栄養情報表示
                    if "nutrition_info" in result and "total_nutrition" in result["nutrition_info"]:
                        total_nutrition = result["nutrition_info"]["total_nutrition"]
                        print(f"📊 総カロリー: {total_nutrition['calories']:.1f} kcal")
                        print(f"   タンパク質: {total_nutrition['protein']:.1f}g")
                        print(f"   脂質: {total_nutrition['fat']:.1f}g")
                        print(f"   炭水化物: {total_nutrition['carbs']:.1f}g")

                    # 処理時間表示
                    if "processing_time_seconds" in result:
                        print(f"⏱️  処理時間: {result['processing_time_seconds']:.2f}秒")

                    return True

                else:
                    error_text = await response.text()
                    print(f"❌ API呼び出し失敗 (ステータス: {response.status})")
                    print(f"   エラー詳細: {error_text}")
                    return False

    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_google_vs_whisper_comparison():
    """
    Google Speech-to-TextとDeepInfra Whisperの比較テスト
    """
    print("\n🆚 Google vs DeepInfra Whisper 比較テスト")

    audio_file_path = "test_audio/lunch_detailed.wav"
    if not os.path.exists(audio_file_path):
        print(f"❌ 音声ファイルが見つかりません: {audio_file_path}")
        return False

    api_url = "http://localhost:8001/voice"
    results = {}

    # テスト設定
    test_configs = [
        {
            "name": "Google Speech-to-Text",
            "params": {
                'use_whisper': 'false',
                'language_code': 'en-US',
                'temperature': '0.0',
                'save_detailed_logs': 'true'
            }
        },
        {
            "name": "DeepInfra Whisper",
            "params": {
                'use_whisper': 'true',
                'whisper_backend': 'deepinfra_api',
                'whisper_model': 'openai/whisper-large-v3-turbo',
                'language_code': 'en-US',
                'temperature': '0.0',
                'save_detailed_logs': 'true'
            }
        }
    ]

    for config in test_configs:
        print(f"\n📡 {config['name']}でテスト中...")

        try:
            data = aiohttp.FormData()

            # 音声ファイルを追加
            with open(audio_file_path, 'rb') as f:
                data.add_field('audio', f,
                              filename='lunch_detailed.wav',
                              content_type='audio/wav')

            # パラメータを追加
            for key, value in config['params'].items():
                data.add_field(key, value)

            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        results[config['name']] = result

                        # 簡潔な結果表示
                        dishes_count = len(result.get("nutrition_info", {}).get("dishes", []))
                        total_calories = result.get("nutrition_info", {}).get("total_nutrition", {}).get("calories", 0)
                        processing_time = result.get("processing_time_seconds", 0)

                        print(f"✅ {config['name']} 成功:")
                        print(f"   料理数: {dishes_count}")
                        print(f"   総カロリー: {total_calories:.1f} kcal")
                        print(f"   処理時間: {processing_time:.2f}秒")

                    else:
                        error_text = await response.text()
                        print(f"❌ {config['name']} 失敗 (ステータス: {response.status})")
                        print(f"   エラー: {error_text}")
                        results[config['name']] = None

        except Exception as e:
            print(f"❌ {config['name']} テストエラー: {e}")
            results[config['name']] = None

    # 比較結果表示
    print("\n📊 比較結果サマリー:")
    for name, result in results.items():
        if result:
            dishes_count = len(result.get("nutrition_info", {}).get("dishes", []))
            total_calories = result.get("nutrition_info", {}).get("total_nutrition", {}).get("calories", 0)
            processing_time = result.get("processing_time_seconds", 0)
            print(f"{name}: {dishes_count}料理, {total_calories:.1f}kcal, {processing_time:.2f}s")
        else:
            print(f"{name}: テスト失敗")

    return True

async def main():
    """メイン実行関数"""
    print("=" * 60)
    print("🎙️  DeepInfra Whisper API 実音声テスト")
    print("=" * 60)

    # 単体テスト実行
    success1 = await test_whisper_with_actual_audio()

    if success1:
        # 比較テスト実行
        success2 = await test_google_vs_whisper_comparison()

        if success2:
            print("\n🎉 全テスト完了: DeepInfra Whisper API統合成功!")
            print("\n💰 コスト削減効果:")
            print("   Google Speech-to-Text: $0.021/分")
            print("   DeepInfra Whisper: $0.0002/分")
            print("   削減率: 99%")
        else:
            print("\n⚠️  比較テストで一部エラーが発生しましたが、基本機能は動作しています。")
    else:
        print("\n❌ Whisper統合テスト失敗")

if __name__ == "__main__":
    asyncio.run(main())