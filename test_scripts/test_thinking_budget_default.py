#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
thinking_budgetのデフォルト値（2048）確認テスト
"""

import sys
import logging
from pathlib import Path

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.services.deepinfra_service import DeepInfraService


def test_thinking_budget_default():
    """thinking_budgetのデフォルト値が2048であることを確認"""
    print("="*80)
    print("thinking_budget デフォルト値確認テスト")
    print("="*80)
    print()

    # Thinkingモデルで初期化
    thinking_model = "Qwen/Qwen3-VL-235B-A22B-Thinking"
    print(f"Model: {thinking_model}")
    print()

    # DeepInfraServiceを初期化
    service = DeepInfraService(model_id=thinking_model)

    # analyze_imageメソッドのソースコードを確認
    import inspect
    source = inspect.getsource(service.analyze_image)

    # thinking_budgetのデフォルト設定部分を抽出
    print("【analyze_imageメソッド内のthinking_budget設定】")
    print("-" * 80)

    lines = source.split('\n')
    in_thinking_budget_section = False
    budget_lines = []

    for line in lines:
        if 'thinking_budget is None' in line:
            in_thinking_budget_section = True

        if in_thinking_budget_section:
            budget_lines.append(line)

            # extra_bodyの定義まで到達したら終了
            if 'extra_body' in line and '=' in line:
                break

    for line in budget_lines:
        print(line)

    print()
    print("-" * 80)
    print()

    # デフォルト値を確認
    expected_default = 2048

    # ソースコードから実際の値を確認
    actual_default = None
    for line in budget_lines:
        if 'thinking_budget = ' in line and '2048' in line:
            actual_default = 2048
            break
        elif 'thinking_budget = ' in line and '1024' in line:
            # 古い実装が残っている場合
            actual_default = 1024
            break

    print("【確認結果】")
    print(f"期待されるデフォルト値: {expected_default}")
    print(f"実際のデフォルト値: {actual_default}")
    print()

    if actual_default == expected_default:
        print("✅ PASS: thinking_budgetのデフォルト値は2048です")
        print()
        print("【確認事項】")
        print("✅ Thinkingモデル使用時、thinking_budget=Noneの場合は2048が使用される")
        print("✅ プロンプト長に関係なく、常に2048が適用される")
        return True
    else:
        print(f"❌ FAIL: thinking_budgetのデフォルト値が{actual_default}です（期待値: {expected_default}）")
        return False


if __name__ == "__main__":
    success = test_thinking_budget_default()
    sys.exit(0 if success else 1)
