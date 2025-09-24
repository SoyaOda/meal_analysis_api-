"""
MyNetDiary関連のユーティリティ関数
"""
import os
from typing import List, Set
from pathlib import Path

def load_mynetdiary_ingredient_names(exclude_uncooked: bool = False) -> List[str]:
    """
    MyNetDiary の食材名リストを読み込む
    
    Args:
        exclude_uncooked: uncooked 食材を除外するかどうか
    
    Returns:
        List[str]: MyNetDiary の食材名のリスト
    """
    # プロジェクトルートからの相対パス
    current_dir = Path(__file__).parent.parent.parent
    
    if exclude_uncooked:
        file_path = current_dir / "data" / "mynetdiary_search_names_no_uncooked.txt"
    else:
        file_path = current_dir / "data" / "mynetdiary_search_names.txt"
    
    if not file_path.exists():
        raise FileNotFoundError(f"MyNetDiary食材名リストが見つかりません: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        ingredient_names = [line.strip() for line in f if line.strip()]
    
    return ingredient_names

def get_mynetdiary_ingredient_names_as_set() -> Set[str]:
    """
    MyNetDiaryの食材名リストをSetとして取得（高速検索用）
    
    Returns:
        Set[str]: MyNetDiaryの食材名のSet
    """
    return set(load_mynetdiary_ingredient_names())

def format_mynetdiary_ingredients_for_prompt(exclude_uncooked: bool = False) -> str:
    """
    MyNetDiary の食材名リストをプロンプト用にフォーマット
    
    Args:
        exclude_uncooked: uncooked 食材を除外するかどうか
    
    Returns:
        str: プロンプトに組み込み可能な形式の食材名リスト
    """
    ingredient_names = load_mynetdiary_ingredient_names(exclude_uncooked=exclude_uncooked)
    
    # 食材名を番号付きリストとしてフォーマット
    formatted_list = []
    for i, name in enumerate(ingredient_names, 1):
        formatted_list.append(f"{i}. {name}")
    
    return "\n".join(formatted_list)

def validate_ingredient_against_mynetdiary(ingredient_name: str) -> bool:
    """
    指定された食材名がMyNetDiaryのリストに含まれているかチェック
    
    Args:
        ingredient_name: チェックする食材名
        
    Returns:
        bool: MyNetDiaryのリストに含まれている場合True
    """
    mynetdiary_names = get_mynetdiary_ingredient_names_as_set()
    return ingredient_name in mynetdiary_names 