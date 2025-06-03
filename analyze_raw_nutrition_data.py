#!/usr/bin/env python3
"""
Raw Nutrition Data Analysis Script

このスクリプトはraw_nutrition_dataディレクトリの全ての内容を分析し、
各カテゴリ（food, branded, restaurant, recipe）の統計情報、
processed.jsonサンプル、JSONキーの統一性をチェックして
詳細なMarkdownレポートを生成します。
"""

import os
import json
import glob
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
import traceback

def count_directories(base_path):
    """指定されたパスの直下のディレクトリ数をカウント"""
    try:
        path = Path(base_path)
        if not path.exists():
            return 0
        return len([item for item in path.iterdir() if item.is_dir() and not item.name.startswith('.')])
    except Exception as e:
        print(f"Error counting directories in {base_path}: {e}")
        return 0

def find_processed_json_files(category_path):
    """指定されたカテゴリパス内の全てのprocessed/*.jsonファイルを検索"""
    processed_files = []
    try:
        pattern = os.path.join(category_path, "*", "processed", "*.json")
        files = glob.glob(pattern)
        processed_files = [Path(f) for f in files]
        print(f"Found {len(processed_files)} processed JSON files in {category_path}")
    except Exception as e:
        print(f"Error finding processed files in {category_path}: {e}")
    return processed_files

def load_json_sample(file_path):
    """JSONファイルを読み込んでサンプルデータとして返す"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading JSON from {file_path}: {e}")
        return None

def extract_json_keys(data, prefix="", max_depth=3, current_depth=0):
    """JSONデータから全てのキーを再帰的に抽出（深さ制限付き）"""
    keys = set()
    if current_depth >= max_depth:
        return keys
    
    if isinstance(data, dict):
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            keys.add(full_key)
            if isinstance(value, (dict, list)) and current_depth < max_depth - 1:
                keys.update(extract_json_keys(value, full_key, max_depth, current_depth + 1))
    elif isinstance(data, list) and len(data) > 0:
        # リストの最初の要素を分析
        keys.update(extract_json_keys(data[0], prefix, max_depth, current_depth + 1))
    
    return keys

def analyze_category(category_name, category_path):
    """特定のカテゴリを分析"""
    print(f"\n🔍 Analyzing {category_name} category...")
    
    analysis = {
        'name': category_name,
        'path': category_path,
        'total_directories': 0,
        'processed_files': [],
        'samples': [],
        'all_keys': set(),
        'key_frequency': Counter(),
        'errors': []
    }
    
    # ディレクトリ数をカウント
    analysis['total_directories'] = count_directories(category_path)
    
    # processed.jsonファイルを検索
    analysis['processed_files'] = find_processed_json_files(category_path)
    
    # サンプル3個を取得
    sample_count = min(3, len(analysis['processed_files']))
    for i in range(sample_count):
        file_path = analysis['processed_files'][i]
        data = load_json_sample(file_path)
        if data is not None:
            # サンプルデータを保存
            analysis['samples'].append({
                'file_path': str(file_path),
                'data': data
            })
            
            # キーを抽出
            keys = extract_json_keys(data)
            analysis['all_keys'].update(keys)
            for key in keys:
                analysis['key_frequency'][key] += 1
        else:
            analysis['errors'].append(f"Failed to load {file_path}")
    
    return analysis

def check_key_consistency(all_analyses):
    """全カテゴリ間でのキーの一貫性をチェック"""
    print("\n🔍 Checking key consistency across categories...")
    
    consistency_report = {
        'common_keys': set(),
        'category_specific_keys': {},
        'key_overlap_matrix': {}
    }
    
    # 各カテゴリのキーセットを取得
    category_keys = {}
    for analysis in all_analyses:
        category_keys[analysis['name']] = analysis['all_keys']
    
    # 共通キーを見つける
    if category_keys:
        consistency_report['common_keys'] = set.intersection(*category_keys.values())
    
    # カテゴリ固有のキーを見つける
    for category, keys in category_keys.items():
        other_keys = set()
        for other_category, other_category_keys in category_keys.items():
            if other_category != category:
                other_keys.update(other_category_keys)
        
        consistency_report['category_specific_keys'][category] = keys - other_keys
    
    # キー重複マトリックスを作成
    for cat1, keys1 in category_keys.items():
        consistency_report['key_overlap_matrix'][cat1] = {}
        for cat2, keys2 in category_keys.items():
            overlap = len(keys1 & keys2)
            total_unique = len(keys1 | keys2)
            similarity = overlap / total_unique if total_unique > 0 else 0
            consistency_report['key_overlap_matrix'][cat1][cat2] = {
                'overlap_count': overlap,
                'similarity_ratio': similarity
            }
    
    return consistency_report

def format_json_for_markdown(data, max_lines=50):
    """JSONデータをMarkdown用に整形（行数制限付き）"""
    try:
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        lines = json_str.split('\n')
        if len(lines) > max_lines:
            lines = lines[:max_lines] + ['  ...', '  // (truncated for readability)', '}']
        return '\n'.join(lines)
    except Exception as e:
        return f"Error formatting JSON: {e}"

def generate_markdown_report(all_analyses, consistency_report, output_file):
    """Markdownレポートを生成"""
    print(f"\n📝 Generating Markdown report: {output_file}")
    
    timestamp = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
    
    markdown_content = f"""# Raw Nutrition Data 分析レポート

**生成日時:** {timestamp}

## 📊 概要統計

このレポートは、`raw_nutrition_data`ディレクトリ内の4つのサブカテゴリ（food, branded, restaurant, recipe）の構造と内容を分析した結果です。

### カテゴリ別統計

| カテゴリ | ディレクトリ数 | 処理済みJSONファイル数 | 
|----------|----------------|------------------------|
"""
    
    # 統計テーブルを作成
    total_dirs = 0
    total_files = 0
    for analysis in all_analyses:
        total_dirs += analysis['total_directories']
        total_files += len(analysis['processed_files'])
        markdown_content += f"| {analysis['name']} | {analysis['total_directories']:,} | {len(analysis['processed_files']):,} |\n"
    
    markdown_content += f"| **合計** | **{total_dirs:,}** | **{total_files:,}** |\n\n"
    
    # 各カテゴリの詳細分析
    for analysis in all_analyses:
        markdown_content += f"""## 📁 {analysis['name'].title()} カテゴリ

### 基本情報
- **ディレクトリ数**: {analysis['total_directories']:,}
- **処理済みJSONファイル数**: {len(analysis['processed_files']):,}
- **サンプル数**: {len(analysis['samples'])}

### JSONサンプル

"""
        
        # サンプルを表示
        for i, sample in enumerate(analysis['samples'], 1):
            relative_path = sample['file_path'].replace(str(Path.cwd()), '.')
            markdown_content += f"""#### サンプル {i}: `{relative_path}`

```json
{format_json_for_markdown(sample['data'])}
```

"""
        
        # キー分析
        markdown_content += f"""### JSONキー分析

**検出されたキー数**: {len(analysis['all_keys'])}

#### 主要キー（出現頻度順）
"""
        
        # 頻度の高いキーをリストアップ
        top_keys = analysis['key_frequency'].most_common(20)
        for key, frequency in top_keys:
            markdown_content += f"- `{key}` (出現: {frequency}回)\n"
        
        if len(analysis['all_keys']) > 20:
            markdown_content += f"\n*(他 {len(analysis['all_keys']) - 20} キー)*\n"
        
        markdown_content += "\n"
        
        # エラーがあれば表示
        if analysis['errors']:
            markdown_content += f"""### ⚠️ 処理エラー

以下のファイルでエラーが発生しました：
"""
            for error in analysis['errors']:
                markdown_content += f"- {error}\n"
            markdown_content += "\n"
    
    # キーの一貫性分析
    markdown_content += f"""## 🔍 キー一貫性分析

### 共通キー

全カテゴリで共通して使用されているキー数: **{len(consistency_report['common_keys'])}**

"""
    
    if consistency_report['common_keys']:
        markdown_content += "#### 共通キー一覧\n"
        for key in sorted(consistency_report['common_keys']):
            markdown_content += f"- `{key}`\n"
        markdown_content += "\n"
    else:
        markdown_content += "*全カテゴリで共通するキーはありません。*\n\n"
    
    # カテゴリ固有キー
    markdown_content += "### カテゴリ固有キー\n\n"
    for category, specific_keys in consistency_report['category_specific_keys'].items():
        markdown_content += f"#### {category.title()} 固有キー ({len(specific_keys)}個)\n"
        if specific_keys:
            for key in sorted(list(specific_keys)[:10]):  # 最初の10個のみ表示
                markdown_content += f"- `{key}`\n"
            if len(specific_keys) > 10:
                markdown_content += f"\n*(他 {len(specific_keys) - 10} キー)*\n"
        else:
            markdown_content += "*カテゴリ固有のキーはありません。*\n"
        markdown_content += "\n"
    
    # キー類似度マトリックス
    markdown_content += "### カテゴリ間キー類似度マトリックス\n\n"
    categories = list(consistency_report['key_overlap_matrix'].keys())
    
    # ヘッダー行
    markdown_content += "| | " + " | ".join(categories) + " |\n"
    markdown_content += "|" + "---|" * (len(categories) + 1) + "\n"
    
    # データ行
    for cat1 in categories:
        row = f"| **{cat1}** |"
        for cat2 in categories:
            similarity = consistency_report['key_overlap_matrix'][cat1][cat2]['similarity_ratio']
            row += f" {similarity:.2%} |"
        markdown_content += row + "\n"
    
    markdown_content += "\n"
    
    # 結論
    markdown_content += f"""## 📋 分析結果まとめ

### 主な発見事項

1. **データ規模**: 合計 {total_dirs:,} ディレクトリ、{total_files:,} 処理済みJSONファイル
2. **キー一貫性**: {len(consistency_report['common_keys'])} 個の共通キーが全カテゴリで使用
3. **カテゴリ特性**: 各カテゴリには固有のデータ構造が存在

### カテゴリ別特徴

"""
    
    for analysis in all_analyses:
        unique_keys = len(consistency_report['category_specific_keys'][analysis['name']])
        markdown_content += f"- **{analysis['name'].title()}**: {analysis['total_directories']:,} ディレクトリ、{unique_keys} 固有キー\n"
    
    markdown_content += f"""

### 推奨事項

1. **データ統合時の注意**: カテゴリごとに異なるスキーマを持つため、統合処理時は適切なマッピングが必要
2. **キー正規化**: 共通キーを基準とした標準化を検討
3. **エラーハンドリング**: 一部のJSONファイルで読み込みエラーが発生している可能性があるため、ロバストな処理が必要

---

*このレポートは `analyze_raw_nutrition_data.py` により自動生成されました。*
"""
    
    # ファイルに書き込み
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"✅ レポートが正常に生成されました: {output_file}")
    except Exception as e:
        print(f"❌ レポート生成エラー: {e}")

def main():
    """メイン実行関数"""
    print("🚀 Raw Nutrition Data Analysis Script")
    print("=" * 50)
    
    # ベースディレクトリの確認
    base_dir = Path("raw_nutrition_data")
    if not base_dir.exists():
        print(f"❌ {base_dir} ディレクトリが見つかりません。")
        return
    
    # 分析対象カテゴリ
    categories = ["food", "branded", "restaurant", "recipe"]
    all_analyses = []
    
    # 各カテゴリを分析
    for category in categories:
        category_path = base_dir / category
        if category_path.exists():
            analysis = analyze_category(category, str(category_path))
            all_analyses.append(analysis)
        else:
            print(f"⚠️ カテゴリ {category} が見つかりません: {category_path}")
    
    if not all_analyses:
        print("❌ 分析するカテゴリが見つかりませんでした。")
        return
    
    # キー一貫性をチェック
    consistency_report = check_key_consistency(all_analyses)
    
    # Markdownレポートを生成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"raw_nutrition_data_analysis_report_{timestamp}.md"
    generate_markdown_report(all_analyses, consistency_report, output_file)
    
    print("\n🎉 分析完了!")
    print(f"📄 詳細レポート: {output_file}")
    
    # 簡単なサマリーを表示
    print("\n📊 簡易サマリー:")
    for analysis in all_analyses:
        print(f"  {analysis['name']}: {analysis['total_directories']:,} dirs, {len(analysis['processed_files']):,} files")

if __name__ == "__main__":
    main() 