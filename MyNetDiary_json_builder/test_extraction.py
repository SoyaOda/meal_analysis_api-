#!/usr/bin/env python3
import re

def test_extraction():
    # テストファイルを読み込み
    with open('MyNetDiary/Staple Foods/Beans & Peas/Beans baked canned plain or vegetarian.txt', 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # テストパターン
    name_match = re.search(r'Food Entry\s+(.+?)\s+\d+\s+cals', content)
    calories_match = re.search(r'Calories\s+(\d+)cals', content)
    protein_match = re.search(r'Protein\s+(\d+(?:\.\d+)?)g', content)
    fat_match = re.search(r'Total Fat\s+(\d+(?:\.\d+)?)g', content)
    carbs_match = re.search(r'Total Carbs\s+(\d+(?:\.\d+)?)g', content)
    weight_match = re.search(r'Weight\s+(\d+)g', content)

    print('名前:', name_match.group(1).strip() if name_match else 'なし')
    print('カロリー:', calories_match.group(1) if calories_match else 'なし')
    print('プロテイン:', protein_match.group(1) if protein_match else 'なし')
    print('脂肪:', fat_match.group(1) if fat_match else 'なし')
    print('炭水化物:', carbs_match.group(1) if carbs_match else 'なし')
    print('重量:', weight_match.group(1) if weight_match else 'なし')

if __name__ == "__main__":
    test_extraction() 