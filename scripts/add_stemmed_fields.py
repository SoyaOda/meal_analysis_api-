#!/usr/bin/env python3
"""
語幹化フィールドを既存のMyNetDiaryデータベースに追加するスクリプト

新しいフィールド:
- stemmed_search_name: search_nameの語幹化版
- stemmed_description: descriptionの語幹化版
"""

import json
import nltk
from nltk.stem import PorterStemmer
import re
from typing import List, Dict, Any

# NLTKデータのダウンロード（初回のみ）
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    print("Downloading NLTK punkt tokenizer...")
    nltk.download('punkt')

def setup_stemmer():
    """PorterStemmerの初期化"""
    return PorterStemmer()

def clean_and_tokenize_single(text: str) -> List[str]:
    """単一テキストのクリーニングとトークン化"""
    if not text:
        return []

    # 文字列でない場合は文字列に変換
    if not isinstance(text, str):
        text = str(text)

    # 小文字に変換
    text = text.lower()

    # 特殊文字を除去（アルファベットとスペースのみ残す）
    text = re.sub(r'[^a-z\s]', ' ', text)

    # 複数のスペースを単一スペースに
    text = re.sub(r'\s+', ' ', text).strip()

    # トークン化
    tokens = text.split()

    return tokens

def stem_single_text(text: str, stemmer: PorterStemmer) -> str:
    """単一テキストの語幹化"""
    if not text:
        return ""

    tokens = clean_and_tokenize_single(text)
    stemmed_tokens = [stemmer.stem(token) for token in tokens]

    return ' '.join(stemmed_tokens)

def stem_text_or_list(text, stemmer: PorterStemmer):
    """テキストまたはリストの語幹化（型を保持）"""
    if not text:
        return text

    # リスト形式の場合: 各要素を個別に語幹化してリストを返す
    if isinstance(text, list):
        if len(text) == 0:
            return []
        return [stem_single_text(item, stemmer) for item in text]

    # 文字列の場合: 語幹化した文字列を返す
    else:
        return stem_single_text(text, stemmer)

def add_stemmed_fields(record: Dict[str, Any], stemmer: PorterStemmer) -> Dict[str, Any]:
    """個別レコードに語幹化フィールドを追加"""

    # 元のレコードをコピー
    new_record = record.copy()

    # search_nameの語幹化（リスト形式も対応）
    search_name = record.get('search_name', '')
    new_record['stemmed_search_name'] = stem_text_or_list(search_name, stemmer)

    # descriptionの語幹化（通常は文字列）
    description = record.get('description', '')
    new_record['stemmed_description'] = stem_text_or_list(description, stemmer)

    return new_record

def process_database():
    """メインの処理関数"""

    print("🔧 MyNetDiary語幹化データベース作成開始...")

    # Stemmerの初期化
    stemmer = setup_stemmer()

    # 元のデータベースを読み込み
    input_file = 'db/mynetdiary_converted_tool_calls_list.json'
    output_file = 'db/mynetdiary_converted_tool_calls_list_stemmed.json'

    print(f"📖 読み込み: {input_file}")

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            original_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ エラー: {input_file} が見つかりません")
        return
    except json.JSONDecodeError as e:
        print(f"❌ JSON読み込みエラー: {e}")
        return

    print(f"📊 処理対象レコード数: {len(original_data)}")

    # 各レコードに語幹化フィールドを追加
    stemmed_data = []

    for i, record in enumerate(original_data):
        if i % 100 == 0:
            print(f"⚡ 処理中... {i}/{len(original_data)} ({i/len(original_data)*100:.1f}%)")

        new_record = add_stemmed_fields(record, stemmer)
        stemmed_data.append(new_record)

    print(f"💾 保存: {output_file}")

    # 新しいデータベースを保存
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(stemmed_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ 保存エラー: {e}")
        return

    # サンプル結果の表示
    print("\n✨ 語幹化結果サンプル:")
    print("-" * 80)

    # 文字列形式のサンプル
    string_samples = [r for r in stemmed_data if isinstance(r.get('search_name'), str)][:3]
    # リスト形式のサンプル
    list_samples = [r for r in stemmed_data if isinstance(r.get('search_name'), list)][:2]

    print("🔤 文字列形式のサンプル:")
    for i, record in enumerate(string_samples):
        print(f"   Record {i+1}:")
        print(f"     original_name: {record.get('original_name', 'N/A')}")
        print(f"     search_name: '{record.get('search_name', 'N/A')}' → '{record.get('stemmed_search_name', 'N/A')}'")
        print(f"     description: '{record.get('description', 'N/A')}' → '{record.get('stemmed_description', 'N/A')}'")
        print()

    print("📋 リスト形式のサンプル:")
    for i, record in enumerate(list_samples):
        print(f"   Record {i+1}:")
        print(f"     original_name: {record.get('original_name', 'N/A')}")
        print(f"     search_name: {record.get('search_name', 'N/A')}")
        print(f"     stemmed_search_name: {record.get('stemmed_search_name', 'N/A')}")
        print(f"     description: '{record.get('description', 'N/A')}' → '{record.get('stemmed_description', 'N/A')}'")
        print()

    print(f"✅ 完了! 新しいデータベース: {output_file}")
    print(f"📊 処理レコード数: {len(stemmed_data)}")

if __name__ == "__main__":
    process_database()