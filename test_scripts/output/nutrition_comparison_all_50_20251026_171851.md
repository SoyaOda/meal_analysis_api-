# Pipeline vs VLM Label 栄養素比較レポート

生成日時: 2025-10-26 17:18:51

対象画像数: 50

## サマリー

### 平均差分（Pipeline - Label）

| 栄養素 | 平均差分 (%) |
|--------|--------------|
| カロリー | +13.3% |
| タンパク質 | +29.9% |
| 脂質 | +5.9% |
| 炭水化物 | +10.7% |

## 詳細比較表

| 画像 | Label Cal | Pipeline Cal | 差分 | Label P | Pipeline P | 差分 | Label F | Pipeline F | 差分 | Label C | Pipeline C | 差分 |
|------|-----------|--------------|------|---------|------------|------|---------|------------|------|---------|------------|------|
| test_food1.jpg | 891 | 984 | +10.5% | 58.9 | 77.4 | +31.4% | 53.8 | 52.6 | -2.2% | 50.9 | 47.3 | -7.1% |
| test_food10.jpg | 854 | 1044 | +22.3% | 59.5 | 93.8 | +57.6% | 48.1 | 51.5 | +7.1% | 53.4 | 45.7 | -14.4% |
| test_food11.jpg | 499 | 728 | +45.8% | 27.4 | 36.3 | +32.5% | 27.4 | 29.6 | +8.0% | 40.2 | 79.9 | +98.8% |
| test_food12.jpg | 441 | 520 | +17.8% | 24.6 | 29.8 | +21.1% | 28.0 | 37.8 | +35.0% | 25.6 | 16.7 | -34.8% |
| test_food13.jpg | 643 | 998 | +55.2% | 31.0 | 59.2 | +91.0% | 26.3 | 51.9 | +97.3% | 80.0 | 93.8 | +17.2% |
| test_food14.jpg | 749 | 625 | -16.6% | 45.8 | 60.0 | +31.0% | 26.9 | 16.6 | -38.3% | 81.0 | 54.5 | -32.7% |
| test_food15.jpg | 488 | 432 | -11.4% | 25.9 | 22.8 | -12.0% | 24.1 | 8.4 | -65.1% | 46.0 | 67.3 | +46.3% |
| test_food16.jpg | 855 | 850 | -0.7% | 58.0 | 60.3 | +4.0% | 42.6 | 45.0 | +5.6% | 62.1 | 49.6 | -20.1% |
| test_food17.jpg | 746 | 723 | -3.0% | 25.7 | 27.0 | +5.1% | 34.7 | 37.7 | +8.6% | 85.4 | 68.2 | -20.1% |
| test_food18.jpg | 582 | 748 | +28.5% | 43.6 | 35.8 | -17.9% | 14.8 | 31.4 | +112.2% | 70.8 | 80.3 | +13.4% |
| test_food19.jpg | 599 | 542 | -9.6% | 52.1 | 52.5 | +0.8% | 16.2 | 15.8 | -2.5% | 60.5 | 53.1 | -12.2% |
| test_food2.jpg | 684 | 917 | +34.0% | 63.9 | 76.1 | +19.1% | 23.8 | 39.8 | +67.2% | 57.6 | 62.3 | +8.2% |
| test_food20.jpg | 519 | 706 | +36.0% | 32.6 | 34.2 | +4.9% | 24.8 | 36.5 | +47.2% | 45.0 | 63.3 | +40.7% |
| test_food21.jpg | 725 | 848 | +17.0% | 46.5 | 55.0 | +18.3% | 41.7 | 55.6 | +33.3% | 43.0 | 51.3 | +19.3% |
| test_food22.jpg | 646 | 568 | -11.9% | 31.4 | 26.0 | -17.2% | 28.2 | 11.7 | -58.5% | 69.8 | 87.6 | +25.5% |
| test_food23.jpg | 706 | 791 | +12.0% | 24.5 | 31.4 | +28.2% | 40.9 | 36.5 | -10.8% | 64.6 | 87.0 | +34.7% |
| test_food24.jpg | 370 | 319 | -14.0% | 47.1 | 45.8 | -2.8% | 12.7 | 13.6 | +7.1% | 15.6 | 6.1 | -60.9% |
| test_food25.jpg | 748 | 872 | +16.6% | 27.6 | 35.4 | +28.3% | 43.2 | 51.4 | +19.0% | 61.6 | 70.0 | +13.6% |
| test_food26.jpg | 786 | 990 | +25.9% | 32.2 | 36.3 | +12.7% | 36.9 | 51.7 | +40.1% | 80.4 | 93.3 | +16.0% |
| test_food27.jpg | 1069 | 904 | -15.5% | 50.8 | 68.9 | +35.6% | 54.3 | 30.7 | -43.5% | 85.5 | 89.1 | +4.2% |
| test_food28.jpg | 944 | 886 | -6.1% | 36.0 | 33.5 | -6.9% | 40.5 | 37.2 | -8.1% | 107.6 | 104.3 | -3.1% |
| test_food29.jpg | 769 | 603 | -21.6% | 62.7 | 33.5 | -46.6% | 28.3 | 12.6 | -55.5% | 70.2 | 87.0 | +23.9% |
| test_food3.jpg | 1000 | 1053 | +5.2% | 56.7 | 53.4 | -5.8% | 60.4 | 68.6 | +13.6% | 68.7 | 54.8 | -20.2% |
| test_food30.jpg | 714 | 593 | -16.9% | 41.5 | 54.3 | +30.8% | 39.3 | 18.2 | -53.7% | 56.2 | 49.0 | -12.8% |
| test_food31.jpg | 609 | 535 | -12.0% | 40.9 | 57.7 | +41.1% | 29.9 | 17.5 | -41.5% | 46.0 | 33.9 | -26.3% |
| test_food32.jpg | 677 | 817 | +20.6% | 32.2 | 50.8 | +57.8% | 32.2 | 51.6 | +60.2% | 66.1 | 35.9 | -45.7% |
| test_food33.jpg | 572 | 665 | +16.3% | 31.5 | 74.6 | +136.8% | 26.2 | 23.0 | -12.2% | 48.7 | 34.7 | -28.7% |
| test_food34.jpg | 672 | 650 | -3.4% | 30.1 | 49.6 | +64.8% | 36.5 | 27.5 | -24.7% | 57.3 | 49.5 | -13.6% |
| test_food35.jpg | 856 | 1209 | +41.3% | 47.9 | 63.2 | +31.9% | 40.5 | 64.3 | +58.8% | 85.5 | 98.7 | +15.4% |
| test_food36.jpg | 607 | 707 | +16.5% | 36.7 | 69.3 | +88.8% | 28.5 | 25.6 | -10.2% | 49.5 | 45.3 | -8.5% |
| test_food37.jpg | 980 | 665 | -32.2% | 39.5 | 60.4 | +52.9% | 59.8 | 18.2 | -69.6% | 74.2 | 60.7 | -18.2% |
| test_food38.jpg | 681 | 506 | -25.8% | 34.6 | 14.9 | -56.9% | 41.1 | 22.9 | -44.3% | 45.7 | 78.4 | +71.6% |
| test_food39.jpg | 696 | 742 | +6.6% | 25.5 | 24.2 | -5.1% | 32.3 | 15.2 | -52.9% | 82.3 | 125.8 | +52.9% |
| test_food4.jpg | 702 | 851 | +21.3% | 53.0 | 74.6 | +40.8% | 36.3 | 33.2 | -8.5% | 46.4 | 60.6 | +30.6% |
| test_food40.jpg | 974 | 1051 | +7.9% | 36.7 | 119.1 | +224.5% | 49.1 | 56.0 | +14.1% | 96.8 | 11.2 | -88.4% |
| test_food41.jpg | 682 | 780 | +14.3% | 50.2 | 57.6 | +14.7% | 33.8 | 31.1 | -8.0% | 43.9 | 67.8 | +54.4% |
| test_food42.jpg | 786 | 642 | -18.2% | 49.4 | 45.3 | -8.3% | 31.8 | 20.0 | -37.1% | 83.7 | 67.3 | -19.6% |
| test_food43.jpg | 566 | 872 | +54.1% | 54.4 | 74.7 | +37.3% | 20.7 | 36.5 | +76.3% | 41.6 | 60.7 | +45.9% |
| test_food44.jpg | 518 | 1131 | +118.2% | 21.9 | 40.8 | +86.3% | 17.8 | 13.0 | -27.0% | 75.2 | 207.9 | +176.5% |
| test_food45.jpg | 791 | 731 | -7.6% | 29.5 | 41.8 | +41.7% | 40.0 | 24.5 | -38.8% | 80.1 | 87.6 | +9.4% |
| test_food46.jpg | 677 | 647 | -4.4% | 31.2 | 54.3 | +74.0% | 29.5 | 27.1 | -8.1% | 74.9 | 46.4 | -38.1% |
| test_food47.jpg | 783 | 867 | +10.8% | 36.5 | 45.0 | +23.3% | 34.2 | 43.3 | +26.6% | 86.8 | 73.6 | -15.2% |
| test_food48.jpg | 546 | 863 | +58.1% | 22.8 | 30.5 | +33.8% | 17.0 | 28.7 | +68.8% | 71.8 | 119.6 | +66.6% |
| test_food49.jpg | 602 | 944 | +56.8% | 24.3 | 37.7 | +55.1% | 23.6 | 36.1 | +53.0% | 73.5 | 117.9 | +60.4% |
| test_food5.jpg | 530 | 629 | +18.7% | 50.8 | 63.9 | +25.8% | 18.1 | 23.4 | +29.3% | 41.6 | 38.2 | -8.2% |
| test_food50.jpg | 733 | 928 | +26.5% | 28.9 | 36.7 | +27.0% | 40.7 | 39.8 | -2.2% | 69.2 | 108.8 | +57.2% |
| test_food6.jpg | 504 | 731 | +45.0% | 25.2 | 26.8 | +6.3% | 17.6 | 35.7 | +102.8% | 65.6 | 77.5 | +18.1% |
| test_food7.jpg | 722 | 763 | +5.6% | 50.9 | 67.0 | +31.6% | 44.4 | 36.1 | -18.7% | 34.1 | 39.3 | +15.2% |
| test_food8.jpg | 634 | 726 | +14.5% | 40.8 | 36.4 | -10.8% | 17.2 | 28.3 | +64.5% | 84.5 | 81.6 | -3.4% |
| test_food9.jpg | 771 | 888 | +15.1% | 46.2 | 62.1 | +34.4% | 49.2 | 40.7 | -17.3% | 45.5 | 69.2 | +52.1% |

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

合計: 984 kcal, P: 77.4g, F: 52.6g, C: 47.3g

**差分 (Pipeline - Label)**

- カロリー: +93.3 kcal (+10.5%)
- タンパク質: +18.5g (+31.4%)
- 脂質: -1.2g (-2.2%)
- 炭水化物: -3.6g (-7.1%)

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

合計: 1044 kcal, P: 93.8g, F: 51.5g, C: 45.7g

**差分 (Pipeline - Label)**

- カロリー: +190.2 kcal (+22.3%)
- タンパク質: +34.3g (+57.6%)
- 脂質: +3.4g (+7.1%)
- 炭水化物: -7.7g (-14.4%)

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

合計: 728 kcal, P: 36.3g, F: 29.6g, C: 79.9g

**差分 (Pipeline - Label)**

- カロリー: +228.7 kcal (+45.8%)
- タンパク質: +8.9g (+32.5%)
- 脂質: +2.2g (+8.0%)
- 炭水化物: +39.7g (+98.8%)

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

合計: 520 kcal, P: 29.8g, F: 37.8g, C: 16.7g

**差分 (Pipeline - Label)**

- カロリー: +78.7 kcal (+17.8%)
- タンパク質: +5.2g (+21.1%)
- 脂質: +9.8g (+35.0%)
- 炭水化物: -8.9g (-34.8%)

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

合計: 998 kcal, P: 59.2g, F: 51.9g, C: 93.8g

**差分 (Pipeline - Label)**

- カロリー: +355.2 kcal (+55.2%)
- タンパク質: +28.2g (+91.0%)
- 脂質: +25.6g (+97.3%)
- 炭水化物: +13.8g (+17.2%)

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

合計: 625 kcal, P: 60.0g, F: 16.6g, C: 54.5g

**差分 (Pipeline - Label)**

- カロリー: -124.5 kcal (-16.6%)
- タンパク質: +14.2g (+31.0%)
- 脂質: -10.3g (-38.3%)
- 炭水化物: -26.5g (-32.7%)

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

合計: 432 kcal, P: 22.8g, F: 8.4g, C: 67.3g

**差分 (Pipeline - Label)**

- カロリー: -55.8 kcal (-11.4%)
- タンパク質: -3.1g (-12.0%)
- 脂質: -15.7g (-65.1%)
- 炭水化物: +21.3g (+46.3%)

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

合計: 850 kcal, P: 60.3g, F: 45.0g, C: 49.6g

**差分 (Pipeline - Label)**

- カロリー: -5.7 kcal (-0.7%)
- タンパク質: +2.3g (+4.0%)
- 脂質: +2.4g (+5.6%)
- 炭水化物: -12.5g (-20.1%)

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

合計: 723 kcal, P: 27.0g, F: 37.7g, C: 68.2g

**差分 (Pipeline - Label)**

- カロリー: -22.6 kcal (-3.0%)
- タンパク質: +1.3g (+5.1%)
- 脂質: +3.0g (+8.6%)
- 炭水化物: -17.2g (-20.1%)

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

合計: 748 kcal, P: 35.8g, F: 31.4g, C: 80.3g

**差分 (Pipeline - Label)**

- カロリー: +165.9 kcal (+28.5%)
- タンパク質: -7.8g (-17.9%)
- 脂質: +16.6g (+112.2%)
- 炭水化物: +9.5g (+13.4%)

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

合計: 542 kcal, P: 52.5g, F: 15.8g, C: 53.1g

**差分 (Pipeline - Label)**

- カロリー: -57.3 kcal (-9.6%)
- タンパク質: +0.4g (+0.8%)
- 脂質: -0.4g (-2.5%)
- 炭水化物: -7.4g (-12.2%)

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

合計: 917 kcal, P: 76.1g, F: 39.8g, C: 62.3g

**差分 (Pipeline - Label)**

- カロリー: +232.5 kcal (+34.0%)
- タンパク質: +12.2g (+19.1%)
- 脂質: +16.0g (+67.2%)
- 炭水化物: +4.7g (+8.2%)

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

合計: 706 kcal, P: 34.2g, F: 36.5g, C: 63.3g

**差分 (Pipeline - Label)**

- カロリー: +187.1 kcal (+36.0%)
- タンパク質: +1.6g (+4.9%)
- 脂質: +11.7g (+47.2%)
- 炭水化物: +18.3g (+40.7%)

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

合計: 848 kcal, P: 55.0g, F: 55.6g, C: 51.3g

**差分 (Pipeline - Label)**

- カロリー: +123.1 kcal (+17.0%)
- タンパク質: +8.5g (+18.3%)
- 脂質: +13.9g (+33.3%)
- 炭水化物: +8.3g (+19.3%)

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

合計: 568 kcal, P: 26.0g, F: 11.7g, C: 87.6g

**差分 (Pipeline - Label)**

- カロリー: -77.0 kcal (-11.9%)
- タンパク質: -5.4g (-17.2%)
- 脂質: -16.5g (-58.5%)
- 炭水化物: +17.8g (+25.5%)

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

合計: 791 kcal, P: 31.4g, F: 36.5g, C: 87.0g

**差分 (Pipeline - Label)**

- カロリー: +84.6 kcal (+12.0%)
- タンパク質: +6.9g (+28.2%)
- 脂質: -4.4g (-10.8%)
- 炭水化物: +22.4g (+34.7%)

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

合計: 319 kcal, P: 45.8g, F: 13.6g, C: 6.1g

**差分 (Pipeline - Label)**

- カロリー: -51.9 kcal (-14.0%)
- タンパク質: -1.3g (-2.8%)
- 脂質: +0.9g (+7.1%)
- 炭水化物: -9.5g (-60.9%)

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

合計: 872 kcal, P: 35.4g, F: 51.4g, C: 70.0g

**差分 (Pipeline - Label)**

- カロリー: +124.4 kcal (+16.6%)
- タンパク質: +7.8g (+28.3%)
- 脂質: +8.2g (+19.0%)
- 炭水化物: +8.4g (+13.6%)

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

合計: 990 kcal, P: 36.3g, F: 51.7g, C: 93.3g

**差分 (Pipeline - Label)**

- カロリー: +203.5 kcal (+25.9%)
- タンパク質: +4.1g (+12.7%)
- 脂質: +14.8g (+40.1%)
- 炭水化物: +12.9g (+16.0%)

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

合計: 904 kcal, P: 68.9g, F: 30.7g, C: 89.1g

**差分 (Pipeline - Label)**

- カロリー: -165.5 kcal (-15.5%)
- タンパク質: +18.1g (+35.6%)
- 脂質: -23.6g (-43.5%)
- 炭水化物: +3.6g (+4.2%)

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

合計: 886 kcal, P: 33.5g, F: 37.2g, C: 104.3g

**差分 (Pipeline - Label)**

- カロリー: -57.3 kcal (-6.1%)
- タンパク質: -2.5g (-6.9%)
- 脂質: -3.3g (-8.1%)
- 炭水化物: -3.3g (-3.1%)

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

合計: 603 kcal, P: 33.5g, F: 12.6g, C: 87.0g

**差分 (Pipeline - Label)**

- カロリー: -166.2 kcal (-21.6%)
- タンパク質: -29.2g (-46.6%)
- 脂質: -15.7g (-55.5%)
- 炭水化物: +16.8g (+23.9%)

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

合計: 1053 kcal, P: 53.4g, F: 68.6g, C: 54.8g

**差分 (Pipeline - Label)**

- カロリー: +52.5 kcal (+5.2%)
- タンパク質: -3.3g (-5.8%)
- 脂質: +8.2g (+13.6%)
- 炭水化物: -13.9g (-20.2%)

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

合計: 593 kcal, P: 54.3g, F: 18.2g, C: 49.0g

**差分 (Pipeline - Label)**

- カロリー: -120.5 kcal (-16.9%)
- タンパク質: +12.8g (+30.8%)
- 脂質: -21.1g (-53.7%)
- 炭水化物: -7.2g (-12.8%)

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

合計: 535 kcal, P: 57.7g, F: 17.5g, C: 33.9g

**差分 (Pipeline - Label)**

- カロリー: -73.3 kcal (-12.0%)
- タンパク質: +16.8g (+41.1%)
- 脂質: -12.4g (-41.5%)
- 炭水化物: -12.1g (-26.3%)

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

合計: 817 kcal, P: 50.8g, F: 51.6g, C: 35.9g

**差分 (Pipeline - Label)**

- カロリー: +139.3 kcal (+20.6%)
- タンパク質: +18.6g (+57.8%)
- 脂質: +19.4g (+60.2%)
- 炭水化物: -30.2g (-45.7%)

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

合計: 665 kcal, P: 74.6g, F: 23.0g, C: 34.7g

**差分 (Pipeline - Label)**

- カロリー: +93.4 kcal (+16.3%)
- タンパク質: +43.1g (+136.8%)
- 脂質: -3.2g (-12.2%)
- 炭水化物: -14.0g (-28.7%)

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

合計: 650 kcal, P: 49.6g, F: 27.5g, C: 49.5g

**差分 (Pipeline - Label)**

- カロリー: -22.9 kcal (-3.4%)
- タンパク質: +19.5g (+64.8%)
- 脂質: -9.0g (-24.7%)
- 炭水化物: -7.8g (-13.6%)

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

合計: 1209 kcal, P: 63.2g, F: 64.3g, C: 98.7g

**差分 (Pipeline - Label)**

- カロリー: +353.2 kcal (+41.3%)
- タンパク質: +15.3g (+31.9%)
- 脂質: +23.8g (+58.8%)
- 炭水化物: +13.2g (+15.4%)

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

合計: 707 kcal, P: 69.3g, F: 25.6g, C: 45.3g

**差分 (Pipeline - Label)**

- カロリー: +100.1 kcal (+16.5%)
- タンパク質: +32.6g (+88.8%)
- 脂質: -2.9g (-10.2%)
- 炭水化物: -4.2g (-8.5%)

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

合計: 665 kcal, P: 60.4g, F: 18.2g, C: 60.7g

**差分 (Pipeline - Label)**

- カロリー: -315.7 kcal (-32.2%)
- タンパク質: +20.9g (+52.9%)
- 脂質: -41.6g (-69.6%)
- 炭水化物: -13.5g (-18.2%)

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

合計: 506 kcal, P: 14.9g, F: 22.9g, C: 78.4g

**差分 (Pipeline - Label)**

- カロリー: -175.9 kcal (-25.8%)
- タンパク質: -19.7g (-56.9%)
- 脂質: -18.2g (-44.3%)
- 炭水化物: +32.7g (+71.6%)

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

合計: 742 kcal, P: 24.2g, F: 15.2g, C: 125.8g

**差分 (Pipeline - Label)**

- カロリー: +45.8 kcal (+6.6%)
- タンパク質: -1.3g (-5.1%)
- 脂質: -17.1g (-52.9%)
- 炭水化物: +43.5g (+52.9%)

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

合計: 851 kcal, P: 74.6g, F: 33.2g, C: 60.6g

**差分 (Pipeline - Label)**

- カロリー: +149.7 kcal (+21.3%)
- タンパク質: +21.6g (+40.8%)
- 脂質: -3.1g (-8.5%)
- 炭水化物: +14.2g (+30.6%)

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

合計: 1051 kcal, P: 119.1g, F: 56.0g, C: 11.2g

**差分 (Pipeline - Label)**

- カロリー: +77.1 kcal (+7.9%)
- タンパク質: +82.4g (+224.5%)
- 脂質: +6.9g (+14.1%)
- 炭水化物: -85.6g (-88.4%)

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

合計: 642 kcal, P: 45.3g, F: 20.0g, C: 67.3g

**差分 (Pipeline - Label)**

- カロリー: -143.3 kcal (-18.2%)
- タンパク質: -4.1g (-8.3%)
- 脂質: -11.8g (-37.1%)
- 炭水化物: -16.4g (-19.6%)

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

合計: 872 kcal, P: 74.7g, F: 36.5g, C: 60.7g

**差分 (Pipeline - Label)**

- カロリー: +306.2 kcal (+54.1%)
- タンパク質: +20.3g (+37.3%)
- 脂質: +15.8g (+76.3%)
- 炭水化物: +19.1g (+45.9%)

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

合計: 1131 kcal, P: 40.8g, F: 13.0g, C: 207.9g

**差分 (Pipeline - Label)**

- カロリー: +612.8 kcal (+118.2%)
- タンパク質: +18.9g (+86.3%)
- 脂質: -4.8g (-27.0%)
- 炭水化物: +132.7g (+176.5%)

---

### test_food45.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | prosciutto and mozzarella sandwich | 220g | 550 | 26.4g | 24.2g | 57.2g |
| main_food | potato chips | 45g | 241 | 3.1g | 15.8g | 22.9g |
| **合計** | - | - | **791** | **29.5g** | **40.0g** | **80.1g** |

**Pipeline栄養素**

合計: 731 kcal, P: 41.8g, F: 24.5g, C: 87.6g

**差分 (Pipeline - Label)**

- カロリー: -60.4 kcal (-7.6%)
- タンパク質: +12.3g (+41.7%)
- 脂質: -15.5g (-38.8%)
- 炭水化物: +7.5g (+9.4%)

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

合計: 647 kcal, P: 54.3g, F: 27.1g, C: 46.4g

**差分 (Pipeline - Label)**

- カロリー: -29.6 kcal (-4.4%)
- タンパク質: +23.1g (+74.0%)
- 脂質: -2.4g (-8.1%)
- 炭水化物: -28.5g (-38.1%)

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

合計: 867 kcal, P: 45.0g, F: 43.3g, C: 73.6g

**差分 (Pipeline - Label)**

- カロリー: +84.4 kcal (+10.8%)
- タンパク質: +8.5g (+23.3%)
- 脂質: +9.1g (+26.6%)
- 炭水化物: -13.2g (-15.2%)

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

合計: 863 kcal, P: 30.5g, F: 28.7g, C: 119.6g

**差分 (Pipeline - Label)**

- カロリー: +317.4 kcal (+58.1%)
- タンパク質: +7.7g (+33.8%)
- 脂質: +11.7g (+68.8%)
- 炭水化物: +47.8g (+66.6%)

---

### test_food49.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | cheese pizza | 220g | 585 | 24.2g | 22.0g | 72.6g |
| extra | black olives | 15g | 17 | 0.1g | 1.6g | 0.9g |
| **合計** | - | - | **602** | **24.3g** | **23.6g** | **73.5g** |

**Pipeline栄養素**

合計: 944 kcal, P: 37.7g, F: 36.1g, C: 117.9g

**差分 (Pipeline - Label)**

- カロリー: +342.1 kcal (+56.8%)
- タンパク質: +13.4g (+55.1%)
- 脂質: +12.5g (+53.0%)
- 炭水化物: +44.4g (+60.4%)

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

合計: 629 kcal, P: 63.9g, F: 23.4g, C: 38.2g

**差分 (Pipeline - Label)**

- カロリー: +99.1 kcal (+18.7%)
- タンパク質: +13.1g (+25.8%)
- 脂質: +5.3g (+29.3%)
- 炭水化物: -3.4g (-8.2%)

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

合計: 928 kcal, P: 36.7g, F: 39.8g, C: 108.8g

**差分 (Pipeline - Label)**

- カロリー: +194.5 kcal (+26.5%)
- タンパク質: +7.8g (+27.0%)
- 脂質: -0.9g (-2.2%)
- 炭水化物: +39.6g (+57.2%)

---

### test_food6.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | cream of chicken soup with vegetables | 400g | 280 | 18.0g | 14.0g | 24.0g |
| main_food | dinner roll | 80g | 224 | 7.2g | 3.6g | 41.6g |
| **合計** | - | - | **504** | **25.2g** | **17.6g** | **65.6g** |

**Pipeline栄養素**

合計: 731 kcal, P: 26.8g, F: 35.7g, C: 77.5g

**差分 (Pipeline - Label)**

- カロリー: +226.8 kcal (+45.0%)
- タンパク質: +1.6g (+6.3%)
- 脂質: +18.1g (+102.8%)
- 炭水化物: +11.9g (+18.1%)

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

合計: 763 kcal, P: 67.0g, F: 36.1g, C: 39.3g

**差分 (Pipeline - Label)**

- カロリー: +40.6 kcal (+5.6%)
- タンパク質: +16.1g (+31.6%)
- 脂質: -8.3g (-18.7%)
- 炭水化物: +5.2g (+15.2%)

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

合計: 726 kcal, P: 36.4g, F: 28.3g, C: 81.6g

**差分 (Pipeline - Label)**

- カロリー: +91.9 kcal (+14.5%)
- タンパク質: -4.4g (-10.8%)
- 脂質: +11.1g (+64.5%)
- 炭水化物: -2.9g (-3.4%)

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

合計: 888 kcal, P: 62.1g, F: 40.7g, C: 69.2g

**差分 (Pipeline - Label)**

- カロリー: +116.6 kcal (+15.1%)
- タンパク質: +15.9g (+34.4%)
- 脂質: -8.5g (-17.3%)
- 炭水化物: +23.7g (+52.1%)

---
