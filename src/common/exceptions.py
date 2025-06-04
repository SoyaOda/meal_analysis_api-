"""
カスタム例外クラス定義

栄養推定ワークフロー用の例外階層
"""


class NutrientEstimationError(Exception):
    """栄養推定プロセス全般のエラー"""
    pass


class InvalidImageFormatError(NutrientEstimationError):
    """無効な画像形式エラー"""
    pass


class FoodRecognitionError(NutrientEstimationError):
    """食品認識エラー"""
    pass


class DatabaseConnectionError(NutrientEstimationError):
    """データベース接続エラー"""
    pass


class DatabaseQueryError(NutrientEstimationError):
    """データベースクエリエラー"""
    pass


class InterpretationRuleError(NutrientEstimationError):
    """データ解釈ルールエラー"""
    pass


class NutritionCalculationError(NutrientEstimationError):
    """栄養計算エラー"""
    pass 