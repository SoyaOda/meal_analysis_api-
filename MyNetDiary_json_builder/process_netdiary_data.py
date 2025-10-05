#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MyNetDiaryデータをJSON形式に変換するスクリプト
"""

import os
import json
import re
from pathlib import Path

def extract_nutrition_data(text_content, filename, file_path=""):
    """
    テキストファイルからnutrition情報を抽出する
    Enhanced版：カテゴリーとserving情報も抽出
    """
    data = {}
    
    # ファイル名から拡張子を除去
    file_base_name = filename.replace('.txt', '')
    
    # カテゴリー情報をファイルパスから抽出
    category = ""
    if file_path:
        # "MyNetDiary/Staple Foods/Beans & Peas" -> "Beans & Peas"
        path_parts = file_path.split('/')
        # Staple Foods配下のカテゴリを抽出
        if len(path_parts) >= 3 and 'Staple Foods' in path_parts:
            try:
                staple_idx = path_parts.index('Staple Foods')
                if staple_idx + 1 < len(path_parts):
                    category = path_parts[staple_idx + 1]
            except (ValueError, IndexError):
                category = ""
        else:
            # Staple Foods以外の場合は最後のディレクトリ名を使用
            for i, part in enumerate(path_parts):
                if part == 'MyNetDiary' and i + 1 < len(path_parts):
                    category = path_parts[i + 1]
                    break
    
    # テキスト内の食品名を抽出（カンマを含む数字にも対応）
    name_match = re.search(r'Food Entry\s+(.+?)\s+[\d,]+\s+cals', text_content)
    text_name = name_match.group(1).strip() if name_match else ""
    
    # 名前の確認
    data['name'] = text_name
    data['name_matches_filename'] = (text_name == file_base_name)
    data['category'] = category
    
    # Serving情報を抽出 "Serving Size cup (254g)" -> unit: "cup", grams: 254
    serving_unit = ""
    serving_grams = 0.0
    
    serving_match = re.search(r'Serving Size\s+(.+?)\s+\((\d+)g\)', text_content)
    if serving_match:
        serving_unit = serving_match.group(1).strip()
        serving_grams = float(serving_match.group(2))
    
    data['serving'] = {
        'unit': serving_unit,
        'grams': serving_grams
    }
    
    # カロリーを抽出（カンマを含む数字にも対応）
    calories_match = re.search(r'Calories\s+([\d,]+)cals', text_content)
    if calories_match:
        calories_str = calories_match.group(1).replace(',', '')  # カンマを除去
        calories = float(calories_str)
    else:
        calories = 0.0
    
    # プロテインを抽出
    protein_match = re.search(r'Protein\s+(\d+(?:\.\d+)?)g', text_content)
    protein = float(protein_match.group(1)) if protein_match else 0.0
    
    # 脂肪を抽出
    fat_match = re.search(r'Total Fat\s+(\d+(?:\.\d+)?)g', text_content)
    fat = float(fat_match.group(1)) if fat_match else 0.0
    
    # 炭水化物を抽出
    carbs_match = re.search(r'Total Carbs\s+(\d+(?:\.\d+)?)g', text_content)
    carbs = float(carbs_match.group(1)) if carbs_match else 0.0
    
    # 重量を抽出
    weight_match = re.search(r'Weight\s+(\d+)g', text_content)
    weight_g = float(weight_match.group(1)) if weight_match else 0.0
    
    data['nutrition'] = {
        'calories': calories,
        'protein': protein,
        'fat': fat,
        'carbs': carbs
    }
    data['weight_g'] = weight_g
    
    return data

def process_directory(source_dir, output_dir):
    """
    ディレクトリを処理してJSONファイルを作成する
    Enhanced版：カテゴリー情報とserving情報も抽出
    """
    source_path = Path(source_dir)
    output_path = Path(output_dir)
    
    # 出力ディレクトリを作成
    output_path.mkdir(exist_ok=True)
    
    processed_files = 0
    error_files = []
    
    # 各サブディレクトリを処理
    for subdir in source_path.iterdir():
        if not subdir.is_dir() or subdir.name.startswith('.'):
            continue
            
        print(f"\n処理中: {subdir.name}")
        
        # 対応する出力サブディレクトリを作成
        output_subdir = output_path / subdir.name
        output_subdir.mkdir(exist_ok=True)
        
        # サブディレクトリ内のテキストファイルを処理
        for txt_file in subdir.glob('*.txt'):
            try:
                print(f"  ファイル処理中: {txt_file.name}")
                
                # テキストファイルを読み込み
                with open(txt_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # ファイルパスを相対パスとして作成（カテゴリー抽出用）
                relative_file_path = str(txt_file.relative_to(source_path.parent))
                
                # データを抽出（ファイルパスも渡す）
                data = extract_nutrition_data(content, txt_file.name, relative_file_path)
                
                # JSONファイル名を生成
                json_filename = txt_file.stem + '.json'
                json_path = output_subdir / json_filename
                
                # JSONファイルに保存
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                processed_files += 1
                
                # データの整合性をチェック
                missing_data = []
                if not data['name']:
                    missing_data.append('name')
                if data['nutrition']['calories'] == 0.0:
                    missing_data.append('calories')
                if data['nutrition']['protein'] == 0.0:
                    missing_data.append('protein')
                if data['nutrition']['fat'] == 0.0:
                    missing_data.append('fat')
                if data['nutrition']['carbs'] == 0.0:
                    missing_data.append('carbs')
                if data['weight_g'] == 0.0:
                    missing_data.append('weight_g')
                    
                if missing_data:
                    print(f"    警告: {txt_file.name} で以下のデータが見つからないか0です: {', '.join(missing_data)}")
                
                if not data['name_matches_filename']:
                    print(f"    警告: {txt_file.name} のファイル名とテキスト内の名前が一致しません")
                    print(f"      ファイル名: {txt_file.stem}")
                    print(f"      テキスト名: {data['name']}")
                
                # 新しいフィールドの確認
                if data.get('category'):
                    print(f"    カテゴリー: {data['category']}")
                
                serving_info = data.get('serving', {})
                if serving_info.get('unit') and serving_info.get('grams'):
                    print(f"    Serving: {serving_info['grams']}g ({serving_info['unit']})")
                
            except Exception as e:
                error_msg = f"{txt_file}: {str(e)}"
                error_files.append(error_msg)
                print(f"    エラー: {error_msg}")
    
    return processed_files, error_files

def main():
    """
    メイン処理
    """
    source_directory = "MyNetDiary/Staple Foods"
    output_directory = "json_data"
    
    print("MyNetDiaryデータをJSON形式に変換しています...")
    print(f"入力ディレクトリ: {source_directory}")
    print(f"出力ディレクトリ: {output_directory}")
    
    # 処理実行
    processed_count, errors = process_directory(source_directory, output_directory)
    
    print(f"\n処理完了!")
    print(f"処理されたファイル数: {processed_count}")
    
    if errors:
        print(f"\nエラーが発生したファイル数: {len(errors)}")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\nすべてのファイルが正常に処理されました!")

if __name__ == "__main__":
    main() 