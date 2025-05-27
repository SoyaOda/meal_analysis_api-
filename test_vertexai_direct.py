#!/usr/bin/env python3
"""
Vertex AIの直接テスト
"""

import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/odasoya/meal_analysis_api /service-account-key.json'

import vertexai
from vertexai.generative_models import GenerativeModel

# Vertex AIの初期化
project_id = "recording-diet-ai-3e7cf"
location = "us-central1"
vertexai.init(project=project_id, location=location)

# テスト用のシステムインストラクション
system_instruction = "You are a helpful assistant."

try:
    # モデルの初期化をテスト
    print("=== GenerativeModel初期化テスト ===")
    
    # 方法1: system_instructionを文字列として渡す
    try:
        model1 = GenerativeModel(
            model_name="gemini-2.5-flash-preview-05-20",
            system_instruction=system_instruction
        )
        print("✓ 文字列として渡す: 成功")
    except Exception as e:
        print(f"✗ 文字列として渡す: エラー - {e}")
    
    # 方法2: system_instructionをリストとして渡す
    try:
        model2 = GenerativeModel(
            model_name="gemini-2.5-flash-preview-05-20",
            system_instruction=[system_instruction]
        )
        print("✓ リストとして渡す: 成功")
    except Exception as e:
        print(f"✗ リストとして渡す: エラー - {e}")
    
    # 方法3: system_instructionなしで初期化
    try:
        model3 = GenerativeModel(
            model_name="gemini-2.5-flash-preview-05-20"
        )
        print("✓ system_instructionなし: 成功")
    except Exception as e:
        print(f"✗ system_instructionなし: エラー - {e}")
        
except Exception as e:
    print(f"エラー: {e}") 