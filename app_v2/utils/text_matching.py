#!/usr/bin/env python3
"""
Text Matching Utilities for Flexible Exact Match

柔軟な完全一致判定を行うユーティリティ関数群
以下の差異を許容する：
- 大文字小文字
- ing, edのあるなし (語形変化)
- 単数形、複数形
- "'s"や","のあるなし (所有格、句読点)
- wordの順序の違い
"""

import re
import string
from typing import List, Dict, Any, Set, Tuple
from collections import Counter

# 英語の語幹処理のためのライブラリ
try:
    import nltk
    from nltk.stem import PorterStemmer
    from nltk.corpus import stopwords
    NLTK_AVAILABLE = True
    # 必要なNLTKデータの自動ダウンロード
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)
    
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
        
except ImportError:
    NLTK_AVAILABLE = False


class FlexibleTextMatcher:
    """柔軟な完全一致判定を行うクラス"""
    
    def __init__(self):
        if NLTK_AVAILABLE:
            self.stemmer = PorterStemmer()
            try:
                self.stop_words = set(stopwords.words('english'))
            except:
                self.stop_words = set()
        else:
            self.stemmer = None
            self.stop_words = set()
        
        # 基本的なストップワード（NLTKが利用できない場合のフォールバック）
        self.basic_stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'were', 'will', 'with'
        }
        
        if not self.stop_words:
            self.stop_words = self.basic_stop_words
    
    def normalize_text(self, text: str) -> str:
        """テキストの基本的な正規化"""
        if not text:
            return ""
        
        # 小文字化
        text = text.lower().strip()
        
        # 所有格の除去 ("'s", "'")
        text = re.sub(r"'s\b", "", text)
        text = re.sub(r"'\b", "", text)
        
        # 句読点の除去・置換
        text = re.sub(r'[,\.!?;:&]', ' ', text)
        text = re.sub(r'[-_/]', ' ', text)
        
        # 複数のスペースを単一スペースに
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def tokenize_and_stem(self, text: str, remove_stop_words: bool = True) -> List[str]:
        """テキストをトークン化し、語幹化を行う"""
        normalized = self.normalize_text(text)
        tokens = normalized.split()
        
        processed_tokens = []
        for token in tokens:
            if remove_stop_words and token in self.stop_words:
                continue
                
            # 語幹化
            if self.stemmer and NLTK_AVAILABLE:
                try:
                    stemmed = self.stemmer.stem(token)
                    processed_tokens.append(stemmed)
                except:
                    processed_tokens.append(token)
            else:
                # 基本的な語尾処理（フォールバック）
                stemmed = self._basic_stem(token)
                processed_tokens.append(stemmed)
        
        return processed_tokens
    
    def _basic_stem(self, word: str) -> str:
        """基本的な語幹化処理（NLTKが利用できない場合のフォールバック）"""
        if len(word) < 3:
            return word
        
        # 複数形の処理
        if word.endswith('ies') and len(word) > 3:
            return word[:-3] + 'y'
        elif word.endswith('es') and len(word) > 2:
            return word[:-2]
        elif word.endswith('s') and len(word) > 1:
            return word[:-1]
        
        # ing形の処理
        if word.endswith('ing') and len(word) > 3:
            base = word[:-3]
            # 重複子音の処理 (running -> run)
            if len(base) >= 2 and base[-1] == base[-2] and base[-1] not in 'aeiou':
                return base[:-1]
            return base
        
        # ed形の処理
        if word.endswith('ed') and len(word) > 2:
            base = word[:-2]
            if len(base) >= 1:
                return base
        
        # ly形の処理
        if word.endswith('ly') and len(word) > 2:
            return word[:-2]
        
        return word
    
    def calculate_word_order_similarity(self, tokens1: List[str], tokens2: List[str]) -> float:
        """語順の類似度を計算（Jaccard係数ベース）"""
        if not tokens1 or not tokens2:
            return 0.0
        
        set1 = set(tokens1)
        set2 = set(tokens2)
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def is_flexible_exact_match(
        self, 
        query_text: str, 
        target_text: str, 
        similarity_threshold: float = 0.85,
        word_order_threshold: float = 0.7
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        柔軟な完全一致判定を行う
        
        Args:
            query_text: 検索クエリテキスト
            target_text: 対象テキスト
            similarity_threshold: 類似度閾値
            word_order_threshold: 語順類似度閾値
            
        Returns:
            (is_match, match_details): 一致判定結果と詳細情報
        """
        
        if not query_text or not target_text:
            return False, {"error": "Empty text provided"}
        
        # 正規化
        query_normalized = self.normalize_text(query_text)
        target_normalized = self.normalize_text(target_text)
        
        # 完全一致チェック（正規化後）
        if query_normalized == target_normalized:
            return True, {
                "match_type": "exact_normalized",
                "query_normalized": query_normalized,
                "target_normalized": target_normalized,
                "similarity_score": 1.0
            }
        
        # トークン化・語幹化
        query_tokens = self.tokenize_and_stem(query_text, remove_stop_words=True)
        target_tokens = self.tokenize_and_stem(target_text, remove_stop_words=True)
        
        # 語順を考慮しない一致チェック
        query_set = set(query_tokens)
        target_set = set(target_tokens)
        
        # 完全一致（語幹化後、語順無視）
        if query_set == target_set:
            return True, {
                "match_type": "exact_stemmed_unordered",
                "query_tokens": query_tokens,
                "target_tokens": target_tokens,
                "similarity_score": 1.0
            }
        
        # 高類似度チェック
        word_order_similarity = self.calculate_word_order_similarity(query_tokens, target_tokens)
        
        # 語順類似度が閾値を上回る場合
        if word_order_similarity >= word_order_threshold:
            # 包含関係チェック
            if query_set.issubset(target_set) or target_set.issubset(query_set):
                return True, {
                    "match_type": "high_similarity_subset",
                    "query_tokens": query_tokens,
                    "target_tokens": target_tokens,
                    "word_order_similarity": word_order_similarity,
                    "similarity_score": word_order_similarity
                }
            
            # 高類似度の場合
            if word_order_similarity >= similarity_threshold:
                return True, {
                    "match_type": "high_similarity",
                    "query_tokens": query_tokens,
                    "target_tokens": target_tokens,
                    "word_order_similarity": word_order_similarity,
                    "similarity_score": word_order_similarity
                }
        
        # 一致しない
        return False, {
            "match_type": "no_match",
            "query_tokens": query_tokens,
            "target_tokens": target_tokens,
            "word_order_similarity": word_order_similarity,
            "similarity_score": word_order_similarity
        }
    
    def batch_match_analysis(
        self, 
        query_text: str, 
        target_texts: List[str],
        similarity_threshold: float = 0.85
    ) -> List[Tuple[str, bool, Dict[str, Any]]]:
        """複数のテキストに対してバッチで一致判定を行う"""
        results = []
        
        for target_text in target_texts:
            is_match, details = self.is_flexible_exact_match(
                query_text, target_text, similarity_threshold
            )
            results.append((target_text, is_match, details))
        
        return results


# グローバルなインスタンス
_text_matcher = None

def get_text_matcher() -> FlexibleTextMatcher:
    """テキストマッチャーのシングルトンインスタンスを取得"""
    global _text_matcher
    if _text_matcher is None:
        _text_matcher = FlexibleTextMatcher()
    return _text_matcher


def is_flexible_exact_match(
    query_text: str, 
    target_text: str, 
    similarity_threshold: float = 0.85
) -> Tuple[bool, Dict[str, Any]]:
    """
    柔軟な完全一致判定を行う（便利関数）
    
    Args:
        query_text: 検索クエリテキスト
        target_text: 対象テキスト
        similarity_threshold: 類似度閾値
        
    Returns:
        (is_match, match_details): 一致判定結果と詳細情報
    """
    matcher = get_text_matcher()
    return matcher.is_flexible_exact_match(query_text, target_text, similarity_threshold)


def analyze_text_matching(query_text: str, target_texts: List[str]) -> Dict[str, Any]:
    """
    テキストマッチングの詳細分析を行う
    
    Args:
        query_text: 検索クエリテキスト
        target_texts: 対象テキストのリスト
        
    Returns:
        分析結果の辞書
    """
    matcher = get_text_matcher()
    results = matcher.batch_match_analysis(query_text, target_texts)
    
    exact_matches = []
    partial_matches = []
    no_matches = []
    
    for target_text, is_match, details in results:
        if is_match:
            exact_matches.append({
                "text": target_text,
                "details": details
            })
        else:
            similarity_score = details.get("similarity_score", 0.0)
            if similarity_score > 0.3:  # 部分一致の閾値
                partial_matches.append({
                    "text": target_text,
                    "details": details
                })
            else:
                no_matches.append({
                    "text": target_text,
                    "details": details
                })
    
    return {
        "query": query_text,
        "total_targets": len(target_texts),
        "exact_matches": exact_matches,
        "partial_matches": partial_matches,
        "no_matches": no_matches,
        "exact_match_count": len(exact_matches),
        "exact_match_rate": len(exact_matches) / len(target_texts) if target_texts else 0.0
    } 