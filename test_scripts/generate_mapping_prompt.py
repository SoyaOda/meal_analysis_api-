#!/usr/bin/env python
"""
generate_mapping_prompt.py

統合マッピング（usda_food_mappings_unified.json）の1,398個のdisplay_nameを
食品リストとして使用するプロンプト生成スクリプト

Usage:
    python test_scripts/generate_mapping_prompt.py
    python test_scripts/generate_mapping_prompt.py --mapping-version v2
    python test_scripts/generate_mapping_prompt.py --mapping-version v3
"""

import sys
import json
import argparse
from pathlib import Path

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def load_mapping_display_names_by_role() -> dict:
    """
    統合マッピングからdisplay_nameをrole別に読み込み

    Returns:
        dict: role別のdisplay_nameリスト
    """
    mapping_path = project_root / "test_scripts" / "mappings" / "mappings_final" / "usda_food_mappings_unified.json"

    if not mapping_path.exists():
        raise FileNotFoundError(f"統合マッピングファイルが見つかりません: {mapping_path}")

    with open(mapping_path, 'r', encoding='utf-8') as f:
        mappings = json.load(f)

    # role別にdisplay_nameを分類
    by_role = {
        'is_base': [],
        'ingredient_only': [],
        'sauce_only': [],
        'either': []
    }

    for key, mapping in mappings.items():
        display_name = mapping.get('display_name', '')
        role = mapping.get('role', 'either')  # デフォルトはeither

        if display_name and role in by_role:
            by_role[role].append(display_name)

    # 各セクションをアルファベット順にソート
    for role in by_role:
        by_role[role].sort()

    return by_role


def generate_food_list_by_role(by_role: dict) -> str:
    """
    Role別セクション形式の食品リストを生成

    Args:
        by_role: role別のdisplay_nameリスト

    Returns:
        str: セクション分割された食品リスト文字列
    """
    sections = []

    # ヘッダー
    total_items = sum(len(items) for items in by_role.values())
    sections.append(f"EXACT_FOOD_LIST (CORE) - {total_items} Unified Mappings")
    sections.append("")

    # IS_BASEセクション
    sections.append(f"[IS_BASE - Base Dishes for HYBRID_DECOMPOSITION] ({len(by_role['is_base'])} items)")
    sections.append("These items are pre-defined dishes that should be used as base_food in HYBRID_DECOMPOSITION method.")
    sections.append("Examples: 'Caesar salad', 'Mac and cheese', 'Pasta with Tomato Sauce'")
    sections.append("")
    for idx, name in enumerate(by_role['is_base'], 1):
        sections.append(f"{idx}. {name}")
    sections.append("")

    # INGREDIENT_ONLYセクション
    sections.append(f"[INGREDIENT_ONLY - Raw Ingredients] ({len(by_role['ingredient_only'])} items)")
    sections.append("These items are raw ingredients and can ONLY be used in ingredients array, NEVER as base_food.")
    sections.append("Examples: 'Cooking oil', 'Wheat flour', 'Lettuce', 'Tomato'")
    sections.append("")
    for idx, name in enumerate(by_role['ingredient_only'], 1):
        sections.append(f"{idx}. {name}")
    sections.append("")

    # SAUCE_ONLYセクション
    sections.append(f"[SAUCE_ONLY - Sauces and Condiments] ({len(by_role['sauce_only'])} items)")
    sections.append("These items are sauces/condiments and can ONLY be used in ingredients array, NEVER as base_food.")
    sections.append("Examples: 'Caesar dressing', 'Ketchup', 'BBQ sauce', 'Ranch dressing'")
    sections.append("")
    for idx, name in enumerate(by_role['sauce_only'], 1):
        sections.append(f"{idx}. {name}")
    sections.append("")

    # EITHERセクション
    sections.append(f"[EITHER - Flexible Usage] ({len(by_role['either'])} items)")
    sections.append("These items can be used either as base_food or in ingredients array depending on context.")
    sections.append("Examples: 'Chicken thigh', 'Mashed potatoes', 'Rice', 'Apple'")
    sections.append("")
    for idx, name in enumerate(by_role['either'], 1):
        sections.append(f"{idx}. {name}")
    sections.append("")

    return '\n'.join(sections)


def generate_vlm_prompt(food_names_list: str, prompt_version: str = "v1") -> str:
    """
    VLMに送信するプロンプトを生成（マッピングdisplay_nameを埋め込み）

    Args:
        food_names_list: 食品名リストの文字列
        prompt_version: プロンプトバージョン (v1, v2, v3)

    Returns:
        str: 完全なプロンプト
    """
    # プロンプトベースファイルを読み込み
    prompt_base_path = project_root / "test_scripts" / "prompt_base" / f"mapping_prompt_{prompt_version}.txt"

    if not prompt_base_path.exists():
        raise FileNotFoundError(f"プロンプトベースファイルが見つかりません: {prompt_base_path}")

    with open(prompt_base_path, 'r', encoding='utf-8') as f:
        prompt_template = f.read()

    return prompt_template.replace("<<FOOD_NAMES_LIST>>", food_names_list)


def main():
    """メイン処理"""
    # コマンドライン引数をパース
    parser = argparse.ArgumentParser(
        description="統合マッピング版プロンプト生成スクリプト（Role別セクション分割）"
    )
    parser.add_argument(
        "--mapping-version",
        type=str,
        default="v1",
        choices=["v1", "v2", "v3"],
        help="mappingプロンプトのバージョン (デフォルト: v1)"
    )
    args = parser.parse_args()

    print("=" * 80)
    print(f"統合マッピング版プロンプト生成スクリプト（Role別セクション分割）- {args.mapping_version}")
    print("=" * 80)
    print()

    # 統合マッピングからdisplay_nameをrole別に読み込み
    mapping_path = project_root / "test_scripts" / "mappings" / "mappings_final" / "usda_food_mappings_unified.json"

    print(f"統合マッピングを読み込み中: {mapping_path}")

    try:
        by_role = load_mapping_display_names_by_role()

        # 統計情報
        total_items = sum(len(items) for items in by_role.values())
        print(f"✅ マッピング読み込み完了: {total_items}個のdisplay_name")
        print(f"   - IS_BASE: {len(by_role['is_base'])}個")
        print(f"   - INGREDIENT_ONLY: {len(by_role['ingredient_only'])}個")
        print(f"   - SAUCE_ONLY: {len(by_role['sauce_only'])}個")
        print(f"   - EITHER: {len(by_role['either'])}個")
        print()

        # Role別セクション形式の食品リストを生成
        food_names_list = generate_food_list_by_role(by_role)
        print(f"   文字数: {len(food_names_list):,} 文字")
        print()

    except FileNotFoundError as e:
        print(f"❌ エラー: {e}")
        sys.exit(1)

    # プロンプト生成
    print(f"プロンプトを生成中... (version: {args.mapping_version})")
    prompt = generate_vlm_prompt(food_names_list, prompt_version=args.mapping_version)
    print(f"✅ プロンプト生成完了: {len(prompt):,} 文字")
    print()

    # 保存先
    output_dir = project_root / "test_scripts" / "output"
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / f"mapping_prompt_{args.mapping_version}.txt"

    # ファイルに保存
    print(f"プロンプトを保存中: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(prompt)

    print(f"✅ 保存完了!")
    print()
    print("=" * 80)
    print(f"統合マッピング版プロンプト ({args.mapping_version}): {output_file}")
    print(f"文字数: {len(prompt):,}")
    print(f"行数: {len(prompt.splitlines()):,}")
    print(f"マッピング数: {total_items}個")
    print(f"  - IS_BASE: {len(by_role['is_base'])}個")
    print(f"  - INGREDIENT_ONLY: {len(by_role['ingredient_only'])}個")
    print(f"  - SAUCE_ONLY: {len(by_role['sauce_only'])}個")
    print(f"  - EITHER: {len(by_role['either'])}個")
    print("=" * 80)


if __name__ == "__main__":
    main()
