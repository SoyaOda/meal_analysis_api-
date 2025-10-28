# Pipeline vs VLM Label 栄養素比較レポート

生成日時: 2025-10-26 16:16:59

対象画像数: 50

## サマリー

### 平均差分（Pipeline - Label）

| 栄養素 | 平均差分 (%) |
|--------|--------------|
| カロリー | +13.5% |
| タンパク質 | +25.6% |
| 脂質 | +7.6% |
| 炭水化物 | +11.9% |

## 詳細比較表

| 画像 | Label Cal | Pipeline Cal | 差分 | Label P | Pipeline P | 差分 | Label F | Pipeline F | 差分 | Label C | Pipeline C | 差分 |
|------|-----------|--------------|------|---------|------------|------|---------|------------|------|---------|------------|------|
| test_food1.jpg | 891 | 1028 | +15.4% | 58.9 | 78.4 | +33.1% | 53.8 | 55.8 | +3.7% | 50.9 | 49.9 | -2.0% |
| test_food2.jpg | 684 | 971 | +41.9% | 63.9 | 69.2 | +8.3% | 23.8 | 35.3 | +48.3% | 57.6 | 65.7 | +14.1% |
| test_food3.jpg | 1000 | 1040 | +3.9% | 56.7 | 52.5 | -7.4% | 60.4 | 68.4 | +13.2% | 68.7 | 53.3 | -22.4% |
| test_food4.jpg | 702 | 830 | +18.3% | 53.0 | 73.2 | +38.1% | 36.3 | 32.9 | -9.4% | 46.4 | 56.0 | +20.7% |
| test_food5.jpg | 530 | 610 | +15.2% | 50.8 | 64.4 | +26.8% | 18.1 | 16.8 | -7.2% | 41.6 | 48.1 | +15.6% |
| test_food6.jpg | 504 | 812 | +61.0% | 25.2 | 28.1 | +11.5% | 17.6 | 26.9 | +52.8% | 65.6 | 112.2 | +71.0% |
| test_food7.jpg | 722 | 876 | +21.3% | 50.9 | 85.8 | +68.6% | 44.4 | 42.6 | -4.1% | 34.1 | 39.1 | +14.7% |
| test_food8.jpg | 634 | 597 | -5.8% | 40.8 | 45.6 | +11.8% | 17.2 | 15.2 | -11.6% | 84.5 | 68.9 | -18.5% |
| test_food9.jpg | 771 | 738 | -4.3% | 46.2 | 51.8 | +12.1% | 49.2 | 34.0 | -30.9% | 45.5 | 57.3 | +25.9% |
| test_food10.jpg | 854 | 1049 | +22.8% | 59.5 | 109.3 | +83.7% | 48.1 | 47.6 | -1.0% | 53.4 | 47.7 | -10.7% |
| test_food11.jpg | 499 | 820 | +64.2% | 27.4 | 36.7 | +33.9% | 27.4 | 38.2 | +39.4% | 40.2 | 85.1 | +111.7% |
| test_food12.jpg | 441 | 412 | -6.5% | 24.6 | 27.1 | +10.2% | 28.0 | 26.4 | -5.7% | 25.6 | 16.2 | -36.7% |
| test_food13.jpg | 643 | 838 | +30.3% | 31.0 | 32.4 | +4.5% | 26.3 | 43.5 | +65.4% | 80.0 | 109.2 | +36.5% |
| test_food14.jpg | 749 | 665 | -11.3% | 45.8 | 61.3 | +33.8% | 26.9 | 17.4 | -35.3% | 81.0 | 61.5 | -24.1% |
| test_food15.jpg | 488 | 640 | +31.3% | 25.9 | 97.4 | +276.1% | 24.1 | 26.0 | +7.9% | 46.0 | 7.4 | -83.9% |
| test_food16.jpg | 855 | 887 | +3.7% | 58.0 | 69.8 | +20.3% | 42.6 | 36.7 | -13.8% | 62.1 | 65.4 | +5.3% |
| test_food17.jpg | 746 | 828 | +11.0% | 25.7 | 20.6 | -19.8% | 34.7 | 36.5 | +5.2% | 85.4 | 104.2 | +22.0% |
| test_food18.jpg | 582 | 722 | +24.0% | 43.6 | 35.8 | -17.9% | 14.8 | 28.3 | +91.2% | 70.8 | 80.6 | +13.8% |
| test_food19.jpg | 599 | 574 | -4.2% | 52.1 | 59.2 | +13.6% | 16.2 | 13.8 | -14.8% | 60.5 | 59.2 | -2.1% |
| test_food20.jpg | 519 | 678 | +30.6% | 32.6 | 35.9 | +10.1% | 24.8 | 38.5 | +55.2% | 45.0 | 58.9 | +30.9% |
| test_food21.jpg | 725 | 788 | +8.6% | 46.5 | 35.1 | -24.5% | 41.7 | 47.5 | +13.9% | 43.0 | 65.4 | +52.1% |
| test_food22.jpg | 646 | 686 | +6.3% | 31.4 | 23.8 | -24.2% | 28.2 | 10.3 | -63.5% | 69.8 | 121.7 | +74.4% |
| test_food23.jpg | 706 | 675 | -4.4% | 24.5 | 28.8 | +17.6% | 40.9 | 30.1 | -26.4% | 64.6 | 72.5 | +12.2% |
| test_food24.jpg | 370 | 364 | -1.9% | 47.1 | 36.0 | -23.6% | 12.7 | 20.7 | +63.0% | 15.6 | 9.5 | -39.1% |
| test_food25.jpg | 748 | 922 | +23.2% | 27.6 | 41.1 | +48.9% | 43.2 | 67.0 | +55.1% | 61.6 | 43.8 | -28.9% |
| test_food26.jpg | 786 | 975 | +24.1% | 32.2 | 33.0 | +2.5% | 36.9 | 55.0 | +49.1% | 80.4 | 86.2 | +7.2% |
| test_food27.jpg | 1069 | 680 | -36.4% | 50.8 | 49.6 | -2.4% | 54.3 | 18.7 | -65.6% | 85.5 | 79.4 | -7.1% |
| test_food28.jpg | 944 | 847 | -10.2% | 36.0 | 45.3 | +25.8% | 40.5 | 34.0 | -16.0% | 107.6 | 90.7 | -15.7% |
| test_food29.jpg | 769 | 635 | -17.4% | 62.7 | 27.7 | -55.8% | 28.3 | 24.7 | -12.7% | 70.2 | 74.2 | +5.7% |
| test_food30.jpg | 714 | 629 | -11.8% | 41.5 | 46.2 | +11.3% | 39.3 | 24.0 | -38.9% | 56.2 | 56.3 | +0.2% |
| test_food31.jpg | 609 | 532 | -12.5% | 40.9 | 57.6 | +40.8% | 29.9 | 17.4 | -41.8% | 46.0 | 32.9 | -28.5% |
| test_food32.jpg | 677 | 584 | -13.8% | 32.2 | 26.7 | -17.1% | 32.2 | 22.2 | -31.1% | 66.1 | 67.8 | +2.6% |
| test_food33.jpg | 572 | 662 | +15.8% | 31.5 | 62.6 | +98.7% | 26.2 | 19.7 | -24.8% | 48.7 | 54.4 | +11.7% |
| test_food34.jpg | 672 | 598 | -11.1% | 30.1 | 49.7 | +65.1% | 36.5 | 23.2 | -36.4% | 57.3 | 44.9 | -21.6% |
| test_food35.jpg | 856 | 942 | +10.1% | 47.9 | 72.2 | +50.7% | 40.5 | 41.3 | +2.0% | 85.5 | 69.9 | -18.2% |
| test_food36.jpg | 607 | 654 | +7.7% | 36.7 | 54.4 | +48.2% | 28.5 | 19.7 | -30.9% | 49.5 | 60.7 | +22.6% |
| test_food37.jpg | 980 | 885 | -9.8% | 39.5 | 62.0 | +57.0% | 59.8 | 34.2 | -42.8% | 74.2 | 80.2 | +8.1% |
| test_food38.jpg | 681 | 914 | +34.2% | 34.6 | 39.6 | +14.5% | 41.1 | 64.2 | +56.2% | 45.7 | 61.7 | +35.0% |
| test_food39.jpg | 696 | 686 | -1.4% | 25.5 | 23.8 | -6.7% | 32.3 | 10.3 | -68.1% | 82.3 | 121.7 | +47.9% |
| test_food40.jpg | 974 | 1332 | +36.7% | 36.7 | 54.1 | +47.4% | 49.1 | 69.6 | +41.8% | 96.8 | 122.3 | +26.3% |
| test_food41.jpg | 682 | 780 | +14.3% | 50.2 | 57.6 | +14.7% | 33.8 | 31.1 | -8.0% | 43.9 | 67.8 | +54.4% |
| test_food42.jpg | 786 | 681 | -13.3% | 49.4 | 53.0 | +7.3% | 31.8 | 19.9 | -37.4% | 83.7 | 70.4 | -15.9% |
| test_food43.jpg | 566 | 897 | +58.6% | 54.4 | 75.2 | +38.2% | 20.7 | 37.1 | +79.2% | 41.6 | 62.3 | +49.8% |
| test_food44.jpg | 518 | 708 | +36.6% | 21.9 | 20.2 | -7.8% | 17.8 | 34.9 | +96.1% | 75.2 | 77.2 | +2.7% |
| test_food45.jpg | 791 | 1156 | +46.2% | 29.5 | 46.9 | +59.0% | 40.0 | 51.7 | +29.3% | 80.1 | 130.7 | +63.2% |
| test_food46.jpg | 677 | 568 | -16.1% | 31.2 | 45.9 | +47.1% | 29.5 | 21.5 | -27.1% | 74.9 | 48.7 | -35.0% |
| test_food47.jpg | 783 | 912 | +16.6% | 36.5 | 34.6 | -5.2% | 34.2 | 38.9 | +13.7% | 86.8 | 107.9 | +24.3% |
| test_food48.jpg | 546 | 764 | +39.9% | 22.8 | 25.4 | +11.4% | 17.0 | 40.2 | +136.5% | 71.8 | 72.9 | +1.5% |
| test_food49.jpg | 602 | 1007 | +67.2% | 24.3 | 38.0 | +56.4% | 23.6 | 37.7 | +59.7% | 73.5 | 129.9 | +76.7% |
| test_food50.jpg | 733 | 946 | +29.0% | 28.9 | 38.4 | +32.9% | 40.7 | 44.4 | +9.1% | 69.2 | 100.5 | +45.2% |

## 個別詳細

### test_food1.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | beef steak | 170g | 425 | 44.2g | 28.9g | 0.0g |
| main_food | zucchini and yellow squash | 130g | 65 | 2.6g | 3.9g | 7.8g |
| main_food | macaroni and cheese | 140g | 266 | 9.8g | 11.2g | 33.6g |
| extra | mixed salad greens | 80g | 16 | 1.4g | 0.2g | 2.9g |
| extra | cherry tomatoes | 60g | 11 | 0.5g | 0.1g | 2.3g |
| extra | cucumber | 25g | 4 | 0.2g | 0.0g | 1.0g |
| extra | carrots | 25g | 10 | 0.2g | 0.1g | 2.5g |
| extra | vinaigrette dressing | 20g | 94 | 0.0g | 9.4g | 0.8g |
| **合計** | - | - | **891** | **58.9g** | **53.8g** | **50.9g** |

**Pipeline栄養素**

合計: 1028 kcal, P: 78.4g, F: 55.8g, C: 49.9g

**差分 (Pipeline - Label)**

- カロリー: +137.1 kcal (+15.4%)
- タンパク質: +19.5g (+33.1%)
- 脂質: +2.0g (+3.7%)
- 炭水化物: -1.0g (-2.0%)

---

### test_food2.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | chicken breast | 150g | 248 | 46.5g | 5.4g | 0.0g |
| main_food | macaroni and cheese | 180g | 342 | 12.6g | 14.4g | 43.2g |
| main_food | broccoli | 100g | 35 | 2.4g | 0.4g | 7.2g |
| main_food | yellow squash | 120g | 60 | 2.4g | 3.6g | 7.2g |
| **合計** | - | - | **684** | **63.9g** | **23.8g** | **57.6g** |

**Pipeline栄養素**

合計: 971 kcal, P: 69.2g, F: 35.3g, C: 65.7g

**差分 (Pipeline - Label)**

- カロリー: +286.5 kcal (+41.9%)
- タンパク質: +5.3g (+8.3%)
- 脂質: +11.5g (+48.3%)
- 炭水化物: +8.1g (+14.1%)

---

### test_food3.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | beef steak | 180g | 450 | 46.8g | 30.6g | 0.0g |
| extra | tomato onion relish | 30g | 18 | 0.3g | 0.6g | 3.0g |
| main_food | roasted potatoes | 220g | 330 | 5.5g | 9.9g | 59.4g |
| main_food | asparagus | 130g | 32 | 3.8g | 0.5g | 6.0g |
| extra | garlic aioli | 25g | 170 | 0.3g | 18.8g | 0.3g |
| **合計** | - | - | **1000** | **56.7g** | **60.4g** | **68.7g** |

**Pipeline栄養素**

合計: 1040 kcal, P: 52.5g, F: 68.4g, C: 53.3g

**差分 (Pipeline - Label)**

- カロリー: +39.0 kcal (+3.9%)
- タンパク質: -4.2g (-7.4%)
- 脂質: +8.0g (+13.2%)
- 炭水化物: -15.4g (-22.4%)

---

### test_food4.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | chicken thigh | 160g | 366 | 40.0g | 24.0g | 0.0g |
| main_food | macaroni and cheese | 150g | 285 | 10.5g | 12.0g | 36.0g |
| extra | mixed salad greens | 70g | 14 | 1.3g | 0.1g | 2.5g |
| extra | cucumber | 40g | 6 | 0.3g | 0.0g | 1.5g |
| extra | red bell pepper | 50g | 16 | 0.5g | 0.2g | 3.0g |
| extra | red onion | 15g | 6 | 0.2g | 0.0g | 1.4g |
| extra | carrots | 20g | 8 | 0.2g | 0.0g | 2.0g |
| **合計** | - | - | **702** | **53.0g** | **36.3g** | **46.4g** |

**Pipeline栄養素**

合計: 830 kcal, P: 73.2g, F: 32.9g, C: 56.0g

**差分 (Pipeline - Label)**

- カロリー: +128.3 kcal (+18.3%)
- タンパク質: +20.2g (+38.1%)
- 脂質: -3.4g (-9.4%)
- 炭水化物: +9.6g (+20.7%)

---

### test_food5.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | asparagus | 140g | 35 | 4.1g | 0.6g | 6.4g |
| main_food | chicken breast | 130g | 214 | 40.3g | 4.7g | 0.0g |
| main_food | garlic bread | 80g | 280 | 6.4g | 12.8g | 35.2g |
| **合計** | - | - | **530** | **50.8g** | **18.1g** | **41.6g** |

**Pipeline栄養素**

合計: 610 kcal, P: 64.4g, F: 16.8g, C: 48.1g

**差分 (Pipeline - Label)**

- カロリー: +80.5 kcal (+15.2%)
- タンパク質: +13.6g (+26.8%)
- 脂質: -1.3g (-7.2%)
- 炭水化物: +6.5g (+15.6%)

---

### test_food6.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | cream of chicken soup with vegetables | 400g | 280 | 18.0g | 14.0g | 24.0g |
| main_food | dinner roll | 80g | 224 | 7.2g | 3.6g | 41.6g |
| **合計** | - | - | **504** | **25.2g** | **17.6g** | **65.6g** |

**Pipeline栄養素**

合計: 812 kcal, P: 28.1g, F: 26.9g, C: 112.2g

**差分 (Pipeline - Label)**

- カロリー: +307.6 kcal (+61.0%)
- タンパク質: +2.9g (+11.5%)
- 脂質: +9.3g (+52.8%)
- 炭水化物: +46.6g (+71.0%)

---

### test_food7.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | beef steak | 170g | 425 | 44.2g | 28.9g | 0.0g |
| main_food | broccoli | 120g | 42 | 2.9g | 0.5g | 8.6g |
| main_food | potato salad | 150g | 255 | 3.8g | 15.0g | 25.5g |
| **合計** | - | - | **722** | **50.9g** | **44.4g** | **34.1g** |

**Pipeline栄養素**

合計: 876 kcal, P: 85.8g, F: 42.6g, C: 39.1g

**差分 (Pipeline - Label)**

- カロリー: +154.0 kcal (+21.3%)
- タンパク質: +34.9g (+68.6%)
- 脂質: -1.8g (-4.1%)
- 炭水化物: +5.0g (+14.7%)

---

### test_food8.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | breaded fish fillet | 150g | 330 | 30.0g | 15.0g | 22.5g |
| main_food | pearl couscous | 180g | 202 | 6.8g | 0.5g | 41.4g |
| main_food | broccoli | 120g | 42 | 2.9g | 0.5g | 8.6g |
| main_food | carrots | 120g | 60 | 1.1g | 1.2g | 12.0g |
| **合計** | - | - | **634** | **40.8g** | **17.2g** | **84.5g** |

**Pipeline栄養素**

合計: 597 kcal, P: 45.6g, F: 15.2g, C: 68.9g

**差分 (Pipeline - Label)**

- カロリー: -36.9 kcal (-5.8%)
- タンパク質: +4.8g (+11.8%)
- 脂質: -2.0g (-11.6%)
- 炭水化物: -15.6g (-18.5%)

---

### test_food9.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | pork ribs with barbecue sauce | 180g | 576 | 36.0g | 45.0g | 10.8g |
| main_food | sweet corn kernels | 100g | 96 | 3.4g | 1.5g | 21.0g |
| extra | mixed salad greens | 60g | 12 | 1.1g | 0.1g | 2.2g |
| extra | figs | 60g | 44 | 0.5g | 0.2g | 11.5g |
| extra | prosciutto | 20g | 43 | 5.2g | 2.4g | 0.0g |
| **合計** | - | - | **771** | **46.2g** | **49.2g** | **45.5g** |

**Pipeline栄養素**

合計: 738 kcal, P: 51.8g, F: 34.0g, C: 57.3g

**差分 (Pipeline - Label)**

- カロリー: -33.4 kcal (-4.3%)
- タンパク質: +5.6g (+12.1%)
- 脂質: -15.2g (-30.9%)
- 炭水化物: +11.8g (+25.9%)

---

### test_food10.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | beef steak | 170g | 425 | 44.2g | 28.9g | 0.0g |
| main_food | broccoli | 120g | 42 | 2.9g | 0.5g | 8.6g |
| main_food | macaroni and cheese | 140g | 266 | 9.8g | 11.2g | 33.6g |
| extra | mixed salad greens | 80g | 16 | 1.4g | 0.2g | 2.9g |
| extra | cucumber | 50g | 8 | 0.4g | 0.1g | 1.9g |
| extra | carrots | 20g | 8 | 0.2g | 0.0g | 2.0g |
| extra | red onion | 15g | 6 | 0.2g | 0.0g | 1.4g |
| extra | red bell pepper | 40g | 12 | 0.4g | 0.1g | 2.4g |
| extra | vinaigrette dressing | 15g | 70 | 0.0g | 7.1g | 0.6g |
| **合計** | - | - | **854** | **59.5g** | **48.1g** | **53.4g** |

**Pipeline栄養素**

合計: 1049 kcal, P: 109.3g, F: 47.6g, C: 47.7g

**差分 (Pipeline - Label)**

- カロリー: +194.5 kcal (+22.8%)
- タンパク質: +49.8g (+83.7%)
- 脂質: -0.5g (-1.0%)
- 炭水化物: -5.7g (-10.7%)

---

### test_food11.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | beef lasagna | 240g | 384 | 21.6g | 19.2g | 33.6g |
| extra | mixed salad greens | 40g | 8 | 0.8g | 0.1g | 1.6g |
| extra | cucumber | 40g | 6 | 0.3g | 0.0g | 1.4g |
| extra | avocado | 40g | 64 | 0.8g | 6.0g | 3.6g |
| extra | prosciutto | 15g | 37 | 3.9g | 2.1g | 0.0g |
| **合計** | - | - | **499** | **27.4g** | **27.4g** | **40.2g** |

**Pipeline栄養素**

合計: 820 kcal, P: 36.7g, F: 38.2g, C: 85.1g

**差分 (Pipeline - Label)**

- カロリー: +320.4 kcal (+64.2%)
- タンパク質: +9.3g (+33.9%)
- 脂質: +10.8g (+39.4%)
- 炭水化物: +44.9g (+111.7%)

---

### test_food12.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | omelet | 180g | 270 | 18.9g | 19.8g | 2.7g |
| extra | salsa | 50g | 18 | 0.8g | 0.1g | 3.5g |
| extra | mixed salad greens | 50g | 10 | 1.0g | 0.2g | 2.0g |
| extra | tomato | 30g | 5 | 0.3g | 0.1g | 1.2g |
| extra | vinaigrette dressing | 25g | 68 | 0.0g | 6.8g | 1.5g |
| extra | broccoli | 90g | 32 | 2.2g | 0.4g | 6.3g |
| extra | corn kernels | 40g | 38 | 1.4g | 0.6g | 8.4g |
| **合計** | - | - | **441** | **24.6g** | **28.0g** | **25.6g** |

**Pipeline栄養素**

合計: 412 kcal, P: 27.1g, F: 26.4g, C: 16.2g

**差分 (Pipeline - Label)**

- カロリー: -28.8 kcal (-6.5%)
- タンパク質: +2.5g (+10.2%)
- 脂質: -1.6g (-5.7%)
- 炭水化物: -9.4g (-36.7%)

---

### test_food13.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | beef fajita tacos with peppers and onions | 270g | 446 | 27.0g | 18.9g | 45.9g |
| extra | sour cream | 30g | 59 | 0.7g | 6.0g | 1.1g |
| main_food | corn on the cob | 80g | 77 | 2.7g | 1.2g | 16.8g |
| main_food | red grapes | 90g | 62 | 0.6g | 0.2g | 16.2g |
| **合計** | - | - | **643** | **31.0g** | **26.3g** | **80.0g** |

**Pipeline栄養素**

合計: 838 kcal, P: 32.4g, F: 43.5g, C: 109.2g

**差分 (Pipeline - Label)**

- カロリー: +195.1 kcal (+30.3%)
- タンパク質: +1.4g (+4.5%)
- 脂質: +17.2g (+65.4%)
- 炭水化物: +29.2g (+36.5%)

---

### test_food14.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | chicken thigh | 140g | 293 | 36.4g | 15.3g | 0.0g |
| main_food | mexican rice | 160g | 240 | 4.8g | 5.6g | 43.2g |
| main_food | mashed sweet potato | 140g | 140 | 2.8g | 0.3g | 32.2g |
| extra | mixed salad greens | 40g | 8 | 0.8g | 0.1g | 1.6g |
| extra | broccoli | 40g | 14 | 1.0g | 0.2g | 2.8g |
| extra | vinaigrette dressing | 20g | 55 | 0.0g | 5.4g | 1.2g |
| **合計** | - | - | **749** | **45.8g** | **26.9g** | **81.0g** |

**Pipeline栄養素**

合計: 665 kcal, P: 61.3g, F: 17.4g, C: 61.5g

**差分 (Pipeline - Label)**

- カロリー: -84.8 kcal (-11.3%)
- タンパク質: +15.5g (+33.8%)
- 脂質: -9.5g (-35.3%)
- 炭水化物: -19.5g (-24.1%)

---

### test_food15.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | shepherd's pie with beef | 250g | 400 | 22.5g | 21.3g | 32.5g |
| main_food | broccoli | 90g | 32 | 2.2g | 0.4g | 6.3g |
| main_food | stewed bell peppers and tomatoes | 80g | 56 | 1.2g | 2.4g | 7.2g |
| **合計** | - | - | **488** | **25.9g** | **24.1g** | **46.0g** |

**Pipeline栄養素**

合計: 640 kcal, P: 97.4g, F: 26.0g, C: 7.4g

**差分 (Pipeline - Label)**

- カロリー: +152.5 kcal (+31.3%)
- タンパク質: +71.5g (+276.1%)
- 脂質: +1.9g (+7.9%)
- 炭水化物: -38.6g (-83.9%)

---

### test_food16.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | pork loin chop | 160g | 400 | 41.6g | 24.0g | 0.0g |
| main_food | macaroni and cheese | 170g | 306 | 11.9g | 13.6g | 37.4g |
| main_food | broccoli | 80g | 28 | 1.9g | 0.3g | 5.6g |
| main_food | carrots | 100g | 40 | 0.8g | 0.2g | 9.0g |
| extra | cabbage | 60g | 15 | 0.8g | 0.1g | 3.6g |
| extra | cucumber | 40g | 6 | 0.3g | 0.0g | 1.4g |
| extra | corn kernels | 20g | 19 | 0.7g | 0.3g | 4.2g |
| extra | vinaigrette dressing | 15g | 41 | 0.0g | 4.1g | 0.9g |
| **合計** | - | - | **855** | **58.0g** | **42.6g** | **62.1g** |

**Pipeline栄養素**

合計: 887 kcal, P: 69.8g, F: 36.7g, C: 65.4g

**差分 (Pipeline - Label)**

- カロリー: +31.9 kcal (+3.7%)
- タンパク質: +11.8g (+20.3%)
- 脂質: -5.9g (-13.8%)
- 炭水化物: +3.3g (+5.3%)

---

### test_food17.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | fried rice with ground beef and corn | 220g | 396 | 13.2g | 13.2g | 57.2g |
| main_food | fried egg | 60g | 118 | 7.8g | 9.0g | 0.6g |
| extra | broccoli | 90g | 32 | 2.2g | 0.4g | 6.3g |
| extra | mayonnaise | 15g | 102 | 0.0g | 11.3g | 0.2g |
| main_food | tomato | 80g | 14 | 0.7g | 0.2g | 3.1g |
| main_food | stewed potatoes and carrots with mushrooms | 120g | 84 | 1.8g | 0.6g | 18.0g |
| **合計** | - | - | **746** | **25.7g** | **34.7g** | **85.4g** |

**Pipeline栄養素**

合計: 828 kcal, P: 20.6g, F: 36.5g, C: 104.2g

**差分 (Pipeline - Label)**

- カロリー: +82.2 kcal (+11.0%)
- タンパク質: -5.1g (-19.8%)
- 脂質: +1.8g (+5.2%)
- 炭水化物: +18.8g (+22.0%)

---

### test_food18.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | breaded chicken breast | 150g | 322 | 34.5g | 13.5g | 16.5g |
| main_food | pearl couscous | 150g | 168 | 5.7g | 0.6g | 34.5g |
| main_food | carrots | 150g | 60 | 1.2g | 0.3g | 13.5g |
| main_food | broccoli | 90g | 32 | 2.2g | 0.4g | 6.3g |
| **合計** | - | - | **582** | **43.6g** | **14.8g** | **70.8g** |

**Pipeline栄養素**

合計: 722 kcal, P: 35.8g, F: 28.3g, C: 80.6g

**差分 (Pipeline - Label)**

- カロリー: +139.5 kcal (+24.0%)
- タンパク質: -7.8g (-17.9%)
- 脂質: +13.5g (+91.2%)
- 炭水化物: +9.8g (+13.8%)

---

### test_food19.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | pork tenderloin | 160g | 229 | 41.6g | 6.4g | 0.0g |
| extra | mustard cream sauce | 30g | 90 | 0.6g | 8.4g | 1.2g |
| main_food | pearl couscous | 180g | 202 | 6.8g | 0.7g | 41.4g |
| main_food | green beans | 120g | 42 | 2.3g | 0.2g | 9.5g |
| main_food | raspberries | 70g | 36 | 0.8g | 0.5g | 8.4g |
| **合計** | - | - | **599** | **52.1g** | **16.2g** | **60.5g** |

**Pipeline栄養素**

合計: 574 kcal, P: 59.2g, F: 13.8g, C: 59.2g

**差分 (Pipeline - Label)**

- カロリー: -25.1 kcal (-4.2%)
- タンパク質: +7.1g (+13.6%)
- 脂質: -2.4g (-14.8%)
- 炭水化物: -1.3g (-2.1%)

---

### test_food20.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | beef stew | 350g | 350 | 24.5g | 17.5g | 24.5g |
| extra | sour cream | 20g | 39 | 0.5g | 4.0g | 0.7g |
| extra | mixed salad greens | 70g | 14 | 1.4g | 0.2g | 2.8g |
| extra | cucumber | 50g | 8 | 0.4g | 0.1g | 1.8g |
| extra | figs | 80g | 59 | 0.6g | 0.2g | 15.2g |
| extra | prosciutto | 20g | 49 | 5.2g | 2.8g | 0.0g |
| **合計** | - | - | **519** | **32.6g** | **24.8g** | **45.0g** |

**Pipeline栄養素**

合計: 678 kcal, P: 35.9g, F: 38.5g, C: 58.9g

**差分 (Pipeline - Label)**

- カロリー: +158.7 kcal (+30.6%)
- タンパク質: +3.3g (+10.1%)
- 脂質: +13.7g (+55.2%)
- 炭水化物: +13.9g (+30.9%)

---

### test_food21.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| extra | flour tortilla | 80g | 240 | 6.4g | 6.4g | 39.2g |
| extra | ground beef | 120g | 305 | 31.2g | 20.4g | 0.0g |
| extra | cheddar cheese | 30g | 121 | 7.5g | 9.9g | 0.4g |
| extra | sour cream | 25g | 48 | 0.6g | 4.8g | 0.9g |
| extra | lettuce | 30g | 4 | 0.4g | 0.1g | 0.9g |
| extra | tomato | 40g | 7 | 0.4g | 0.1g | 1.6g |
| **合計** | - | - | **725** | **46.5g** | **41.7g** | **43.0g** |

**Pipeline栄養素**

合計: 788 kcal, P: 35.1g, F: 47.5g, C: 65.4g

**差分 (Pipeline - Label)**

- カロリー: +62.2 kcal (+8.6%)
- タンパク質: -11.4g (-24.5%)
- 脂質: +5.8g (+13.9%)
- 炭水化物: +22.4g (+52.1%)

---

### test_food22.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| extra | spaghetti | 180g | 283 | 10.4g | 1.6g | 55.6g |
| extra | shrimp | 70g | 69 | 16.8g | 0.2g | 0.1g |
| extra | broccoli | 80g | 28 | 1.9g | 0.3g | 5.8g |
| extra | olive oil | 20g | 177 | 0.0g | 20.0g | 0.0g |
| extra | mixed salad greens | 90g | 15 | 1.6g | 0.3g | 2.7g |
| extra | tomato | 40g | 7 | 0.4g | 0.1g | 1.6g |
| extra | carrot | 25g | 10 | 0.2g | 0.1g | 2.4g |
| extra | vinaigrette dressing | 20g | 56 | 0.1g | 5.6g | 1.6g |
| main_food | water | 300g | 0 | 0.0g | 0.0g | 0.0g |
| **合計** | - | - | **646** | **31.4g** | **28.2g** | **69.8g** |

**Pipeline栄養素**

合計: 686 kcal, P: 23.8g, F: 10.3g, C: 121.7g

**差分 (Pipeline - Label)**

- カロリー: +40.8 kcal (+6.3%)
- タンパク質: -7.6g (-24.2%)
- 脂質: -17.9g (-63.5%)
- 炭水化物: +51.9g (+74.4%)

---

### test_food23.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | beef fried rice | 200g | 400 | 14.0g | 16.0g | 52.0g |
| main_food | fried egg | 50g | 98 | 6.8g | 7.5g | 0.6g |
| main_food | broccoli | 60g | 21 | 1.4g | 0.2g | 4.3g |
| extra | mayonnaise | 15g | 102 | 0.2g | 11.3g | 0.2g |
| extra | mixed salad greens | 80g | 14 | 1.4g | 0.2g | 2.4g |
| extra | tomato | 40g | 7 | 0.4g | 0.1g | 1.6g |
| extra | carrot | 20g | 8 | 0.2g | 0.0g | 1.9g |
| extra | vinaigrette dressing | 20g | 56 | 0.1g | 5.6g | 1.6g |
| **合計** | - | - | **706** | **24.5g** | **40.9g** | **64.6g** |

**Pipeline栄養素**

合計: 675 kcal, P: 28.8g, F: 30.1g, C: 72.5g

**差分 (Pipeline - Label)**

- カロリー: -31.3 kcal (-4.4%)
- タンパク質: +4.3g (+17.6%)
- 脂質: -10.8g (-26.4%)
- 炭水化物: +7.9g (+12.2%)

---

### test_food24.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| extra | mixed salad greens | 80g | 14 | 1.4g | 0.2g | 2.4g |
| extra | chicken breast | 120g | 198 | 37.2g | 4.3g | 0.0g |
| extra | teriyaki sauce | 35g | 46 | 0.7g | 0.1g | 9.8g |
| extra | sesame seeds | 5g | 29 | 0.9g | 2.5g | 1.2g |
| extra | boiled egg | 50g | 78 | 6.5g | 5.5g | 0.6g |
| extra | tomato | 40g | 7 | 0.4g | 0.1g | 1.6g |
| **合計** | - | - | **370** | **47.1g** | **12.7g** | **15.6g** |

**Pipeline栄養素**

合計: 364 kcal, P: 36.0g, F: 20.7g, C: 9.5g

**差分 (Pipeline - Label)**

- カロリー: -7.0 kcal (-1.9%)
- タンパク質: -11.1g (-23.6%)
- 脂質: +8.0g (+63.0%)
- 炭水化物: -6.1g (-39.1%)

---

### test_food25.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | hot dog with bun | 120g | 348 | 13.2g | 19.2g | 28.8g |
| extra | beef chili | 90g | 105 | 6.6g | 3.4g | 11.3g |
| extra | cheddar cheese | 20g | 80 | 5.0g | 6.6g | 0.3g |
| main_food | potato chips | 40g | 214 | 2.8g | 14.0g | 21.2g |
| **合計** | - | - | **748** | **27.6g** | **43.2g** | **61.6g** |

**Pipeline栄養素**

合計: 922 kcal, P: 41.1g, F: 67.0g, C: 43.8g

**差分 (Pipeline - Label)**

- カロリー: +173.5 kcal (+23.2%)
- タンパク質: +13.5g (+48.9%)
- 脂質: +23.8g (+55.1%)
- 炭水化物: -17.8g (-28.9%)

---

### test_food26.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | spaghetti with tomato sauce | 280g | 392 | 13.4g | 7.0g | 70.0g |
| extra | italian sausage | 100g | 301 | 12.0g | 26.0g | 2.0g |
| extra | parmesan cheese | 10g | 43 | 3.8g | 2.9g | 0.4g |
| main_food | bean sprout salad | 100g | 50 | 3.0g | 1.0g | 8.0g |
| **合計** | - | - | **786** | **32.2g** | **36.9g** | **80.4g** |

**Pipeline栄養素**

合計: 975 kcal, P: 33.0g, F: 55.0g, C: 86.2g

**差分 (Pipeline - Label)**

- カロリー: +189.3 kcal (+24.1%)
- タンパク質: +0.8g (+2.5%)
- 脂質: +18.1g (+49.1%)
- 炭水化物: +5.8g (+7.2%)

---

### test_food27.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | white rice | 200g | 260 | 5.4g | 0.6g | 56.0g |
| main_food | beef with peppers and onions | 150g | 270 | 21.0g | 15.0g | 9.0g |
| main_food | pork with cabbage | 170g | 289 | 20.4g | 18.7g | 8.5g |
| main_food | mayonnaise salad | 100g | 250 | 4.0g | 20.0g | 12.0g |
| **合計** | - | - | **1069** | **50.8g** | **54.3g** | **85.5g** |

**Pipeline栄養素**

合計: 680 kcal, P: 49.6g, F: 18.7g, C: 79.4g

**差分 (Pipeline - Label)**

- カロリー: -389.0 kcal (-36.4%)
- タンパク質: -1.2g (-2.4%)
- 脂質: -35.6g (-65.6%)
- 炭水化物: -6.1g (-7.1%)

---

### test_food28.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | pizza with cheese and olives | 300g | 840 | 33.0g | 33.0g | 99.0g |
| extra | mixed salad greens | 120g | 20 | 2.2g | 0.4g | 3.6g |
| extra | tomato | 40g | 7 | 0.4g | 0.1g | 1.6g |
| extra | cucumber | 40g | 6 | 0.3g | 0.0g | 1.4g |
| extra | vinaigrette dressing | 25g | 70 | 0.1g | 7.0g | 2.0g |
| **合計** | - | - | **944** | **36.0g** | **40.5g** | **107.6g** |

**Pipeline栄養素**

合計: 847 kcal, P: 45.3g, F: 34.0g, C: 90.7g

**差分 (Pipeline - Label)**

- カロリー: -96.6 kcal (-10.2%)
- タンパク質: +9.3g (+25.8%)
- 脂質: -6.5g (-16.0%)
- 炭水化物: -16.9g (-15.7%)

---

### test_food29.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | linguine with creamy sauce | 220g | 418 | 13.2g | 15.4g | 61.6g |
| extra | chicken breast | 150g | 248 | 46.5g | 5.4g | 0.0g |
| extra | mixed salad greens | 120g | 20 | 2.2g | 0.4g | 3.6g |
| extra | tomato | 40g | 7 | 0.4g | 0.1g | 1.6g |
| extra | cucumber | 40g | 6 | 0.3g | 0.0g | 1.4g |
| extra | vinaigrette dressing | 25g | 70 | 0.1g | 7.0g | 2.0g |
| **合計** | - | - | **769** | **62.7g** | **28.3g** | **70.2g** |

**Pipeline栄養素**

合計: 635 kcal, P: 27.7g, F: 24.7g, C: 74.2g

**差分 (Pipeline - Label)**

- カロリー: -133.9 kcal (-17.4%)
- タンパク質: -35.0g (-55.8%)
- 脂質: -3.6g (-12.7%)
- 炭水化物: +4.0g (+5.7%)

---

### test_food30.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | chicken with cream sauce | 140g | 280 | 28.0g | 16.8g | 5.6g |
| main_food | pasta shells with pesto | 150g | 330 | 10.5g | 15.0g | 42.0g |
| extra | mixed salad greens | 120g | 20 | 2.2g | 0.4g | 3.6g |
| extra | tomato | 40g | 7 | 0.4g | 0.1g | 1.6g |
| extra | cucumber | 40g | 6 | 0.3g | 0.0g | 1.4g |
| extra | vinaigrette dressing | 25g | 70 | 0.1g | 7.0g | 2.0g |
| **合計** | - | - | **714** | **41.5g** | **39.3g** | **56.2g** |

**Pipeline栄養素**

合計: 629 kcal, P: 46.2g, F: 24.0g, C: 56.3g

**差分 (Pipeline - Label)**

- カロリー: -84.3 kcal (-11.8%)
- タンパク質: +4.7g (+11.3%)
- 脂質: -15.3g (-38.9%)
- 炭水化物: +0.1g (+0.2%)

---

### test_food31.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | cod fillet | 150g | 225 | 34.5g | 9.0g | 0.0g |
| main_food | sweet potatoes | 160g | 184 | 3.2g | 4.8g | 33.6g |
| extra | mixed salad greens | 50g | 10 | 1.0g | 0.1g | 2.0g |
| extra | strawberries | 70g | 22 | 0.5g | 0.2g | 5.4g |
| extra | cucumber | 35g | 5 | 0.2g | 0.0g | 1.3g |
| extra | pecans | 15g | 108 | 1.4g | 10.8g | 2.1g |
| extra | vinaigrette dressing | 20g | 54 | 0.1g | 5.0g | 1.6g |
| **合計** | - | - | **609** | **40.9g** | **29.9g** | **46.0g** |

**Pipeline栄養素**

合計: 532 kcal, P: 57.6g, F: 17.4g, C: 32.9g

**差分 (Pipeline - Label)**

- カロリー: -76.2 kcal (-12.5%)
- タンパク質: +16.7g (+40.8%)
- 脂質: -12.5g (-41.8%)
- 炭水化物: -13.1g (-28.5%)

---

### test_food32.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | beef stroganoff | 220g | 385 | 26.4g | 26.4g | 13.2g |
| main_food | white rice | 160g | 208 | 3.8g | 0.5g | 45.1g |
| extra | mixed salad greens | 60g | 12 | 1.2g | 0.2g | 2.4g |
| extra | cucumber | 40g | 6 | 0.3g | 0.0g | 1.4g |
| extra | red bell pepper | 40g | 12 | 0.4g | 0.1g | 2.4g |
| extra | vinaigrette dressing | 20g | 54 | 0.1g | 5.0g | 1.6g |
| **合計** | - | - | **677** | **32.2g** | **32.2g** | **66.1g** |

**Pipeline栄養素**

合計: 584 kcal, P: 26.7g, F: 22.2g, C: 67.8g

**差分 (Pipeline - Label)**

- カロリー: -93.6 kcal (-13.8%)
- タンパク質: -5.5g (-17.1%)
- 脂質: -10.0g (-31.1%)
- 炭水化物: +1.7g (+2.6%)

---

### test_food33.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | chicken thigh | 130g | 280 | 23.4g | 19.5g | 0.0g |
| main_food | pearl couscous | 150g | 180 | 5.7g | 0.3g | 37.5g |
| main_food | ratatouille | 160g | 112 | 2.4g | 6.4g | 11.2g |
| **合計** | - | - | **572** | **31.5g** | **26.2g** | **48.7g** |

**Pipeline栄養素**

合計: 662 kcal, P: 62.6g, F: 19.7g, C: 54.4g

**差分 (Pipeline - Label)**

- カロリー: +90.3 kcal (+15.8%)
- タンパク質: +31.1g (+98.7%)
- 脂質: -6.5g (-24.8%)
- 炭水化物: +5.7g (+11.7%)

---

### test_food34.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | potato rosti | 180g | 306 | 4.5g | 11.7g | 48.6g |
| main_food | chicken thigh | 130g | 280 | 23.4g | 19.5g | 0.0g |
| extra | lettuce | 70g | 14 | 1.4g | 0.2g | 2.8g |
| extra | tomato | 60g | 11 | 0.5g | 0.1g | 2.3g |
| extra | carrot | 20g | 8 | 0.2g | 0.0g | 2.0g |
| extra | vinaigrette dressing | 20g | 54 | 0.1g | 5.0g | 1.6g |
| **合計** | - | - | **672** | **30.1g** | **36.5g** | **57.3g** |

**Pipeline栄養素**

合計: 598 kcal, P: 49.7g, F: 23.2g, C: 44.9g

**差分 (Pipeline - Label)**

- カロリー: -74.9 kcal (-11.1%)
- タンパク質: +19.6g (+65.1%)
- 脂質: -13.3g (-36.4%)
- 炭水化物: -12.4g (-21.6%)

---

### test_food35.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | beef steak | 140g | 336 | 36.4g | 23.8g | 0.0g |
| main_food | potato wedges | 150g | 240 | 4.5g | 7.5g | 40.5g |
| main_food | broccoli | 80g | 28 | 1.9g | 0.3g | 5.8g |
| main_food | mexican rice | 120g | 168 | 3.0g | 3.6g | 31.2g |
| extra | mixed salad greens | 60g | 12 | 1.2g | 0.2g | 2.4g |
| extra | cucumber | 35g | 5 | 0.2g | 0.0g | 1.3g |
| extra | tomato | 70g | 13 | 0.6g | 0.1g | 2.7g |
| extra | vinaigrette dressing | 20g | 54 | 0.1g | 5.0g | 1.6g |
| **合計** | - | - | **856** | **47.9g** | **40.5g** | **85.5g** |

**Pipeline栄養素**

合計: 942 kcal, P: 72.2g, F: 41.3g, C: 69.9g

**差分 (Pipeline - Label)**

- カロリー: +86.6 kcal (+10.1%)
- タンパク質: +24.3g (+50.7%)
- 脂質: +0.8g (+2.0%)
- 炭水化物: -15.6g (-18.2%)

---

### test_food36.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | chicken thigh | 150g | 322 | 27.0g | 22.5g | 0.0g |
| main_food | pearl couscous | 140g | 168 | 5.3g | 0.3g | 35.0g |
| main_food | broccoli | 100g | 35 | 2.4g | 0.4g | 7.2g |
| extra | mixed salad greens | 70g | 14 | 1.4g | 0.2g | 2.8g |
| extra | cucumber | 30g | 4 | 0.2g | 0.0g | 1.1g |
| extra | red bell pepper | 30g | 9 | 0.3g | 0.1g | 1.8g |
| extra | vinaigrette dressing | 20g | 54 | 0.1g | 5.0g | 1.6g |
| **合計** | - | - | **607** | **36.7g** | **28.5g** | **49.5g** |

**Pipeline栄養素**

合計: 654 kcal, P: 54.4g, F: 19.7g, C: 60.7g

**差分 (Pipeline - Label)**

- カロリー: +47.0 kcal (+7.7%)
- タンパク質: +17.7g (+48.2%)
- 脂質: -8.8g (-30.9%)
- 炭水化物: +11.2g (+22.6%)

---

### test_food37.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | chicken thigh | 140g | 301 | 25.2g | 21.0g | 0.0g |
| extra | pine nuts | 10g | 67 | 1.4g | 6.8g | 1.3g |
| main_food | penne with pesto | 180g | 414 | 10.8g | 19.8g | 52.2g |
| main_food | tomato | 100g | 18 | 0.9g | 0.2g | 3.9g |
| main_food | coleslaw | 120g | 180 | 1.2g | 12.0g | 16.8g |
| **合計** | - | - | **980** | **39.5g** | **59.8g** | **74.2g** |

**Pipeline栄養素**

合計: 885 kcal, P: 62.0g, F: 34.2g, C: 80.2g

**差分 (Pipeline - Label)**

- カロリー: -95.7 kcal (-9.8%)
- タンパク質: +22.5g (+57.0%)
- 脂質: -25.6g (-42.8%)
- 炭水化物: +6.0g (+8.1%)

---

### test_food38.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | beef stew | 380g | 456 | 30.4g | 22.8g | 30.4g |
| extra | sour cream | 20g | 40 | 0.6g | 4.0g | 0.9g |
| extra | mixed salad greens | 60g | 12 | 1.2g | 0.2g | 2.4g |
| extra | cucumber | 60g | 9 | 0.4g | 0.1g | 2.2g |
| extra | tomato | 80g | 14 | 0.7g | 0.2g | 3.1g |
| extra | avocado | 60g | 96 | 1.2g | 8.8g | 5.1g |
| extra | vinaigrette dressing | 20g | 54 | 0.1g | 5.0g | 1.6g |
| **合計** | - | - | **681** | **34.6g** | **41.1g** | **45.7g** |

**Pipeline栄養素**

合計: 914 kcal, P: 39.6g, F: 64.2g, C: 61.7g

**差分 (Pipeline - Label)**

- カロリー: +233.1 kcal (+34.2%)
- タンパク質: +5.0g (+14.5%)
- 脂質: +23.1g (+56.2%)
- 炭水化物: +16.0g (+35.0%)

---

### test_food39.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | spaghetti with ham and asparagus | 280g | 532 | 22.4g | 19.6g | 70.0g |
| extra | mixed salad greens | 60g | 12 | 1.2g | 0.2g | 2.4g |
| extra | cucumber | 50g | 8 | 0.3g | 0.1g | 1.8g |
| extra | tomato | 60g | 11 | 0.5g | 0.1g | 2.3g |
| extra | avocado | 50g | 80 | 1.0g | 7.3g | 4.2g |
| extra | vinaigrette dressing | 20g | 54 | 0.1g | 5.0g | 1.6g |
| **合計** | - | - | **696** | **25.5g** | **32.3g** | **82.3g** |

**Pipeline栄養素**

合計: 686 kcal, P: 23.8g, F: 10.3g, C: 121.7g

**差分 (Pipeline - Label)**

- カロリー: -10.0 kcal (-1.4%)
- タンパク質: -1.7g (-6.7%)
- 脂質: -22.0g (-68.1%)
- 炭水化物: +39.4g (+47.9%)

---

### test_food40.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | pizza with prosciutto and olives | 280g | 784 | 33.6g | 33.6g | 84.0g |
| extra | mixed salad greens | 60g | 12 | 1.2g | 0.2g | 2.4g |
| extra | cucumber | 40g | 6 | 0.3g | 0.0g | 1.4g |
| extra | avocado | 70g | 112 | 1.4g | 10.3g | 5.9g |
| extra | carrot | 15g | 6 | 0.1g | 0.0g | 1.5g |
| extra | vinaigrette dressing | 20g | 54 | 0.1g | 5.0g | 1.6g |
| **合計** | - | - | **974** | **36.7g** | **49.1g** | **96.8g** |

**Pipeline栄養素**

合計: 1332 kcal, P: 54.1g, F: 69.6g, C: 122.3g

**差分 (Pipeline - Label)**

- カロリー: +357.9 kcal (+36.7%)
- タンパク質: +17.4g (+47.4%)
- 脂質: +20.5g (+41.8%)
- 炭水化物: +25.5g (+26.3%)

---

### test_food41.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | chicken thigh | 160g | 334 | 41.6g | 17.6g | 0.0g |
| main_food | broccoli | 140g | 49 | 3.4g | 0.6g | 10.1g |
| main_food | macaroni salad | 130g | 299 | 5.2g | 15.6g | 33.8g |
| **合計** | - | - | **682** | **50.2g** | **33.8g** | **43.9g** |

**Pipeline栄養素**

合計: 780 kcal, P: 57.6g, F: 31.1g, C: 67.8g

**差分 (Pipeline - Label)**

- カロリー: +97.7 kcal (+14.3%)
- タンパク質: +7.4g (+14.7%)
- 脂質: -2.7g (-8.0%)
- 炭水化物: +23.9g (+54.4%)

---

### test_food42.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | roast turkey | 130g | 176 | 37.7g | 3.9g | 0.0g |
| extra | turkey gravy | 25g | 12 | 0.2g | 0.8g | 1.2g |
| main_food | mashed potatoes | 160g | 176 | 3.2g | 7.2g | 27.2g |
| extra | turkey gravy | 30g | 15 | 0.3g | 0.9g | 1.5g |
| main_food | green bean casserole | 120g | 144 | 3.6g | 9.6g | 12.0g |
| main_food | carrots | 80g | 48 | 0.5g | 1.6g | 8.0g |
| main_food | cornbread muffin | 65g | 214 | 3.9g | 7.8g | 33.8g |
| **合計** | - | - | **786** | **49.4g** | **31.8g** | **83.7g** |

**Pipeline栄養素**

合計: 681 kcal, P: 53.0g, F: 19.9g, C: 70.4g

**差分 (Pipeline - Label)**

- カロリー: -104.2 kcal (-13.3%)
- タンパク質: +3.6g (+7.3%)
- 脂質: -11.9g (-37.4%)
- 炭水化物: -13.3g (-15.9%)

---

### test_food43.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | chicken breast | 130g | 214 | 40.3g | 4.7g | 0.0g |
| main_food | macaroni and cheese | 160g | 264 | 11.2g | 11.2g | 32.0g |
| main_food | mixed salad greens | 60g | 12 | 1.2g | 0.2g | 2.2g |
| extra | carrot | 30g | 12 | 0.3g | 0.1g | 2.9g |
| main_food | zucchini | 90g | 63 | 1.4g | 4.5g | 4.5g |
| **合計** | - | - | **566** | **54.4g** | **20.7g** | **41.6g** |

**Pipeline栄養素**

合計: 897 kcal, P: 75.2g, F: 37.1g, C: 62.3g

**差分 (Pipeline - Label)**

- カロリー: +331.4 kcal (+58.6%)
- タンパク質: +20.8g (+38.2%)
- 脂質: +16.4g (+79.2%)
- 炭水化物: +20.7g (+49.8%)

---

### test_food44.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | baked pasta with cheese | 250g | 475 | 20.0g | 17.5g | 65.0g |
| extra | cabbage | 80g | 20 | 1.0g | 0.1g | 4.8g |
| extra | cucumber | 30g | 4 | 0.2g | 0.0g | 1.1g |
| extra | red onion | 15g | 6 | 0.2g | 0.0g | 1.4g |
| extra | corn | 15g | 13 | 0.5g | 0.2g | 2.9g |
| **合計** | - | - | **518** | **21.9g** | **17.8g** | **75.2g** |

**Pipeline栄養素**

合計: 708 kcal, P: 20.2g, F: 34.9g, C: 77.2g

**差分 (Pipeline - Label)**

- カロリー: +189.8 kcal (+36.6%)
- タンパク質: -1.7g (-7.8%)
- 脂質: +17.1g (+96.1%)
- 炭水化物: +2.0g (+2.7%)

---

### test_food45.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | prosciutto and mozzarella sandwich | 220g | 550 | 26.4g | 24.2g | 57.2g |
| main_food | potato chips | 45g | 241 | 3.1g | 15.8g | 22.9g |
| **合計** | - | - | **791** | **29.5g** | **40.0g** | **80.1g** |

**Pipeline栄養素**

合計: 1156 kcal, P: 46.9g, F: 51.7g, C: 130.7g

**差分 (Pipeline - Label)**

- カロリー: +365.2 kcal (+46.2%)
- タンパク質: +17.4g (+59.0%)
- 脂質: +11.7g (+29.3%)
- 炭水化物: +50.6g (+63.2%)

---

### test_food46.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | salisbury steak with gravy | 180g | 324 | 21.6g | 21.6g | 9.0g |
| main_food | baked potato | 220g | 205 | 5.5g | 0.2g | 46.2g |
| extra | sour cream | 30g | 58 | 0.7g | 5.7g | 1.4g |
| extra | green onion | 10g | 3 | 0.2g | 0.0g | 0.7g |
| main_food | green beans | 120g | 42 | 2.3g | 0.2g | 9.5g |
| main_food | carrots | 90g | 45 | 0.9g | 1.8g | 8.1g |
| **合計** | - | - | **677** | **31.2g** | **29.5g** | **74.9g** |

**Pipeline栄養素**

合計: 568 kcal, P: 45.9g, F: 21.5g, C: 48.7g

**差分 (Pipeline - Label)**

- カロリー: -109.0 kcal (-16.1%)
- タンパク質: +14.7g (+47.1%)
- 脂質: -8.0g (-27.1%)
- 炭水化物: -26.2g (-35.0%)

---

### test_food47.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | cheeseburger | 200g | 520 | 32.0g | 24.0g | 46.0g |
| extra | tomato | 20g | 4 | 0.2g | 0.0g | 0.8g |
| extra | onion | 10g | 4 | 0.1g | 0.0g | 0.9g |
| main_food | potato wedges | 170g | 255 | 4.2g | 10.2g | 39.1g |
| **合計** | - | - | **783** | **36.5g** | **34.2g** | **86.8g** |

**Pipeline栄養素**

合計: 912 kcal, P: 34.6g, F: 38.9g, C: 107.9g

**差分 (Pipeline - Label)**

- カロリー: +129.9 kcal (+16.6%)
- タンパク質: -1.9g (-5.2%)
- 脂質: +4.7g (+13.7%)
- 炭水化物: +21.1g (+24.3%)

---

### test_food48.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | beef stew | 200g | 240 | 16.0g | 12.0g | 16.0g |
| main_food | white rice | 180g | 234 | 4.3g | 0.5g | 50.4g |
| main_food | cucumber salad | 90g | 72 | 2.5g | 4.5g | 5.4g |
| **合計** | - | - | **546** | **22.8g** | **17.0g** | **71.8g** |

**Pipeline栄養素**

合計: 764 kcal, P: 25.4g, F: 40.2g, C: 72.9g

**差分 (Pipeline - Label)**

- カロリー: +217.6 kcal (+39.9%)
- タンパク質: +2.6g (+11.4%)
- 脂質: +23.2g (+136.5%)
- 炭水化物: +1.1g (+1.5%)

---

### test_food49.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | cheese pizza | 220g | 585 | 24.2g | 22.0g | 72.6g |
| extra | black olives | 15g | 17 | 0.1g | 1.6g | 0.9g |
| **合計** | - | - | **602** | **24.3g** | **23.6g** | **73.5g** |

**Pipeline栄養素**

合計: 1007 kcal, P: 38.0g, F: 37.7g, C: 129.9g

**差分 (Pipeline - Label)**

- カロリー: +404.7 kcal (+67.2%)
- タンパク質: +13.7g (+56.4%)
- 脂質: +14.1g (+59.7%)
- 炭水化物: +56.4g (+76.7%)

---

### test_food50.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | blt sandwich | 180g | 486 | 23.4g | 25.2g | 41.4g |
| main_food | carrot soup | 240g | 120 | 2.4g | 4.8g | 19.2g |
| main_food | mixed salad greens | 70g | 14 | 1.4g | 0.2g | 2.5g |
| extra | avocado | 60g | 96 | 1.2g | 9.0g | 5.4g |
| extra | sesame seeds | 3g | 17 | 0.5g | 1.5g | 0.7g |
| **合計** | - | - | **733** | **28.9g** | **40.7g** | **69.2g** |

**Pipeline栄養素**

合計: 946 kcal, P: 38.4g, F: 44.4g, C: 100.5g

**差分 (Pipeline - Label)**

- カロリー: +212.3 kcal (+29.0%)
- タンパク質: +9.5g (+32.9%)
- 脂質: +3.7g (+9.1%)
- 炭水化物: +31.3g (+45.2%)

---
