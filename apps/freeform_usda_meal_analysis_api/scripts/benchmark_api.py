#!/usr/bin/env python3
"""
Freeform USDA Meal Analysis API ベンチマークスクリプト

使用方法:
    # ローカルAPI (ポート8006)
    python -m apps.freeform_usda_meal_analysis_api.scripts.benchmark_api --url http://localhost:8006

    # 本番API
    python -m apps.freeform_usda_meal_analysis_api.scripts.benchmark_api --url https://your-api.run.app
"""

import argparse
import asyncio
import time
import statistics
import json
from pathlib import Path
from typing import List, Dict, Any
import httpx


async def analyze_image(
    client: httpx.AsyncClient,
    base_url: str,
    image_path: str,
    test_name: str
) -> Dict[str, Any]:
    """単一画像の分析を実行"""
    url = f"{base_url}/api/v1/meal-analyses/complete"

    with open(image_path, "rb") as f:
        image_data = f.read()

    start_time = time.time()

    try:
        response = await client.post(
            url,
            files={"image": (Path(image_path).name, image_data, "image/jpeg")},
            data={"user_context": f"Benchmark test: {test_name}"},
            timeout=300.0  # VLMは時間がかかるので長めに設定
        )

        end_time = time.time()
        elapsed = end_time - start_time

        if response.status_code == 200:
            result = response.json()
            dish_count = len(result.get("dishes", []))
            ingredient_count = sum(
                len(dish.get("ingredients", []))
                for dish in result.get("dishes", [])
            )
            return {
                "success": True,
                "elapsed_seconds": elapsed,
                "dish_count": dish_count,
                "ingredient_count": ingredient_count,
                "test_name": test_name,
            }
        else:
            return {
                "success": False,
                "elapsed_seconds": elapsed,
                "error": f"HTTP {response.status_code}: {response.text[:200]}",
                "test_name": test_name,
            }
    except Exception as e:
        end_time = time.time()
        return {
            "success": False,
            "elapsed_seconds": end_time - start_time,
            "error": str(e),
            "test_name": test_name,
        }


async def run_benchmark(base_url: str, image_paths: List[str], iterations: int = 3) -> Dict[str, Any]:
    """ベンチマークを実行"""
    results = {
        "base_url": base_url,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "iterations": iterations,
        "tests": []
    }

    async with httpx.AsyncClient() as client:
        # ウォームアップ（初回リクエストはコールドスタートの可能性）
        print("🔥 Warming up API...")
        health_response = await client.get(f"{base_url}/health", timeout=60.0)
        print(f"   Health check: {health_response.status_code}")

        # 各画像でベンチマーク
        for image_path in image_paths:
            image_name = Path(image_path).name
            print(f"\n📊 Benchmarking {image_name}...")

            test_results = []
            for i in range(iterations):
                print(f"   Iteration {i + 1}/{iterations}...", end=" ", flush=True)
                result = await analyze_image(
                    client, base_url, image_path, f"{image_name}_iter{i+1}"
                )
                test_results.append(result)

                if result["success"]:
                    print(f"✅ {result['elapsed_seconds']:.2f}s ({result['ingredient_count']} ingredients)")
                else:
                    print(f"❌ {result.get('error', 'Unknown error')[:50]}")

                # 連続リクエストの間に少し待機
                if i < iterations - 1:
                    await asyncio.sleep(1)

            # 統計計算
            successful_times = [r["elapsed_seconds"] for r in test_results if r["success"]]

            test_summary = {
                "image": image_name,
                "iterations": iterations,
                "success_count": len(successful_times),
                "failure_count": iterations - len(successful_times),
            }

            if successful_times:
                test_summary.update({
                    "avg_seconds": statistics.mean(successful_times),
                    "min_seconds": min(successful_times),
                    "max_seconds": max(successful_times),
                    "std_dev": statistics.stdev(successful_times) if len(successful_times) > 1 else 0,
                })

                # 最初のリクエストと2回目以降の比較（コールドスタート判定）
                if len(successful_times) >= 2:
                    test_summary["first_request_seconds"] = successful_times[0]
                    test_summary["subsequent_avg_seconds"] = statistics.mean(successful_times[1:])

            test_summary["raw_results"] = test_results
            results["tests"].append(test_summary)

    return results


def print_summary(results: Dict[str, Any]):
    """結果のサマリーを表示"""
    print("\n" + "=" * 60)
    print("📈 BENCHMARK SUMMARY")
    print("=" * 60)
    print(f"URL: {results['base_url']}")
    print(f"Time: {results['timestamp']}")
    print(f"Iterations per test: {results['iterations']}")
    print()

    for test in results["tests"]:
        print(f"📷 {test['image']}")
        print(f"   Success: {test['success_count']}/{test['iterations']}")

        if "avg_seconds" in test:
            print(f"   Average: {test['avg_seconds']:.2f}s")
            print(f"   Min/Max: {test['min_seconds']:.2f}s / {test['max_seconds']:.2f}s")

            if "first_request_seconds" in test:
                print(f"   First request: {test['first_request_seconds']:.2f}s")
                print(f"   Subsequent avg: {test['subsequent_avg_seconds']:.2f}s")
        print()

    # 全体統計
    all_times = []
    for test in results["tests"]:
        if "avg_seconds" in test:
            all_times.extend([r["elapsed_seconds"] for r in test["raw_results"] if r["success"]])

    if all_times:
        print("📊 OVERALL STATISTICS")
        print(f"   Total requests: {len(all_times)}")
        print(f"   Average: {statistics.mean(all_times):.2f}s")
        print(f"   P50: {statistics.median(all_times):.2f}s")
        sorted_times = sorted(all_times)
        p95_idx = int(len(sorted_times) * 0.95)
        print(f"   P95: {sorted_times[p95_idx] if p95_idx < len(sorted_times) else sorted_times[-1]:.2f}s")


async def main():
    parser = argparse.ArgumentParser(description="Benchmark Freeform USDA Meal Analysis API")
    parser.add_argument("--url", default="http://localhost:8006", help="API base URL")
    parser.add_argument("--iterations", type=int, default=3, help="Number of iterations per test")
    parser.add_argument("--output", help="Output JSON file path")
    parser.add_argument("--images", nargs="+", help="Specific image paths to test")
    args = parser.parse_args()

    # デフォルトのテスト画像
    if args.images:
        image_paths = args.images
    else:
        test_images_dir = Path(__file__).parent.parent.parent.parent.parent / "test_images"
        image_paths = [
            str(test_images_dir / "food1.jpg"),
            str(test_images_dir / "food2.jpg"),
            str(test_images_dir / "food3.jpg"),
        ]

    # 存在確認
    valid_paths = []
    for path in image_paths:
        if Path(path).exists():
            valid_paths.append(path)
        else:
            print(f"⚠️  Image not found: {path}")

    if not valid_paths:
        print("❌ No valid image paths found")
        return

    print(f"🚀 Starting benchmark against {args.url}")
    print(f"   Testing {len(valid_paths)} images with {args.iterations} iterations each")

    results = await run_benchmark(args.url, valid_paths, args.iterations)

    print_summary(results)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Results saved to: {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
