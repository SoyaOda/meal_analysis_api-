#!/usr/bin/env python3
"""
USDA食材データの前処理スクリプト

このスクリプトは、generate_usda_food_database.pyで生成されたJSONファイルを
LLM処理前にクリーニングします。

処理内容:
1. NFS (Not Further Specified) の除去
2. 括弧とその内容の除去
3. "NS as to" を含む項目の除外
4. ブランド名の分離
5. 特殊文字の正規化

入力:
- usda_raw_ingredients_all.json
- usda_prepared_ingredients_all.json

出力:
- usda_raw_ingredients_preprocessed.json
- usda_prepared_ingredients_preprocessed.json
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import Counter

# カテゴリ絵文字マッピングテーブル
CATEGORY_EMOJIS = {
    # パン・ベーカリー類
    "Yeast breads": "🍞",
    "Bagels and English muffins": "🥯",
    "Rolls and buns": "🥖",
    "Biscuits, muffins, quick breads": "🧁",
    "Crackers, excludes saltines": "🍘",
    "Saltine crackers": "🍘",

    # 肉類
    "Beef, excludes ground": "🥩",
    "Ground beef": "🥩",
    "Pork": "🐷",
    "Lamb, goat, game": "🍖",
    "Liver and organ meats": "🥩",
    "Bacon": "🥓",
    "Chicken, whole pieces": "🍗",
    "Chicken patties, nuggets and tenders": "🍗",
    "Turkey, duck, other poultry": "🦃",
    "Cold cuts and cured meats": "🥪",
    "Burgers": "🍔",
    "Sausages": "🌭",
    "Frankfurters": "🌭",

    # 海産物
    "Fish": "🐟",
    "Shellfish": "🦐",

    # 乳製品
    "Cheese": "🧀",
    "Cottage/ricotta cheese": "🧀",
    "Cream cheese, sour cream, whipped cream": "🍨",
    "Milk and milk drinks": "🥛",
    "Milk, whole": "🥛",
    "Milk, nonfat": "🥛",
    "Milk, reduced fat": "🥛",
    "Milk, lowfat": "🥛",
    "Plant-based milk": "🥛",
    "Flavored milk": "🥛",
    "Flavored milk, whole": "🥛",
    "Flavored milk, reduced fat": "🥛",
    "Flavored milk, nonfat": "🥛",
    "Flavored milk, lowfat": "🥛",
    "Yogurt": "🍶",
    "Yogurt, Greek": "🍶",
    "Yogurt, regular": "🍶",
    "Milk shakes and other dairy drinks": "🥤",
    "Ice cream and frozen dairy desserts": "🍦",
    "Butter and animal fats": "🧈",
    "Margarine": "🧈",
    "Cream and cream substitutes": "🥛",

    # 野菜
    "Broccoli": "🥦",
    "Carrots": "🥕",
    "Corn": "🌽",
    "Tomatoes": "🍅",
    "Lettuce and lettuce salads": "🥬",
    "Spinach": "🥬",
    "Cabbage": "🥬",
    "White potatoes": "🥔",
    "White potatoes, baked or boiled": "🥔",
    "French fries and other fried white potatoes": "🍟",
    "Mashed potatoes and white potato mixtures": "🥔",
    "Sweet potatoes": "🍠",
    "String beans": "🥬",
    "Onions": "🧅",
    "Other vegetables and combinations": "🥗",
    "Other dark green vegetables": "🥬",
    "Other red and orange vegetables": "🥕",
    "Other starchy vegetables": "🥔",
    "Coleslaw, non-lettuce salads": "🥗",
    "Vegetables on a sandwich": "🥗",
    "Fried vegetables": "🍟",

    # 果物
    "Apples": "🍎",
    "Bananas": "🍌",
    "Citrus fruits": "🍊",
    "Grapes": "🍇",
    "Melons": "🍉",
    "Stone fruit": "🍑",
    "Peaches and nectarines": "🍑",
    "Strawberries": "🍓",
    "Blueberries and other berries": "🫐",
    "Dried fruits": "🍒",
    "Other fruits and fruit salads": "🍈",
    "Mango and papaya": "🥭",
    "Pineapple": "🍍",
    "Pears": "🍐",
    "Olives, pickles, pickled vegetables": "🫒",

    # 飲料
    "Coffee": "☕",
    "Tea": "🍵",
    "Soft drinks": "🥤",
    "Diet soft drinks": "🥤",
    "Enhanced water": "💧",
    "Bottled water": "💧",
    "Tap water": "💧",
    "Flavored or carbonated water": "💧",
    "Sport and energy drinks": "⚡",
    "Diet sport and energy drinks": "⚡",
    "Nutritional beverages": "🥤",
    "Fruit drinks": "🧃",
    "Apple juice": "🧃",
    "Citrus juice": "🍊",
    "Orange juice": "🍊",
    "Other fruit juice": "🧃",
    "Tomato and vegetable juice": "🥤",
    "Vegetable juice": "🥤",
    "Smoothies and grain drinks": "🥤",
    "Other diet drinks": "🥤",
    "Beer": "🍺",
    "Wine": "🍷",
    "Liquor and cocktails": "🍹",

    # スナック・お菓子
    "Cookies and brownies": "🍪",
    "Cakes and pies": "🍰",
    "Candy containing chocolate": "🍫",
    "Candy not containing chocolate": "🍬",
    "Doughnuts, sweet rolls, pastries": "🍩",
    "Cereal bars": "🥜",
    "Nutritional bars": "🥜",
    "Nutrition bars": "🍫",
    "Protein and nutritional powders": "💪",
    "Potato chips": "🥔",
    "Tortilla, corn, other chips": "🥨",
    "Tortillas": "🫓",
    "Pretzels/snack mix": "🥨",
    "Popcorn": "🍿",
    "Sugars and honey": "🍯",
    "Jams, syrups, toppings": "🍯",
    "Sugar substitutes": "🍬",
    "Gelatins, ices, sorbets": "🍧",
    "Pudding": "🍮",

    # メイン料理
    "Pizza": "🍕",
    "Burritos and tacos": "🌮",
    "Nachos": "🌮",
    "Other Mexican mixed dishes": "🌮",
    "Pasta, noodles, cooked grains": "🍝",
    "Rice": "🍚",
    "Rice mixed dishes": "🍚",
    "Pasta mixed dishes, excludes macaroni and cheese": "🍝",
    "Pasta sauces, tomato-based": "🍅",
    "Macaroni and cheese": "🧀",
    "Turnovers and other grain-based items": "🥟",
    "Fried rice and lo/chow mein": "🍜",
    "Ramen and Asian broth-based soups": "🍜",
    "Stir-fry and soy-based sauce mixtures": "🥘",
    "Egg rolls, dumplings, sushi": "🍱",
    "Soups": "🍲",
    "Pancakes, waffles, French toast": "🥞",
    "Meat mixed dishes": "🍽️",
    "Poultry mixed dishes": "🍗",

    # サンドイッチ類
    "Chicken fillet sandwiches": "🍔",
    "Egg/breakfast sandwiches": "🥪",
    "Frankfurter sandwiches": "🌭",
    "Deli and cured meat sandwiches": "🥪",
    "Seafood sandwiches": "🐟",
    "Other sandwiches": "🥪",

    # その他
    "Eggs and omelets": "🥚",
    "Nuts and seeds": "🥜",
    "Beans, peas, legumes": "🫘",
    "Processed soy products": "🌱",
    "Soy and meat-alternative products": "🌱",
    "Salad dressings and vegetable oils": "🫒",
    "Mayonnaise": "🥄",
    "Tomato-based condiments": "🍅",
    "Mustard and other condiments": "🌶️",
    "Soy-based condiments": "🥢",
    "Dips, gravies, other sauces": "🍛",
    "Ready-to-eat cereal, higher sugar (>21.2g/100g)": "🥣",
    "Ready-to-eat cereal, lower sugar (≤21.2g/100g)": "🥣",
    "Oatmeal": "🥣",
    "Grits and other cooked cereals": "🥣",
    "Protein and nutritional powders": "💪",
    "Baby food: cereals": "👶",
    "Baby food: fruit": "👶",
    "Baby food: meat and dinners": "👶",
    "Baby food: snacks and sweets": "👶",
    "Baby food: vegetables": "👶",
    "Baby juice": "👶",
    "Baby water": "👶",
    "Infant formula": "🍼",
    "Formula, ready-to-feed": "🍼",
    "Formula, prepared from powder": "🍼",
    "Human milk": "🍼",

    # 複合カテゴリ・その他
    "Not included in a food category": "🍽️",
    "Other": "🥘"
}

# 食品固有の絵文字マッピング（カテゴリレベルの絵文字より優先される）
# foodCode: emoji の辞書形式
FOOD_SPECIFIC_EMOJIS = {
    # 乾燥ミルク・粉末飲料
    "11810000": "🥛",  # Milk, dry, not reconstituted
    "11825000": "🥛",  # Whey, sweet, dry
    "11830150": "☕",  # Cocoa powder, not reconstituted
    "11830160": "☕",  # Chocolate beverage powder, dry mix
    "11830165": "☕",  # Chocolate beverage powder, light, dry mix
    "11830260": "🥛",  # Milk, malted, dry mix
    "11830400": "🧃",  # Strawberry beverage powder, dry mix
    "92900300": "⚡",  # Sports drink, dry concentrate

    # 穀物・穀類
    "57412000": "🌾",  # Wheat germ
    "57601100": "🌾",  # Wheat bran
    "57602100": "🥣",  # Oats, raw

    # ハーブ類
    "75109400": "🌿",  # Basil, raw
    "75109500": "🌿",  # Chives, raw
    "75109550": "🌿",  # Cilantro, raw
    "75119000": "🌿",  # Parsley, raw
    "75236000": "🍞",  # Yeast

    # 料理用肉
    "89901000": "🥓",  # Bacon, for use with vegetables
    "89901002": "🍖",  # Ham, for use with vegetables
    "89901004": "🥩",  # Beef, for use with vegetables
    "89901006": "🍗",  # Chicken, for use with vegetables

    # インスタント飲料
    "92191100": "☕",  # Coffee, instant, not reconstituted
    "92191200": "☕",  # Coffee, instant, decaffeinated
    "92193005": "☕",  # Coffee, instant, decaffeinated, pre-lightened and pre-sweetened
    "92307000": "🍵",  # Tea, iced, instant, black, unsweetened, dry
    "92307400": "🍵",  # Tea, iced, instant, black, pre-sweetened, dry
    "92900100": "🧃",  # Fruit flavored drink, with high vitamin C, powdered
    "92900110": "🧃",  # Fruit flavored drink, powdered
    "92900200": "🧃",  # Fruit flavored drink, powdered, diet

    # 料理用野菜（prepared ingredients）
    "99997210": "🥬",  # Spinach, cooked, as ingredient
    "99997220": "🥦",  # Broccoli, cooked, as ingredient
    "99997310": "🥕",  # Carrots, cooked, as ingredient
    "99997340": "🍠",  # Sweet potato, cooked, as ingredient
    "99997410": "🍅",  # Tomatoes, cooked, as ingredient
    "99997510": "🧅",  # Onions, cooked, as ingredient
    "99997515": "🍄",  # Mushrooms, cooked, as ingredient
    "99997520": "🫑",  # Green pepper, cooked, as ingredient
    "99997525": "🫑",  # Red pepper, cooked, as ingredient
    "99997530": "🥬",  # Cabbage, cooked, as ingredient
    "99997535": "🥦",  # Cauliflower, cooked, as ingredient
    "99997540": "🍆",  # Eggplant, cooked, as ingredient
    "99997545": "🥬",  # Green beans, cooked, as ingredient
    "99997555": "🥬",  # Celery, cooked, as ingredient

    # 肉料理（Meat mixed dishes）
    "27111400": "🌶️",  # Chili
    "27112010": "🥩",  # Salisbury steak with gravy
    "27211400": "🥩",  # Corned beef hash
    "27214500": "🥩",  # Corned beef patty
    "28101000": "🍱",  # Frozen dinner
    "28110000": "🥩",  # Beef dinner, frozen meal
    "28110300": "🥩",  # Salisbury steak dinner, frozen meal
    "28160300": "🥩",  # Meat loaf dinner, frozen meal
}

def get_category_emoji(category: str) -> str:
    """カテゴリに対応する絵文字を取得（後方互換性のため残す）"""
    return CATEGORY_EMOJIS.get(category, "🍽️")  # デフォルト絵文字

def get_emoji(food_code: str, category: str = None) -> str:
    """
    食品固有またはカテゴリの絵文字を取得

    優先順位:
    1. 食品固有の絵文字（FOOD_SPECIFIC_EMOJIS）
    2. カテゴリの絵文字（CATEGORY_EMOJIS）
    3. デフォルト絵文字（🍽️）

    Args:
        food_code: 食品コード
        category: カテゴリ名（オプション）

    Returns:
        適切な絵文字
    """
    # 食品固有の絵文字があればそれを返す
    if food_code in FOOD_SPECIFIC_EMOJIS:
        return FOOD_SPECIFIC_EMOJIS[food_code]

    # カテゴリの絵文字を返す
    if category:
        return CATEGORY_EMOJIS.get(category, "🍽️")

    # デフォルト絵文字
    return "🍽️"


def load_display_name_mappings(gpt_file_path: Path) -> Dict[int, Dict[str, Optional[str]]]:
    """
    display_info_list.txtからdisplay name mappingsを読み込む

    Args:
        gpt_file_path: display_info_list.txtファイルのパス

    Returns:
        番号をキーとし、display_name, display_variant, brand_nameを含む辞書を値とする辞書
        例: {1: {'display_name': 'Agave syrup', 'display_variant': None, 'brand_name': None}, ...}
    """
    mappings = {}
    
    try:
        with open(gpt_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # フォーマット: "番号. display_name;display_variant;brand_name"
                if '. ' in line:
                    parts = line.split('. ', 1)
                    if len(parts) == 2 and parts[0].isdigit():
                        number = int(parts[0])
                        content = parts[1]
                        
                        # セミコロンで分割
                        fields = content.split(';')
                        if len(fields) >= 3:
                            display_name = fields[0].strip()
                            display_variant = fields[1].strip() if fields[1].strip() != 'null' else None
                            brand_name = fields[2].strip() if fields[2].strip() != 'null' else None
                            
                            mappings[number] = {
                                'display_name': display_name,
                                'display_variant': display_variant,
                                'brand_name': brand_name
                            }
    except FileNotFoundError:
        print(f"⚠️ GPTファイルが見つかりません: {gpt_file_path}")
        return {}
    except Exception as e:
        print(f"⚠️ GPTファイルの読み込み中にエラーが発生しました: {e}")
        return {}
    
    return mappings


def load_exclusion_set(exclusion_file_path: Path) -> set:
    """
    exclusion_list.txtから除外する番号のセットを読み込む
    
    Args:
        exclusion_file_path: exclusion_list.txtファイルのパス
    
    Returns:
        除外する番号のセット
        例: {29, 31, 36, 45, ...}
    """
    exclusion_set = set()
    
    try:
        with open(exclusion_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # フォーマット: "番号. display_name;display_variant;brand_name"
                # 番号だけ抽出
                if '. ' in line:
                    parts = line.split('. ', 1)
                    if len(parts) >= 1 and parts[0].isdigit():
                        number = int(parts[0])
                        exclusion_set.add(number)
    except FileNotFoundError:
        print(f"⚠️ 除外リストファイルが見つかりません: {exclusion_file_path}")
        return set()
    except Exception as e:
        print(f"⚠️ 除外リストファイルの読み込み中にエラーが発生しました: {e}")
        return set()
    
    return exclusion_set


def load_search_name_mappings(search_name_file_path: Path) -> Dict[int, List[str]]:
    """
    search_name_list.txtからsearch name mappingsを読み込む
    
    Returns:
        番号をキーとし、search nameのリストを値とする辞書
        例: {1: ['agave syrup', 'agave nectar', 'liquid agave sweetener', 'agave sweetener'], ...}
    """
    mappings = {}
    
    try:
        with open(search_name_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # フォーマット: "番号. [...search names...]"
                if '. ' in line:
                    parts = line.split('. ', 1)
                    if len(parts) == 2 and parts[0].isdigit():
                        number = int(parts[0])
                        
                        # JSON配列をパース
                        try:
                            search_names = json.loads(parts[1])
                            if isinstance(search_names, list):
                                mappings[number] = search_names
                        except json.JSONDecodeError as e:
                            print(f"⚠️ JSON解析エラー (行番号{number}): {e}")
                            continue
    except FileNotFoundError:
        print(f"⚠️ Search nameファイルが見つかりません: {search_name_file_path}")
        return {}
    except Exception as e:
        print(f"⚠️ Search nameファイルの読み込み中にエラーが発生しました: {e}")
        return {}
    
    return mappings


def load_original_name_mapping(original_name_path: Path) -> Dict[str, int]:
    """
    original_name.txtから元の食品名と番号のマッピングを読み込む
    
    Args:
        original_name_path: original_name.txtファイルのパス
    
    Returns:
        元の食品名をキーとし、番号を値とする辞書
        例: {'Agave liquid sweetener': 1, ...}
    """
    name_to_number = {}
    
    try:
        with open(original_name_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # フォーマット: "番号. 元の食品名"
                if '. ' in line:
                    parts = line.split('. ', 1)
                    if len(parts) == 2 and parts[0].isdigit():
                        number = int(parts[0])
                        original_name = parts[1].strip()
                        name_to_number[original_name] = number
    except FileNotFoundError:
        print(f"⚠️ 元の食品名ファイルが見つかりません: {original_name_path}")
        return {}
    except Exception as e:
        print(f"⚠️ 元の食品名ファイルの読み込み中にエラーが発生しました: {e}")
        return {}
    
    return name_to_number


def load_frequency_emoji_mappings(frequency_emoji_path: Path) -> Dict[int, Dict[str, Optional[str]]]:
    """
    frequency_emoji_list.txtから番号と消費頻度・絵文字のマッピングを読み込む
    
    Args:
        frequency_emoji_path: frequency_emoji_list.txtファイルのパス
    
    Returns:
        番号をキーとし、consumption_frequencyとfood_specific_emojiを含む辞書を値とする辞書
        例: {1: {'consumption_frequency': 'rare', 'food_specific_emoji': '🍯'}, ...}
    """
    number_to_freq_emoji = {}
    
    try:
        with open(frequency_emoji_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                # フォーマット: "番号. JSONオブジェクト"
                if '. ' in line:
                    parts = line.split('. ', 1)
                    if len(parts) == 2 and parts[0].isdigit():
                        number = int(parts[0])
                        try:
                            # JSONオブジェクトをパース
                            freq_emoji_data = json.loads(parts[1])
                            number_to_freq_emoji[number] = {
                                'consumption_frequency': freq_emoji_data.get('consumption_frequency'),
                                'food_specific_emoji': freq_emoji_data.get('food_specific_emoji')
                            }
                        except json.JSONDecodeError as e:
                            print(f"⚠️ JSON解析エラー (行番号 {number}): {e}")
                            continue
    except FileNotFoundError:
        print(f"⚠️ 消費頻度・絵文字ファイルが見つかりません: {frequency_emoji_path}")
        return {}
    except Exception as e:
        print(f"⚠️ 消費頻度・絵文字ファイルの読み込み中にエラーが発生しました: {e}")
        return {}
    
    print(f"✅ {len(number_to_freq_emoji)}件の消費頻度・絵文字情報を読み込みました")
    return number_to_freq_emoji

def normalize_description(description: str) -> Tuple[str, Optional[str]]:
    """
    食材説明の正規化と追加情報の抽出

    Returns:
        Tuple[str, Optional[str]]: (クリーンな説明, 除去された追加情報)
    """
    original = description
    removed_info = []

    # 括弧とその内容を抽出（後で追加情報として保存）
    # 変更: 括弧を削除せず、LLMで処理させる
    # bracket_pattern = r'\s*\([^)]*\)'
    # brackets = re.findall(bracket_pattern, description)
    # if brackets:
    #     removed_info.extend([b.strip('() ') for b in brackets])
    #     description = re.sub(bracket_pattern, '', description)

    # NFSを除去（"or NFS"パターンを優先的に処理）
    if " or NFS" in description:
        # "white or NFS" → "white" にする
        description = description.replace(" or NFS", "")
        removed_info.append("NFS")
    elif ", or NFS" in description:
        # ", or NFS" パターンも処理
        description = description.replace(", or NFS", "")
        removed_info.append("NFS")
    elif description.endswith(", NFS"):
        description = description[:-5].strip()
        removed_info.append("NFS")
    elif description == "NFS":
        return None, "NFS"
    elif "NFS" in description:
        description = description.replace(", NFS", "").replace(" NFS", "")
        removed_info.append("NFS")

    # ヨーグルトの特別処理（NS as to type of milk）
    if description.startswith("Yogurt,") and "NS as to type of milk" in description and "Greek" not in description:
        # 通常のヨーグルト（非Greek）は特別処理
        if "NS as to type of milk, plain" in description:
            return "Yogurt, plain", "NS as to type of milk"
        elif "NS as to type of milk, fruit" in description:
            return "Yogurt, fruit", "NS as to type of milk"
        elif "NS as to type of milk, flavors other than fruit" in description:
            return "Yogurt, flavors other than fruit", "NS as to type of milk"
        elif "NS as to type of milk or flavor" in description:
            return "Yogurt", "NS as to type of milk or flavor"  # 保持する（後処理と同じ）
        else:
            return "Yogurt", "NS as to type of milk"

    # その他の特殊表記を除去
    if ", NS as to" in description:
        # "NS as to"を含む項目は信頼性が低いのでNoneを返す（ヨーグルト以外）
        return None, original

    # 前後の空白を除去
    description = description.strip()

    # 空文字列の場合はNone
    if not description:
        return None, original

    # 除去された情報を文字列として返す
    additional_info = ", ".join(removed_info) if removed_info else None

    return description, additional_info

def extract_brand_or_variety(description: str) -> Tuple[str, Optional[str]]:
    """
    ブランド名や種類を抽出

    例: "Cookie, chocolate chip, Brand X" -> ("Cookie, chocolate chip", "Brand X")

    注: USDAデータでは実際のブランド名はほとんど含まれていないため、
    この機能は限定的です。
    """
    # 明確なブランド表記パターンのみを抽出
    brand_patterns = [
        r',\s*([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)\s*brand',
        r',\s*brand\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)',
    ]

    for pattern in brand_patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            brand = match.group(1)
            clean_desc = description[:match.start()].strip().rstrip(',')
            return clean_desc, brand

    # USDAデータは基本的にジェネリック食品のため、ブランド抽出は不要
    return description, None


def parse_unit_from_description(description: str) -> Optional[str]:
    """
    portionDescriptionから単位を抽出
    
    例:
        "1 cup" -> "cup"
        "2 tablespoons" -> "tablespoon"
        "1 fl oz" -> "fl oz"
        "1 piece" -> "piece"
    """
    if not description:
        return None
    
    # 数字とスペースを削除してテキスト部分のみ抽出
    description = description.lower().strip()
    
    # 数字部分を削除（例: "1 cup" -> "cup"）
    text_part = re.sub(r'^\d+\.?\d*\s*', '', description).strip()
    
    if not text_part:
        return None
    
    # 複数形を単数形に変換（簡易版）
    unit_mappings = {
        'cups': 'cup',
        'tablespoons': 'tablespoon',
        'teaspoons': 'teaspoon',
        'ounces': 'oz',
        'fluid ounces': 'fl oz',
        'pieces': 'piece',
        'slices': 'slice',
        'servings': 'serving',
    }
    
    # マッピングで変換
    for plural, singular in unit_mappings.items():
        if plural in text_part:
            return singular
    
    # そのまま返す（既に単数形の場合）
    return text_part


def extract_unit_to_grams(food_portions: List[Dict]) -> Dict[str, float]:
    """
    foodPortionsからunit_to_gramsを生成
    
    Args:
        food_portions: foodPortionsの配列
    
    Returns:
        単位名をキー、グラム数を値とする辞書
    """
    unit_to_grams = {"gram": 1.0}  # 基準単位
    
    if not food_portions:
        return unit_to_grams
    
    for portion in food_portions:
        gram_weight = portion.get('gramWeight', 0)
        description = portion.get('portionDescription', '')
        
        # gramWeightが0または存在しない場合はスキップ
        if gram_weight <= 0 or not description:
            continue
        
        # 説明から単位を抽出
        unit = parse_unit_from_description(description)
        
        if unit and unit != 'undetermined' and unit != 'quantity not specified':
            # 既に存在する単位の場合、最初の値を優先（sequenceNumber順）
            if unit not in unit_to_grams:
                unit_to_grams[unit] = round(gram_weight, 2)
    
    # 共通の単位が含まれていない場合、デフォルト値を追加
    common_units = {
        'oz': 28.35,
        'lb': 453.6
    }
    
    for unit, weight in common_units.items():
        if unit not in unit_to_grams:
            unit_to_grams[unit] = weight
    
    return unit_to_grams

def preprocess_food_item(
    food_item: Dict,
    category: str = None,
    display_name_mappings: Dict[int, Dict[str, Optional[str]]] = None,
    original_name_mapping: Dict[str, int] = None,
    exclusion_set: set = None,
    stats: Dict = None,
    search_name_mappings: Dict[int, List[str]] = None,
    frequency_emoji_mappings: Dict[int, Dict[str, Optional[str]]] = None
) -> Optional[Dict]:
    """
    個別の食品項目を前処理

    Args:
        food_item: 食品項目の辞書（foodCode, description, etc.）
        category: 食品のカテゴリ名
        display_name_mappings: GPTファイルから読み込んだdisplay name mappings
        original_name_mapping: original nameから番号へのマッピング
        exclusion_set: 除外する番号のセット
        stats: 統計情報（除外理由の記録用）
        search_name_mappings: search_name_list.txtから読み込んだsearch name mappings
        frequency_emoji_mappings: frequency_emoji_list.txtから読み込んだ消費頻度・絵文字mappings

    Returns:
        前処理済みの食品項目、または除外する場合はNone
    """
    # descriptionのコピーを作成
    item = food_item.copy()
    original_desc = item['description']

    # 除外リストチェック（original descriptionと照合）
    if exclusion_set and original_name_mapping:
        item_number = original_name_mapping.get(original_desc)
        if item_number and item_number in exclusion_set:
            # 除外リストに含まれている場合
            if stats:
                stats['excluded_by_list'] = stats.get('excluded_by_list', 0) + 1
                stats['excluded_reasons']['Exclusion list'] += 1
            return None

    # display name mappingsの適用
    display_name = None
    display_variant = None
    brand_name = None
    display_name_applied = False
    
    if display_name_mappings and original_name_mapping:
        item_number = original_name_mapping.get(original_desc)
        if item_number and item_number in display_name_mappings:
            mapping = display_name_mappings[item_number]
            display_name = mapping.get('display_name')
            display_variant = mapping.get('display_variant')
            brand_name = mapping.get('brand_name')
            display_name_applied = True
            
            if stats:
                stats['display_name_applied'] = stats.get('display_name_applied', 0) + 1

    # search name mappingsの適用
    search_names = None
    if search_name_mappings and original_name_mapping:
        item_number = original_name_mapping.get(original_desc)
        if item_number and item_number in search_name_mappings:
            search_names = search_name_mappings[item_number]

    # frequency_emoji mappingsの適用
    consumption_frequency = None
    food_specific_emoji = None
    if frequency_emoji_mappings and original_name_mapping:
        item_number = original_name_mapping.get(original_desc)
        if item_number and item_number in frequency_emoji_mappings:
            freq_emoji_data = frequency_emoji_mappings[item_number]
            consumption_frequency = freq_emoji_data.get('consumption_frequency')
            food_specific_emoji = freq_emoji_data.get('food_specific_emoji')

    # 正規化（既存の処理も維持）
    normalized_desc, removed_info = normalize_description(original_desc)

    # NS as toやその他の理由で除外される場合
    if normalized_desc is None:
        return None

    # ブランド名の抽出（既存の処理）
    clean_desc, extracted_brand = extract_brand_or_variety(normalized_desc)

    # display nameが適用されている場合、それを使用
    if display_name_applied and display_name:
        # display nameを使用
        final_description = display_name
    else:
        # 既存の正規化された説明を使用
        final_description = clean_desc

    # 前処理済みデータの構造
    preprocessed = {
        'foodCode': item['foodCode'],
        'description': final_description,
        'original_description': original_desc,
        'category': category,  # カテゴリを追加
        'category_emoji': get_emoji(item['foodCode'], category),  # 食品固有またはカテゴリの絵文字を取得
        'preprocessed_info': {
            'removed': removed_info,
            'brand_or_variety': extracted_brand if not display_name_applied else brand_name,
            'was_modified': final_description != original_desc,
            'display_name_applied': display_name_applied
        }
    }

    # display_variantとbrand_nameを追加
    if display_name_applied:
        preprocessed['display_variant'] = display_variant
        preprocessed['brand_name'] = brand_name

    # search_namesを追加
    if search_names:
        preprocessed['search_names'] = search_names

    # consumption_frequencyとfood_specific_emojiを追加
    if consumption_frequency:
        preprocessed['consumption_frequency'] = consumption_frequency
    if food_specific_emoji:
        preprocessed['food_specific_emoji'] = food_specific_emoji

    # 栄養情報がある場合は保持
    if 'foodNutrients' in item:
        preprocessed['foodNutrients'] = item['foodNutrients']
    
    # foodPortionsを保持（unit_to_grams生成に必要）
    if 'foodPortions' in item:
        preprocessed['foodPortions'] = item['foodPortions']
        # unit_to_gramsを生成
        preprocessed['unit_to_grams'] = extract_unit_to_grams(item['foodPortions'])

    return preprocessed

def preprocess_category(
    category_data: Dict[str, Dict],
    display_name_mappings: Dict[int, Dict[str, Optional[str]]],
    original_name_mapping: Dict[str, int],
    exclusion_set: set,
    search_name_mappings: Dict[int, List[str]] = None,
    frequency_emoji_mappings: Dict[int, Dict[str, Optional[str]]] = None
) -> Tuple[Dict[str, Dict], Dict]:
    """
    カテゴリごとの食品データを前処理

    Args:
        category_data: カテゴリごとの食品データ
        display_name_mappings: GPTファイルから読み込んだdisplay name mappings
        original_name_mapping: original nameから番号へのマッピング
        exclusion_set: 除外する番号のセット
        search_name_mappings: search_name_list.txtから読み込んだsearch name mappings
        frequency_emoji_mappings: frequency_emoji_list.txtから読み込んだ消費頻度・絵文字mappings

    Returns:
        Tuple[前処理済みデータ, 統計情報]
    """
    preprocessed_data = {}
    stats = {
        'total_items': 0,
        'processed_items': 0,
        'excluded_items': 0,
        'excluded_by_list': 0,
        'modified_items': 0,
        'display_name_applied': 0,
        'excluded_reasons': Counter()
    }

    for category, category_info in category_data.items():
        # category_infoは {'count': n, 'foods': [...]} の形式
        if not isinstance(category_info, dict) or 'foods' not in category_info:
            continue

        items = category_info['foods']
        preprocessed_items = []

        for item in items:
            stats['total_items'] += 1
            # カテゴリ名を渡して前処理
            processed = preprocess_food_item(
                item,
                category,
                display_name_mappings,
                original_name_mapping,
                exclusion_set,
                stats,
                search_name_mappings,
                frequency_emoji_mappings
            )

            if processed:
                preprocessed_items.append(processed)
                stats['processed_items'] += 1

                if processed['preprocessed_info']['was_modified']:
                    stats['modified_items'] += 1
            else:
                stats['excluded_items'] += 1
                # 除外理由を記録
                if "NS as to" in item['description']:
                    stats['excluded_reasons']['NS as to'] += 1
                else:
                    stats['excluded_reasons']['Other'] += 1

        if preprocessed_items:
            # 元の構造を保持（count と foods）
            preprocessed_data[category] = {
                'count': len(preprocessed_items),
                'foods': preprocessed_items
            }

    return preprocessed_data, stats

def main():
    """メイン処理"""
    # パス設定
    base_dir = Path("/Users/odasoya/meal_analysis_api_2")
    input_dir = base_dir / "usda_data_processing" / "docs"
    output_dir = base_dir / "usda_data_processing" / "output"
    display_name_dir = base_dir / "usda_data_processing" / "display_name_generation"

    # 出力ディレクトリ作成
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print("🧹 USDA食材データ前処理")
    print("="*80)

    # Display name mappingsの読み込み
    print("\n📚 Display name mappings の読み込み中...")
    gpt_file = display_name_dir / "display_info_list.txt"
    original_name_file = display_name_dir / "original_name.txt"
    exclusion_file = display_name_dir / "exclusion_list.txt"
    
    display_name_mappings = load_display_name_mappings(gpt_file)
    original_name_mapping = load_original_name_mapping(original_name_file)
    exclusion_set = load_exclusion_set(exclusion_file)

    # Search name mappingsの読み込み
    search_name_file = display_name_dir / "search_name_list.txt"
    search_name_mappings = load_search_name_mappings(search_name_file)

    # Frequency emoji mappingsの読み込み
    frequency_emoji_file = display_name_dir / "frequency_emoji_list.txt"
    frequency_emoji_mappings = load_frequency_emoji_mappings(frequency_emoji_file)

    print(f"   ✅ Display name mappings: {len(display_name_mappings)}件")
    print(f"   ✅ Original name mappings: {len(original_name_mapping)}件")
    print(f"   ✅ Exclusion list: {len(exclusion_set)}件")
    print(f"   ✅ Search name mappings: {len(search_name_mappings)}件")
    print(f"   ✅ Frequency emoji mappings: {len(frequency_emoji_mappings)}件")

    # 処理対象ファイル
    files_to_process = [
        ("usda_raw_ingredients_all.json", "usda_raw_ingredients_preprocessed.json"),
        ("usda_prepared_ingredients_all.json", "usda_prepared_ingredients_preprocessed.json")
    ]

    overall_stats = {}

    for input_file, output_file in files_to_process:
        input_path = input_dir / input_file
        output_path = output_dir / output_file

        print(f"\n📂 処理中: {input_file}")
        print(f"   入力: {input_path}")
        print(f"   出力: {output_path}")

        # データ読み込み
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"❌ ファイルが見つかりません: {input_path}")
            continue
        except json.JSONDecodeError as e:
            print(f"❌ JSONの解析エラー: {e}")
            continue

        # カテゴリごとのデータか確認
        if 'categories' in data:
            category_data = data['categories']
        else:
            print(f"❌ 想定外のデータ形式です")
            continue

        # 前処理実行（マッピングを渡す）
        preprocessed_data, stats = preprocess_category(
            category_data,
            display_name_mappings,
            original_name_mapping,
            exclusion_set,
            search_name_mappings,
            frequency_emoji_mappings
        )

        # 結果を保存
        output_json = {
            "metadata": {
                "source": input_file,
                "preprocessing_applied": True,
                "display_names_applied": True,
                "processing_stats": {
                    "total_items": stats['total_items'],
                    "processed_items": stats['processed_items'],
                    "excluded_items": stats['excluded_items'],
                    "excluded_by_list": stats.get('excluded_by_list', 0),
                    "modified_items": stats['modified_items'],
                    "display_name_applied": stats.get('display_name_applied', 0),
                    "modification_rate": f"{(stats['modified_items']/stats['total_items']*100):.1f}%",
                    "exclusion_rate": f"{(stats['excluded_items']/stats['total_items']*100):.1f}%"
                }
            },
            "categories": preprocessed_data
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_json, f, ensure_ascii=False, indent=2)

        # 統計表示
        print(f"\n📊 処理結果:")
        print(f"   総項目数: {stats['total_items']:,}")
        print(f"   処理済み: {stats['processed_items']:,}")
        print(f"   除外項目: {stats['excluded_items']:,}")
        print(f"     - 除外リストによる除外: {stats.get('excluded_by_list', 0):,}")
        print(f"   修正項目: {stats['modified_items']:,}")
        print(f"   Display name適用: {stats.get('display_name_applied', 0):,}")
        print(f"   修正率: {(stats['modified_items']/stats['total_items']*100):.1f}%")

        if stats['excluded_reasons']:
            print(f"\n   除外理由:")
            for reason, count in stats['excluded_reasons'].most_common():
                print(f"     - {reason}: {count}件")

        print(f"\n✅ 保存完了: {output_path}")
        print(f"   ファイルサイズ: {output_path.stat().st_size / 1024:.1f} KB")

        overall_stats[input_file] = stats

    # 全体サマリー
    print("\n" + "="*80)
    print("🎯 前処理完了サマリー")
    print("="*80)

    total_items = sum(s['total_items'] for s in overall_stats.values())
    total_processed = sum(s['processed_items'] for s in overall_stats.values())
    total_excluded = sum(s['excluded_items'] for s in overall_stats.values())
    total_excluded_by_list = sum(s.get('excluded_by_list', 0) for s in overall_stats.values())
    total_modified = sum(s['modified_items'] for s in overall_stats.values())
    total_display_name_applied = sum(s.get('display_name_applied', 0) for s in overall_stats.values())

    print(f"\n📈 全体統計:")
    print(f"   総処理項目: {total_items:,}")
    print(f"   処理成功: {total_processed:,} ({total_processed/total_items*100:.1f}%)")
    print(f"   除外項目: {total_excluded:,} ({total_excluded/total_items*100:.1f}%)")
    print(f"     - 除外リストによる除外: {total_excluded_by_list:,}")
    print(f"   修正項目: {total_modified:,} ({total_modified/total_items*100:.1f}%)")
    print(f"   Display name適用: {total_display_name_applied:,} ({total_display_name_applied/total_items*100:.1f}%)")

    print("\n✨ 前処理が完了しました！")
    print("   次のステップ: split_ingredient_names_with_llm.py を実行してください")

if __name__ == "__main__":
    main()