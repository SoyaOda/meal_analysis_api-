import json
import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def parse_json_from_string(text: str) -> Dict[str, Any]:
    """
    テキストからJSON部分を抽出してパースする
    
    Args:
        text: JSON文字列を含むテキスト
        
    Returns:
        パースされたJSONオブジェクト
        
    Raises:
        ValueError: JSONが見つからない、またはパースできない場合
    """
    if not text or not isinstance(text, str):
        raise ValueError("Invalid input: text must be a non-empty string")
    
    # まず、テキスト全体がJSONかどうかを試す
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    
    # JSONブロックを探す（```json ... ``` または { ... }）
    json_patterns = [
        r'```json\s*(\{.*?\})\s*```',  # Markdown JSONブロック
        r'```\s*(\{.*?\})\s*```',      # 一般的なMarkdownブロック
        r'(\{.*\})',                   # 単純な{}ブロック
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                # JSONとしてパース
                parsed = json.loads(match.strip())
                logger.info(f"Successfully parsed JSON from pattern: {pattern[:20]}...")
                return parsed
            except json.JSONDecodeError:
                continue
    
    # 最後の手段：行ごとに{}を探す
    lines = text.split('\n')
    json_lines = []
    in_json = False
    brace_count = 0
    
    for line in lines:
        if '{' in line and not in_json:
            in_json = True
            json_lines = [line]
            brace_count = line.count('{') - line.count('}')
        elif in_json:
            json_lines.append(line)
            brace_count += line.count('{') - line.count('}')
            if brace_count <= 0:
                # JSONブロック終了
                json_text = '\n'.join(json_lines)
                try:
                    parsed = json.loads(json_text)
                    logger.info("Successfully parsed JSON from line-by-line extraction")
                    return parsed
                except json.JSONDecodeError:
                    pass
                in_json = False
                json_lines = []
                brace_count = 0
    
    # すべての方法が失敗した場合
    logger.error(f"Failed to parse JSON from text: {text[:200]}...")
    raise ValueError("No valid JSON found in the provided text")

def extract_json_content(text: str) -> Optional[str]:
    """
    テキストからJSON部分のみを抽出する（パースはしない）
    
    Args:
        text: JSON文字列を含むテキスト
        
    Returns:
        JSON文字列、または見つからない場合はNone
    """
    if not text or not isinstance(text, str):
        return None
    
    # JSONブロックを探す
    json_patterns = [
        r'```json\s*(\{.*?\})\s*```',
        r'```\s*(\{.*?\})\s*```',
        r'(\{.*\})',
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            return matches[0].strip()
    
    return None 