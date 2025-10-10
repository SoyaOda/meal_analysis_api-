#!/usr/bin/env python3
"""
Manual Input TemplatesとStemmed DBの対応を取るスクリプト

機能:
1. manual_input_templatesから全食材を抽出
2. stemmed DBと照合
3. 対応表（correspondence）を生成
4. 片方のみに存在する食材リストを生成

出力ファイル:
- manual_to_stemmed_correspondence.json: 対応表
- manual_only_foods.json: マニュアルのみに存在
- stemmed_only_foods.json: stemmed DBのみに存在
- correspondence_summary.json: サマリー統計
"""

import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple


class ManualStemmedMapper:
    """Manual TemplatesとStemmed DBのマッピングを管理するクラス"""

    def __init__(
        self,
        manual_templates_dir: str,
        stemmed_db_path: str,
        existing_mapping_path: str,
        output_dir: str
    ):
        self.manual_templates_dir = Path(manual_templates_dir)
        self.stemmed_db_path = Path(stemmed_db_path)
        self.existing_mapping_path = Path(existing_mapping_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.manual_foods = []
        self.stemmed_db = []
        self.existing_mapping = None

    def load_data(self):
        """データを読み込む"""
        print("📖 データ読み込み中...")

        # Stemmed DB読み込み
        with open(self.stemmed_db_path, 'r', encoding='utf-8') as f:
            self.stemmed_db = json.load(f)
        print(f"  ✅ Stemmed DB: {len(self.stemmed_db)}件")

        # 既存マッピング読み込み
        with open(self.existing_mapping_path, 'r', encoding='utf-8') as f:
            self.existing_mapping = json.load(f)
        print(f"  ✅ 既存マッピング: {self.existing_mapping['total_mappings']}件")

        # Manual Templates読み込み
        self.manual_foods = self._extract_manual_foods()
        print(f"  ✅ マニュアルテンプレート: {len(self.manual_foods)}件")

    def _extract_manual_foods(self) -> List[Dict]:
        """Manual Templatesから食材を抽出"""
        manual_files = list(self.manual_templates_dir.glob("*_manual_input.txt"))
        all_foods = []

        for manual_file in manual_files:
            with open(manual_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # カテゴリ名抽出
            category_match = re.search(r'カテゴリ: (.+)', content)
            category = category_match.group(1) if category_match else manual_file.stem

            # 食材抽出（番号. 食材名, unit\nカロリー）
            # カンマ付きカロリー対応: [\d,]+ でカンマを含む数字にマッチ
            pattern = r'\n(\d+)\. (.+?)\n([\d,]+cals)'
            matches = re.findall(pattern, content)

            for sequence, food_name, calories in matches:
                final_food_name = f"{food_name}\n{calories}"
                all_foods.append({
                    'sequence': int(sequence),
                    'category': category,
                    'food_name': food_name,
                    'calories': calories,
                    'final_food_name': final_food_name,
                    'source_file': manual_file.name
                })

        return all_foods

    def create_correspondence(self) -> Dict:
        """対応表を作成"""
        print("\n🔗 対応表作成中...")

        # 既存マッピングを辞書化
        mapping_dict = {}
        for mapping in self.existing_mapping['mappings']:
            mapping_dict[mapping['final_food_name']] = mapping

        # Stemmed DB IDセット
        stemmed_ids_set = set(str(food['id']) for food in self.stemmed_db)
        stemmed_dict = {str(food['id']): food for food in self.stemmed_db}

        # 対応を作成
        correspondences = []
        manual_only = []
        matched_stemmed_ids = set()

        for manual_food in self.manual_foods:
            final_name = manual_food['final_food_name']

            if final_name in mapping_dict:
                # マッピング成功
                mapping = mapping_dict[final_name]
                stemmed_id = mapping['stemmed_id']
                matched_stemmed_ids.add(stemmed_id)

                stemmed_food = stemmed_dict.get(stemmed_id)

                correspondence = {
                    'manual_food': {
                        'food_name': manual_food['food_name'],
                        'category': manual_food['category'],
                        'calories': manual_food['calories'],
                        'final_food_name': manual_food['final_food_name'],
                        'source_file': manual_food['source_file']
                    },
                    'stemmed_food': {
                        'id': stemmed_id,
                        'original_name': stemmed_food['original_name'] if stemmed_food else 'Unknown',
                        'search_name': stemmed_food['search_name'] if stemmed_food else 'Unknown',
                        'description': stemmed_food.get('description', 'N/A') if stemmed_food else 'N/A',
                        'nutrition': stemmed_food['nutrition'] if stemmed_food else None
                    },
                    'mapping_info': {
                        'final_food_id': mapping['final_food_id'],
                        'sequence': mapping['sequence']
                    }
                }
                correspondences.append(correspondence)
            else:
                # マッピング失敗 = マニュアルのみ
                manual_only.append(manual_food)

        # Stemmed DBのみに存在する食材
        stemmed_only_ids = stemmed_ids_set - matched_stemmed_ids
        stemmed_only = []
        for stemmed_id in stemmed_only_ids:
            stemmed_food = stemmed_dict[stemmed_id]
            stemmed_only.append({
                'id': stemmed_id,
                'original_name': stemmed_food['original_name'],
                'search_name': stemmed_food['search_name'],
                'description': stemmed_food.get('description', 'N/A'),
                'nutrition': stemmed_food['nutrition']
            })

        print(f"  ✅ 対応成功: {len(correspondences)}件")
        print(f"  ⚠️  マニュアルのみ: {len(manual_only)}件")
        print(f"  ⚠️  Stemmed DBのみ: {len(stemmed_only)}件")

        return {
            'correspondences': correspondences,
            'manual_only': manual_only,
            'stemmed_only': stemmed_only
        }

    def save_results(self, result: Dict):
        """結果を保存"""
        print("\n💾 結果保存中...")

        timestamp = datetime.now().isoformat()

        # 1. 対応表
        correspondence_data = {
            'metadata': {
                'timestamp': timestamp,
                'total_correspondences': len(result['correspondences']),
                'manual_templates_dir': str(self.manual_templates_dir),
                'stemmed_db_path': str(self.stemmed_db_path),
                'mapping_path': str(self.existing_mapping_path)
            },
            'correspondences': result['correspondences']
        }

        correspondence_file = self.output_dir / 'manual_to_stemmed_correspondence.json'
        with open(correspondence_file, 'w', encoding='utf-8') as f:
            json.dump(correspondence_data, f, ensure_ascii=False, indent=2)
        print(f"  ✅ 対応表: {correspondence_file}")

        # 2. マニュアルのみ
        manual_only_data = {
            'metadata': {
                'timestamp': timestamp,
                'total_foods': len(result['manual_only']),
                'description': 'マニュアルテンプレートにのみ存在する食材（Stemmed DBに未登録）'
            },
            'foods': result['manual_only']
        }

        manual_only_file = self.output_dir / 'manual_only_foods.json'
        with open(manual_only_file, 'w', encoding='utf-8') as f:
            json.dump(manual_only_data, f, ensure_ascii=False, indent=2)
        print(f"  ✅ マニュアルのみ: {manual_only_file}")

        # 3. Stemmed DBのみ
        stemmed_only_data = {
            'metadata': {
                'timestamp': timestamp,
                'total_foods': len(result['stemmed_only']),
                'description': 'Stemmed DBにのみ存在する食材（マニュアルテンプレートに未登録）'
            },
            'foods': result['stemmed_only']
        }

        stemmed_only_file = self.output_dir / 'stemmed_only_foods.json'
        with open(stemmed_only_file, 'w', encoding='utf-8') as f:
            json.dump(stemmed_only_data, f, ensure_ascii=False, indent=2)
        print(f"  ✅ Stemmed DBのみ: {stemmed_only_file}")

        # 4. サマリー統計
        summary = self._create_summary(result)
        summary_file = self.output_dir / 'correspondence_summary.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"  ✅ サマリー: {summary_file}")

        # 5. カテゴリ別統計
        self._save_category_stats(result)

    def _create_summary(self, result: Dict) -> Dict:
        """サマリー統計を作成"""
        total_manual = len(self.manual_foods)
        total_stemmed = len(self.stemmed_db)
        total_matched = len(result['correspondences'])
        manual_only_count = len(result['manual_only'])
        stemmed_only_count = len(result['stemmed_only'])

        # カテゴリ別集計
        category_stats = defaultdict(lambda: {'total': 0, 'matched': 0, 'unmatched': 0})
        for food in self.manual_foods:
            category_stats[food['category']]['total'] += 1

        for corr in result['correspondences']:
            category = corr['manual_food']['category']
            category_stats[category]['matched'] += 1

        for food in result['manual_only']:
            category = food['category']
            category_stats[category]['unmatched'] += 1

        return {
            'timestamp': datetime.now().isoformat(),
            'overall_statistics': {
                'total_manual_foods': total_manual,
                'total_stemmed_foods': total_stemmed,
                'successfully_matched': total_matched,
                'match_rate': f"{total_matched / total_manual * 100:.2f}%",
                'manual_only': manual_only_count,
                'stemmed_only': stemmed_only_count
            },
            'category_statistics': dict(category_stats),
            'data_sources': {
                'manual_templates': str(self.manual_templates_dir),
                'stemmed_db': str(self.stemmed_db_path),
                'existing_mapping': str(self.existing_mapping_path)
            }
        }

    def _save_category_stats(self, result: Dict):
        """カテゴリ別統計を保存"""
        category_stats = defaultdict(lambda: {
            'total': 0,
            'matched': 0,
            'unmatched': 0,
            'matched_foods': [],
            'unmatched_foods': []
        })

        # 対応成功
        for corr in result['correspondences']:
            category = corr['manual_food']['category']
            category_stats[category]['total'] += 1
            category_stats[category]['matched'] += 1
            category_stats[category]['matched_foods'].append(
                corr['manual_food']['food_name']
            )

        # 未対応
        for food in result['manual_only']:
            category = food['category']
            category_stats[category]['total'] += 1
            category_stats[category]['unmatched'] += 1
            category_stats[category]['unmatched_foods'].append(food['food_name'])

        # 保存
        category_file = self.output_dir / 'category_statistics.json'
        with open(category_file, 'w', encoding='utf-8') as f:
            json.dump(dict(category_stats), f, ensure_ascii=False, indent=2)
        print(f"  ✅ カテゴリ別統計: {category_file}")

    def print_summary(self, result: Dict):
        """サマリーを表示"""
        print("\n" + "="*80)
        print("📊 処理結果サマリー")
        print("="*80)

        total_manual = len(self.manual_foods)
        total_stemmed = len(self.stemmed_db)
        total_matched = len(result['correspondences'])

        print(f"\n総食材数:")
        print(f"  マニュアルテンプレート: {total_manual}件")
        print(f"  Stemmed DB: {total_stemmed}件")

        print(f"\nマッピング結果:")
        print(f"  ✅ 対応成功: {total_matched}件 ({total_matched/total_manual*100:.2f}%)")
        print(f"  ⚠️  マニュアルのみ: {len(result['manual_only'])}件 ({len(result['manual_only'])/total_manual*100:.2f}%)")
        print(f"  ⚠️  Stemmed DBのみ: {len(result['stemmed_only'])}件 ({len(result['stemmed_only'])/total_stemmed*100:.2f}%)")

        if result['manual_only']:
            print(f"\nマニュアルのみに存在する食材（最初の5件）:")
            for i, food in enumerate(result['manual_only'][:5], 1):
                print(f"  {i}. {food['food_name']} ({food['category']})")

        if result['stemmed_only']:
            print(f"\nStemmed DBのみに存在する食材（最初の5件）:")
            for i, food in enumerate(result['stemmed_only'][:5], 1):
                print(f"  {i}. {food['original_name']}")

        print("\n" + "="*80)


def main():
    """メイン処理"""
    print("=" * 80)
    print("🔄 Manual Templates と Stemmed DB の対応表作成")
    print("=" * 80)

    # パス設定
    base_dir = Path(__file__).parent
    manual_templates_dir = base_dir / "manual_input_templates"
    stemmed_db_path = base_dir.parent / "db" / "mynetdiary_converted_tool_calls_list_stemmed.json"
    existing_mapping_path = base_dir.parent / "web_scraping" / "processed_data" / "complete_mapping_with_14_foods.json"
    output_dir = base_dir / "output"

    # 存在確認
    if not manual_templates_dir.exists():
        print(f"❌ エラー: {manual_templates_dir} が見つかりません")
        return

    if not stemmed_db_path.exists():
        print(f"❌ エラー: {stemmed_db_path} が見つかりません")
        return

    if not existing_mapping_path.exists():
        print(f"❌ エラー: {existing_mapping_path} が見つかりません")
        return

    # マッパー初期化
    mapper = ManualStemmedMapper(
        manual_templates_dir=str(manual_templates_dir),
        stemmed_db_path=str(stemmed_db_path),
        existing_mapping_path=str(existing_mapping_path),
        output_dir=str(output_dir)
    )

    # データ読み込み
    mapper.load_data()

    # 対応表作成
    result = mapper.create_correspondence()

    # 結果保存
    mapper.save_results(result)

    # サマリー表示
    mapper.print_summary(result)

    print("\n✅ 処理完了!")


if __name__ == "__main__":
    main()
