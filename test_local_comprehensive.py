#!/usr/bin/env python3
"""
Comprehensive test for local Meal Analysis API with images and audio files
"""
import requests
import json
import time
from pathlib import Path

API_URL = "http://localhost:8001"
RESULTS_DIR = Path("/tmp/local_test_results")
RESULTS_DIR.mkdir(exist_ok=True)

def test_image(image_path: str, test_name: str):
    """Test with an image file"""
    print(f"\n{'='*60}")
    print(f"Testing: {test_name}")
    print(f"Image: {image_path}")
    print(f"{'='*60}")

    try:
        with open(image_path, 'rb') as f:
            files = {'image': (Path(image_path).name, f, 'image/jpeg')}
            start_time = time.time()
            response = requests.post(f"{API_URL}/api/v1/meal-analyses/complete", files=files)
            elapsed = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            result_file = RESULTS_DIR / f"{test_name}_image.json"
            with open(result_file, 'w') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            print(f"✅ SUCCESS ({elapsed:.2f}s)")
            print(f"   Total dishes: {result.get('total_dishes', 'N/A')}")
            print(f"   Total calories: {result.get('total_nutrition', {}).get('calories', 'N/A'):.1f} kcal")
            print(f"   Match rate: {result.get('match_rate_percent', 'N/A')}%")
            print(f"   Result saved: {result_file}")

            # Print dish details
            for dish in result.get('dishes', []):
                print(f"\n   📍 {dish['dish_name']} ({dish['confidence']*100:.0f}% confidence)")
                for ing in dish.get('ingredients', []):
                    print(f"      - {ing['ingredient_name']}: {ing['weight_g']}g, {ing['calculated_nutrition']['calories']:.1f} kcal")

            return True
        else:
            print(f"❌ FAILED: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_audio(audio_path: str, test_name: str):
    """Test with an audio file"""
    print(f"\n{'='*60}")
    print(f"Testing: {test_name}")
    print(f"Audio: {audio_path}")
    print(f"{'='*60}")

    try:
        with open(audio_path, 'rb') as f:
            files = {'audio': (Path(audio_path).name, f, 'audio/wav')}
            start_time = time.time()
            response = requests.post(f"{API_URL}/api/v1/meal-analyses/voice", files=files)
            elapsed = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            result_file = RESULTS_DIR / f"{test_name}_audio.json"
            with open(result_file, 'w') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            print(f"✅ SUCCESS ({elapsed:.2f}s)")
            print(f"   Total dishes: {result.get('total_dishes', 'N/A')}")
            print(f"   Total calories: {result.get('total_nutrition', {}).get('calories', 'N/A'):.1f} kcal")
            print(f"   Match rate: {result.get('match_rate_percent', 'N/A')}%")
            print(f"   Result saved: {result_file}")

            # Print dish details
            for dish in result.get('dishes', []):
                print(f"\n   📍 {dish['dish_name']} ({dish['confidence']*100:.0f}% confidence)")
                for ing in dish.get('ingredients', []):
                    print(f"      - {ing['ingredient_name']}: {ing['weight_g']}g, {ing['calculated_nutrition']['calories']:.1f} kcal")

            return True
        else:
            print(f"❌ FAILED: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def main():
    print("\n" + "="*60)
    print("🧪 LOCAL API COMPREHENSIVE TEST")
    print("="*60)

    # Test API health
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is running")
        else:
            print("❌ API health check failed")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return

    results = {
        'images': {},
        'audio': {}
    }

    # Test images
    print("\n" + "="*60)
    print("📷 TESTING IMAGES")
    print("="*60)

    image_tests = [
        ('test_images/food1.jpg', 'food1'),
        ('test_images/food2.jpg', 'food2'),
        ('test_images/food3.jpg', 'food3'),
    ]

    for img_path, test_name in image_tests:
        results['images'][test_name] = test_image(img_path, test_name)
        time.sleep(1)  # Brief pause between tests

    # Test audio
    print("\n" + "="*60)
    print("🎤 TESTING AUDIO")
    print("="*60)

    audio_tests = [
        ('test_audio/breakfast_detailed.wav', 'breakfast_detailed'),
        ('test_audio/lunch_detailed.wav', 'lunch_detailed'),
        ('test_audio/dinner_detailed.wav', 'dinner_detailed'),
    ]

    for audio_path, test_name in audio_tests:
        results['audio'][test_name] = test_audio(audio_path, test_name)
        time.sleep(1)  # Brief pause between tests

    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)

    img_passed = sum(1 for v in results['images'].values() if v)
    img_total = len(results['images'])
    audio_passed = sum(1 for v in results['audio'].values() if v)
    audio_total = len(results['audio'])

    print(f"\nImages: {img_passed}/{img_total} passed")
    for name, passed in results['images'].items():
        status = "✅" if passed else "❌"
        print(f"  {status} {name}")

    print(f"\nAudio: {audio_passed}/{audio_total} passed")
    for name, passed in results['audio'].items():
        status = "✅" if passed else "❌"
        print(f"  {status} {name}")

    print(f"\nOverall: {img_passed + audio_passed}/{img_total + audio_total} tests passed")
    print(f"\n💾 All results saved to: {RESULTS_DIR}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
