#!/usr/bin/env python3
"""
HTMLファイルからAPIレスポンスのJSONデータを抽出し、人気度指標を含めた
新しいprocessed JSONファイルを作成するスクリプト
"""

import os
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup
import logging

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_api_data_from_html(html_file_path):
    """HTMLファイルからAPIレスポンスのJSONデータを抽出"""
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # script tag内のAPIレスポンスを検索
        # data-sveltekit-fetched属性を持つscriptタグを探す
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # APIレスポンスのscriptタグを取得
        api_scripts = soup.find_all('script', {'data-sveltekit-fetched': True})
        
        for script in api_scripts:
            script_content = script.get_text()
            if 'num_favorites' in script_content and 'num_ratings' in script_content:
                try:
                    # JSONオブジェクトを抽出
                    json_data = json.loads(script_content)
                    if 'body' in json_data:
                        body_data = json.loads(json_data['body'])
                        if 'data' in body_data:
                            return body_data['data']
                except json.JSONDecodeError:
                    continue
        
        logger.warning(f"人気度指標が見つかりませんでした: {html_file_path}")
        return None
        
    except Exception as e:
        logger.error(f"HTMLファイル読み取りエラー {html_file_path}: {e}")
        return None

def extract_popularity_metrics(api_data):
    """APIデータから人気度指標を抽出"""
    if not api_data:
        return {}
    
    metrics = {}
    
    # 人気度指標を抽出
    if 'num_favorites' in api_data:
        metrics['num_favorites'] = api_data['num_favorites']
    if 'num_ratings' in api_data:
        metrics['num_ratings'] = api_data['num_ratings']
    if 'score' in api_data:
        metrics['score'] = api_data['score']
    if 'num_reviews' in api_data:
        metrics['num_reviews'] = api_data['num_reviews']
    
    logger.info(f"抽出された人気度指標: {metrics}")
    return metrics

def create_enhanced_processed_json(original_processed_file, popularity_metrics, output_dir):
    """既存のprocessed JSONに人気度指標を追加した新しいJSONを作成"""
    try:
        # 既存のprocessed JSONを読み込み
        with open(original_processed_file, 'r', encoding='utf-8') as f:
            processed_data = json.load(f)
        
        # 人気度指標を追加
        processed_data['popularity_metrics'] = popularity_metrics
        
        # processed_newディレクトリを作成
        os.makedirs(output_dir, exist_ok=True)
        
        # 新しいJSONファイルを保存
        output_file = os.path.join(output_dir, 'data_with_popularity.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"強化されたJSONファイルを作成しました: {output_file}")
        return output_file
        
    except Exception as e:
        logger.error(f"強化されたJSONファイル作成エラー: {e}")
        return None

def process_food_items(base_dir="raw_nutrition_data"):
    """すべての食品アイテムを処理"""
    processed_count = 0
    error_count = 0
    
    # recipe, food, brandedの各ディレクトリを処理
    for category in ['recipe', 'food', 'branded']:
        category_dir = os.path.join(base_dir, category)
        
        if not os.path.exists(category_dir):
            logger.warning(f"ディレクトリが存在しません: {category_dir}")
            continue
        
        logger.info(f"{category}カテゴリの処理を開始...")
        
        # 各食品IDのディレクトリを処理
        for item_id in os.listdir(category_dir):
            item_dir = os.path.join(category_dir, item_id)
            
            if not os.path.isdir(item_dir):
                continue
            
            # HTMLファイルのパス
            html_file = os.path.join(item_dir, 'raw', 'html', 'page.html')
            
            # processedディレクトリ内のJSONファイルを探す
            processed_dir = os.path.join(item_dir, 'processed')
            processed_file = None
            
            if os.path.exists(processed_dir):
                for file in os.listdir(processed_dir):
                    if file.endswith('.json'):
                        processed_file = os.path.join(processed_dir, file)
                        break
            
            if not os.path.exists(html_file):
                logger.warning(f"HTMLファイルが見つかりません: {html_file}")
                error_count += 1
                continue
                
            if not processed_file:
                logger.warning(f"processedファイルが見つかりません: {processed_dir}")
                error_count += 1
                continue
            
            try:
                # HTMLからAPIデータを抽出
                api_data = extract_api_data_from_html(html_file)
                
                # 人気度指標を抽出
                popularity_metrics = extract_popularity_metrics(api_data)
                
                # processed_newディレクトリのパス
                processed_new_dir = os.path.join(item_dir, 'processed_new')
                
                # 強化されたJSONを作成
                if popularity_metrics:
                    enhanced_file = create_enhanced_processed_json(
                        processed_file, popularity_metrics, processed_new_dir
                    )
                    if enhanced_file:
                        processed_count += 1
                        logger.info(f"処理完了: {item_id} ({category})")
                else:
                    error_count += 1
                    logger.warning(f"人気度指標が取得できませんでした: {item_id}")
                    
            except Exception as e:
                logger.error(f"処理エラー {item_id}: {e}")
                error_count += 1
    
    logger.info(f"処理完了: 成功 {processed_count}, エラー {error_count}")

def main():
    """メイン関数"""
    logger.info("人気度指標抽出処理を開始...")
    
    # テスト: 特定のアイテムで確認
    test_item = "raw_nutrition_data/recipe/33494"
    if os.path.exists(test_item):
        html_file = os.path.join(test_item, 'raw', 'html', 'page.html')
        processed_dir = os.path.join(test_item, 'processed')
        
        if os.path.exists(html_file) and os.path.exists(processed_dir):
            logger.info("テストアイテムで確認中...")
            
            # processedファイルを探す
            processed_file = None
            for file in os.listdir(processed_dir):
                if file.endswith('.json'):
                    processed_file = os.path.join(processed_dir, file)
                    break
            
            if processed_file:
                api_data = extract_api_data_from_html(html_file)
                popularity_metrics = extract_popularity_metrics(api_data)
                
                if popularity_metrics:
                    processed_new_dir = os.path.join(test_item, 'processed_new')
                    enhanced_file = create_enhanced_processed_json(
                        processed_file, popularity_metrics, processed_new_dir
                    )
                    
                    if enhanced_file:
                        logger.info("テスト成功！全体処理を開始します...")
                        # 全体処理を実行
                        process_food_items()
                    else:
                        logger.error("テスト失敗")
                else:
                    logger.error("テスト失敗: 人気度指標が取得できませんでした")
            else:
                logger.error("テスト失敗: processedファイルが見つかりません")
        else:
            logger.error("テスト失敗: 必要なファイルが見つかりません")
    else:
        logger.error("テストアイテムが見つかりません")

if __name__ == "__main__":
    main() 