#!/usr/bin/env python3
"""
FDCデータベース検索サービス

FDCデータベースからバーコード情報と栄養情報を検索するサービス
"""

import sqlite3
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

from ..models.nutrition import (
    ProductInfo, ServingInfo, MainNutrients, ServingNutrients,
    NutrientInfo, NutritionResponse, NutrientConstants,
    HouseholdServingInfo, AlternativeNutrients
)
from ..utils.unit_parser import UnitParser


logger = logging.getLogger(__name__)


class FDCDatabaseService:
    """FDCデータベース検索サービス"""

    def __init__(self, database_path: Optional[str] = None):
        """
        FDCデータベースサービスの初期化

        Args:
            database_path: データベースファイルのパス。Noneの場合はデフォルトパスを使用
        """
        if database_path is None:
            # プロジェクトルートからの相対パス
            project_root = Path(__file__).parent.parent.parent.parent
            self.db_path = project_root / "db" / "FoodData_Central" / "fdc_barcode.db"
        else:
            self.db_path = Path(database_path)

        if not self.db_path.exists():
            raise FileNotFoundError(f"FDCデータベースファイルが見つかりません: {self.db_path}")

        # 単位解析器を初期化
        self.unit_parser = UnitParser()

        logger.info(f"FDCデータベース初期化完了: {self.db_path}")

    def search_by_gtin(self, gtin: str, include_all_nutrients: bool = False) -> Optional[NutritionResponse]:
        """
        GTINコードで製品を検索（多単位栄養価対応）

        Args:
            gtin: GTINまたはUPCコード
            include_all_nutrients: 全栄養素情報を含めるかどうか

        Returns:
            栄養情報レスポンス、見つからない場合はNone
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 辞書形式でアクセス可能にする

            # 1. GTINから製品情報を検索（最新版を取得）
            product_info = self._get_product_by_gtin(conn, gtin)
            if not product_info:
                conn.close()
                return None

            # 2. 栄養情報を取得
            main_nutrients = self._get_main_nutrients(conn, product_info['fdc_id'])

            # 3. サービング情報を取得
            serving_info = self._get_serving_info(product_info)

            # 4. サービングあたりの栄養素を計算
            serving_nutrients = self._calculate_serving_nutrients(
                main_nutrients, serving_info
            )

            # 5. household_serving_fulltextを解析
            household_serving_info = None
            alternative_nutrients = []
            
            if product_info.get('household_serving_fulltext'):
                parsed_unit = self.unit_parser.parse_household_serving(
                    product_info['household_serving_fulltext'],
                    product_info['description']
                )
                
                if parsed_unit:
                    # HouseholdServingInfo作成
                    household_serving_info = HouseholdServingInfo(
                        original_text=parsed_unit.original_text,
                        unit_type=parsed_unit.unit_type,
                        quantity=parsed_unit.quantity,
                        unit=parsed_unit.unit,
                        weight_equivalent_g=parsed_unit.weight_equivalent_g
                    )

                    # 代替単位での栄養価を計算
                    if serving_info and serving_info.serving_size:
                        # 100gあたりの栄養素を辞書に変換
                        nutrients_dict = {
                            "energy_kcal": main_nutrients.energy_kcal,
                            "energy_kj": main_nutrients.energy_kj,
                            "protein_g": main_nutrients.protein_g,
                            "fat_g": main_nutrients.fat_g,
                            "carbohydrate_g": main_nutrients.carbohydrate_g,
                            "fiber_g": main_nutrients.fiber_g,
                            "sugars_g": main_nutrients.sugars_g,
                            "saturated_fat_g": main_nutrients.saturated_fat_g,
                            "trans_fat_g": main_nutrients.trans_fat_g,
                            "cholesterol_mg": main_nutrients.cholesterol_mg,
                            "sodium_mg": main_nutrients.sodium_mg,
                            "calcium_mg": main_nutrients.calcium_mg,
                            "iron_mg": main_nutrients.iron_mg,
                            "potassium_mg": main_nutrients.potassium_mg,
                            "vitamin_c_mg": main_nutrients.vitamin_c_mg,
                            "vitamin_a_iu": main_nutrients.vitamin_a_iu,
                            "vitamin_d_iu": main_nutrients.vitamin_d_iu
                        }

                        alt_nutrients = self.unit_parser.calculate_alternative_units(
                            nutrients_dict,
                            serving_info.serving_size,
                            parsed_unit,
                            product_info['description']
                        )

                        # AlternativeNutrientsオブジェクトに変換
                        for alt in alt_nutrients:
                            alternative_nutrients.append(AlternativeNutrients(**alt))

            # 6. 全栄養素情報を取得（オプション）
            all_nutrients = None
            if include_all_nutrients:
                all_nutrients = self._get_all_nutrients(conn, product_info['fdc_id'])

            conn.close()

            return NutritionResponse(
                success=True,
                gtin=gtin,
                product=ProductInfo(**product_info),
                serving_info=serving_info,
                household_serving_info=household_serving_info,
                nutrients_per_100g=main_nutrients,
                nutrients_per_serving=serving_nutrients,
                alternative_nutrients=alternative_nutrients if alternative_nutrients else None,
                all_nutrients=all_nutrients,
                data_source="FDC",
                cached=False
            )

        except Exception as e:
            logger.error(f"GTIN検索エラー ({gtin}): {e}")
            if 'conn' in locals():
                conn.close()
            return None

    def _get_product_by_gtin(self, conn: sqlite3.Connection, gtin: str) -> Optional[Dict[str, Any]]:
        """
        GTINから製品情報を取得（最新版）

        Args:
            conn: データベース接続
            gtin: GTINコード

        Returns:
            製品情報辞書、見つからない場合はNone
        """
        cursor = conn.cursor()

        # 重複GTINの場合は最新のpublication_dateを持つレコードを取得
        query = """
        SELECT
            bf.fdc_id,
            bf.gtin_upc,
            bf.brand_owner,
            bf.brand_name,
            bf.ingredients,
            bf.serving_size,
            bf.serving_size_unit,
            bf.household_serving_fulltext,
            f.description,
            f.publication_date
        FROM branded_food bf
        JOIN food f ON bf.fdc_id = f.fdc_id
        WHERE bf.gtin_upc = ?
        ORDER BY f.publication_date DESC, bf.fdc_id DESC
        LIMIT 1
        """

        cursor.execute(query, (gtin,))
        row = cursor.fetchone()

        if row:
            return dict(row)
        return None

    def _get_main_nutrients(self, conn: sqlite3.Connection, fdc_id: int) -> Optional[MainNutrients]:
        """
        主要栄養素（拡張版）を取得

        Args:
            conn: データベース接続
            fdc_id: FDC ID

        Returns:
            主要栄養素情報
        """
        cursor = conn.cursor()

        # 拡張された栄養素のIDリスト
        nutrient_ids = [
            NutrientConstants.ENERGY_KCAL,
            NutrientConstants.ENERGY_KJ,
            NutrientConstants.FAT,
            NutrientConstants.CARBOHYDRATE,
            NutrientConstants.PROTEIN,
            NutrientConstants.FIBER,
            NutrientConstants.SUGARS,
            NutrientConstants.SATURATED_FAT,
            NutrientConstants.TRANS_FAT,
            NutrientConstants.CHOLESTEROL,
            NutrientConstants.SODIUM,
            NutrientConstants.CALCIUM,
            NutrientConstants.IRON,
            NutrientConstants.POTASSIUM,
            NutrientConstants.VITAMIN_C,
            NutrientConstants.VITAMIN_A_IU,
            NutrientConstants.VITAMIN_D_IU
        ]

        placeholders = ','.join(['?'] * len(nutrient_ids))
        query = f"""
        SELECT nutrient_id, amount
        FROM food_nutrient
        WHERE fdc_id = ? AND nutrient_id IN ({placeholders})
        """

        cursor.execute(query, [fdc_id] + nutrient_ids)
        rows = cursor.fetchall()

        # 栄養素IDをキーとする辞書に変換
        nutrients = {row['nutrient_id']: row['amount'] for row in rows}

        return MainNutrients(
            energy_kcal=nutrients.get(NutrientConstants.ENERGY_KCAL),
            energy_kj=nutrients.get(NutrientConstants.ENERGY_KJ),
            protein_g=nutrients.get(NutrientConstants.PROTEIN),
            fat_g=nutrients.get(NutrientConstants.FAT),
            carbohydrate_g=nutrients.get(NutrientConstants.CARBOHYDRATE),
            fiber_g=nutrients.get(NutrientConstants.FIBER),
            sugars_g=nutrients.get(NutrientConstants.SUGARS),
            saturated_fat_g=nutrients.get(NutrientConstants.SATURATED_FAT),
            trans_fat_g=nutrients.get(NutrientConstants.TRANS_FAT),
            cholesterol_mg=nutrients.get(NutrientConstants.CHOLESTEROL),
            sodium_mg=nutrients.get(NutrientConstants.SODIUM),
            calcium_mg=nutrients.get(NutrientConstants.CALCIUM),
            iron_mg=nutrients.get(NutrientConstants.IRON),
            potassium_mg=nutrients.get(NutrientConstants.POTASSIUM),
            vitamin_c_mg=nutrients.get(NutrientConstants.VITAMIN_C),
            vitamin_a_iu=nutrients.get(NutrientConstants.VITAMIN_A_IU),
            vitamin_d_iu=nutrients.get(NutrientConstants.VITAMIN_D_IU)
        )

    def _get_serving_info(self, product_info: Dict[str, Any]) -> Optional[ServingInfo]:
        """
        サービング情報を取得

        Args:
            product_info: 製品情報

        Returns:
            サービング情報
        """
        serving_size = product_info.get('serving_size')
        serving_unit = product_info.get('serving_size_unit')

        if serving_size:
            return ServingInfo(
                serving_size=float(serving_size),
                serving_unit=serving_unit
            )
        return None

    def _calculate_serving_nutrients(self, main_nutrients: MainNutrients,
                                   serving_info: Optional[ServingInfo]) -> Optional[ServingNutrients]:
        """
        1食分の栄養素を計算（拡張版）

        Args:
            main_nutrients: 100gあたりの主要栄養素
            serving_info: サービング情報

        Returns:
            1食分の栄養素
        """
        if not serving_info or not serving_info.serving_size:
            return None

        # グラム単位の場合のみ計算（ml等の場合は密度がわからないため計算しない）
        if serving_info.serving_unit and serving_info.serving_unit.lower() != 'g':
            return None

        serving_ratio = serving_info.serving_size / 100.0

        def calculate_serving_amount(amount_per_100g: Optional[float]) -> Optional[float]:
            if amount_per_100g is None:
                return None
            return round(amount_per_100g * serving_ratio, 2)

        return ServingNutrients(
            energy_kcal=calculate_serving_amount(main_nutrients.energy_kcal),
            energy_kj=calculate_serving_amount(main_nutrients.energy_kj),
            protein_g=calculate_serving_amount(main_nutrients.protein_g),
            fat_g=calculate_serving_amount(main_nutrients.fat_g),
            carbohydrate_g=calculate_serving_amount(main_nutrients.carbohydrate_g),
            fiber_g=calculate_serving_amount(main_nutrients.fiber_g),
            sugars_g=calculate_serving_amount(main_nutrients.sugars_g),
            saturated_fat_g=calculate_serving_amount(main_nutrients.saturated_fat_g),
            trans_fat_g=calculate_serving_amount(main_nutrients.trans_fat_g),
            cholesterol_mg=calculate_serving_amount(main_nutrients.cholesterol_mg),
            sodium_mg=calculate_serving_amount(main_nutrients.sodium_mg),
            calcium_mg=calculate_serving_amount(main_nutrients.calcium_mg),
            iron_mg=calculate_serving_amount(main_nutrients.iron_mg),
            potassium_mg=calculate_serving_amount(main_nutrients.potassium_mg),
            vitamin_c_mg=calculate_serving_amount(main_nutrients.vitamin_c_mg),
            vitamin_a_iu=calculate_serving_amount(main_nutrients.vitamin_a_iu),
            vitamin_d_iu=calculate_serving_amount(main_nutrients.vitamin_d_iu)
        )

    def _get_all_nutrients(self, conn: sqlite3.Connection, fdc_id: int) -> List[NutrientInfo]:
        """
        全栄養素情報を取得

        Args:
            conn: データベース接続
            fdc_id: FDC ID

        Returns:
            全栄養素情報のリスト
        """
        cursor = conn.cursor()

        query = """
        SELECT
            fn.nutrient_id,
            fn.amount,
            n.name,
            n.unit_name
        FROM food_nutrient fn
        JOIN nutrient n ON fn.nutrient_id = n.id
        WHERE fn.fdc_id = ?
        ORDER BY n.rank, n.id
        """

        cursor.execute(query, (fdc_id,))
        rows = cursor.fetchall()

        nutrients = []
        for row in rows:
            if row['amount'] is not None:
                nutrients.append(NutrientInfo(
                    nutrient_id=row['nutrient_id'],
                    name=row['name'],
                    unit=row['unit_name'] or '',
                    amount_per_100g=float(row['amount'])
                ))

        return nutrients

    def get_database_stats(self) -> Dict[str, int]:
        """
        データベース統計情報を取得

        Returns:
            統計情報辞書
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            stats = {}

            # 各テーブルの行数を取得
            tables = ['food', 'branded_food', 'food_nutrient', 'nutrient']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()[0]

            # バーコード付き商品数
            cursor.execute("SELECT COUNT(*) FROM branded_food WHERE gtin_upc IS NOT NULL AND gtin_upc != ''")
            stats['products_with_barcode'] = cursor.fetchone()[0]

            conn.close()
            return stats

        except Exception as e:
            logger.error(f"データベース統計取得エラー: {e}")
            return {}

    def health_check(self) -> bool:
        """
        データベース接続とテーブル存在確認

        Returns:
            正常な場合True
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 必要なテーブルの存在確認
            required_tables = ['food', 'branded_food', 'food_nutrient', 'nutrient']
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = {row[0] for row in cursor.fetchall()}

            missing_tables = set(required_tables) - existing_tables
            if missing_tables:
                logger.error(f"必要なテーブルが見つかりません: {missing_tables}")
                return False

            # 主要栄養素の存在確認
            main_nutrient_ids = [
                NutrientConstants.ENERGY_KCAL,
                NutrientConstants.FAT,
                NutrientConstants.CARBOHYDRATE,
                NutrientConstants.PROTEIN
            ]

            placeholders = ','.join(['?'] * len(main_nutrient_ids))
            cursor.execute(f"SELECT COUNT(*) FROM nutrient WHERE id IN ({placeholders})", main_nutrient_ids)
            nutrient_count = cursor.fetchone()[0]

            if nutrient_count < len(main_nutrient_ids):
                logger.warning(f"主要栄養素の一部が見つかりません。期待数: {len(main_nutrient_ids)}, 実際数: {nutrient_count}")

            conn.close()
            return True

        except Exception as e:
            logger.error(f"ヘルスチェックエラー: {e}")
            return False