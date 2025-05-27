#!/usr/bin/env python3
"""
フェーズ2 API テストスクリプト
フェーズ1の結果を使用してUSDA統合による精緻化をテスト
"""

import requests
import json
import os
import time

# APIのベースURL
BASE_URL = "http://localhost:8000/api/v1"

# テスト用画像パス（既存のテスト画像を使用）
TEST_IMAGES = [
    "test_images/food1.jpg",
    "test_images/food2.jpg",
    "test_images/food3.jpg"
]

def test_phase1_analysis(image_path):
    """フェーズ1の分析を実行"""
    print(f"\n=== Phase 1: {image_path} の分析 ===")
    
    endpoint = f"{BASE_URL}/meal-analyses"
    
    try:
        with open(image_path, 'rb') as f:
            files = {'image': (image_path, f, 'image/jpeg')}
            response = requests.post(endpoint, files=files)
        
        if response.status_code == 200:
            result = response.json()
            print(f"成功！ {len(result.get('dishes', []))} 個の料理を検出")
            return json.dumps(result, ensure_ascii=False)
        else:
            print(f"エラー: {response.status_code}")
            print(f"詳細: {response.text}")
            return None
            
    except Exception as e:
        print(f"例外発生: {e}")
        return None

def test_phase2_refinement(image_path, phase1_result):
    """フェーズ2の精緻化を実行"""
    print(f"\n=== Phase 2: {image_path} の精緻化 ===")
    
    endpoint = f"{BASE_URL}/meal-analyses/refine"
    
    try:
        with open(image_path, 'rb') as f:
            files = {'image': (image_path, f, 'image/jpeg')}
            data = {'initial_analysis_data': phase1_result}
            response = requests.post(endpoint, files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"成功！ {len(result.get('dishes', []))} 個の料理を精緻化")
            
            # 結果の詳細を表示
            for dish in result.get('dishes', []):
                print(f"\n料理: {dish['dish_name']} ({dish['type']})")
                print(f"量: {dish['quantity_on_plate']}")
                
                for ingredient in dish.get('ingredients', []):
                    print(f"  - {ingredient['ingredient_name']}: {ingredient['weight_g']}g")
                    if ingredient.get('fdc_id'):
                        print(f"    FDC ID: {ingredient['fdc_id']}")
                        print(f"    USDA名: {ingredient.get('usda_source_description', 'N/A')}")
                        
                        # 栄養素情報
                        nutrients = ingredient.get('key_nutrients_per_100g', {})
                        if nutrients:
                            print(f"    栄養素(100gあたり):")
                            for key, value in nutrients.items():
                                print(f"      - {key}: {value}")
            
            return result
        else:
            print(f"エラー: {response.status_code}")
            print(f"詳細: {response.text}")
            return None
            
    except Exception as e:
        print(f"例外発生: {e}")
        return None

def run_full_test():
    """フェーズ1→フェーズ2の完全なテストを実行"""
    print("=== フェーズ2 API テスト開始 ===")
    
    # ヘルスチェック
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✓ APIサーバーは正常に動作しています")
        else:
            print("✗ APIサーバーに接続できません")
            return
    except:
        print("✗ APIサーバーに接続できません。サーバーが起動していることを確認してください。")
        return
    
    # 各テスト画像に対してテスト実行
    for image_path in TEST_IMAGES:
        if not os.path.exists(image_path):
            print(f"\n✗ {image_path} が見つかりません")
            continue
        
        print(f"\n{'='*60}")
        print(f"テスト画像: {image_path}")
        print(f"{'='*60}")
        
        # フェーズ1の実行
        phase1_result = test_phase1_analysis(image_path)
        if not phase1_result:
            print(f"✗ フェーズ1の分析に失敗しました")
            continue
        
        # 少し待機（APIの負荷を考慮）
        time.sleep(2)
        
        # フェーズ2の実行
        phase2_result = test_phase2_refinement(image_path, phase1_result)
        if not phase2_result:
            print(f"✗ フェーズ2の精緻化に失敗しました")
        else:
            print(f"✓ フェーズ2の精緻化が成功しました")
        
        # 次のテストまで少し待機
        time.sleep(3)
    
    print("\n=== テスト完了 ===")

if __name__ == "__main__":
    run_full_test() 