#!/usr/bin/env python3
"""
Query Preprocessor - spaCyベースのクエリ前処理パイプライン

食品検索のためのクエリ前処理を行い、以下の機能を提供：
- トークン化
- 小文字化
- カスタムストップワード除去
- 保護ターム処理
- レンマ化（上書きルール適用）
- 類義語展開（オプション）
"""

import os
import spacy
from spacy.tokens import Token
from spacy.language import Language
from typing import List, Dict, Set, Optional
import re

class FoodQueryPreprocessor:
    def __init__(self):
        """クエリ前処理パイプラインを初期化"""
        self.nlp = None
        self.protected_terms: Set[str] = set()
        self.lemma_overrides: Dict[str, str] = {}
        self.custom_stopwords: Set[str] = set()
        self.food_synonyms: Dict[str, List[str]] = {}
        
        # レキシコンデータのパス
        self.lexicon_base_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            "lexicon_data"
        )
        
        self._load_lexicon_data()
        self._setup_spacy_pipeline()
    
    def _load_lexicon_data(self):
        """レキシコンファイルからデータを読み込み"""
        # 保護タームの読み込み
        protected_file = os.path.join(self.lexicon_base_path, "protected_food_terms.txt")
        try:
            with open(protected_file, "r", encoding="utf-8") as f:
                for line in f:
                    term = line.strip().lower()
                    if term and not term.startswith("#"):
                        self.protected_terms.add(term)
        except FileNotFoundError:
            print(f"Warning: protected_food_terms.txt not found at {protected_file}")
        
        # レンマ上書きルールの読み込み
        override_file = os.path.join(self.lexicon_base_path, "food_lemma_overrides.txt")
        try:
            with open(override_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        parts = line.split("=>")
                        if len(parts) == 2:
                            original = parts[0].strip().lower()
                            override = parts[1].strip().lower()
                            self.lemma_overrides[original] = override
        except FileNotFoundError:
            print(f"Warning: food_lemma_overrides.txt not found at {override_file}")
        
        # カスタムストップワードの読み込み
        stopwords_file = os.path.join(self.lexicon_base_path, "custom_food_stopwords.txt")
        try:
            with open(stopwords_file, "r", encoding="utf-8") as f:
                for line in f:
                    word = line.strip().lower()
                    if word and not word.startswith("#"):
                        self.custom_stopwords.add(word)
        except FileNotFoundError:
            print(f"Warning: custom_food_stopwords.txt not found at {stopwords_file}")
        
        # 類義語の読み込み（オプション）
        synonyms_file = os.path.join(self.lexicon_base_path, "food_synonyms.txt")
        try:
            with open(synonyms_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # 双方向類義語: word1, word2, word3
                        if "=>" not in line and "," in line:
                            words = [w.strip().lower() for w in line.split(",")]
                            for word in words:
                                if word not in self.food_synonyms:
                                    self.food_synonyms[word] = []
                                self.food_synonyms[word].extend([w for w in words if w != word])
                        
                        # 片方向類義語: source => target1, target2
                        elif "=>" in line:
                            parts = line.split("=>")
                            if len(parts) == 2:
                                source = parts[0].strip().lower()
                                targets = [t.strip().lower() for t in parts[1].split(",")]
                                self.food_synonyms[source] = targets
        except FileNotFoundError:
            print(f"Warning: food_synonyms.txt not found at {synonyms_file}")
    
    def _setup_spacy_pipeline(self):
        """spaCyパイプラインをセットアップ"""
        try:
            # 英語の小さいモデルを読み込み（効率性重視）
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Warning: en_core_web_sm model not found. Installing...")
            try:
                import subprocess
                subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=True)
                self.nlp = spacy.load("en_core_web_sm")
            except Exception as e:
                print(f"Error: Could not load spaCy model: {e}")
                return
        
        # カスタム拡張属性を追加
        if not Token.has_extension("is_protected"):
            Token.set_extension("is_protected", default=False)
        if not Token.has_extension("custom_lemma"):
            Token.set_extension("custom_lemma", default=None)
    
    def food_lexicon_processor_component(self, doc):
        """食品レキシコン処理コンポーネント"""
        for token in doc:
            token_lower = token.lower_
            
            # 保護タームのチェック
            if token_lower in self.protected_terms:
                token._.is_protected = True
                token._.custom_lemma = token_lower
            
            # レンマ上書きのチェック
            elif token_lower in self.lemma_overrides:
                token._.is_protected = True  # 上書きターもレンマ化から保護
                token._.custom_lemma = self.lemma_overrides[token_lower]
        
        return doc
    
    def preprocess_query(self, query_text: str, expand_synonyms: bool = False) -> str:
        """
        クエリテキストを前処理
        
        Args:
            query_text: 生のクエリテキスト
            expand_synonyms: 類義語展開を行うかどうか
            
        Returns:
            処理済みクエリ文字列
        """
        if not self.nlp:
            return query_text.lower()
        
        # spaCyで処理
        doc = self.nlp(query_text)
        
        # カスタムコンポーネントを手動で適用
        doc = self.food_lexicon_processor_component(doc)
        
        processed_tokens = []
        
        for token in doc:
            # 句読点、空白、数字のみのトークンをスキップ
            if token.is_punct or token.is_space or (token.is_digit and len(token.text) > 2):
                continue
            
            # カスタムストップワードのチェック
            if token.lower_ in self.custom_stopwords:
                continue
            
            # 保護された単語のレンマ処理
            if token._.is_protected and token._.custom_lemma:
                processed_tokens.append(token._.custom_lemma)
            
            # 標準レンマ化
            else:
                lemma = token.lemma_.lower()
                processed_tokens.append(lemma)
        
        # 類義語展開（オプション）
        if expand_synonyms:
            expanded_tokens = []
            for token in processed_tokens:
                expanded_tokens.append(token)
                if token in self.food_synonyms:
                    expanded_tokens.extend(self.food_synonyms[token])
            processed_tokens = expanded_tokens
        
        # 重複除去と結合
        processed_tokens = list(dict.fromkeys(processed_tokens))  # 順序を保持して重複除去
        
        return " ".join(processed_tokens)
    
    def get_processed_tokens(self, query_text: str) -> List[str]:
        """
        処理済みトークンのリストを取得
        
        Args:
            query_text: 生のクエリテキスト
            
        Returns:
            処理済みトークンのリスト
        """
        processed_query = self.preprocess_query(query_text)
        return processed_query.split()
    
    def analyze_query(self, query_text: str) -> Dict:
        """
        クエリの詳細分析情報を取得（デバッグ用）
        
        Args:
            query_text: 生のクエリテキスト
            
        Returns:
            分析結果の辞書
        """
        if not self.nlp:
            return {"error": "spaCy model not loaded"}
        
        doc = self.nlp(query_text)
        
        # カスタムコンポーネントを手動で適用
        doc = self.food_lexicon_processor_component(doc)
        
        analysis = {
            "original": query_text,
            "tokens": [],
            "processed": self.preprocess_query(query_text),
            "statistics": {
                "original_tokens": len(doc),
                "processed_tokens": len(self.get_processed_tokens(query_text)),
                "protected_terms": 0,
                "overridden_terms": 0,
                "removed_stopwords": 0
            }
        }
        
        for token in doc:
            token_info = {
                "text": token.text,
                "lemma": token.lemma_,
                "is_protected": getattr(token._, 'is_protected', False),
                "custom_lemma": getattr(token._, 'custom_lemma', None),
                "is_stopword": token.lower_ in self.custom_stopwords,
                "is_punct": token.is_punct,
                "pos": token.pos_
            }
            
            if token_info["is_protected"]:
                analysis["statistics"]["protected_terms"] += 1
            if token_info["custom_lemma"]:
                analysis["statistics"]["overridden_terms"] += 1
            if token_info["is_stopword"]:
                analysis["statistics"]["removed_stopwords"] += 1
            
            analysis["tokens"].append(token_info)
        
        return analysis

# グローバルインスタンス
_preprocessor = None

def get_preprocessor() -> FoodQueryPreprocessor:
    """グローバルプリプロセッサインスタンスを取得"""
    global _preprocessor
    if _preprocessor is None:
        _preprocessor = FoodQueryPreprocessor()
    return _preprocessor

def preprocess_query(query_text: str, expand_synonyms: bool = False) -> str:
    """便利関数：クエリを前処理"""
    return get_preprocessor().preprocess_query(query_text, expand_synonyms)

def analyze_query(query_text: str) -> Dict:
    """便利関数：クエリを分析"""
    return get_preprocessor().analyze_query(query_text) 