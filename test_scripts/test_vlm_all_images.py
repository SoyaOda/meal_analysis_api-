#!/usr/bin/env python
"""
test_vlm_all_images.py

test_imagesディレクトリ内の全ての画像に対してVLM（Vision Language Model）を呼び出し、
結果をJSON形式で保存するテストスクリプト。

Usage:
    # 逐次処理（従来通り）
    PYTHONPATH=/Users/odasoya/meal_analysis_api_2 python test_scripts/test_vlm_all_images.py [--model MODEL_ID] [--images-dir IMAGES_DIR]

    # 並列処理（5画像ずつ並列処理、50画像なら最大5倍高速化）
    PYTHONPATH=/Users/odasoya/meal_analysis_api_2 python test_scripts/test_vlm_all_images.py --parallel [--batch-size 5]

Arguments:
    --model MODEL_ID  VLMモデルID (デフォルト: 設定ファイルから取得)
    --images-dir IMAGES_DIR  画像ファイルのディレクトリ (デフォルト: test_images)
    --parallel  並列処理モードを有効化（デフォルト: 5画像ずつ並列処理）
    --batch-size N  並列処理時のバッチサイズ（デフォルト: 5）
"""

import sys
import json
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
import mimetypes
from typing import Dict, Any, Optional, Tuple

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.services.deepinfra_service import DeepInfraService
from shared.config import get_settings

# 最新のプロンプト生成関数をインポート
sys.path.insert(0, str(Path(__file__).parent))
from generate_complete_prompt import generate_vlm_prompt


# サポートする画像形式
SUPPORTED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}


def load_model_pricing() -> Dict[str, Any]:
    """
    モデル料金情報をJSONファイルから読み込む

    Returns:
        料金情報の辞書
    """
    pricing_file = Path(__file__).parent / "model_pricing.json"

    if pricing_file.exists():
        with open(pricing_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    # ファイルが存在しない場合はデフォルト値を返す
    return {
        "models": {},
        "default": {
            "name": "Unknown Model",
            "input_price_per_million": 0.50,
            "output_price_per_million": 0.50
        }
    }


def calculate_cost(
    model_id: str,
    input_tokens: int,
    output_tokens: int,
    pricing_data: Dict[str, Any]
) -> Tuple[float, Dict[str, Any]]:
    """
    トークン数から料金を計算

    Args:
        model_id: モデルID
        input_tokens: 入力トークン数
        output_tokens: 出力トークン数
        pricing_data: 料金情報

    Returns:
        (合計料金, 詳細情報の辞書)
    """
    # モデル固有の料金を取得、なければデフォルトを使用
    model_pricing = pricing_data.get("models", {}).get(model_id, pricing_data.get("default", {}))

    # 1Mトークンあたりの料金から計算
    input_cost = (input_tokens / 1_000_000) * model_pricing.get("input_price_per_million", 0.50)
    output_cost = (output_tokens / 1_000_000) * model_pricing.get("output_price_per_million", 0.50)
    total_cost = input_cost + output_cost

    return total_cost, {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "input_cost_usd": round(input_cost, 6),
        "output_cost_usd": round(output_cost, 6),
        "total_cost_usd": round(total_cost, 6),
        "input_price_per_million": model_pricing.get("input_price_per_million", 0.50),
        "output_price_per_million": model_pricing.get("output_price_per_million", 0.50)
    }


async def process_single_image(
    image_path: Path,
    deepinfra_service: DeepInfraService,
    prompt: str,
    pricing_data: Dict[str, Any],
    temperature: float = 0.0,
    seed: int = 123456,
    max_tokens: int = 4096,
    thinking_budget: Optional[int] = None
) -> dict:
    """
    単一の画像を処理し、VLMの結果を返す
    
    Args:
        image_path: 画像ファイルのパス
        deepinfra_service: DeepInfraServiceインスタンス
        prompt: VLMに送信するプロンプト
        temperature: AI推論のランダム性制御 (0.0-1.0)
        seed: 再現性のためのシード値
        max_tokens: 最大出力トークン数
        thinking_budget: Thinkingモデルの推論トークン数の上限（Noneで自動設定）
    
    Returns:
        dict: 処理結果（画像ファイル名、VLMレスポンス、エラー情報など）
    """
    print(f"\n{'='*80}")
    print(f"処理中: {image_path.name}")
    print(f"{'='*80}")
    
    result = {
        "image_file": image_path.name,
        "image_path": str(image_path),
        "timestamp": datetime.now().isoformat(),
        "success": False,
        "vlm_response": None,
        "error": None
    }
    
    try:
        # 画像ファイルを読み込み
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        # MIMEタイプを取得
        mime_type, _ = mimetypes.guess_type(str(image_path))
        if not mime_type:
            mime_type = "image/jpeg"  # デフォルト
        
        result["mime_type"] = mime_type
        result["image_size_bytes"] = len(image_bytes)
        
        print(f"画像サイズ: {len(image_bytes):,} bytes")
        print(f"MIMEタイプ: {mime_type}")
        print(f"Temperature: {temperature}, Seed: {seed}, Max tokens: {max_tokens}")
        if thinking_budget is not None:
            print(f"Thinking budget: {thinking_budget}")
        
        # VLMを呼び出し (usage情報も取得)
        print(f"\nVLM呼び出し中...")
        raw_response, usage = await deepinfra_service.analyze_image(
            image_bytes=image_bytes,
            image_mime_type=mime_type,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            seed=seed,
            return_usage=True,
            thinking_budget=thinking_budget
        )

        # JSONパース
        vlm_response = json.loads(raw_response)
        result["vlm_response"] = vlm_response
        result["success"] = True

        # usage情報を追加
        if usage:
            result["usage"] = usage

            # 料金計算
            _, cost_details = calculate_cost(
                deepinfra_service.model_id,
                usage.get("prompt_tokens", 0),
                usage.get("completion_tokens", 0),
                pricing_data
            )
            result["cost"] = cost_details

            print(f"\n💰 トークン数: 入力={usage.get('prompt_tokens', 0):,}, 出力={usage.get('completion_tokens', 0):,}, 合計={usage.get('total_tokens', 0):,}")
            print(f"💵 料金: ${cost_details['total_cost_usd']:.6f} (入力: ${cost_details['input_cost_usd']:.6f}, 出力: ${cost_details['output_cost_usd']:.6f})")
        
        # 結果のサマリーを表示
        print(f"\n✅ 成功!")
        if "dishes" in vlm_response:
            dishes_count = len(vlm_response["dishes"])
            print(f"検出された料理数: {dishes_count}")

            # JSONの簡潔な表示（形式に依存しない汎用的な表示）
            for idx, dish in enumerate(vlm_response["dishes"], 1):
                # 各dishを簡潔に表示（形式を問わない）
                dish_str = json.dumps(dish, ensure_ascii=False)
                # 長すぎる場合は省略
                if len(dish_str) > 150:
                    dish_preview = dish_str[:150] + "..."
                else:
                    dish_preview = dish_str
                print(f"  {idx}. {dish_preview}")
        
    except Exception as e:
        result["error"] = str(e)
        result["success"] = False
        print(f"\n❌ エラー: {e}")
    
    return result


async def main():
    """メイン処理"""
    # コマンドライン引数を解析
    parser = argparse.ArgumentParser(
        description="test_imagesディレクトリ内の全画像でVLMを呼び出し、結果をJSON形式で保存"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="使用するVLMモデルID (例: google/gemma-3-27b-it, meta-llama/Llama-3.2-90B-Vision-Instruct)"
    )
    parser.add_argument(
        "--images-dir",
        type=str,
        default=None,
        help="画像ファイルを読み込むディレクトリ (相対パスはプロジェクトルート基準)"
    )
    parser.add_argument(
        "--freeform",
        action="store_true",
        help="freeformプロンプト（食品リスト不要版）を使用する"
    )
    parser.add_argument(
        "--freeform-usda",
        action="store_true",
        help="freeform USDA形式プロンプト（main_food/extras構造）を使用する"
    )
    parser.add_argument(
        "--mapping",
        action="store_true",
        help="mappingプロンプト（統合マッピング1,398個のdisplay_name使用）を使用する"
    )
    parser.add_argument(
        "--mapping-version",
        type=str,
        default="v1",
        choices=["v1", "v2", "v3"],
        help="mappingプロンプトのバージョン (デフォルト: v1)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="処理する画像数の上限 (例: --limit 20 で最初の20枚のみ処理)"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=4096,
        help="最大出力トークン数 (デフォルト: 4096, Thinkingモデルには8192推奨)"
    )
    parser.add_argument(
        "--no-think",
        action="store_true",
        help="Thinkingモデルでthinkingを無効化（/no_thinkをプロンプトに追加）"
    )
    parser.add_argument(
        "--thinking-budget",
        type=int,
        default=None,
        help="Thinkingモデルの推論トークン数の上限 (Noneで自動設定: mapping=2048, freeform=1024)"
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="並列処理モードを有効化（デフォルト: 5画像ずつ並列処理）"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="並列処理時のバッチサイズ (デフォルト: 5)"
    )
    args = parser.parse_args()
    print(f"\n{'#'*80}")
    print(f"# VLM全画像テストスクリプト")
    print(f"{'#'*80}\n")
    
    # 画像ディレクトリのパスを決定
    if args.images_dir:
        test_images_dir = Path(args.images_dir).expanduser()
        if not test_images_dir.is_absolute():
            test_images_dir = (project_root / test_images_dir).resolve()
    else:
        test_images_dir = project_root / "test_images"

    print(f"画像ディレクトリ: {test_images_dir}")
    
    if not test_images_dir.exists():
        print(f"❌ エラー: {test_images_dir} が存在しません")
        sys.exit(1)
    
    # 画像ファイルを取得
    image_files = []
    for ext in SUPPORTED_IMAGE_EXTENSIONS:
        image_files.extend(test_images_dir.glob(f"*{ext}"))
        image_files.extend(test_images_dir.glob(f"*{ext.upper()}"))
    
    # ファイル名でソート（数値順）
    import re
    def natural_sort_key(path):
        """ファイル名の数値部分を考慮した自然順ソートキー"""
        parts = re.split(r'(\d+)', path.stem)
        return [int(part) if part.isdigit() else part.lower() for part in parts]

    image_files = sorted(set(image_files), key=natural_sort_key)

    if not image_files:
        print(f"⚠️  警告: {test_images_dir} に画像ファイルが見つかりませんでした")
        print(f"サポートされている拡張子: {', '.join(SUPPORTED_IMAGE_EXTENSIONS)}")
        sys.exit(0)

    # 画像数の制限を適用
    total_images_found = len(image_files)
    if args.limit and args.limit > 0:
        image_files = image_files[:args.limit]
        print(f"検出された画像ファイル: {total_images_found}件 (制限により{len(image_files)}件を処理)")
    else:
        print(f"検出された画像ファイル: {len(image_files)}件")
    for idx, img_file in enumerate(image_files, 1):
        print(f"  {idx}. {img_file.name}")
    
    # DeepInfraServiceを初期化
    print(f"\nDeepInfraServiceを初期化中...")
    settings = get_settings()
    
    # コマンドライン引数からモデルIDを取得（指定がない場合は設定ファイルから）
    model_id = args.model if args.model else settings.DEEPINFRA_MODEL_ID
    
    deepinfra_service = DeepInfraService(
        model_id=model_id
    )
    print(f"モデル: {deepinfra_service.model_id}")
    
    # プロンプトを生成
    print(f"\nプロンプトを生成中...")

    # モード排他チェック
    mode_flags = [args.freeform, args.freeform_usda, args.mapping]
    if sum(mode_flags) > 1:
        print(f"❌ エラー: --freeform, --freeform-usda, --mappingは同時に指定できません")
        sys.exit(1)

    if args.freeform:
        # Freeform版（食品リスト不要）
        print(f"モード: Freeform（食品リストなし）")
        # prompt_base/freeform_prompt.txtを読み込み
        freeform_prompt_path = project_root / "test_scripts" / "prompt_base" / "freeform_prompt.txt"

        if not freeform_prompt_path.exists():
            print(f"❌ エラー: {freeform_prompt_path} が存在しません")
            sys.exit(1)

        with open(freeform_prompt_path, 'r', encoding='utf-8') as f:
            prompt = f.read()
        prompt_type = "freeform"
    elif args.freeform_usda:
        # Freeform USDA形式版（main_food/extras構造）
        print(f"モード: Freeform USDA形式（main_food/extras構造）")
        # prompt_base/freeform_prompt_usda_format_ver.txtを読み込み
        freeform_usda_prompt_path = project_root / "test_scripts" / "prompt_base" / "freeform_prompt_usda_format_ver.txt"

        if not freeform_usda_prompt_path.exists():
            print(f"❌ エラー: {freeform_usda_prompt_path} が存在しません")
            sys.exit(1)

        with open(freeform_usda_prompt_path, 'r', encoding='utf-8') as f:
            prompt = f.read()
        prompt_type = "freeform_usda"
    elif args.mapping:
        # Mapping版（統合マッピングのdisplay_name使用、Role別セクション分割）
        print(f"モード: Mapping（統合マッピング1,398個のdisplay_name使用、Role別セクション分割）")
        print(f"プロンプトバージョン: {args.mapping_version}")
        # generate_mapping_promptをインポート
        from generate_mapping_prompt import load_mapping_display_names_by_role, generate_food_list_by_role, generate_vlm_prompt as generate_mapping

        try:
            by_role = load_mapping_display_names_by_role()
            total_items = sum(len(items) for items in by_role.values())
            print(f"マッピングdisplay_name読み込み完了: {total_items}個")
            print(f"  - IS_BASE: {len(by_role['is_base'])}個")
            print(f"  - INGREDIENT_ONLY: {len(by_role['ingredient_only'])}個")
            print(f"  - SAUCE_ONLY: {len(by_role['sauce_only'])}個")
            print(f"  - EITHER: {len(by_role['either'])}個")

            mapping_display_names = generate_food_list_by_role(by_role)
            prompt = generate_mapping(mapping_display_names, prompt_version=args.mapping_version)
            prompt_type = f"mapping_{args.mapping_version}"
        except FileNotFoundError as e:
            print(f"❌ エラー: {e}")
            sys.exit(1)
    else:
        # Complete版（食品リスト必要）
        print(f"モード: Complete（食品リスト使用）")
        # food_names_list.txtを読み込み
        food_names_list_path = project_root / "test_scripts" / "food_names_list" / "food_names_list.txt"

        if not food_names_list_path.exists():
            print(f"❌ エラー: {food_names_list_path} が存在しません")
            sys.exit(1)

        with open(food_names_list_path, 'r', encoding='utf-8') as f:
            food_names_list = f.read()

        print(f"食品名リスト読み込み完了: {len(food_names_list):,} 文字")
        prompt = generate_vlm_prompt(food_names_list)
        prompt_type = "complete"

    # --no-thinkフラグが指定されている場合、プロンプトの先頭に/no_thinkを追加
    if args.no_think:
        prompt = "/no_think\n\n" + prompt
        print(f"⚠️  /no_think追加: Thinkingモードを無効化")

    print(f"プロンプト長: {len(prompt):,} 文字")
    print(f"最大トークン数: {args.max_tokens}")
    if args.thinking_budget is not None:
        print(f"Thinking budget: {args.thinking_budget} (手動設定)")
    else:
        print(f"Thinking budget: 自動設定 (mapping=2048, freeform=1024)")

    # 料金情報を読み込み
    print(f"\n料金情報を読み込み中...")
    pricing_data = load_model_pricing()

    # 各画像を処理
    results = []
    total_cost = 0.0
    total_tokens = {"input": 0, "output": 0, "total": 0}

    if args.parallel:
        # 並列処理モード
        print(f"\n🚀 並列処理モード: バッチサイズ={args.batch_size}")
        print(f"{'='*80}")

        # 画像をバッチに分割
        batches = []
        for i in range(0, len(image_files), args.batch_size):
            batches.append(image_files[i:i + args.batch_size])

        print(f"バッチ数: {len(batches)}")

        # バッチごとに並列処理
        for batch_idx, batch in enumerate(batches, 1):
            print(f"\n{'='*80}")
            print(f"📦 バッチ {batch_idx}/{len(batches)} ({len(batch)}画像)")
            print(f"{'='*80}")

            # バッチ内の画像を並列処理
            batch_tasks = []
            for image_path in batch:
                task = process_single_image(
                    image_path=image_path,
                    deepinfra_service=deepinfra_service,
                    prompt=prompt,
                    pricing_data=pricing_data,
                    temperature=0.0,
                    seed=123456,
                    max_tokens=args.max_tokens,
                    thinking_budget=args.thinking_budget
                )
                batch_tasks.append(task)

            # バッチ内のタスクを並列実行
            batch_results = await asyncio.gather(*batch_tasks)

            # 結果を元の順序で追加
            results.extend(batch_results)

            # 料金とトークン数の集計
            for result in batch_results:
                if result.get("cost"):
                    total_cost += result["cost"]["total_cost_usd"]
                    total_tokens["input"] += result["cost"]["input_tokens"]
                    total_tokens["output"] += result["cost"]["output_tokens"]
                    total_tokens["total"] += result["cost"]["total_tokens"]

            print(f"\n✅ バッチ {batch_idx}/{len(batches)} 完了")
    else:
        # 逐次処理モード（従来通り）
        print(f"\n⏳ 逐次処理モード")
        for idx, image_path in enumerate(image_files, 1):
            print(f"\n進捗: {idx}/{len(image_files)}")
            result = await process_single_image(
                image_path=image_path,
                deepinfra_service=deepinfra_service,
                prompt=prompt,
                pricing_data=pricing_data,
                temperature=0.0,
                seed=123456,
                max_tokens=args.max_tokens,
                thinking_budget=args.thinking_budget
            )
            results.append(result)

            # 料金とトークン数の集計
            if result.get("cost"):
                total_cost += result["cost"]["total_cost_usd"]
                total_tokens["input"] += result["cost"]["input_tokens"]
                total_tokens["output"] += result["cost"]["output_tokens"]
                total_tokens["total"] += result["cost"]["total_tokens"]
    
    # 結果を保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = project_root / "test_scripts" / "output"
    output_dir.mkdir(exist_ok=True)
    
    # モデル名とプロンプトタイプをファイル名に含める
    model_name_safe = deepinfra_service.model_id.replace("/", "_").replace(":", "_")
    output_file = output_dir / f"vlm_test_results_{model_name_safe}_{prompt_type}_{timestamp}.json"
    
    print(f"\n{'='*80}")
    print(f"結果を保存中...")
    print(f"{'='*80}")
    
    summary = {
        "test_metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_images": len(image_files),
            "successful": sum(1 for r in results if r["success"]),
            "failed": sum(1 for r in results if not r["success"]),
            "model_id": deepinfra_service.model_id,
            "prompt_type": prompt_type,
            "temperature": 0.0,
            "seed": 123456,
            "prompt_length": len(prompt),
            "total_cost_usd": round(total_cost, 6),
            "total_tokens": total_tokens
        },
        "results": results
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n✅ 結果を保存しました: {output_file}")
    print(f"\n{'='*80}")
    print(f"サマリー:")
    print(f"  プロンプトタイプ: {prompt_type}")
    print(f"  総画像数: {summary['test_metadata']['total_images']}")
    print(f"  成功: {summary['test_metadata']['successful']}")
    print(f"  失敗: {summary['test_metadata']['failed']}")
    print(f"\n💰 料金サマリー:")
    print(f"  トークン合計: {total_tokens['total']:,}")
    print(f"    - 入力: {total_tokens['input']:,}")
    print(f"    - 出力: {total_tokens['output']:,}")
    print(f"  合計料金: ${total_cost:.6f} USD")
    print(f"  画像1枚あたり: ${(total_cost / len(image_files) if len(image_files) > 0 else 0):.6f} USD")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    asyncio.run(main())
