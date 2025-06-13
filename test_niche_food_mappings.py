#!/usr/bin/env python3
"""
Test for Niche Food Mappings functionality

ニッチな食材マッピング機能の動作確認テスト
"""

from app_v2.config.prompts.phase1_prompts import Phase1Prompts

def test_niche_food_mappings():
    """ニッチな食材マッピング機能のテスト"""
    print("🧪 Testing niche food mappings functionality...")
    
    # 1. JSONファイルの読み込みテスト
    print("\n1. JSONファイル読み込みテスト:")
    try:
        mappings = Phase1Prompts._load_niche_food_mappings()
        print(f"   ✅ JSONファイル読み込み成功")
        print(f"   📊 Dishes: {len(mappings['dishes']['no_exact_match_items'])} items")
        print(f"   📊 Ingredients: {len(mappings['ingredients']['no_exact_match_items'])} items")
        
        # 読み込んだ内容を表示
        if mappings['ingredients']['no_exact_match_items']:
            print("   📋 登録済み食材:")
            for item in mappings['ingredients']['no_exact_match_items']:
                print(f"      - {item}")
        
        if mappings['dishes']['no_exact_match_items']:
            print("   📋 登録済み料理:")
            for item in mappings['dishes']['no_exact_match_items']:
                print(f"      - {item}")
    except Exception as e:
        print(f"   ❌ JSONファイル読み込み失敗: {e}")
        return False
    
    # 2. プロンプト生成テスト
    print("\n2. プロンプト生成テスト:")
    try:
        niche_text = Phase1Prompts._generate_niche_mapping_text()
        print(f"   ✅ ニッチマッピングテキスト生成成功")
        print(f"   📝 テキスト長: {len(niche_text)} characters")
        
        if niche_text:
            print("   🔍 生成されたテキスト:")
            print(niche_text)
    except Exception as e:
        print(f"   ❌ ニッチマッピングテキスト生成失敗: {e}")
        return False
    
    # 3. 完全なシステムプロンプト生成テスト
    print("\n3. システムプロンプト生成テスト:")
    try:
        system_prompt = Phase1Prompts.get_system_prompt()
        print(f"   ✅ システムプロンプト生成成功")
        print(f"   📝 プロンプト長: {len(system_prompt)} characters")
        
        # ニッチマッピング情報が含まれているかチェック
        if "microgreens" in system_prompt.lower():
            print("   ✅ ニッチマッピング情報がプロンプトに含まれています")
        else:
            print("   ⚠️  ニッチマッピング情報がプロンプトに含まれていません")
    except Exception as e:
        print(f"   ❌ システムプロンプト生成失敗: {e}")
        return False
    
    print("\n🎉 すべてのテストが完了しました！")
    return True

if __name__ == "__main__":
    test_niche_food_mappings() 