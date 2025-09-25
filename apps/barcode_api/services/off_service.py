#!/usr/bin/env python3
"""
Open Food Facts APIサービス

FDC未ヒット時のフォールバック検索用サービス
"""

import httpx
import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

from ..models.nutrition import NutritionResponse, ProductInfo, MainNutrients, ServingNutrients, AlternativeNutrients, HouseholdServingInfo

logger = logging.getLogger(__name__)


class OpenFoodFactsService:
    """Open Food Facts APIクライアント"""

    def __init__(self, timeout: float = 10.0):
        """
        サービスの初期化

        Args:
            timeout: HTTPリクエストのタイムアウト秒数
        """
        self.base_url = "https://world.openfoodfacts.org/api/v0"
        self.timeout = timeout
        self.session = None

        # SmartUnitGeneratorを初期化
        from ..utils.smart_unit_generator import SmartUnitGenerator
        self.unit_generator = SmartUnitGenerator()

        logger.info(f"Open Food Facts サービス初期化完了: timeout={timeout}秒")

    async def _get_http_client(self) -> httpx.AsyncClient:
        """HTTPクライアントを取得（遅延初期化）"""
        if self.session is None:
            self.session = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers={
                    'User-Agent': 'meal-analysis-api/1.0 (https://github.com/user/repo)'
                }
            )
        return self.session

    async def lookup_barcode(self, gtin: str) -> Optional[NutritionResponse]:
        """
        バーコードから栄養情報を取得

        Args:
            gtin: GTIN/バーコード文字列

        Returns:
            栄養情報レスポンス、見つからない場合はNone
        """
        try:
            logger.info(f"Open Food Facts検索開始: {gtin}")

            client = await self._get_http_client()

            # GTINを正規化
            normalized_gtin = gtin.strip()

            # Open Food Facts API呼び出し
            url = f"{self.base_url}/product/{normalized_gtin}.json"

            response = await client.get(url)
            response.raise_for_status()

            data = response.json()

            # ステータス確認
            if data.get('status') != 1:
                logger.warning(f"Open Food Facts: 製品が見つかりません: {gtin}")
                return None

            # 製品データを抽出
            product_data = data.get('product', {})
            if not product_data:
                logger.warning(f"Open Food Facts: 製品データが空です: {gtin}")
                return None

            # 栄養情報レスポンスを構築
            nutrition_response = await self._build_nutrition_response(gtin, product_data)

            if nutrition_response:
                logger.info(f"Open Food Facts検索成功: {gtin} -> {product_data.get('product_name', 'Unknown')}")

            return nutrition_response

        except httpx.TimeoutException:
            logger.error(f"Open Food Facts APIタイムアウト ({gtin}): {self.timeout}秒")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"Open Food Facts HTTPエラー ({gtin}): {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Open Food Facts検索エラー ({gtin}): {e}")
            return None

    async def _build_nutrition_response(self, gtin: str, product_data: Dict[str, Any]) -> Optional[NutritionResponse]:
        """製品データから栄養情報レスポンスを構築"""
        try:
            # 栄養素データ取得
            nutriments = product_data.get('nutriments', {})

            # 基本栄養素を抽出
            nutrients_100g = self._extract_main_nutrients(nutriments)
            if not nutrients_100g:
                logger.warning(f"Open Food Facts: 栄養素データが不足: {gtin}")
                return None

            # 製品情報構築（Open Food FactsにはFDC IDがないためNone）
            product_info = ProductInfo(
                fdc_id=None,  # Open Food Facts由来はNone
                gtin_upc=gtin,
                description=product_data.get('product_name', 'Unknown Product'),
                brand_owner=product_data.get('brands', ''),
                brand_name=product_data.get('brands', ''),
                ingredients=product_data.get('ingredients_text', ''),
                publication_date=datetime.now().strftime('%Y-%m-%d'),
                household_serving_fulltext=None
            )

            # サービング情報（Open Food Factsではサービングサイズが明確でない場合が多い）
            serving_size = nutriments.get('serving_size', 100)  # デフォルト100g
            serving_unit = "g"

            # 1食分の栄養素計算
            serving_factor = serving_size / 100.0
            nutrients_serving = ServingNutrients(
                energy_kcal=round(nutrients_100g.energy_kcal * serving_factor, 1) if nutrients_100g.energy_kcal else None,
                energy_kj=round(nutrients_100g.energy_kj * serving_factor, 1) if nutrients_100g.energy_kj else None,
                protein_g=round(nutrients_100g.protein_g * serving_factor, 2) if nutrients_100g.protein_g else None,
                fat_g=round(nutrients_100g.fat_g * serving_factor, 2) if nutrients_100g.fat_g else None,
                carbohydrate_g=round(nutrients_100g.carbohydrate_g * serving_factor, 2) if nutrients_100g.carbohydrate_g else None,
                fiber_g=round(nutrients_100g.fiber_g * serving_factor, 2) if nutrients_100g.fiber_g else None,
                sugars_g=round(nutrients_100g.sugars_g * serving_factor, 2) if nutrients_100g.sugars_g else None,
                saturated_fat_g=round(nutrients_100g.saturated_fat_g * serving_factor, 2) if nutrients_100g.saturated_fat_g else None,
                trans_fat_g=round(nutrients_100g.trans_fat_g * serving_factor, 2) if nutrients_100g.trans_fat_g else None,
                cholesterol_mg=round(nutrients_100g.cholesterol_mg * serving_factor, 2) if nutrients_100g.cholesterol_mg else None,
                sodium_mg=round(nutrients_100g.sodium_mg * serving_factor, 1) if nutrients_100g.sodium_mg else None,
                calcium_mg=round(nutrients_100g.calcium_mg * serving_factor, 1) if nutrients_100g.calcium_mg else None,
                iron_mg=round(nutrients_100g.iron_mg * serving_factor, 2) if nutrients_100g.iron_mg else None,
                potassium_mg=round(nutrients_100g.potassium_mg * serving_factor, 1) if nutrients_100g.potassium_mg else None,
                vitamin_c_mg=round(nutrients_100g.vitamin_c_mg * serving_factor, 1) if nutrients_100g.vitamin_c_mg else None,
                vitamin_a_iu=round(nutrients_100g.vitamin_a_iu * serving_factor, 1) if nutrients_100g.vitamin_a_iu else None,
                vitamin_d_iu=round(nutrients_100g.vitamin_d_iu * serving_factor, 1) if nutrients_100g.vitamin_d_iu else None
            )

            # スマートユニットオプションを生成
            unit_options = None
            try:
                unit_options = self.unit_generator.generate_unit_options(
                    nutrients_100g=nutrients_100g,
                    product_info=product_info,
                    household_serving_info=None,  # OFF由来では基本的にNone
                    serving_size_g=serving_size if serving_size != 100 else None
                )
                logger.debug(f"OFF スマートユニット生成完了: {len(unit_options)}個 ({gtin})")
            except Exception as e:
                logger.warning(f"OFF スマートユニット生成エラー ({gtin}): {e}")

            return NutritionResponse(
                success=True,
                gtin=gtin,
                product=product_info,
                serving_info={
                    "serving_size": serving_size,
                    "serving_unit": serving_unit
                },
                household_serving_info=None,
                nutrients_per_100g=nutrients_100g,
                nutrients_per_serving=nutrients_serving,
                alternative_nutrients=[],  # Open Food Factsでは追加単位計算は省略
                unit_options=unit_options,
                all_nutrients=None,
                data_source="Open Food Facts",
                cached=False
            )

        except Exception as e:
            logger.error(f"Open Food Facts レスポンス構築エラー ({gtin}): {e}")
            return None

    def _extract_main_nutrients(self, nutriments: Dict[str, Any]) -> Optional[MainNutrients]:
        """栄養素データから主要栄養素を抽出"""
        try:
            # Open Food Factsのエネルギー値はkJで保存されている
            energy_kj = nutriments.get('energy_100g')
            energy_kcal = nutriments.get('energy-kcal_100g')

            # kJからkcal変換（必要に応じて）
            if energy_kj and not energy_kcal:
                energy_kcal = round(energy_kj / 4.184, 1)

            # ナトリウムをソルトに変換
            sodium_g = nutriments.get('sodium_100g')
            salt_g = nutriments.get('salt_100g')
            if sodium_g and not salt_g:
                salt_g = sodium_g * 2.54  # ナトリウム → 塩換算

            return MainNutrients(
                energy_kcal=energy_kcal,
                energy_kj=energy_kj,
                protein_g=nutriments.get('proteins_100g'),
                fat_g=nutriments.get('fat_100g'),
                carbohydrate_g=nutriments.get('carbohydrates_100g'),
                fiber_g=nutriments.get('fiber_100g'),
                sugars_g=nutriments.get('sugars_100g'),
                saturated_fat_g=nutriments.get('saturated-fat_100g'),
                trans_fat_g=nutriments.get('trans-fat_100g'),
                cholesterol_mg=nutriments.get('cholesterol_100g'),
                sodium_mg=sodium_g * 1000 if sodium_g else None,  # g → mg変換
                calcium_mg=nutriments.get('calcium_100g'),
                iron_mg=nutriments.get('iron_100g'),
                potassium_mg=nutriments.get('potassium_100g'),
                vitamin_c_mg=nutriments.get('vitamin-c_100g'),
                vitamin_a_iu=nutriments.get('vitamin-a_100g'),
                vitamin_d_iu=nutriments.get('vitamin-d_100g')
            )

        except Exception as e:
            logger.error(f"栄養素抽出エラー: {e}")
            return None

    async def health_check(self) -> bool:
        """
        Open Food Facts APIのヘルスチェック

        Returns:
            API接続可能時True
        """
        try:
            # 有名な商品（Nutella）でテスト
            test_result = await self.lookup_barcode("3017624010701")
            return test_result is not None

        except Exception as e:
            logger.error(f"Open Food Facts ヘルスチェックエラー: {e}")
            return False

    async def close(self):
        """HTTPクライアントをクリーンアップ"""
        if self.session:
            await self.session.aclose()
            self.session = None

    def __del__(self):
        """デストラクタ"""
        if self.session:
            # 非同期クリーンアップは__del__では実行できないため警告のみ
            logger.warning("Open Food Facts セッションが適切にクローズされていません")


# グローバルインスタンス（シングルトン）
_off_instance: Optional[OpenFoodFactsService] = None


def get_off_service(timeout: float = 10.0) -> OpenFoodFactsService:
    """
    Open Food Facts サービスのシングルトンインスタンスを取得

    Args:
        timeout: HTTPリクエストのタイムアウト秒数

    Returns:
        OpenFoodFactsServiceインスタンス
    """
    global _off_instance

    if _off_instance is None:
        _off_instance = OpenFoodFactsService(timeout=timeout)
        logger.info("グローバル Open Food Facts サービスインスタンス作成")

    return _off_instance


async def cleanup_off_service():
    """グローバルサービスインスタンスのクリーンアップ"""
    global _off_instance

    if _off_instance:
        await _off_instance.close()
        _off_instance = None
        logger.info("グローバル Open Food Facts サービスインスタンスクリーンアップ完了")