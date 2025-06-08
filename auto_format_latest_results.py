#!/usr/bin/env python3
"""
Auto Format Latest Search Results

最新の栄養検索結果を自動的に整形するスクリプト
test_local_nutrition_search_v2.py実行後に使用することを想定
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """最新の分析結果を自動的にMarkdownとHTML形式で整形する"""
    
    print("🔍 最新の栄養検索結果を整形中...")
    
    # Markdown形式で整形
    print("📝 Markdown形式で整形中...")
    result = subprocess.run([
        "python", "format_search_results.py", 
        "--latest", "--format", "markdown", "."
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Markdown形式の整形が完了しました")
        print(result.stdout.strip())
    else:
        print("❌ Markdown形式の整形でエラーが発生しました:")
        print(result.stderr)
        return False
    
    print()
    
    # HTML形式で整形
    print("🌐 HTML形式で整形中...")
    result = subprocess.run([
        "python", "format_search_results.py", 
        "--latest", "--format", "html", "."
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ HTML形式の整形が完了しました")
        print(result.stdout.strip())
    else:
        print("❌ HTML形式の整形でエラーが発生しました:")
        print(result.stderr)
        return False
    
    print()
    print("🎉 すべての整形が完了しました！")
    print("📂 整形されたファイルは nutrition_search_query/ ディレクトリ内に保存されています:")
    print("   - formatted_search_results.md (Markdown形式)")
    print("   - formatted_search_results.html (HTML形式)")
    
    return True


if __name__ == "__main__":
    main() 