# Pipeline vs VLM Label 栄養素比較レポート

生成日時: 2025-10-26 17:01:30

対象画像数: 50

## サマリー

### 平均差分（Pipeline - Label）

| 栄養素 | 平均差分 (%) |
|--------|--------------|
| カロリー | +10.5% |
| タンパク質 | +19.8% |
| 脂質 | +4.9% |
| 炭水化物 | +8.7% |

## 詳細比較表

| 画像 | Label Cal | Pipeline Cal | 差分 | Label P | Pipeline P | 差分 | Label F | Pipeline F | 差分 | Label C | Pipeline C | 差分 |
|------|-----------|--------------|------|---------|------------|------|---------|------------|------|---------|------------|------|
| test_food1.jpg | 891 | 1099 | +23.3% | 58.9 | 80.4 | +36.5% | 53.8 | 60.4 | +12.3% | 50.9 | 55.2 | +8.4% |
| test_food10.jpg | 854 | 1122 | +31.3% | 59.5 | 97.2 | +63.4% | 48.1 | 54.7 | +13.7% | 53.4 | 54.3 | +1.7% |
| test_food11.jpg | 499 | 670 | +34.2% | 27.4 | 28.8 | +5.1% | 27.4 | 32.5 | +18.6% | 40.2 | 67.8 | +68.7% |
| test_food12.jpg | 441 | 512 | +15.9% | 24.6 | 28.3 | +15.0% | 28.0 | 36.4 | +30.0% | 25.6 | 17.4 | -32.0% |
| test_food13.jpg | 643 | 571 | -11.3% | 31.0 | 19.0 | -38.7% | 26.3 | 28.1 | +6.8% | 80.0 | 89.7 | +12.1% |
| test_food14.jpg | 749 | 648 | -13.6% | 45.8 | 60.5 | +32.1% | 26.9 | 17.2 | -36.1% | 81.0 | 58.5 | -27.8% |
| test_food15.jpg | 488 | 465 | -4.6% | 25.9 | 26.4 | +1.9% | 24.1 | 21.3 | -11.6% | 46.0 | 46.1 | +0.2% |
| test_food16.jpg | 855 | 1006 | +17.6% | 58.0 | 64.9 | +11.9% | 42.6 | 51.8 | +21.6% | 62.1 | 65.4 | +5.3% |
| test_food17.jpg | 746 | 854 | +14.5% | 25.7 | 20.5 | -20.2% | 34.7 | 39.7 | +14.4% | 85.4 | 104.0 | +21.8% |
| test_food18.jpg | 582 | 617 | +6.1% | 43.6 | 63.2 | +45.0% | 14.8 | 13.7 | -7.4% | 70.8 | 56.1 | -20.8% |
| test_food19.jpg | 599 | 585 | -2.3% | 52.1 | 59.8 | +14.8% | 16.2 | 13.9 | -14.2% | 60.5 | 64.1 | +6.0% |
| test_food2.jpg | 684 | 1046 | +52.9% | 63.9 | 77.2 | +20.8% | 23.8 | 40.0 | +68.1% | 57.6 | 65.7 | +14.1% |
| test_food20.jpg | 519 | 702 | +35.2% | 32.6 | 34.3 | +5.2% | 24.8 | 38.8 | +56.5% | 45.0 | 65.7 | +46.0% |
| test_food21.jpg | 725 | 1014 | +39.8% | 46.5 | 63.1 | +35.7% | 41.7 | 62.7 | +50.4% | 43.0 | 60.9 | +41.6% |
| test_food22.jpg | 646 | 639 | -1.0% | 31.4 | 22.1 | -29.6% | 28.2 | 10.0 | -64.5% | 69.8 | 112.5 | +61.2% |
| test_food23.jpg | 706 | 675 | -4.4% | 24.5 | 28.8 | +17.6% | 40.9 | 30.1 | -26.4% | 64.6 | 72.5 | +12.2% |
| test_food24.jpg | 370 | 282 | -23.8% | 47.1 | 35.5 | -24.6% | 12.7 | 11.7 | -7.9% | 15.6 | 9.5 | -39.1% |
| test_food25.jpg | 748 | 940 | +25.6% | 27.6 | 41.1 | +48.9% | 43.2 | 68.2 | +57.9% | 61.6 | 42.9 | -30.4% |
| test_food26.jpg | 786 | 795 | +1.1% | 32.2 | 28.9 | -10.2% | 36.9 | 41.9 | +13.6% | 80.4 | 74.6 | -7.2% |
| test_food27.jpg | 1069 | 680 | -36.4% | 50.8 | 49.6 | -2.4% | 54.3 | 18.7 | -65.6% | 85.5 | 79.4 | -7.1% |
| test_food28.jpg | 944 | 746 | -20.9% | 36.0 | 35.0 | -2.8% | 40.5 | 43.8 | +8.1% | 107.6 | 54.5 | -49.3% |
| test_food29.jpg | 769 | 744 | -3.3% | 62.7 | 21.1 | -66.3% | 28.3 | 25.7 | -9.2% | 70.2 | 103.8 | +47.9% |
| test_food3.jpg | 1000 | 1040 | +3.9% | 56.7 | 52.5 | -7.4% | 60.4 | 68.4 | +13.2% | 68.7 | 53.3 | -22.4% |
| test_food30.jpg | 714 | 645 | -9.6% | 41.5 | 46.8 | +12.8% | 39.3 | 24.0 | -38.9% | 56.2 | 59.4 | +5.7% |
| test_food31.jpg | 609 | 532 | -12.5% | 40.9 | 57.6 | +40.8% | 29.9 | 17.4 | -41.8% | 46.0 | 32.9 | -28.5% |
| test_food32.jpg | 677 | 605 | -10.7% | 32.2 | 23.9 | -25.8% | 32.2 | 28.9 | -10.2% | 66.1 | 61.2 | -7.4% |
| test_food33.jpg | 572 | 662 | +15.8% | 31.5 | 62.6 | +98.7% | 26.2 | 19.7 | -24.8% | 48.7 | 54.4 | +11.7% |
| test_food34.jpg | 672 | 629 | -6.5% | 30.1 | 50.5 | +67.8% | 36.5 | 24.1 | -34.0% | 57.3 | 50.0 | -12.7% |
| test_food35.jpg | 856 | 903 | +5.5% | 47.9 | 67.2 | +40.3% | 40.5 | 40.1 | -1.0% | 85.5 | 64.6 | -24.4% |
| test_food36.jpg | 607 | 640 | +5.3% | 36.7 | 53.8 | +46.6% | 28.5 | 19.0 | -33.3% | 49.5 | 59.1 | +19.4% |
| test_food37.jpg | 980 | 996 | +1.6% | 39.5 | 68.9 | +74.4% | 59.8 | 39.9 | -33.3% | 74.2 | 88.0 | +18.6% |
| test_food38.jpg | 681 | 753 | +10.5% | 34.6 | 32.9 | -4.9% | 41.1 | 53.6 | +30.4% | 45.7 | 52.0 | +13.8% |
| test_food39.jpg | 696 | 661 | -5.1% | 25.5 | 22.2 | -12.9% | 32.3 | 12.2 | -62.2% | 82.3 | 112.8 | +37.1% |
| test_food4.jpg | 702 | 903 | +28.8% | 53.0 | 87.5 | +65.1% | 36.3 | 35.0 | -3.6% | 46.4 | 55.3 | +19.2% |
| test_food40.jpg | 974 | 1328 | +36.3% | 36.7 | 53.8 | +46.6% | 49.1 | 69.6 | +41.8% | 96.8 | 121.6 | +25.6% |
| test_food41.jpg | 682 | 780 | +14.3% | 50.2 | 57.6 | +14.7% | 33.8 | 31.1 | -8.0% | 43.9 | 67.8 | +54.4% |
| test_food42.jpg | 786 | 751 | -4.4% | 49.4 | 67.4 | +36.4% | 31.8 | 20.9 | -34.3% | 83.7 | 70.4 | -15.9% |
| test_food43.jpg | 566 | 901 | +59.2% | 54.4 | 74.9 | +37.7% | 20.7 | 40.1 | +93.7% | 41.6 | 60.5 | +45.4% |
| test_food44.jpg | 518 | 742 | +43.2% | 21.9 | 25.1 | +14.6% | 17.8 | 37.3 | +109.6% | 75.2 | 75.4 | +0.3% |
| test_food45.jpg | 791 | 1156 | +46.2% | 29.5 | 46.9 | +59.0% | 40.0 | 51.7 | +29.3% | 80.1 | 130.7 | +63.2% |
| test_food46.jpg | 677 | 679 | +0.4% | 31.2 | 55.4 | +77.6% | 29.5 | 26.1 | -11.5% | 74.9 | 57.1 | -23.8% |
| test_food47.jpg | 783 | 774 | -1.1% | 36.5 | 30.7 | -15.9% | 34.2 | 33.5 | -2.0% | 86.8 | 89.3 | +2.9% |
| test_food48.jpg | 546 | 715 | +30.9% | 22.8 | 23.3 | +2.2% | 17.0 | 38.1 | +124.1% | 71.8 | 68.2 | -5.0% |
| test_food49.jpg | 602 | 705 | +17.0% | 24.3 | 27.9 | +14.8% | 23.6 | 27.9 | +18.2% | 73.5 | 86.1 | +17.1% |
| test_food5.jpg | 530 | 610 | +15.2% | 50.8 | 64.4 | +26.8% | 18.1 | 16.8 | -7.2% | 41.6 | 48.1 | +15.6% |
| test_food50.jpg | 733 | 770 | +5.0% | 28.9 | 32.1 | +11.1% | 40.7 | 33.2 | -18.4% | 69.2 | 87.6 | +26.6% |
| test_food6.jpg | 504 | 736 | +46.0% | 25.2 | 22.4 | -11.1% | 17.6 | 32.2 | +83.0% | 65.6 | 89.8 | +36.9% |
| test_food7.jpg | 722 | 736 | +2.0% | 50.9 | 67.1 | +31.8% | 44.4 | 32.9 | -25.9% | 34.1 | 39.5 | +15.8% |
| test_food8.jpg | 634 | 620 | -2.2% | 40.8 | 63.8 | +56.4% | 17.2 | 13.6 | -20.9% | 84.5 | 56.6 | -33.0% |
| test_food9.jpg | 771 | 866 | +12.3% | 46.2 | 61.1 | +32.3% | 49.2 | 40.5 | -17.7% | 45.5 | 66.7 | +46.6% |

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

合計: 1099 kcal, P: 80.4g, F: 60.4g, C: 55.2g

**差分 (Pipeline - Label)**

- カロリー: +207.9 kcal (+23.3%)
- タンパク質: +21.5g (+36.5%)
- 脂質: +6.6g (+12.3%)
- 炭水化物: +4.3g (+8.4%)

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

合計: 1122 kcal, P: 97.2g, F: 54.7g, C: 54.3g

**差分 (Pipeline - Label)**

- カロリー: +267.6 kcal (+31.3%)
- タンパク質: +37.7g (+63.4%)
- 脂質: +6.6g (+13.7%)
- 炭水化物: +0.9g (+1.7%)

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

合計: 670 kcal, P: 28.8g, F: 32.5g, C: 67.8g

**差分 (Pipeline - Label)**

- カロリー: +170.6 kcal (+34.2%)
- タンパク質: +1.4g (+5.1%)
- 脂質: +5.1g (+18.6%)
- 炭水化物: +27.6g (+68.7%)

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

合計: 512 kcal, P: 28.3g, F: 36.4g, C: 17.4g

**差分 (Pipeline - Label)**

- カロリー: +70.2 kcal (+15.9%)
- タンパク質: +3.7g (+15.0%)
- 脂質: +8.4g (+30.0%)
- 炭水化物: -8.2g (-32.0%)

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

合計: 571 kcal, P: 19.0g, F: 28.1g, C: 89.7g

**差分 (Pipeline - Label)**

- カロリー: -72.5 kcal (-11.3%)
- タンパク質: -12.0g (-38.7%)
- 脂質: +1.8g (+6.8%)
- 炭水化物: +9.7g (+12.1%)

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

合計: 648 kcal, P: 60.5g, F: 17.2g, C: 58.5g

**差分 (Pipeline - Label)**

- カロリー: -101.8 kcal (-13.6%)
- タンパク質: +14.7g (+32.1%)
- 脂質: -9.7g (-36.1%)
- 炭水化物: -22.5g (-27.8%)

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

合計: 465 kcal, P: 26.4g, F: 21.3g, C: 46.1g

**差分 (Pipeline - Label)**

- カロリー: -22.5 kcal (-4.6%)
- タンパク質: +0.5g (+1.9%)
- 脂質: -2.8g (-11.6%)
- 炭水化物: +0.1g (+0.2%)

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

合計: 1006 kcal, P: 64.9g, F: 51.8g, C: 65.4g

**差分 (Pipeline - Label)**

- カロリー: +150.7 kcal (+17.6%)
- タンパク質: +6.9g (+11.9%)
- 脂質: +9.2g (+21.6%)
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

合計: 854 kcal, P: 20.5g, F: 39.7g, C: 104.0g

**差分 (Pipeline - Label)**

- カロリー: +108.4 kcal (+14.5%)
- タンパク質: -5.2g (-20.2%)
- 脂質: +5.0g (+14.4%)
- 炭水化物: +18.6g (+21.8%)

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

合計: 617 kcal, P: 63.2g, F: 13.7g, C: 56.1g

**差分 (Pipeline - Label)**

- カロリー: +35.4 kcal (+6.1%)
- タンパク質: +19.6g (+45.0%)
- 脂質: -1.1g (-7.4%)
- 炭水化物: -14.7g (-20.8%)

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

合計: 585 kcal, P: 59.8g, F: 13.9g, C: 64.1g

**差分 (Pipeline - Label)**

- カロリー: -14.0 kcal (-2.3%)
- タンパク質: +7.7g (+14.8%)
- 脂質: -2.3g (-14.2%)
- 炭水化物: +3.6g (+6.0%)

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

合計: 1046 kcal, P: 77.2g, F: 40.0g, C: 65.7g

**差分 (Pipeline - Label)**

- カロリー: +361.8 kcal (+52.9%)
- タンパク質: +13.3g (+20.8%)
- 脂質: +16.2g (+68.1%)
- 炭水化物: +8.1g (+14.1%)

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

合計: 702 kcal, P: 34.3g, F: 38.8g, C: 65.7g

**差分 (Pipeline - Label)**

- カロリー: +183.0 kcal (+35.2%)
- タンパク質: +1.7g (+5.2%)
- 脂質: +14.0g (+56.5%)
- 炭水化物: +20.7g (+46.0%)

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

合計: 1014 kcal, P: 63.1g, F: 62.7g, C: 60.9g

**差分 (Pipeline - Label)**

- カロリー: +288.8 kcal (+39.8%)
- タンパク質: +16.6g (+35.7%)
- 脂質: +21.0g (+50.4%)
- 炭水化物: +17.9g (+41.6%)

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

合計: 639 kcal, P: 22.1g, F: 10.0g, C: 112.5g

**差分 (Pipeline - Label)**

- カロリー: -6.3 kcal (-1.0%)
- タンパク質: -9.3g (-29.6%)
- 脂質: -18.2g (-64.5%)
- 炭水化物: +42.7g (+61.2%)

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

合計: 282 kcal, P: 35.5g, F: 11.7g, C: 9.5g

**差分 (Pipeline - Label)**

- カロリー: -88.2 kcal (-23.8%)
- タンパク質: -11.6g (-24.6%)
- 脂質: -1.0g (-7.9%)
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

合計: 940 kcal, P: 41.1g, F: 68.2g, C: 42.9g

**差分 (Pipeline - Label)**

- カロリー: +191.5 kcal (+25.6%)
- タンパク質: +13.5g (+48.9%)
- 脂質: +25.0g (+57.9%)
- 炭水化物: -18.7g (-30.4%)

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

合計: 795 kcal, P: 28.9g, F: 41.9g, C: 74.6g

**差分 (Pipeline - Label)**

- カロリー: +8.9 kcal (+1.1%)
- タンパク質: -3.3g (-10.2%)
- 脂質: +5.0g (+13.6%)
- 炭水化物: -5.8g (-7.2%)

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

合計: 746 kcal, P: 35.0g, F: 43.8g, C: 54.5g

**差分 (Pipeline - Label)**

- カロリー: -197.3 kcal (-20.9%)
- タンパク質: -1.0g (-2.8%)
- 脂質: +3.3g (+8.1%)
- 炭水化物: -53.1g (-49.3%)

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

合計: 744 kcal, P: 21.1g, F: 25.7g, C: 103.8g

**差分 (Pipeline - Label)**

- カロリー: -25.6 kcal (-3.3%)
- タンパク質: -41.6g (-66.3%)
- 脂質: -2.6g (-9.2%)
- 炭水化物: +33.6g (+47.9%)

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

合計: 645 kcal, P: 46.8g, F: 24.0g, C: 59.4g

**差分 (Pipeline - Label)**

- カロリー: -68.6 kcal (-9.6%)
- タンパク質: +5.3g (+12.8%)
- 脂質: -15.3g (-38.9%)
- 炭水化物: +3.2g (+5.7%)

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

合計: 605 kcal, P: 23.9g, F: 28.9g, C: 61.2g

**差分 (Pipeline - Label)**

- カロリー: -72.2 kcal (-10.7%)
- タンパク質: -8.3g (-25.8%)
- 脂質: -3.3g (-10.2%)
- 炭水化物: -4.9g (-7.4%)

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

合計: 629 kcal, P: 50.5g, F: 24.1g, C: 50.0g

**差分 (Pipeline - Label)**

- カロリー: -43.4 kcal (-6.5%)
- タンパク質: +20.4g (+67.8%)
- 脂質: -12.4g (-34.0%)
- 炭水化物: -7.3g (-12.7%)

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

合計: 903 kcal, P: 67.2g, F: 40.1g, C: 64.6g

**差分 (Pipeline - Label)**

- カロリー: +47.0 kcal (+5.5%)
- タンパク質: +19.3g (+40.3%)
- 脂質: -0.4g (-1.0%)
- 炭水化物: -20.9g (-24.4%)

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

合計: 640 kcal, P: 53.8g, F: 19.0g, C: 59.1g

**差分 (Pipeline - Label)**

- カロリー: +32.3 kcal (+5.3%)
- タンパク質: +17.1g (+46.6%)
- 脂質: -9.5g (-33.3%)
- 炭水化物: +9.6g (+19.4%)

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

合計: 996 kcal, P: 68.9g, F: 39.9g, C: 88.0g

**差分 (Pipeline - Label)**

- カロリー: +15.9 kcal (+1.6%)
- タンパク質: +29.4g (+74.4%)
- 脂質: -19.9g (-33.3%)
- 炭水化物: +13.8g (+18.6%)

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

合計: 753 kcal, P: 32.9g, F: 53.6g, C: 52.0g

**差分 (Pipeline - Label)**

- カロリー: +71.7 kcal (+10.5%)
- タンパク質: -1.7g (-4.9%)
- 脂質: +12.5g (+30.4%)
- 炭水化物: +6.3g (+13.8%)

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

合計: 661 kcal, P: 22.2g, F: 12.2g, C: 112.8g

**差分 (Pipeline - Label)**

- カロリー: -35.6 kcal (-5.1%)
- タンパク質: -3.3g (-12.9%)
- 脂質: -20.1g (-62.2%)
- 炭水化物: +30.5g (+37.1%)

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

合計: 903 kcal, P: 87.5g, F: 35.0g, C: 55.3g

**差分 (Pipeline - Label)**

- カロリー: +201.9 kcal (+28.8%)
- タンパク質: +34.5g (+65.1%)
- 脂質: -1.3g (-3.6%)
- 炭水化物: +8.9g (+19.2%)

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

合計: 1328 kcal, P: 53.8g, F: 69.6g, C: 121.6g

**差分 (Pipeline - Label)**

- カロリー: +353.7 kcal (+36.3%)
- タンパク質: +17.1g (+46.6%)
- 脂質: +20.5g (+41.8%)
- 炭水化物: +24.8g (+25.6%)

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

合計: 751 kcal, P: 67.4g, F: 20.9g, C: 70.4g

**差分 (Pipeline - Label)**

- カロリー: -34.7 kcal (-4.4%)
- タンパク質: +18.0g (+36.4%)
- 脂質: -10.9g (-34.3%)
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

合計: 901 kcal, P: 74.9g, F: 40.1g, C: 60.5g

**差分 (Pipeline - Label)**

- カロリー: +334.9 kcal (+59.2%)
- タンパク質: +20.5g (+37.7%)
- 脂質: +19.4g (+93.7%)
- 炭水化物: +18.9g (+45.4%)

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

合計: 742 kcal, P: 25.1g, F: 37.3g, C: 75.4g

**差分 (Pipeline - Label)**

- カロリー: +223.7 kcal (+43.2%)
- タンパク質: +3.2g (+14.6%)
- 脂質: +19.5g (+109.6%)
- 炭水化物: +0.2g (+0.3%)

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

合計: 679 kcal, P: 55.4g, F: 26.1g, C: 57.1g

**差分 (Pipeline - Label)**

- カロリー: +2.7 kcal (+0.4%)
- タンパク質: +24.2g (+77.6%)
- 脂質: -3.4g (-11.5%)
- 炭水化物: -17.8g (-23.8%)

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

合計: 774 kcal, P: 30.7g, F: 33.5g, C: 89.3g

**差分 (Pipeline - Label)**

- カロリー: -8.3 kcal (-1.1%)
- タンパク質: -5.8g (-15.9%)
- 脂質: -0.7g (-2.0%)
- 炭水化物: +2.5g (+2.9%)

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

合計: 715 kcal, P: 23.3g, F: 38.1g, C: 68.2g

**差分 (Pipeline - Label)**

- カロリー: +168.8 kcal (+30.9%)
- タンパク質: +0.5g (+2.2%)
- 脂質: +21.1g (+124.1%)
- 炭水化物: -3.6g (-5.0%)

---

### test_food49.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | cheese pizza | 220g | 585 | 24.2g | 22.0g | 72.6g |
| extra | black olives | 15g | 17 | 0.1g | 1.6g | 0.9g |
| **合計** | - | - | **602** | **24.3g** | **23.6g** | **73.5g** |

**Pipeline栄養素**

合計: 705 kcal, P: 27.9g, F: 27.9g, C: 86.1g

**差分 (Pipeline - Label)**

- カロリー: +102.2 kcal (+17.0%)
- タンパク質: +3.6g (+14.8%)
- 脂質: +4.3g (+18.2%)
- 炭水化物: +12.6g (+17.1%)

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

合計: 770 kcal, P: 32.1g, F: 33.2g, C: 87.6g

**差分 (Pipeline - Label)**

- カロリー: +36.4 kcal (+5.0%)
- タンパク質: +3.2g (+11.1%)
- 脂質: -7.5g (-18.4%)
- 炭水化物: +18.4g (+26.6%)

---

### test_food6.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | cream of chicken soup with vegetables | 400g | 280 | 18.0g | 14.0g | 24.0g |
| main_food | dinner roll | 80g | 224 | 7.2g | 3.6g | 41.6g |
| **合計** | - | - | **504** | **25.2g** | **17.6g** | **65.6g** |

**Pipeline栄養素**

合計: 736 kcal, P: 22.4g, F: 32.2g, C: 89.8g

**差分 (Pipeline - Label)**

- カロリー: +231.6 kcal (+46.0%)
- タンパク質: -2.8g (-11.1%)
- 脂質: +14.6g (+83.0%)
- 炭水化物: +24.2g (+36.9%)

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

合計: 736 kcal, P: 67.1g, F: 32.9g, C: 39.5g

**差分 (Pipeline - Label)**

- カロリー: +14.2 kcal (+2.0%)
- タンパク質: +16.2g (+31.8%)
- 脂質: -11.5g (-25.9%)
- 炭水化物: +5.4g (+15.8%)

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

合計: 620 kcal, P: 63.8g, F: 13.6g, C: 56.6g

**差分 (Pipeline - Label)**

- カロリー: -13.7 kcal (-2.2%)
- タンパク質: +23.0g (+56.4%)
- 脂質: -3.6g (-20.9%)
- 炭水化物: -27.9g (-33.0%)

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

合計: 866 kcal, P: 61.1g, F: 40.5g, C: 66.7g

**差分 (Pipeline - Label)**

- カロリー: +95.0 kcal (+12.3%)
- タンパク質: +14.9g (+32.3%)
- 脂質: -8.7g (-17.7%)
- 炭水化物: +21.2g (+46.6%)

---
