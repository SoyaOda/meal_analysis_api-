#!/usr/bin/env python3
"""
test_vlm_all_images.py

test_imagesディレクトリ内の全ての画像に対してVLM（Vision Language Model）を呼び出し、
結果をJSON形式で保存するテストスクリプト。

Usage:
    PYTHONPATH=/Users/odasoya/meal_analysis_api_2 python test_scripts/test_vlm_all_images.py [--model MODEL_ID] [--images-dir IMAGES_DIR]
    
Arguments:
    --model MODEL_ID  VLMモデルID (デフォルト: 設定ファイルから取得)
    --images-dir IMAGES_DIR  画像ファイルのディレクトリ (デフォルト: test_images)
"""

import os
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
    seed: int = 123456
) -> dict:
    """
    単一の画像を処理し、VLMの結果を返す
    
    Args:
        image_path: 画像ファイルのパス
        deepinfra_service: DeepInfraServiceインスタンス
        prompt: VLMに送信するプロンプト
        temperature: AI推論のランダム性制御 (0.0-1.0)
        seed: 再現性のためのシード値
    
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
        print(f"Temperature: {temperature}, Seed: {seed}")
        
        # VLMを呼び出し (usage情報も取得)
        print(f"\nVLM呼び出し中...")
        raw_response, usage = await deepinfra_service.analyze_image(
            image_bytes=image_bytes,
            image_mime_type=mime_type,
            prompt=prompt,
            temperature=temperature,
            seed=seed,
            return_usage=True
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
            for idx, dish in enumerate(vlm_response["dishes"], 1):
                dish_name = dish.get("dish_name", "N/A")
                confidence = dish.get("confidence", 0)
                ingredients_count = len(dish.get("ingredients", []))
                analysis_method = dish.get("analysis_method", "N/A")
                print(f"  {idx}. {dish_name} (confidence: {confidence:.2f}, "
                      f"ingredients: {ingredients_count}, method: {analysis_method})")
        
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
    
    # ファイル名でソート
    image_files = sorted(set(image_files))
    
    if not image_files:
        print(f"⚠️  警告: {test_images_dir} に画像ファイルが見つかりませんでした")
        print(f"サポートされている拡張子: {', '.join(SUPPORTED_IMAGE_EXTENSIONS)}")
        sys.exit(0)
    
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
    
    # USDA用のプロンプトを生成（exclude_uncooked=False）
    print(f"\nプロンプトを生成中...")
    # food_names_list.txtを読み込み
    food_names_list_path = project_root / "test_scripts" / "food_names_list" / "food_names_list.txt"
    
    if not food_names_list_path.exists():
        print(f"❌ エラー: {food_names_list_path} が存在しません")
        sys.exit(1)
    
    with open(food_names_list_path, 'r', encoding='utf-8') as f:
        food_names_list = f.read()
    
    print(f"食品名リスト読み込み完了: {len(food_names_list):,} 文字")
    
    prompt = generate_vlm_prompt(food_names_list)
    print(f"プロンプト長: {len(prompt):,} 文字")

    # 料金情報を読み込み
    print(f"\n料金情報を読み込み中...")
    pricing_data = load_model_pricing()

    # 各画像を処理
    results = []
    total_cost = 0.0
    total_tokens = {"input": 0, "output": 0, "total": 0}

    for idx, image_path in enumerate(image_files, 1):
        print(f"\n進捗: {idx}/{len(image_files)}")
        result = await process_single_image(
            image_path=image_path,
            deepinfra_service=deepinfra_service,
            prompt=prompt,
            pricing_data=pricing_data,
            temperature=0.0,
            seed=123456
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
    
    # モデル名をファイル名に含める（スラッシュやコロンを_に置換）
    model_name_safe = deepinfra_service.model_id.replace("/", "_").replace(":", "_")
    output_file = output_dir / f"vlm_test_results_{model_name_safe}_{timestamp}.json"
    
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
