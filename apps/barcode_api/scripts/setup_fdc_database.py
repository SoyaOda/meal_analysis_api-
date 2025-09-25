#!/usr/bin/env python3
"""
FoodData Central データベースセットアップスクリプト

USDAのFoodData Centralから最新データをダウンロードし、
バーコード検索用のSQLiteデータベースを構築します。

使用方法:
    python setup_fdc_database.py [--force-download]
"""

import os
import sys
import zipfile
import requests
import sqlite3
import pandas as pd
import shutil
from pathlib import Path
from datetime import datetime
import logging
import argparse
import re
from typing import Optional

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FDCDatabaseSetup:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.fdc_dir = self.project_root / "db" / "FoodData_Central"
        self.fdc_dir.mkdir(parents=True, exist_ok=True)

        # FDCデータベースファイルパス
        self.db_path = self.fdc_dir / "fdc_barcode.db"
        self.csv_dir = self.fdc_dir / "csv"

        # FDCダウンロードURL（動的に取得）
        self.base_url = "https://fdc.nal.usda.gov"
        self.download_page_url = f"{self.base_url}/download-datasets/"

    def get_latest_download_url(self) -> Optional[str]:
        """FDCの最新ダウンロードURLを取得"""
        try:
            logger.info("最新のFDCダウンロードURLを取得中...")
            response = requests.get(self.download_page_url, timeout=30)
            response.raise_for_status()

            # CSVフォーマットの最新URLを検索
            pattern = r'href="([^"]*FoodData_Central_csv[^"]*\.zip)"'
            matches = re.findall(pattern, response.text)

            if matches:
                latest_url = self.base_url + matches[0]
                logger.info(f"最新のダウンロードURL: {latest_url}")
                return latest_url
            else:
                logger.error("ダウンロードURLが見つかりませんでした")
                return None

        except Exception as e:
            logger.error(f"ダウンロードURL取得エラー: {e}")
            return None

    def clean_existing_data(self):
        """既存のFDCデータとデータベースファイルを削除"""
        logger.info("既存のFDCデータを削除中...")

        # CSVディレクトリを削除
        if self.csv_dir.exists():
            shutil.rmtree(self.csv_dir)
            logger.info(f"削除完了: {self.csv_dir}")

        # データベースファイルを削除
        if self.db_path.exists():
            os.remove(self.db_path)
            logger.info(f"削除完了: {self.db_path}")

        # ZIPファイルも削除
        for zip_file in self.fdc_dir.glob("*.zip"):
            os.remove(zip_file)
            logger.info(f"削除完了: {zip_file}")

    def download_fdc_data(self, force_download: bool = False) -> bool:
        """FDCデータをダウンロード"""
        try:
            download_url = self.get_latest_download_url()
            if not download_url:
                return False

            zip_filename = download_url.split('/')[-1]
            zip_path = self.fdc_dir / zip_filename

            # 既存ファイルのチェック
            if zip_path.exists() and not force_download:
                logger.info(f"既存のZIPファイルが見つかりました: {zip_path}")
                return True

            logger.info(f"FDCデータをダウンロード中... ({download_url})")
            logger.info("注意: ファイルサイズが約453MBのため、時間がかかる場合があります")

            response = requests.get(download_url, stream=True, timeout=300)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\rダウンロード進行: {progress:.1f}%", end='')

            print()  # 改行
            logger.info(f"ダウンロード完了: {zip_path}")
            return True

        except Exception as e:
            logger.error(f"ダウンロードエラー: {e}")
            return False

    def extract_zip_data(self) -> bool:
        """ZIPファイルを展開"""
        try:
            zip_files = list(self.fdc_dir.glob("*.zip"))
            if not zip_files:
                logger.error("ZIPファイルが見つかりません")
                return False

            zip_path = zip_files[0]  # 最新のZIPファイルを使用
            self.csv_dir.mkdir(exist_ok=True)

            logger.info(f"ZIPファイルを展開中: {zip_path}")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.csv_dir)

            logger.info(f"展開完了: {self.csv_dir}")
            return True

        except Exception as e:
            logger.error(f"展開エラー: {e}")
            return False

    def create_database_schema(self):
        """SQLiteデータベースのスキーマを作成"""
        logger.info("データベーススキーマを作成中...")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # foodテーブル - 実際のCSV構造に合わせて修正
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS food (
                fdc_id INTEGER PRIMARY KEY,
                data_type TEXT,
                description TEXT,
                food_category_id INTEGER,
                publication_date TEXT
            )
        ''')

        # branded_foodテーブル - 実際のCSV構造に合わせて修正
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS branded_food (
                fdc_id INTEGER PRIMARY KEY,
                brand_owner TEXT,
                brand_name TEXT,
                subbrand_name TEXT,
                gtin_upc TEXT,
                ingredients TEXT,
                not_a_significant_source_of TEXT,
                serving_size REAL,
                serving_size_unit TEXT,
                household_serving_fulltext TEXT,
                branded_food_category TEXT,
                data_source TEXT,
                package_weight TEXT,
                modified_date TEXT,
                available_date TEXT,
                market_country TEXT,
                discontinued_date TEXT,
                preparation_state_code TEXT,
                trade_channel TEXT,
                short_description TEXT,
                material_code TEXT,
                FOREIGN KEY (fdc_id) REFERENCES food (fdc_id)
            )
        ''')

        # food_nutrientテーブル - 実際のCSV構造に合わせて修正（loqとpercent_daily_value列を追加）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS food_nutrient (
                id INTEGER PRIMARY KEY,
                fdc_id INTEGER,
                nutrient_id INTEGER,
                amount REAL,
                data_points INTEGER,
                derivation_id INTEGER,
                min REAL,
                max REAL,
                median REAL,
                loq REAL,
                footnote TEXT,
                min_year_acquired INTEGER,
                percent_daily_value REAL,
                FOREIGN KEY (fdc_id) REFERENCES food (fdc_id),
                FOREIGN KEY (nutrient_id) REFERENCES nutrient (id)
            )
        ''')

        # nutrientテーブル - 実際のCSV構造に合わせて修正（numberではなくnutrient_nbr）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nutrient (
                id INTEGER PRIMARY KEY,
                name TEXT,
                unit_name TEXT,
                nutrient_nbr REAL,
                rank REAL
            )
        ''')

        # インデックス作成
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_branded_food_gtin_upc ON branded_food (gtin_upc)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_food_fdc_id ON food (fdc_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_food_nutrient_fdc_id ON food_nutrient (fdc_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_food_nutrient_nutrient_id ON food_nutrient (nutrient_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_food_publication_date ON food (publication_date)')

        conn.commit()
        conn.close()
        logger.info("データベーススキーマ作成完了")

    def import_csv_data(self) -> bool:
        """CSVデータをデータベースにインポート"""
        try:
            logger.info("CSVデータをインポート中...")

            # CSVファイルパスを検索
            csv_files = {}
            for pattern in ['food.csv', 'branded_food.csv', 'food_nutrient.csv', 'nutrient.csv']:
                found_files = list(self.csv_dir.rglob(pattern))
                if found_files:
                    csv_files[pattern] = found_files[0]
                else:
                    logger.warning(f"{pattern} が見つかりません")

            if len(csv_files) < 4:
                logger.error("必要なCSVファイルが見つかりません")
                return False

            conn = sqlite3.connect(self.db_path)

            # 各CSVファイルをインポート
            for table_name, csv_path in csv_files.items():
                table = table_name.replace('.csv', '')
                logger.info(f"{table}テーブルにデータをインポート中... ({csv_path})")

                try:
                    # チャンクサイズでデータを読み込み（メモリ使用量を制限）
                    chunk_size = 10000
                    chunks_imported = 0

                    for chunk in pd.read_csv(csv_path, chunksize=chunk_size, low_memory=False):
                        # データ型の最適化
                        chunk = chunk.where(pd.notnull(chunk), None)

                        # データベースに挿入
                        chunk.to_sql(table, conn, if_exists='append', index=False, method='multi')
                        chunks_imported += 1

                        if chunks_imported % 10 == 0:
                            logger.info(f"  {chunks_imported * chunk_size:,} 行処理完了")

                    logger.info(f"{table}テーブルのインポート完了")

                except Exception as e:
                    logger.error(f"{table}テーブルのインポートエラー: {e}")
                    conn.close()
                    return False

            conn.close()
            logger.info("全CSVデータのインポート完了")
            return True

        except Exception as e:
            logger.error(f"CSVインポートエラー: {e}")
            return False

    def verify_database(self) -> bool:
        """データベースの整合性を確認"""
        try:
            logger.info("データベースの整合性を確認中...")

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 各テーブルの行数確認
            tables = ['food', 'branded_food', 'food_nutrient', 'nutrient']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                logger.info(f"{table}テーブル: {count:,} 行")

            # バーコード付き商品数確認
            cursor.execute("SELECT COUNT(*) FROM branded_food WHERE gtin_upc IS NOT NULL AND gtin_upc != ''")
            barcode_count = cursor.fetchone()[0]
            logger.info(f"バーコード付き商品: {barcode_count:,} 件")

            # 主要栄養素の確認（Energy=1008, Fat=1004, Carbohydrate=1005, Protein=1003）
            main_nutrients = [1008, 1004, 1005, 1003]
            for nutrient_id in main_nutrients:
                cursor.execute("SELECT name FROM nutrient WHERE id = ?", (nutrient_id,))
                result = cursor.fetchone()
                if result:
                    logger.info(f"栄養素ID {nutrient_id}: {result[0]}")
                else:
                    logger.warning(f"栄養素ID {nutrient_id} が見つかりません")

            conn.close()
            logger.info("データベース確認完了")
            return True

        except Exception as e:
            logger.error(f"データベース確認エラー: {e}")
            return False

    def run_setup(self, force_download: bool = False) -> bool:
        """FDCデータベースセットアップの実行"""
        logger.info("=== FoodData Central データベースセットアップ開始 ===")

        try:
            # 1. 既存データの削除
            if force_download or not self.db_path.exists():
                self.clean_existing_data()

            # 2. データダウンロード
            if not self.download_fdc_data(force_download):
                return False

            # 3. ZIP展開
            if not self.extract_zip_data():
                return False

            # 4. データベーススキーマ作成
            self.create_database_schema()

            # 5. CSVデータインポート
            if not self.import_csv_data():
                return False

            # 6. データベース確認
            if not self.verify_database():
                return False

            logger.info("=== FDCデータベースセットアップ完了 ===")
            logger.info(f"データベースファイル: {self.db_path}")
            return True

        except Exception as e:
            logger.error(f"セットアップエラー: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description='FoodData Central データベースセットアップ')
    parser.add_argument('--force-download', action='store_true',
                       help='既存ファイルを無視して強制的にダウンロード')

    args = parser.parse_args()

    # プロジェクトルートを特定
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent  # apps/barcode_api/scripts -> project root

    setup = FDCDatabaseSetup(str(project_root))
    success = setup.run_setup(force_download=args.force_download)

    if success:
        print("\n✅ FDCデータベースセットアップが正常に完了しました")
        sys.exit(0)
    else:
        print("\n❌ FDCデータベースセットアップに失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    main()