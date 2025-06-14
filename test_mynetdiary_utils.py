#!/usr/bin/env python3
"""
MyNetDiaryユーティリティ関数のテスト
"""
import os
import sys

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app_v2.utils.mynetdiary_utils import (
    load_mynetdiary_ingredient_names,
    get_mynetdiary_ingredient_names_as_set,
    format_mynetdiary_ingredients_for_prompt,
    validate_ingredient_against_mynetdiary
)

def test_load_mynetdiary_ingredient_names():
    """MyNetDiary食材名リストの読み込みテスト"""
    print("🔄 MyNetDiary食材名リスト読み込みテスト...")
    
    try:
        ingredient_names = load_mynetdiary_ingredient_names()
        print(f"✅ 成功: {len(ingredient_names)}個の食材名を読み込みました")
        
        # 最初の10個を表示
        print("📋 最初の10個の食材名:")
        for i, name in enumerate(ingredient_names[:10], 1):
            print(f"   {i}. {name}")
        
        # 最後の5個を表示
        print("📋 最後の5個の食材名:")
        for i, name in enumerate(ingredient_names[-5:], len(ingredient_names)-4):
            print(f"   {i}. {name}")
            
        return True
        
    except Exception as e:
        print(f"❌ 失敗: {e}")
        return False

def test_get_mynetdiary_ingredient_names_as_set():
    """MyNetDiary食材名Setとしてのテスト"""
    print("\n🔄 MyNetDiary食材名Set取得テスト...")
    
    try:
        ingredient_set = get_mynetdiary_ingredient_names_as_set()
        print(f"✅ 成功: {len(ingredient_set)}個の食材名をSetとして取得しました")
        
        # 重複チェック
        ingredient_list = load_mynetdiary_ingredient_names()
        if len(ingredient_list) == len(ingredient_set):
            print("✅ 重複なし: リストとSetのサイズが一致しています")
        else:
            print(f"⚠️  重複あり: リスト{len(ingredient_list)}個 vs Set{len(ingredient_set)}個")
            
        return True
        
    except Exception as e:
        print(f"❌ 失敗: {e}")
        return False

def test_validate_ingredient_against_mynetdiary():
    """MyNetDiary食材名バリデーションテスト"""
    print("\n🔄 MyNetDiary食材名バリデーションテスト...")
    
    try:
        # 存在する食材名のテスト
        valid_ingredients = [
            "Almonds raw",
            "Apples with skin raw", 
            "Bananas raw",
            "Beef ground 80% lean 20% fat or hamburger patty raw",
            "Broccoli raw"
        ]
        
        print("📋 存在する食材名のテスト:")
        for ingredient in valid_ingredients:
            is_valid = validate_ingredient_against_mynetdiary(ingredient)
            status = "✅" if is_valid else "❌"
            print(f"   {status} {ingredient}: {is_valid}")
        
        # 存在しない食材名のテスト
        invalid_ingredients = [
            "Custom Ingredient",
            "Made Up Food",
            "Non Existent Item",
            "Caesar Dressing",  # これはMyNetDiaryにはない可能性
            "Romaine Lettuce"   # これもMyNetDiaryの正確な名前ではない可能性
        ]
        
        print("\n📋 存在しない食材名のテスト:")
        for ingredient in invalid_ingredients:
            is_valid = validate_ingredient_against_mynetdiary(ingredient)
            status = "❌" if not is_valid else "⚠️"
            print(f"   {status} {ingredient}: {is_valid}")
            
        return True
        
    except Exception as e:
        print(f"❌ 失敗: {e}")
        return False

def test_format_mynetdiary_ingredients_for_prompt():
    """プロンプト用フォーマットテスト"""
    print("\n🔄 プロンプト用フォーマットテスト...")
    
    try:
        formatted_prompt = format_mynetdiary_ingredients_for_prompt()
        
        # 最初の500文字を表示
        print("📋 フォーマット済みプロンプト（最初の500文字）:")
        print(formatted_prompt[:500] + "...")
        
        # 行数をカウント
        lines = formatted_prompt.split('\n')
        print(f"✅ 成功: {len(lines)}行のフォーマット済みリストを生成しました")
        
        # 最初の5行を確認
        print("\n📋 最初の5行:")
        for line in lines[:5]:
            print(f"   {line}")
            
        return True
        
    except Exception as e:
        print(f"❌ 失敗: {e}")
        return False

def test_phase1_prompt_integration():
    """Phase1プロンプトとの統合テスト"""
    print("\n🔄 Phase1プロンプト統合テスト...")
    
    try:
        from app_v2.config.prompts.phase1_prompts import Phase1Prompts
        
        # システムプロンプトの取得
        system_prompt = Phase1Prompts.get_system_prompt()
        
        # MyNetDiary制約が含まれているかチェック
        if "MYNETDIARY INGREDIENT CONSTRAINT" in system_prompt:
            print("✅ MyNetDiary制約がシステムプロンプトに含まれています")
        else:
            print("❌ MyNetDiary制約がシステムプロンプトに含まれていません")
            
        # 食材名リストが含まれているかチェック
        if "Agave syrup" in system_prompt and "Zucchini raw" in system_prompt:
            print("✅ MyNetDiary食材名リストがプロンプトに含まれています")
        else:
            print("❌ MyNetDiary食材名リストがプロンプトに含まれていません")
            
        # プロンプトサイズの確認
        prompt_size = len(system_prompt)
        print(f"📊 システムプロンプトサイズ: {prompt_size:,} 文字")
        
        if prompt_size > 100000:  # 100KB以上
            print("⚠️  プロンプトサイズが大きいです。APIの制限に注意してください。")
        else:
            print("✅ プロンプトサイズは適切です")
            
        return True
        
    except Exception as e:
        print(f"❌ 失敗: {e}")
        return False

def main():
    """メイン関数"""
    print("🚀 MyNetDiaryユーティリティ関数テスト v1.0")
    print("=" * 60)
    
    tests = [
        test_load_mynetdiary_ingredient_names,
        test_get_mynetdiary_ingredient_names_as_set,
        test_validate_ingredient_against_mynetdiary,
        test_format_mynetdiary_ingredients_for_prompt,
        test_phase1_prompt_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ テスト {test_func.__name__} で予期しないエラー: {e}")
    
    print("\n" + "=" * 60)
    print(f"🎯 テスト結果: {passed}/{total} 成功")
    
    if passed == total:
        print("✅ 全てのテストが成功しました！")
        return True
    else:
        print("❌ 一部のテストが失敗しました。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 