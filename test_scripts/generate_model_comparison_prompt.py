#!/usr/bin/env python3
"""
VLMモデル比較用プロンプト生成スクリプト
栄養算出のための食品認識と量推定の精度を比較するためのデータを提供
"""
import json
import argparse
from pathlib import Path

# モデルファイルと使用プロンプト
# デフォルト: mapping v2/v3比較
MODELS_MAPPING = {
    "235B-Thinking-v2": {
        "file": "/Users/odasoya/meal_analysis_api_2/test_scripts/output/vlm_test_results_Qwen_Qwen3-VL-235B-A22B-Thinking_mapping_v2_20251024_182831.json",
        "prompt_file": "mapping_prompt_v2.txt"
    },
    "235B-Thinking-v3": {
        "file": "/Users/odasoya/meal_analysis_api_2/test_scripts/output/vlm_test_results_Qwen_Qwen3-VL-235B-A22B-Thinking_mapping_v3_20251024_183333.json",
        "prompt_file": "mapping_prompt_v3.txt"
    },
    "30B-Thinking-v2": {
        "file": "/Users/odasoya/meal_analysis_api_2/test_scripts/output/vlm_test_results_Qwen_Qwen3-VL-30B-A3B-Thinking_mapping_v2_20251024_183843.json",
        "prompt_file": "mapping_prompt_v2.txt"
    },
    "30B-Thinking-v3": {
        "file": "/Users/odasoya/meal_analysis_api_2/test_scripts/output/vlm_test_results_Qwen_Qwen3-VL-30B-A3B-Thinking_mapping_v3_20251024_184520.json",
        "prompt_file": "mapping_prompt_v3.txt"
    }
}

# freeform_usda比較用（freeform_usda + mapping_v3）
MODELS_FREEFORM_USDA = {
    "235B-Thinking-freeform-usda": {
        "file": "/Users/odasoya/meal_analysis_api_2/test_scripts/output/vlm_test_results_Qwen_Qwen3-VL-235B-A22B-Thinking_freeform_usda_20251025_110445.json",
        "prompt_file": "freeform_prompt_usda_format_ver.txt"
    },
    "30B-Thinking-freeform-usda": {
        "file": "/Users/odasoya/meal_analysis_api_2/test_scripts/output/vlm_test_results_Qwen_Qwen3-VL-30B-A3B-Thinking_freeform_usda_20251025_110520.json",
        "prompt_file": "freeform_prompt_usda_format_ver.txt"
    },
    "235B-Thinking-mapping-v3": {
        "file": "/Users/odasoya/meal_analysis_api_2/test_scripts/output/vlm_test_results_Qwen_Qwen3-VL-235B-A22B-Thinking_mapping_v3_20251024_183333.json",
        "prompt_file": "mapping_prompt_v3.txt"
    },
    "30B-Thinking-mapping-v3": {
        "file": "/Users/odasoya/meal_analysis_api_2/test_scripts/output/vlm_test_results_Qwen_Qwen3-VL-30B-A3B-Thinking_mapping_v3_20251024_184520.json",
        "prompt_file": "mapping_prompt_v3.txt"
    }
}

# デフォルトはmapping比較
MODELS = MODELS_MAPPING

def load_model_results(file_path: str) -> dict:
    """モデル結果を読み込み"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    if 'results' in data:
        return {r['image_file']: r for r in data['results']}
    return data

def get_total_weight(dishes):
    """料理の総重量を計算（v1/v2/v3/freeform_usdaスキーマ対応）"""
    total = 0
    for dish in dishes:
        # v1スキーマ（base_food/ingredients）
        if dish.get('base_food'):
            total += dish['base_food'].get('weight_g', 0)
        if dish.get('ingredients'):
            for ing in dish.get('ingredients', []):
                total += ing.get('weight_g', 0)

        # v2/v3スキーマ（items配列）
        if dish.get('items'):
            for item in dish['items']:
                total += item.get('weight_g', 0)

        # freeform_usdaスキーマ（main_food/extras）
        if dish.get('main_food'):
            total += dish['main_food'].get('weight_g', 0)
        if dish.get('extras'):
            for extra in dish.get('extras', []):
                total += extra.get('weight_g', 0)
    return total

def format_dish_json(dish, indent=2):
    """料理情報を見やすいJSON形式で整形（v1/v2/v3/freeform_usdaスキーマ対応）"""
    lines = []
    spaces = " " * indent

    lines.append(f'{spaces}{{')
    lines.append(f'{spaces}  "dish_name": "{dish.get("dish_name", "")}"')

    # analysis_methodがあれば表示（v2/v3）
    if dish.get('analysis_method'):
        lines.append(f'{spaces}  "analysis_method": "{dish.get("analysis_method")}"')

    # v2/v3スキーマ（items配列）
    if dish.get('items'):
        lines.append(f'{spaces}  "items": [')
        for i, item in enumerate(dish['items']):
            comma = "," if i < len(dish['items']) - 1 else ""
            role = item.get('role', 'N/A')
            item_name = item.get('item_name', '')
            weight_g = item.get('weight_g', 0)
            found = item.get('found_in_list', False)
            lines.append(f'{spaces}    {{"role": "{role}", "item_name": "{item_name}", "weight_g": {weight_g}, "found_in_list": {str(found).lower()}}}{comma}')
        lines.append(f'{spaces}  ]')

    # freeform_usdaスキーマ（main_food/extras）
    elif dish.get('main_food') is not None or dish.get('extras'):
        if dish.get('main_food'):
            main = dish['main_food']
            # search_nameとdescriptionがあればそれを使用、なければitem_name
            search_name = main.get('search_name', main.get('item_name', ''))
            desc = main.get('description', '')
            weight_g = main.get('weight_g', 0)
            if desc:
                lines.append(f'{spaces}  "main_food": {{"search_name": "{search_name}", "description": "{desc}", "weight_g": {weight_g}}}')
            else:
                lines.append(f'{spaces}  "main_food": {{"search_name": "{search_name}", "weight_g": {weight_g}}}')
        else:
            lines.append(f'{spaces}  "main_food": null')

        if dish.get('extras'):
            lines.append(f'{spaces}  "extras": [')
            for i, extra in enumerate(dish['extras']):
                comma = "," if i < len(dish['extras']) - 1 else ""
                search_name = extra.get('search_name', extra.get('item_name', ''))
                desc = extra.get('description', '')
                weight_g = extra.get('weight_g', 0)
                if desc:
                    lines.append(f'{spaces}    {{"search_name": "{search_name}", "description": "{desc}", "weight_g": {weight_g}}}{comma}')
                else:
                    lines.append(f'{spaces}    {{"search_name": "{search_name}", "weight_g": {weight_g}}}{comma}')
            lines.append(f'{spaces}  ]')

    # v1スキーマ（base_food/ingredients）
    else:
        if dish.get('base_food'):
            base = dish['base_food']
            lines.append(f'{spaces}  "base_food": {{"item_name": "{base["item_name"]}", "weight_g": {base["weight_g"]}}}')

        if dish.get('ingredients'):
            lines.append(f'{spaces}  "ingredients": [')
            for i, ing in enumerate(dish['ingredients']):
                comma = "," if i < len(dish['ingredients']) - 1 else ""
                lines.append(f'{spaces}    {{"item_name": "{ing["item_name"]}", "weight_g": {ing["weight_g"]}}}{comma}')
            lines.append(f'{spaces}  ]')

    lines.append(f'{spaces}}}')
    return '\n'.join(lines)

def generate_header(comparison_type="mapping"):
    """ヘッダーを生成

    Args:
        comparison_type: "mapping" または "freeform_usda"
    """
    # 各モデルが使用したプロンプトを読み込み
    output_dir = Path(__file__).parent / "output"
    prompt_base_dir = Path(__file__).parent / "prompt_base"
    
    # プロンプトファイルごとにグループ化（重複を避けるため）
    prompt_file_to_models = {}
    
    for model_name, model_info in MODELS.items():
        prompt_file_name = model_info["prompt_file"]
        if prompt_file_name not in prompt_file_to_models:
            prompt_file_to_models[prompt_file_name] = []
        prompt_file_to_models[prompt_file_name].append(model_name)
    
    # プロンプトファイルごとに読み込み
    prompts_loaded = {}
    for prompt_file_name in prompt_file_to_models.keys():
        # まずoutputディレクトリを確認、なければprompt_baseを確認
        prompt_file = output_dir / prompt_file_name
        if not prompt_file.exists():
            prompt_file = prompt_base_dir / prompt_file_name

        if prompt_file.exists():
            with open(prompt_file, 'r', encoding='utf-8') as f:
                # プロンプト全体を読み込み
                prompts_loaded[prompt_file_name] = f.read()
        else:
            prompts_loaded[prompt_file_name] = "(プロンプトファイルが見つかりません)"

    # プロンプトセクションを生成（ファイルごとに1回のみ）
    prompt_sections = []
    for prompt_file_name, prompt_content in prompts_loaded.items():
        models_using_this = prompt_file_to_models[prompt_file_name]
        models_text = "、".join([f"**{m}**" for m in models_using_this])
        prompt_sections.append(f"### {prompt_file_name}\n\n使用モデル: {models_text}\n\n```\n{prompt_content}\n```\n")

    prompts_text = '\n'.join(prompt_sections)

    if comparison_type == "freeform_usda":
        # freeform_usda比較用のヘッダー
        model_list = "\n".join([f"{i+1}. **{name}** - {info['prompt_file']}使用"
                                for i, (name, info) in enumerate(MODELS.items())])

        return f"""# Vision Language Model (VLM) 比較データ - Freeform USDA Format vs Mapping v3

## 目的

Freeform USDA形式プロンプト(main_food/extras構造)とMapping v3プロンプト(items配列構造)を用いて各VLMモデルに食事写真を分析させた結果を共有します。
食事写真(別途添付する)と各モデルの出力を比較し、プロンプト形式による違いとモデルごとの精度を評価してください。

## 評価対象モデルと使用プロンプト

{model_list}

## 使用したプロンプト

{prompts_text}

---

"""
    else:
        # mapping比較用のヘッダー(従来通り)
        model_list = "\n".join([f"{i+1}. **{name}** - {info['prompt_file']}使用"
                                for i, (name, info) in enumerate(MODELS.items())])

        return f"""# Vision Language Model (VLM) 比較データ - Mapping Prompt v2/v3

## 目的

Mapping prompt(v2とv3)を用いて各VLMモデルに食事写真を分析させた結果を共有します。
食事写真(別途添付する)と各モデルの出力を比較し、モデルごとに栄養算出に必要な食品認識と量推定の精度を評価してください。

## 評価対象モデルと使用プロンプト

{model_list}

## 使用したプロンプト

{prompts_text}

---

"""

def generate_image_section(image_num, model_results):
    """画像セクションを生成"""
    lines = []

    lines.append(f"## 📸 画像{image_num}\n")

    # 各モデルの結果
    for model_name, model_data in model_results.items():
        if not model_data or not model_data.get('success'):
            lines.append(f"### {model_name}")
            lines.append("```json")
            lines.append('{"error": "モデル実行失敗"}')
            lines.append("```\n")
            continue

        model_dishes = model_data['vlm_response'].get('dishes', [])

        lines.append(f"### {model_name}")
        lines.append("```json")
        lines.append("{")
        lines.append('  "dishes": [')
        for i, dish in enumerate(model_dishes):
            comma = "," if i < len(model_dishes) - 1 else ""
            lines.append(format_dish_json(dish, indent=4) + comma)
        lines.append("  ]")
        lines.append("}")
        lines.append("```\n")

    lines.append("---\n")
    return '\n'.join(lines)

def generate_prompt_file(start_image, end_image, output_file=None, comparison_type="mapping"):
    """プロンプトファイルを生成

    Args:
        start_image: 開始画像番号
        end_image: 終了画像番号
        output_file: 出力ファイルパス (Noneで自動生成)
        comparison_type: "mapping" または "freeform_usda"
    """
    print(f"📝 画像{start_image}-{end_image}の比較データを生成中...")
    print(f"比較タイプ: {comparison_type}")

    # 出力ファイル名を自動生成
    if output_file is None:
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"model_comparison_{comparison_type}_{start_image}_{end_image}_{timestamp}.md"

    # モデル結果を読み込み
    all_results = {}
    for model_name, model_info in MODELS.items():
        file_path = model_info["file"]
        all_results[model_name] = load_model_results(file_path)

    # ファイル生成
    content = []
    content.append(generate_header(comparison_type=comparison_type))
    content.append(f"# 📸 画像{start_image}-{end_image}のデータ\n")
    content.append("---\n")

    # 各画像のセクションを生成
    for i in range(start_image, end_image + 1):
        image_name = f"test_food{i}.jpg"  # 結果JSON内のファイル名

        model_results = {}
        for model_name in MODELS.keys():
            model_results[model_name] = all_results[model_name].get(image_name)

        content.append(generate_image_section(i, model_results))

    # ファイル保存
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content))

    print(f"✅ 保存完了: {output_file}")

def main():
    global MODELS  # グローバル変数を参照

    parser = argparse.ArgumentParser(
        description='VLMモデル比較用プロンプト生成',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # mapping v2/v3比較（デフォルト）
  python generate_model_comparison_prompt.py --start 1 --end 5

  # freeform_usda比較
  python generate_model_comparison_prompt.py --start 1 --end 5 --type freeform_usda

  # 出力先を指定する場合
  python generate_model_comparison_prompt.py --start 1 --end 10 --output /tmp/comparison.md
        """
    )

    parser.add_argument('--start', type=int, required=True,
                        help='開始画像番号 (例: 1)')
    parser.add_argument('--end', type=int, required=True,
                        help='終了画像番号 (例: 10)')
    parser.add_argument('--type', type=str, default='mapping',
                        choices=['mapping', 'freeform_usda'],
                        help='比較タイプ: mapping (v2/v3) または freeform_usda (デフォルト: mapping)')
    parser.add_argument('--output', type=str, required=False, default=None,
                        help='出力ファイルパス (省略時は test_scripts/output に自動保存)')

    args = parser.parse_args()

    # バリデーション
    if args.start < 1 or args.end < args.start:
        print("❌ エラー: 無効な画像範囲です")
        return

    # 比較タイプに応じてMODELSを設定
    if args.type == 'freeform_usda':
        MODELS = MODELS_FREEFORM_USDA
    else:
        MODELS = MODELS_MAPPING

    print("="*80)
    print("🤖 VLMモデル比較プロンプト生成スクリプト")
    print(f"比較タイプ: {args.type}")
    print("="*80)
    print()

    generate_prompt_file(args.start, args.end, args.output, comparison_type=args.type)

    print()
    print("="*80)
    print("✅ 完了")
    print("="*80)

if __name__ == "__main__":
    main()
