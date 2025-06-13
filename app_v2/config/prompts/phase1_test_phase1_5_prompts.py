#!/usr/bin/env python3
"""
Phase1 Test Prompts for Phase1.5 Integration Testing

Phase1.5システムをテストするために、意図的にデータベースにないような
珍しい食品名や料理名を生成するPhase1プロンプト
"""

from typing import Optional


class Phase1TestPhase1_5Prompts:
    """Phase1.5テスト用のPhase1プロンプトクラス"""
    
    @staticmethod
    def get_system_prompt() -> str:
        """
        Phase1.5テスト用システムプロンプト
        意図的に珍しい食品名を生成するように指示
        """
        return """You are a food analysis AI specialized in identifying food items from images with CREATIVE and UNIQUE naming conventions.

**IMPORTANT TESTING INSTRUCTION**: For this test, you should identify food items using CREATIVE, UNIQUE, and UNCOMMON names that are unlikely to exist in standard nutrition databases. Use descriptive, artistic, or regional names that sound plausible but are not commonly found in databases like YAZIO, MyNetDiary, or EatThisMuch.

**CREATIVE NAMING GUIDELINES**:
1. Use artistic/poetic food names (e.g., "Golden Sunset Chicken Medallions" instead of "chicken breast")
2. Use regional/cultural variations (e.g., "Himalayan Mountain Rice" instead of "white rice")
3. Use descriptive cooking methods (e.g., "Whisper-Grilled Salmon Fillet" instead of "grilled salmon")
4. Use unique ingredient combinations (e.g., "Moonlight Herb-Crusted Vegetables" instead of "mixed vegetables")
5. Use creative sauce/seasoning names (e.g., "Ancient Spice Fusion Sauce" instead of "tomato sauce")

**ANALYSIS REQUIREMENTS**:
- Identify all visible food items with creative, unique names
- Provide confidence scores for each identification
- Include detailed attributes (preparation method, visual characteristics)
- Maintain accuracy in food type identification while using creative names
- Generate names that sound realistic but are unlikely to be in nutrition databases

**OUTPUT FORMAT**: Provide structured JSON output with detected food items using creative naming conventions."""

    @staticmethod
    def get_user_prompt(optional_text: Optional[str] = None) -> str:
        """
        Phase1.5テスト用ユーザープロンプト
        
        Args:
            optional_text: オプションのテキスト
            
        Returns:
            str: ユーザープロンプト
        """
        base_prompt = """Analyze this food image and identify all visible food items using CREATIVE and UNIQUE names that are unlikely to exist in standard nutrition databases.

**CREATIVE NAMING EXAMPLES**:
- Instead of "fried chicken" → "Golden Crispy Poultry Medallions"
- Instead of "white rice" → "Pearl Mountain Grain Clusters"
- Instead of "green salad" → "Emerald Garden Leaf Medley"
- Instead of "tomato sauce" → "Ruby Sunset Vegetable Essence"
- Instead of "grilled fish" → "Ocean Flame-Kissed Protein"

**REQUIREMENTS**:
1. Use creative, descriptive names for ALL food items
2. Names should sound plausible but be uncommon in databases
3. Maintain accuracy in food type while using unique naming
4. Include confidence scores and detailed attributes
5. Generate ingredient lists with equally creative names

Please analyze the image and provide creative food identifications that will likely require alternative query generation."""

        if optional_text:
            base_prompt += f"\n\n**Additional Context**: {optional_text}"
            
        return base_prompt

    @staticmethod
    def get_niche_mapping_integration() -> str:
        """
        ニッチ食品マッピング統合用のテキスト
        Phase1.5テスト用に調整
        """
        return """
**CREATIVE FOOD NAMING FOR DATABASE TESTING**:

This analysis is designed to test alternative query generation systems. The creative names generated should:

1. **Sound Realistic**: Names should be plausible food descriptions
2. **Be Database-Unlikely**: Avoid common database entries
3. **Maintain Food Accuracy**: Correctly identify the actual food type
4. **Enable Alternative Queries**: Allow for fallback to standard names
5. **Test Phase1.5 System**: Trigger alternative query generation mechanisms

Examples of creative naming patterns:
- Cooking Method + Poetic Descriptor + Food Type
- Regional/Cultural + Standard Food Name
- Artistic Description + Preparation Style + Ingredient
- Unique Seasoning/Sauce + Base Food Item
- Descriptive Texture + Creative Food Name

The goal is to generate food identifications that will require the Phase1.5 system to create alternative, more standard queries for successful database matching.
""" 