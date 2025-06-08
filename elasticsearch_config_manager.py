#!/usr/bin/env python3
"""
Elasticsearch設定管理ツール

検索パラメータの動的変更、確認、実験用プリセット適用などを行う
"""

import os
import sys
from typing import Dict, Any
from app_v2.elasticsearch.config import es_config

class ElasticsearchConfigManager:
    """Elasticsearch設定管理クラス"""
    
    def __init__(self):
        self.config = es_config
    
    def show_current_config(self):
        """現在の設定を表示"""
        print("🔍 現在のElasticsearch検索設定")
        print("=" * 60)
        
        print("\n📡 接続設定:")
        print(f"  Host: {self.config.host}:{self.config.port}")
        print(f"  Index: {self.config.food_nutrition_index}")
        
        print("\n🎯 Function Score設定:")
        print(f"  人気度ブースト: {self.config.enable_popularity_boost} (重み: {self.config.popularity_boost_weight})")
        print(f"  栄養類似性: {self.config.enable_nutritional_similarity} (重み: {self.config.nutritional_similarity_weight})")
        print(f"  セマンティック類似性: {self.config.enable_semantic_similarity} (重み: {self.config.semantic_similarity_weight})")
        
        print("\n🥗 栄養素重み設定:")
        nutrition_weights = self.config.get_nutrition_weights()
        for nutrient, weight in nutrition_weights.items():
            print(f"  {nutrient}: {weight}")
        
        print("\n📏 正規化係数:")
        norm_factors = self.config.get_nutrition_normalization_factors()
        for nutrient, factor in norm_factors.items():
            print(f"  {nutrient}: {factor}")
        
        print("\n🔍 フィールドブースト:")
        field_boosts = self.config.get_field_boosts()
        for field, boost in field_boosts.items():
            print(f"  {field}: {boost}")
        
        print(f"\n🔤 フレーズマッチブースト: {self.config.phrase_match_boost}")
    
    def apply_preset(self, preset_name: str):
        """実験用プリセットを適用"""
        presets = {
            "lexical_only": {
                "description": "純粋語彙的検索（現在の最適設定）",
                "settings": {
                    "enable_popularity_boost": False,
                    "popularity_boost_weight": 0.0,
                    "enable_nutritional_similarity": False,
                    "nutritional_similarity_weight": 0.0,
                    "nutrition_weight_calories": 0.1,
                    "nutrition_weight_protein": 0.1,
                    "nutrition_weight_fat": 0.1,
                    "nutrition_weight_carbs": 0.1
                }
            },
            "popularity_focused": {
                "description": "人気度重視実験",
                "settings": {
                    "enable_popularity_boost": True,
                    "popularity_boost_weight": 0.5,
                    "enable_nutritional_similarity": False,
                    "nutritional_similarity_weight": 0.0,
                }
            },
            "nutrition_focused": {
                "description": "栄養プロファイル重視実験",
                "settings": {
                    "enable_popularity_boost": False,
                    "popularity_boost_weight": 0.0,
                    "enable_nutritional_similarity": True,
                    "nutritional_similarity_weight": 2.5,
                    "nutrition_weight_calories": 0.25,
                    "nutrition_weight_protein": 0.25,
                    "nutrition_weight_fat": 0.25,
                    "nutrition_weight_carbs": 0.25
                }
            },
            "balanced": {
                "description": "バランス重視実験",
                "settings": {
                    "enable_popularity_boost": True,
                    "popularity_boost_weight": 0.3,
                    "enable_nutritional_similarity": True,
                    "nutritional_similarity_weight": 1.0,
                    "nutrition_weight_calories": 0.15,
                    "nutrition_weight_protein": 0.15,
                    "nutrition_weight_fat": 0.15,
                    "nutrition_weight_carbs": 0.15
                }
            }
        }
        
        if preset_name not in presets:
            print(f"❌ 未知のプリセット: {preset_name}")
            print(f"利用可能なプリセット: {', '.join(presets.keys())}")
            return False
        
        preset = presets[preset_name]
        print(f"🎯 プリセット適用: {preset_name}")
        print(f"📝 説明: {preset['description']}")
        
        # 設定を動的に更新（注意：これは一時的な変更）
        for attr_name, value in preset['settings'].items():
            if hasattr(self.config, attr_name):
                setattr(self.config, attr_name, value)
                print(f"  ✅ {attr_name} = {value}")
            else:
                print(f"  ⚠️ 未知の設定: {attr_name}")
        
        print("\n⚠️ 注意: この変更は一時的です。永続化するには .env ファイルを編集してください。")
        return True
    
    def list_presets(self):
        """利用可能なプリセット一覧を表示"""
        print("📋 利用可能な実験用プリセット:")
        print("=" * 50)
        print("1. lexical_only    - 純粋語彙的検索（現在の最適設定）")
        print("2. popularity_focused - 人気度重視実験")
        print("3. nutrition_focused  - 栄養プロファイル重視実験")
        print("4. balanced          - バランス重視実験")
    
    def run_quick_test(self):
        """設定変更後の簡単なテスト実行"""
        print("\n🧪 設定変更後のクイックテスト実行...")
        try:
            import subprocess
            result = subprocess.run(
                ["python", "test_local_nutrition_search_v2.py"], 
                capture_output=True, text=True, timeout=60
            )
            
            if result.returncode == 0:
                print("✅ テスト成功！")
                # 主要な結果を抽出
                if "Analysis ID:" in result.stdout:
                    analysis_id = result.stdout.split("Analysis ID: ")[1].split("\n")[0]
                    print(f"📋 分析ID: {analysis_id}")
                
                if "Match rate:" in result.stdout:
                    match_rate_line = [line for line in result.stdout.split("\n") if "Match rate:" in line][0]
                    print(f"📊 {match_rate_line.strip()}")
            else:
                print(f"❌ テスト失敗: {result.stderr}")
                
        except Exception as e:
            print(f"❌ テスト実行エラー: {e}")
    
    def generate_env_config(self, preset_name: str = None):
        """現在の設定または指定プリセットの .env 設定を生成"""
        if preset_name:
            if not self.apply_preset(preset_name):
                return
        
        print(f"\n📄 .env ファイル用設定 ({preset_name or '現在の設定'}):")
        print("=" * 60)
        
        env_lines = [
            f"ELASTICSEARCH_ENABLE_POPULARITY_BOOST={str(self.config.enable_popularity_boost).lower()}",
            f"ELASTICSEARCH_POPULARITY_BOOST_WEIGHT={self.config.popularity_boost_weight}",
            f"ELASTICSEARCH_ENABLE_NUTRITIONAL_SIMILARITY={str(self.config.enable_nutritional_similarity).lower()}",
            f"ELASTICSEARCH_NUTRITIONAL_SIMILARITY_WEIGHT={self.config.nutritional_similarity_weight}",
            f"ELASTICSEARCH_NUTRITION_WEIGHT_CALORIES={self.config.nutrition_weight_calories}",
            f"ELASTICSEARCH_NUTRITION_WEIGHT_PROTEIN={self.config.nutrition_weight_protein}",
            f"ELASTICSEARCH_NUTRITION_WEIGHT_FAT={self.config.nutrition_weight_fat}",
            f"ELASTICSEARCH_NUTRITION_WEIGHT_CARBS={self.config.nutrition_weight_carbs}",
        ]
        
        for line in env_lines:
            print(line)

def main():
    """メイン関数"""
    if len(sys.argv) < 2:
        print("🔧 Elasticsearch設定管理ツール")
        print("=" * 50)
        print("使用方法:")
        print("  python elasticsearch_config_manager.py show              - 現在の設定を表示")
        print("  python elasticsearch_config_manager.py presets           - プリセット一覧を表示")
        print("  python elasticsearch_config_manager.py apply <preset>    - プリセットを適用")
        print("  python elasticsearch_config_manager.py test              - クイックテスト実行")
        print("  python elasticsearch_config_manager.py env [preset]      - .env設定を生成")
        print()
        print("例:")
        print("  python elasticsearch_config_manager.py apply lexical_only")
        print("  python elasticsearch_config_manager.py env nutrition_focused")
        return
    
    manager = ElasticsearchConfigManager()
    command = sys.argv[1]
    
    if command == "show":
        manager.show_current_config()
    elif command == "presets":
        manager.list_presets()
    elif command == "apply" and len(sys.argv) >= 3:
        preset_name = sys.argv[2]
        if manager.apply_preset(preset_name):
            print(f"\n🧪 テストを実行しますか？ (y/n): ", end="")
            if input().lower() == 'y':
                manager.run_quick_test()
    elif command == "test":
        manager.run_quick_test()
    elif command == "env":
        preset_name = sys.argv[2] if len(sys.argv) >= 3 else None
        manager.generate_env_config(preset_name)
    else:
        print(f"❌ 未知のコマンド: {command}")

if __name__ == "__main__":
    main() 