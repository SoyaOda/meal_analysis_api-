"""
食品名の見出し語化機能を提供するユーティリティモジュール

主な機能：
- 単数形・複数形の正規化（tomatoes → tomato）
- 複合語の各単語の見出し語化（tomato soup → tomato soup）
- 検索クエリとデータベース項目名の正規化
"""

from nltk.stem import WordNetLemmatizer
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

# グローバルなLemmatizerインスタンス（初期化コストを削減）
_lemmatizer = None

def get_lemmatizer() -> WordNetLemmatizer:
    """Lemmatizerのシングルトンインスタンスを取得"""
    global _lemmatizer
    if _lemmatizer is None:
        _lemmatizer = WordNetLemmatizer()
        logger.info("WordNetLemmatizer initialized")
    return _lemmatizer

def lemmatize_term(term: str) -> str:
    """
    食品名を見出し語化する
    
    Args:
        term: 見出し語化する文字列（例：「tomatoes」、「tomato soup」）
        
    Returns:
        見出し語化された文字列（例：「tomato」、「tomato soup」）
        
    Examples:
        >>> lemmatize_term("tomatoes")
        "tomato"
        >>> lemmatize_term("tomato soup")
        "tomato soup"
        >>> lemmatize_term("apples")
        "apple"
    """
    if not isinstance(term, str) or not term.strip():
        return term
    
    try:
        lemmatizer = get_lemmatizer()
        
        # 小文字に変換してトークン化
        tokens = term.lower().strip().split()
        
        # 各トークンを見出し語化（名詞として処理）
        lemmatized_tokens = []
        for token in tokens:
            # 英数字以外の文字を含む場合はそのまま処理
            lemmatized_token = lemmatizer.lemmatize(token, pos='n')  # 名詞として見出し語化
            lemmatized_tokens.append(lemmatized_token)
        
        result = " ".join(lemmatized_tokens)
        logger.debug(f"Lemmatized '{term}' -> '{result}'")
        return result
        
    except Exception as e:
        logger.warning(f"Failed to lemmatize '{term}': {e}")
        return term.lower()  # エラー時は小文字化のみ

def lemmatize_terms_batch(terms: List[str]) -> List[str]:
    """
    複数の食品名を一括で見出し語化する
    
    Args:
        terms: 見出し語化する文字列のリスト
        
    Returns:
        見出し語化された文字列のリスト
    """
    return [lemmatize_term(term) for term in terms]

def create_lemmatized_query_variations(query: str) -> List[str]:
    """
    クエリの見出し語化されたバリエーションを生成
    
    Args:
        query: 検索クエリ
        
    Returns:
        [元のクエリ, 見出し語化されたクエリ] のリスト（重複除去済み）
    """
    if not query:
        return []
    
    original = query.strip()
    lemmatized = lemmatize_term(original)
    
    # 重複を除去してリストを返す
    variations = []
    if original and original not in variations:
        variations.append(original)
    if lemmatized and lemmatized not in variations:
        variations.append(lemmatized)
    
    return variations

# テスト用の関数
def test_lemmatization():
    """見出し語化機能のテスト"""
    test_cases = [
        ("tomatoes", "tomato"),
        ("tomato soup", "tomato soup"), 
        ("apples", "apple"),
        ("potatoes", "potato"),
        ("potato salad", "potato salad"),
        ("onions", "onion"),
        ("beef", "beef"),  # 単数形はそのまま
        ("chicken", "chicken"),  # 単数形はそのまま
        ("", ""),  # 空文字列
        ("TOMATOES", "tomato"),  # 大文字
    ]
    
    print("=== 見出し語化テスト ===")
    for input_term, expected in test_cases:
        result = lemmatize_term(input_term)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{input_term}' -> '{result}' (期待値: '{expected}')")
    
    print("\n=== クエリバリエーションテスト ===")
    query_tests = ["tomatoes", "tomato soup", "apples"]
    for query in query_tests:
        variations = create_lemmatized_query_variations(query)
        print(f"'{query}' -> {variations}")

if __name__ == "__main__":
    test_lemmatization() 