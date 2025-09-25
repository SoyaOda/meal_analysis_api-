#!/usr/bin/env python3
"""
栄養情報データモデル

FDCデータベースから取得した栄養情報を構造化するためのPydanticモデル
"""

from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from datetime import datetime


class NutrientInfo(BaseModel):
    """栄養素情報"""
    nutrient_id: int = Field(..., description="栄養素ID（FDC標準）")
    name: str = Field(..., description="栄養素名")
    unit: str = Field(..., description="単位")
    amount_per_100g: float = Field(..., description="100gあたりの含有量")

    class Config:
        json_schema_extra = {
            "example": {
                "nutrient_id": 1008,
                "name": "Energy",
                "unit": "kcal",
                "amount_per_100g": 250.5
            }
        }


class ServingInfo(BaseModel):
    """サービング情報"""
    serving_size: Optional[float] = Field(None, description="1食分のサイズ")
    serving_unit: Optional[str] = Field(None, description="サービング単位")

    class Config:
        json_schema_extra = {
            "example": {
                "serving_size": 30.0,
                "serving_unit": "g"
            }
        }


class ProductInfo(BaseModel):
    """製品基本情報"""
    fdc_id: Optional[int] = Field(None, description="FDC ID（FDCデータベース由来の場合のみ）")
    gtin_upc: str = Field(..., description="GTINまたはUPCコード")
    description: str = Field(..., description="製品名・説明")
    brand_owner: Optional[str] = Field(None, description="ブランドオーナー")
    brand_name: Optional[str] = Field(None, description="ブランド名")
    ingredients: Optional[str] = Field(None, description="原材料表示")
    publication_date: Optional[str] = Field(None, description="データ公開日")
    household_serving_fulltext: Optional[str] = Field(None, description="家庭用サービング表記（カップ、個数など）")

    class Config:
        json_schema_extra = {
            "example": {
                "fdc_id": 123456,
                "gtin_upc": "012345678901",
                "description": "Chocolate Chip Cookies",
                "brand_owner": "Sample Food Company",
                "brand_name": "Sample Brand",
                "ingredients": "Wheat flour, sugar, chocolate chips...",
                "publication_date": "2024-04-24",
                "household_serving_fulltext": "2 cookies (30g)"
            }
        }


class MainNutrients(BaseModel):
    """主要栄養素（拡張版）"""
    # エネルギー
    energy_kcal: Optional[float] = Field(None, description="エネルギー (kcal/100g)")
    energy_kj: Optional[float] = Field(None, description="エネルギー (kJ/100g)")
    
    # 三大栄養素
    protein_g: Optional[float] = Field(None, description="タンパク質 (g/100g)")
    fat_g: Optional[float] = Field(None, description="脂質 (g/100g)")
    carbohydrate_g: Optional[float] = Field(None, description="炭水化物 (g/100g)")
    
    # 詳細な炭水化物
    fiber_g: Optional[float] = Field(None, description="食物繊維 (g/100g)")
    sugars_g: Optional[float] = Field(None, description="糖類 (g/100g)")
    
    # 詳細な脂質
    saturated_fat_g: Optional[float] = Field(None, description="飽和脂肪酸 (g/100g)")
    trans_fat_g: Optional[float] = Field(None, description="トランス脂肪酸 (g/100g)")
    cholesterol_mg: Optional[float] = Field(None, description="コレステロール (mg/100g)")
    
    # 主要ミネラル
    sodium_mg: Optional[float] = Field(None, description="ナトリウム (mg/100g)")
    calcium_mg: Optional[float] = Field(None, description="カルシウム (mg/100g)")
    iron_mg: Optional[float] = Field(None, description="鉄 (mg/100g)")
    potassium_mg: Optional[float] = Field(None, description="カリウム (mg/100g)")
    
    # 主要ビタミン
    vitamin_c_mg: Optional[float] = Field(None, description="ビタミンC (mg/100g)")
    vitamin_a_iu: Optional[float] = Field(None, description="ビタミンA (IU/100g)")
    vitamin_d_iu: Optional[float] = Field(None, description="ビタミンD (IU/100g)")

    class Config:
        json_schema_extra = {
            "example": {
                "energy_kcal": 533.0,
                "protein_g": 16.67,
                "fat_g": 36.67,
                "carbohydrate_g": 36.67,
                "fiber_g": 6.7,
                "sugars_g": 3.33,
                "saturated_fat_g": 5.0,
                "sodium_mg": 633.0,
                "calcium_mg": 133.0,
                "iron_mg": 3.6
            }
        }


class ServingNutrients(BaseModel):
    """1食分の栄養素"""
    # エネルギー
    energy_kcal: Optional[float] = Field(None, description="エネルギー (kcal/食)")
    energy_kj: Optional[float] = Field(None, description="エネルギー (kJ/食)")
    
    # 三大栄養素
    protein_g: Optional[float] = Field(None, description="タンパク質 (g/食)")
    fat_g: Optional[float] = Field(None, description="脂質 (g/食)")
    carbohydrate_g: Optional[float] = Field(None, description="炭水化物 (g/食)")
    
    # 詳細な炭水化物
    fiber_g: Optional[float] = Field(None, description="食物繊維 (g/食)")
    sugars_g: Optional[float] = Field(None, description="糖類 (g/食)")
    
    # 詳細な脂質
    saturated_fat_g: Optional[float] = Field(None, description="飽和脂肪酸 (g/食)")
    trans_fat_g: Optional[float] = Field(None, description="トランス脂肪酸 (g/食)")
    cholesterol_mg: Optional[float] = Field(None, description="コレステロール (mg/食)")
    
    # 主要ミネラル
    sodium_mg: Optional[float] = Field(None, description="ナトリウム (mg/食)")
    calcium_mg: Optional[float] = Field(None, description="カルシウム (mg/食)")
    iron_mg: Optional[float] = Field(None, description="鉄 (mg/食)")
    potassium_mg: Optional[float] = Field(None, description="カリウム (mg/食)")
    
    # 主要ビタミン
    vitamin_c_mg: Optional[float] = Field(None, description="ビタミンC (mg/食)")
    vitamin_a_iu: Optional[float] = Field(None, description="ビタミンA (IU/食)")
    vitamin_d_iu: Optional[float] = Field(None, description="ビタミンD (IU/食)")

    class Config:
        json_schema_extra = {
            "example": {
                "energy_kcal": 135.0,
                "fat_g": 5.6,
                "carbohydrate_g": 19.6,
                "protein_g": 2.0,
                "fiber_g": 1.5,
                "sodium_mg": 120.0,
                "calcium_mg": 25.0
            }
        }

class HouseholdServingInfo(BaseModel):
    """家庭用サービング情報"""
    original_text: Optional[str] = Field(None, description="元のテキスト（例：'0.25 cup', '27 Crackers'）")
    unit_type: Optional[str] = Field(None, description="単位タイプ（volume, count, weight）")
    quantity: Optional[float] = Field(None, description="数量")
    unit: Optional[str] = Field(None, description="単位（cup, crackers, tbsp等）")
    weight_equivalent_g: Optional[float] = Field(None, description="重量換算（グラム）")

    class Config:
        json_schema_extra = {
            "example": {
                "original_text": "0.25 cup",
                "unit_type": "volume",
                "quantity": 0.25,
                "unit": "cup",
                "weight_equivalent_g": 30.0
            }
        }


class AlternativeNutrients(BaseModel):
    """代替単位での栄養素情報"""
    unit_description: str = Field(..., description="単位の説明")
    energy_kcal: Optional[float] = Field(None, description="エネルギー (kcal)")
    energy_kj: Optional[float] = Field(None, description="エネルギー (kJ)")
    protein_g: Optional[float] = Field(None, description="タンパク質 (g)")
    fat_g: Optional[float] = Field(None, description="脂質 (g)")
    carbohydrate_g: Optional[float] = Field(None, description="炭水化物 (g)")
    fiber_g: Optional[float] = Field(None, description="食物繊維 (g)")
    sugars_g: Optional[float] = Field(None, description="糖類 (g)")
    saturated_fat_g: Optional[float] = Field(None, description="飽和脂肪酸 (g)")
    trans_fat_g: Optional[float] = Field(None, description="トランス脂肪酸 (g)")
    cholesterol_mg: Optional[float] = Field(None, description="コレステロール (mg)")
    sodium_mg: Optional[float] = Field(None, description="ナトリウム (mg)")
    calcium_mg: Optional[float] = Field(None, description="カルシウム (mg)")
    iron_mg: Optional[float] = Field(None, description="鉄 (mg)")
    potassium_mg: Optional[float] = Field(None, description="カリウム (mg)")
    vitamin_c_mg: Optional[float] = Field(None, description="ビタミンC (mg)")
    vitamin_a_iu: Optional[float] = Field(None, description="ビタミンA (IU)")
    vitamin_d_iu: Optional[float] = Field(None, description="ビタミンD (IU)")

    class Config:
        json_schema_extra = {
            "example": {
                "unit_description": "per 1 cup",
                "energy_kcal": 540.0,
                "protein_g": 20.0,
                "fat_g": 44.0,
                "carbohydrate_g": 44.0
            }
        }

class NutrientUnitOption(BaseModel):
    """単位オプションごとの栄養価"""
    unit_id: str = Field(..., description="単位ID（1g, 1cup, 1piece等）")
    display_name: str = Field(..., description="表示名")
    unit_type: str = Field(..., description="単位種別（weight/volume/count）")
    is_primary: bool = Field(False, description="メーカー推奨単位かどうか")
    equivalent_weight_g: Optional[float] = Field(None, description="グラム換算値")
    
    # 栄養価データ
    energy_kcal: Optional[float] = Field(None, description="エネルギー (kcal)")
    energy_kj: Optional[float] = Field(None, description="エネルギー (kJ)")
    protein_g: Optional[float] = Field(None, description="タンパク質 (g)")
    fat_g: Optional[float] = Field(None, description="脂質 (g)")
    carbohydrate_g: Optional[float] = Field(None, description="炭水化物 (g)")
    fiber_g: Optional[float] = Field(None, description="食物繊維 (g)")
    sugars_g: Optional[float] = Field(None, description="糖類 (g)")
    saturated_fat_g: Optional[float] = Field(None, description="飽和脂肪酸 (g)")
    trans_fat_g: Optional[float] = Field(None, description="トランス脂肪酸 (g)")
    cholesterol_mg: Optional[float] = Field(None, description="コレステロール (mg)")
    sodium_mg: Optional[float] = Field(None, description="ナトリウム (mg)")
    calcium_mg: Optional[float] = Field(None, description="カルシウム (mg)")
    iron_mg: Optional[float] = Field(None, description="鉄 (mg)")
    potassium_mg: Optional[float] = Field(None, description="カリウム (mg)")
    vitamin_c_mg: Optional[float] = Field(None, description="ビタミンC (mg)")
    vitamin_a_iu: Optional[float] = Field(None, description="ビタミンA (IU)")
    vitamin_d_iu: Optional[float] = Field(None, description="ビタミンD (IU)")

    class Config:
        json_schema_extra = {
            "example": {
                "unit_id": "1cup",
                "display_name": "1 cup (30g)",
                "unit_type": "volume",
                "is_primary": True,
                "equivalent_weight_g": 30.0,
                "energy_kcal": 135.0,
                "protein_g": 5.0,
                "fat_g": 11.0,
                "carbohydrate_g": 11.0
            }
        }


class NutritionResponse(BaseModel):
    """バーコード検索APIのレスポンス"""
    success: bool = Field(..., description="検索成功フラグ")
    gtin: str = Field(..., description="検索したGTIN/UPCコード")
    product: Optional[ProductInfo] = Field(None, description="製品情報")
    serving_info: Optional[ServingInfo] = Field(None, description="サービング情報")
    household_serving_info: Optional[HouseholdServingInfo] = Field(None, description="家庭用サービング情報")
    nutrients_per_100g: Optional[MainNutrients] = Field(None, description="100gあたりの主要栄養素")
    nutrients_per_serving: Optional[ServingNutrients] = Field(None, description="1食分の栄養素")
    alternative_nutrients: Optional[List[AlternativeNutrients]] = Field(None, description="代替単位での栄養素")
    unit_options: Optional[List[NutrientUnitOption]] = Field(None, description="複数単位での栄養価オプション")
    all_nutrients: Optional[List[NutrientInfo]] = Field(None, description="全栄養素詳細情報")
    data_source: str = Field(default="FDC", description="データソース")
    cached: bool = Field(default=False, description="キャッシュから取得したかどうか")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "gtin": "012345678901",
                "product": {
                    "fdc_id": 123456,
                    "gtin_upc": "012345678901",
                    "description": "Chocolate Chip Cookies",
                    "brand_owner": "Sample Food Company",
                    "brand_name": "Sample Brand",
                    "household_serving_fulltext": "2 cookies (30g)"
                },
                "serving_info": {
                    "serving_size": 30.0,
                    "serving_unit": "g"
                },
                "household_serving_info": {
                    "original_text": "2 cookies (30g)",
                    "unit_type": "count",
                    "quantity": 2.0,
                    "unit": "cookies",
                    "weight_equivalent_g": 30.0
                },
                "nutrients_per_100g": {
                    "energy_kcal": 450.0,
                    "fat_g": 18.5,
                    "carbohydrate_g": 65.2,
                    "protein_g": 6.8
                },
                "nutrients_per_serving": {
                    "energy_kcal": 135.0,
                    "fat_g": 5.6,
                    "carbohydrate_g": 19.6,
                    "protein_g": 2.0
                },
                "alternative_nutrients": [
                    {
                        "unit_description": "per cookie",
                        "energy_kcal": 67.5,
                        "fat_g": 2.8,
                        "carbohydrate_g": 9.8,
                        "protein_g": 1.0
                    }
                ],
                "unit_options": [
                    {
                        "unit_id": "1g",
                        "display_name": "1グラム",
                        "unit_type": "weight",
                        "is_primary": False,
                        "equivalent_weight_g": 1.0,
                        "energy_kcal": 4.5,
                        "fat_g": 0.185,
                        "carbohydrate_g": 0.652,
                        "protein_g": 0.068
                    },
                    {
                        "unit_id": "1cookie",
                        "display_name": "1枚（クッキー）",
                        "unit_type": "count",
                        "is_primary": True,
                        "equivalent_weight_g": 15.0,
                        "energy_kcal": 67.5,
                        "fat_g": 2.8,
                        "carbohydrate_g": 9.8,
                        "protein_g": 1.0
                    }
                ],
                "data_source": "FDC",
                "cached": False
            }
        }


class BarcodeRequest(BaseModel):
    """バーコード検索リクエスト"""
    gtin: str = Field(..., description="GTINまたはUPCコード", min_length=8, max_length=14)
    include_all_nutrients: bool = Field(default=False, description="全栄養素情報を含めるかどうか")

    class Config:
        json_schema_extra = {
            "example": {
                "gtin": "012345678901",
                "include_all_nutrients": False
            }
        }


class ErrorResponse(BaseModel):
    """エラーレスポンス"""
    success: bool = Field(default=False, description="成功フラグ")
    error_code: str = Field(..., description="エラーコード")
    error_message: str = Field(..., description="エラーメッセージ")
    gtin: Optional[str] = Field(None, description="検索したGTIN/UPCコード")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error_code": "PRODUCT_NOT_FOUND",
                "error_message": "指定されたバーコードの製品が見つかりません",
                "gtin": "012345678901"
            }
        }


# 定数: 主要栄養素のFDC ID
class NutrientConstants:
    """FDCの主要栄養素ID定数"""
    # 基本栄養素
    ENERGY_KCAL = 1008  # Energy (kcal)
    ENERGY_KJ = 1062    # Energy (kJ) 
    FAT = 1004          # Total lipid (fat) (g)
    CARBOHYDRATE = 1005 # Carbohydrate, by difference (g)
    PROTEIN = 1003      # Protein (g)
    
    # 詳細な炭水化物
    FIBER = 1079        # Fiber, total dietary (g)
    SUGARS = 1063       # Sugars, Total (g)
    
    # 詳細な脂質
    SATURATED_FAT = 1258    # Fatty acids, total saturated (g)
    TRANS_FAT = 1257        # Fatty acids, total trans (g) 
    CHOLESTEROL = 1253      # Cholesterol (mg)
    
    # 主要ミネラル
    SODIUM = 1093       # Sodium, Na (mg)
    CALCIUM = 1087      # Calcium, Ca (mg)
    IRON = 1089         # Iron, Fe (mg)
    POTASSIUM = 1092    # Potassium, K (mg)
    
    # 主要ビタミン
    VITAMIN_C = 1162    # Vitamin C, total ascorbic acid (mg)
    VITAMIN_A_IU = 1104 # Vitamin A, IU (IU)
    VITAMIN_D_IU = 1114 # Vitamin D (D2 + D3) (IU)

    # 栄養素名マッピング  
    NUTRIENT_NAMES = {
        ENERGY_KCAL: "Energy",
        ENERGY_KJ: "Energy", 
        FAT: "Total lipid (fat)",
        CARBOHYDRATE: "Carbohydrate, by difference",
        PROTEIN: "Protein",
        FIBER: "Fiber, total dietary",
        SUGARS: "Sugars, Total",
        SATURATED_FAT: "Fatty acids, total saturated",
        TRANS_FAT: "Fatty acids, total trans",
        CHOLESTEROL: "Cholesterol",
        SODIUM: "Sodium, Na",
        CALCIUM: "Calcium, Ca", 
        IRON: "Iron, Fe",
        POTASSIUM: "Potassium, K",
        VITAMIN_C: "Vitamin C, total ascorbic acid",
        VITAMIN_A_IU: "Vitamin A, IU",
        VITAMIN_D_IU: "Vitamin D (D2 + D3)"
    }

    # 単位マッピング
    NUTRIENT_UNITS = {
        ENERGY_KCAL: "kcal",
        ENERGY_KJ: "kJ",
        FAT: "g",
        CARBOHYDRATE: "g", 
        PROTEIN: "g",
        FIBER: "g",
        SUGARS: "g",
        SATURATED_FAT: "g",
        TRANS_FAT: "g",
        CHOLESTEROL: "mg",
        SODIUM: "mg",
        CALCIUM: "mg",
        IRON: "mg", 
        POTASSIUM: "mg",
        VITAMIN_C: "mg",
        VITAMIN_A_IU: "IU",
        VITAMIN_D_IU: "IU"
    }