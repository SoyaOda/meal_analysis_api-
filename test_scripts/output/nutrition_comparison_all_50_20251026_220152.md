# Pipeline vs VLM Label 栄養素比較レポート

生成日時: 2025-10-26 22:01:52

対象画像数: 50

## サマリー

### 平均差分（Pipeline - Label）

| 栄養素 | 平均差分 (%) |
|--------|--------------|
| カロリー | +0.9% |
| タンパク質 | +15.8% |
| 脂質 | -15.8% |
| 炭水化物 | +9.0% |

## 詳細比較表

| 画像 | Label Cal | Pipeline Cal | 差分 | Label P | Pipeline P | 差分 | Label F | Pipeline F | 差分 | Label C | Pipeline C | 差分 |
|------|-----------|--------------|------|---------|------------|------|---------|------------|------|---------|------------|------|
| test_food1.jpg | 891 | 519 | -41.7% | 58.9 | 65.9 | +11.9% | 53.8 | 14.4 | -73.2% | 50.9 | 33.4 | -34.4% |
| test_food10.jpg | 854 | 962 | +12.7% | 59.5 | 87.2 | +46.6% | 48.1 | 42.3 | -12.1% | 53.4 | 52.6 | -1.5% |
| test_food11.jpg | 499 | 383 | -23.3% | 27.4 | 17.7 | -35.4% | 27.4 | 17.4 | -36.5% | 40.2 | 39.4 | -2.0% |
| test_food12.jpg | 441 | 311 | -29.5% | 24.6 | 20.6 | -16.3% | 28.0 | 19.1 | -31.8% | 25.6 | 12.2 | -52.3% |
| test_food13.jpg | 643 | 1038 | +61.4% | 31.0 | 48.8 | +57.4% | 26.3 | 50.6 | +92.4% | 80.0 | 101.2 | +26.5% |
| test_food14.jpg | 749 | 710 | -5.3% | 45.8 | 63.4 | +38.4% | 26.9 | 11.2 | -58.4% | 81.0 | 83.5 | +3.1% |
| test_food15.jpg | 488 | 410 | -15.8% | 25.9 | 20.0 | -22.8% | 24.1 | 23.3 | -3.3% | 46.0 | 32.4 | -29.6% |
| test_food16.jpg | 855 | 945 | +10.5% | 58.0 | 62.5 | +7.8% | 42.6 | 41.8 | -1.9% | 62.1 | 77.1 | +24.2% |
| test_food17.jpg | 746 | 847 | +13.6% | 25.7 | 25.0 | -2.7% | 34.7 | 31.9 | -8.1% | 85.4 | 115.6 | +35.4% |
| test_food18.jpg | 582 | 816 | +40.3% | 43.6 | 40.1 | -8.0% | 14.8 | 32.0 | +116.2% | 70.8 | 91.0 | +28.5% |
| test_food19.jpg | 599 | 575 | -4.0% | 52.1 | 57.1 | +9.6% | 16.2 | 11.0 | -32.1% | 60.5 | 59.8 | -1.2% |
| test_food2.jpg | 684 | 767 | +12.1% | 63.9 | 65.7 | +2.8% | 23.8 | 18.4 | -22.7% | 57.6 | 59.8 | +3.8% |
| test_food20.jpg | 519 | 767 | +47.7% | 32.6 | 35.2 | +8.0% | 24.8 | 40.7 | +64.1% | 45.0 | 68.6 | +52.4% |
| test_food21.jpg | 725 | 847 | +16.7% | 46.5 | 50.8 | +9.2% | 41.7 | 46.1 | +10.6% | 43.0 | 55.1 | +28.1% |
| test_food22.jpg | 646 | 612 | -5.1% | 31.4 | 22.7 | -27.7% | 28.2 | 3.4 | -87.9% | 69.8 | 121.1 | +73.5% |
| test_food23.jpg | 706 | 851 | +20.5% | 24.5 | 32.4 | +32.2% | 40.9 | 43.1 | +5.4% | 64.6 | 83.3 | +28.9% |
| test_food24.jpg | 370 | 350 | -5.5% | 47.1 | 40.2 | -14.6% | 12.7 | 15.4 | +21.3% | 15.6 | 12.9 | -17.3% |
| test_food25.jpg | 748 | 518 | -30.8% | 27.6 | 22.8 | -17.4% | 43.2 | 28.4 | -34.3% | 61.6 | 43.0 | -30.2% |
| test_food26.jpg | 786 | 691 | -12.1% | 32.2 | 25.5 | -20.8% | 36.9 | 36.5 | -1.1% | 80.4 | 64.2 | -20.1% |
| test_food27.jpg | 1069 | 495 | -53.7% | 50.8 | 38.7 | -23.8% | 54.3 | 10.0 | -81.6% | 85.5 | 61.4 | -28.2% |
| test_food28.jpg | 944 | 623 | -34.0% | 36.0 | 32.3 | -10.3% | 40.5 | 22.3 | -44.9% | 107.6 | 79.8 | -25.8% |
| test_food29.jpg | 769 | 542 | -29.5% | 62.7 | 21.6 | -65.6% | 28.3 | 28.5 | +0.7% | 70.2 | 54.1 | -22.9% |
| test_food3.jpg | 1000 | 815 | -18.6% | 56.7 | 58.3 | +2.8% | 60.4 | 48.7 | -19.4% | 68.7 | 38.0 | -44.7% |
| test_food30.jpg | 714 | 758 | +6.3% | 41.5 | 56.5 | +36.1% | 39.3 | 23.4 | -40.5% | 56.2 | 76.3 | +35.8% |
| test_food31.jpg | 609 | 556 | -8.7% | 40.9 | 35.3 | -13.7% | 29.9 | 16.1 | -46.2% | 46.0 | 109.1 | +137.2% |
| test_food32.jpg | 677 | 849 | +25.3% | 32.2 | 57.0 | +77.0% | 32.2 | 51.5 | +59.9% | 66.1 | 39.8 | -39.8% |
| test_food33.jpg | 572 | 702 | +22.8% | 31.5 | 48.3 | +53.3% | 26.2 | 28.0 | +6.9% | 48.7 | 60.8 | +24.8% |
| test_food34.jpg | 672 | 613 | -8.8% | 30.1 | 36.8 | +22.3% | 36.5 | 28.9 | -20.8% | 57.3 | 51.2 | -10.6% |
| test_food35.jpg | 856 | 818 | -4.4% | 47.9 | 58.8 | +22.8% | 40.5 | 13.6 | -66.4% | 85.5 | 109.7 | +28.3% |
| test_food36.jpg | 607 | 592 | -2.5% | 36.7 | 56.1 | +52.9% | 28.5 | 15.4 | -46.0% | 49.5 | 53.2 | +7.5% |
| test_food37.jpg | 980 | 739 | -24.6% | 39.5 | 48.7 | +23.3% | 59.8 | 26.8 | -55.2% | 74.2 | 71.9 | -3.1% |
| test_food38.jpg | 681 | 522 | -23.3% | 34.6 | 35.2 | +1.7% | 41.1 | 29.5 | -28.2% | 45.7 | 30.1 | -34.1% |
| test_food39.jpg | 696 | 499 | -28.3% | 25.5 | 18.3 | -28.2% | 32.3 | 4.6 | -85.8% | 82.3 | 95.5 | +16.0% |
| test_food4.jpg | 702 | 1144 | +63.0% | 53.0 | 125.2 | +136.2% | 36.3 | 41.2 | +13.5% | 46.4 | 60.9 | +31.2% |
| test_food40.jpg | 974 | 792 | -18.7% | 36.7 | 102.6 | +179.6% | 49.1 | 35.3 | -28.1% | 96.8 | 11.8 | -87.8% |
| test_food41.jpg | 682 | 716 | +5.0% | 50.2 | 76.1 | +51.6% | 33.8 | 11.1 | -67.2% | 43.9 | 75.9 | +72.9% |
| test_food42.jpg | 786 | 642 | -18.3% | 49.4 | 47.2 | -4.5% | 31.8 | 16.2 | -49.1% | 83.7 | 75.7 | -9.6% |
| test_food43.jpg | 566 | 702 | +24.0% | 54.4 | 65.7 | +20.8% | 20.7 | 18.0 | -13.0% | 41.6 | 67.8 | +63.0% |
| test_food44.jpg | 518 | 592 | +14.2% | 21.9 | 21.1 | -3.7% | 17.8 | 1.3 | -92.7% | 75.2 | 122.6 | +63.0% |
| test_food45.jpg | 791 | 796 | +0.6% | 29.5 | 33.1 | +12.2% | 40.0 | 35.0 | -12.5% | 80.1 | 90.2 | +12.6% |
| test_food46.jpg | 677 | 752 | +11.1% | 31.2 | 50.6 | +62.2% | 29.5 | 34.6 | +17.3% | 74.9 | 60.1 | -19.8% |
| test_food47.jpg | 783 | 1236 | +57.9% | 36.5 | 36.0 | -1.4% | 34.2 | 52.3 | +52.9% | 86.8 | 156.7 | +80.5% |
| test_food48.jpg | 546 | 662 | +21.3% | 22.8 | 29.8 | +30.7% | 17.0 | 26.0 | +52.9% | 71.8 | 79.4 | +10.6% |
| test_food49.jpg | 602 | 588 | -2.4% | 24.3 | 23.3 | -4.1% | 23.6 | 22.6 | -4.2% | 73.5 | 73.0 | -0.7% |
| test_food5.jpg | 530 | 554 | +4.7% | 50.8 | 67.1 | +32.1% | 18.1 | 12.1 | -33.1% | 41.6 | 44.7 | +7.5% |
| test_food50.jpg | 733 | 642 | -12.5% | 28.9 | 30.3 | +4.8% | 40.7 | 24.2 | -40.5% | 69.2 | 79.7 | +15.2% |
| test_food6.jpg | 504 | 810 | +60.8% | 25.2 | 30.4 | +20.6% | 17.6 | 34.6 | +96.6% | 65.6 | 97.4 | +48.5% |
| test_food7.jpg | 722 | 701 | -2.9% | 50.9 | 67.5 | +32.6% | 44.4 | 29.0 | -34.7% | 34.1 | 37.8 | +10.9% |
| test_food8.jpg | 634 | 410 | -35.2% | 40.8 | 43.0 | +5.4% | 17.2 | 8.9 | -48.3% | 84.5 | 36.9 | -56.3% |
| test_food9.jpg | 771 | 729 | -5.4% | 46.2 | 48.6 | +5.2% | 49.2 | 30.4 | -38.2% | 45.5 | 68.3 | +50.1% |

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

合計: 519 kcal, P: 65.9g, F: 14.4g, C: 33.4g

**差分 (Pipeline - Label)**

- カロリー: -371.7 kcal (-41.7%)
- タンパク質: +7.0g (+11.9%)
- 脂質: -39.4g (-73.2%)
- 炭水化物: -17.5g (-34.4%)

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

合計: 962 kcal, P: 87.2g, F: 42.3g, C: 52.6g

**差分 (Pipeline - Label)**

- カロリー: +108.1 kcal (+12.7%)
- タンパク質: +27.7g (+46.6%)
- 脂質: -5.8g (-12.1%)
- 炭水化物: -0.8g (-1.5%)

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

合計: 383 kcal, P: 17.7g, F: 17.4g, C: 39.4g

**差分 (Pipeline - Label)**

- カロリー: -116.1 kcal (-23.3%)
- タンパク質: -9.7g (-35.4%)
- 脂質: -10.0g (-36.5%)
- 炭水化物: -0.8g (-2.0%)

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

合計: 311 kcal, P: 20.6g, F: 19.1g, C: 12.2g

**差分 (Pipeline - Label)**

- カロリー: -130.4 kcal (-29.5%)
- タンパク質: -4.0g (-16.3%)
- 脂質: -8.9g (-31.8%)
- 炭水化物: -13.4g (-52.3%)

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

合計: 1038 kcal, P: 48.8g, F: 50.6g, C: 101.2g

**差分 (Pipeline - Label)**

- カロリー: +395.1 kcal (+61.4%)
- タンパク質: +17.8g (+57.4%)
- 脂質: +24.3g (+92.4%)
- 炭水化物: +21.2g (+26.5%)

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

合計: 710 kcal, P: 63.4g, F: 11.2g, C: 83.5g

**差分 (Pipeline - Label)**

- カロリー: -39.5 kcal (-5.3%)
- タンパク質: +17.6g (+38.4%)
- 脂質: -15.7g (-58.4%)
- 炭水化物: +2.5g (+3.1%)

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

合計: 410 kcal, P: 20.0g, F: 23.3g, C: 32.4g

**差分 (Pipeline - Label)**

- カロリー: -77.0 kcal (-15.8%)
- タンパク質: -5.9g (-22.8%)
- 脂質: -0.8g (-3.3%)
- 炭水化物: -13.6g (-29.6%)

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

合計: 945 kcal, P: 62.5g, F: 41.8g, C: 77.1g

**差分 (Pipeline - Label)**

- カロリー: +89.9 kcal (+10.5%)
- タンパク質: +4.5g (+7.8%)
- 脂質: -0.8g (-1.9%)
- 炭水化物: +15.0g (+24.2%)

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

合計: 847 kcal, P: 25.0g, F: 31.9g, C: 115.6g

**差分 (Pipeline - Label)**

- カロリー: +101.6 kcal (+13.6%)
- タンパク質: -0.7g (-2.7%)
- 脂質: -2.8g (-8.1%)
- 炭水化物: +30.2g (+35.4%)

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

合計: 816 kcal, P: 40.1g, F: 32.0g, C: 91.0g

**差分 (Pipeline - Label)**

- カロリー: +234.3 kcal (+40.3%)
- タンパク質: -3.5g (-8.0%)
- 脂質: +17.2g (+116.2%)
- 炭水化物: +20.2g (+28.5%)

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

合計: 575 kcal, P: 57.1g, F: 11.0g, C: 59.8g

**差分 (Pipeline - Label)**

- カロリー: -23.8 kcal (-4.0%)
- タンパク質: +5.0g (+9.6%)
- 脂質: -5.2g (-32.1%)
- 炭水化物: -0.7g (-1.2%)

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

合計: 767 kcal, P: 65.7g, F: 18.4g, C: 59.8g

**差分 (Pipeline - Label)**

- カロリー: +82.5 kcal (+12.1%)
- タンパク質: +1.8g (+2.8%)
- 脂質: -5.4g (-22.7%)
- 炭水化物: +2.2g (+3.8%)

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

合計: 767 kcal, P: 35.2g, F: 40.7g, C: 68.6g

**差分 (Pipeline - Label)**

- カロリー: +247.8 kcal (+47.7%)
- タンパク質: +2.6g (+8.0%)
- 脂質: +15.9g (+64.1%)
- 炭水化物: +23.6g (+52.4%)

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

合計: 847 kcal, P: 50.8g, F: 46.1g, C: 55.1g

**差分 (Pipeline - Label)**

- カロリー: +121.3 kcal (+16.7%)
- タンパク質: +4.3g (+9.2%)
- 脂質: +4.4g (+10.6%)
- 炭水化物: +12.1g (+28.1%)

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

合計: 612 kcal, P: 22.7g, F: 3.4g, C: 121.1g

**差分 (Pipeline - Label)**

- カロリー: -33.0 kcal (-5.1%)
- タンパク質: -8.7g (-27.7%)
- 脂質: -24.8g (-87.9%)
- 炭水化物: +51.3g (+73.5%)

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

合計: 851 kcal, P: 32.4g, F: 43.1g, C: 83.3g

**差分 (Pipeline - Label)**

- カロリー: +144.9 kcal (+20.5%)
- タンパク質: +7.9g (+32.2%)
- 脂質: +2.2g (+5.4%)
- 炭水化物: +18.7g (+28.9%)

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

合計: 350 kcal, P: 40.2g, F: 15.4g, C: 12.9g

**差分 (Pipeline - Label)**

- カロリー: -20.5 kcal (-5.5%)
- タンパク質: -6.9g (-14.6%)
- 脂質: +2.7g (+21.3%)
- 炭水化物: -2.7g (-17.3%)

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

合計: 518 kcal, P: 22.8g, F: 28.4g, C: 43.0g

**差分 (Pipeline - Label)**

- カロリー: -230.5 kcal (-30.8%)
- タンパク質: -4.8g (-17.4%)
- 脂質: -14.8g (-34.3%)
- 炭水化物: -18.6g (-30.2%)

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

合計: 691 kcal, P: 25.5g, F: 36.5g, C: 64.2g

**差分 (Pipeline - Label)**

- カロリー: -94.9 kcal (-12.1%)
- タンパク質: -6.7g (-20.8%)
- 脂質: -0.4g (-1.1%)
- 炭水化物: -16.2g (-20.1%)

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

合計: 495 kcal, P: 38.7g, F: 10.0g, C: 61.4g

**差分 (Pipeline - Label)**

- カロリー: -573.9 kcal (-53.7%)
- タンパク質: -12.1g (-23.8%)
- 脂質: -44.3g (-81.6%)
- 炭水化物: -24.1g (-28.2%)

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

合計: 623 kcal, P: 32.3g, F: 22.3g, C: 79.8g

**差分 (Pipeline - Label)**

- カロリー: -320.8 kcal (-34.0%)
- タンパク質: -3.7g (-10.3%)
- 脂質: -18.2g (-44.9%)
- 炭水化物: -27.8g (-25.8%)

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

合計: 542 kcal, P: 21.6g, F: 28.5g, C: 54.1g

**差分 (Pipeline - Label)**

- カロリー: -226.6 kcal (-29.5%)
- タンパク質: -41.1g (-65.6%)
- 脂質: +0.2g (+0.7%)
- 炭水化物: -16.1g (-22.9%)

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

合計: 815 kcal, P: 58.3g, F: 48.7g, C: 38.0g

**差分 (Pipeline - Label)**

- カロリー: -185.7 kcal (-18.6%)
- タンパク質: +1.6g (+2.8%)
- 脂質: -11.7g (-19.4%)
- 炭水化物: -30.7g (-44.7%)

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

合計: 758 kcal, P: 56.5g, F: 23.4g, C: 76.3g

**差分 (Pipeline - Label)**

- カロリー: +44.6 kcal (+6.3%)
- タンパク質: +15.0g (+36.1%)
- 脂質: -15.9g (-40.5%)
- 炭水化物: +20.1g (+35.8%)

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

合計: 556 kcal, P: 35.3g, F: 16.1g, C: 109.1g

**差分 (Pipeline - Label)**

- カロリー: -53.0 kcal (-8.7%)
- タンパク質: -5.6g (-13.7%)
- 脂質: -13.8g (-46.2%)
- 炭水化物: +63.1g (+137.2%)

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

合計: 849 kcal, P: 57.0g, F: 51.5g, C: 39.8g

**差分 (Pipeline - Label)**

- カロリー: +171.4 kcal (+25.3%)
- タンパク質: +24.8g (+77.0%)
- 脂質: +19.3g (+59.9%)
- 炭水化物: -26.3g (-39.8%)

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

合計: 702 kcal, P: 48.3g, F: 28.0g, C: 60.8g

**差分 (Pipeline - Label)**

- カロリー: +130.3 kcal (+22.8%)
- タンパク質: +16.8g (+53.3%)
- 脂質: +1.8g (+6.9%)
- 炭水化物: +12.1g (+24.8%)

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

合計: 613 kcal, P: 36.8g, F: 28.9g, C: 51.2g

**差分 (Pipeline - Label)**

- カロリー: -59.5 kcal (-8.8%)
- タンパク質: +6.7g (+22.3%)
- 脂質: -7.6g (-20.8%)
- 炭水化物: -6.1g (-10.6%)

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

合計: 818 kcal, P: 58.8g, F: 13.6g, C: 109.7g

**差分 (Pipeline - Label)**

- カロリー: -37.7 kcal (-4.4%)
- タンパク質: +10.9g (+22.8%)
- 脂質: -26.9g (-66.4%)
- 炭水化物: +24.2g (+28.3%)

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

合計: 592 kcal, P: 56.1g, F: 15.4g, C: 53.2g

**差分 (Pipeline - Label)**

- カロリー: -15.3 kcal (-2.5%)
- タンパク質: +19.4g (+52.9%)
- 脂質: -13.1g (-46.0%)
- 炭水化物: +3.7g (+7.5%)

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

合計: 739 kcal, P: 48.7g, F: 26.8g, C: 71.9g

**差分 (Pipeline - Label)**

- カロリー: -241.3 kcal (-24.6%)
- タンパク質: +9.2g (+23.3%)
- 脂質: -33.0g (-55.2%)
- 炭水化物: -2.3g (-3.1%)

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

合計: 522 kcal, P: 35.2g, F: 29.5g, C: 30.1g

**差分 (Pipeline - Label)**

- カロリー: -159.0 kcal (-23.3%)
- タンパク質: +0.6g (+1.7%)
- 脂質: -11.6g (-28.2%)
- 炭水化物: -15.6g (-34.1%)

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

合計: 499 kcal, P: 18.3g, F: 4.6g, C: 95.5g

**差分 (Pipeline - Label)**

- カロリー: -196.9 kcal (-28.3%)
- タンパク質: -7.2g (-28.2%)
- 脂質: -27.7g (-85.8%)
- 炭水化物: +13.2g (+16.0%)

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

合計: 1144 kcal, P: 125.2g, F: 41.2g, C: 60.9g

**差分 (Pipeline - Label)**

- カロリー: +442.1 kcal (+63.0%)
- タンパク質: +72.2g (+136.2%)
- 脂質: +4.9g (+13.5%)
- 炭水化物: +14.5g (+31.2%)

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

合計: 792 kcal, P: 102.6g, F: 35.3g, C: 11.8g

**差分 (Pipeline - Label)**

- カロリー: -182.6 kcal (-18.7%)
- タンパク質: +65.9g (+179.6%)
- 脂質: -13.8g (-28.1%)
- 炭水化物: -85.0g (-87.8%)

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

合計: 716 kcal, P: 76.1g, F: 11.1g, C: 75.9g

**差分 (Pipeline - Label)**

- カロリー: +34.1 kcal (+5.0%)
- タンパク質: +25.9g (+51.6%)
- 脂質: -22.7g (-67.2%)
- 炭水化物: +32.0g (+72.9%)

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

合計: 642 kcal, P: 47.2g, F: 16.2g, C: 75.7g

**差分 (Pipeline - Label)**

- カロリー: -143.4 kcal (-18.3%)
- タンパク質: -2.2g (-4.5%)
- 脂質: -15.6g (-49.1%)
- 炭水化物: -8.0g (-9.6%)

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

合計: 702 kcal, P: 65.7g, F: 18.0g, C: 67.8g

**差分 (Pipeline - Label)**

- カロリー: +135.7 kcal (+24.0%)
- タンパク質: +11.3g (+20.8%)
- 脂質: -2.7g (-13.0%)
- 炭水化物: +26.2g (+63.0%)

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

合計: 592 kcal, P: 21.1g, F: 1.3g, C: 122.6g

**差分 (Pipeline - Label)**

- カロリー: +73.4 kcal (+14.2%)
- タンパク質: -0.8g (-3.7%)
- 脂質: -16.5g (-92.7%)
- 炭水化物: +47.4g (+63.0%)

---

### test_food45.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | prosciutto and mozzarella sandwich | 220g | 550 | 26.4g | 24.2g | 57.2g |
| main_food | potato chips | 45g | 241 | 3.1g | 15.8g | 22.9g |
| **合計** | - | - | **791** | **29.5g** | **40.0g** | **80.1g** |

**Pipeline栄養素**

合計: 796 kcal, P: 33.1g, F: 35.0g, C: 90.2g

**差分 (Pipeline - Label)**

- カロリー: +4.4 kcal (+0.6%)
- タンパク質: +3.6g (+12.2%)
- 脂質: -5.0g (-12.5%)
- 炭水化物: +10.1g (+12.6%)

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

合計: 752 kcal, P: 50.6g, F: 34.6g, C: 60.1g

**差分 (Pipeline - Label)**

- カロリー: +75.3 kcal (+11.1%)
- タンパク質: +19.4g (+62.2%)
- 脂質: +5.1g (+17.3%)
- 炭水化物: -14.8g (-19.8%)

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

合計: 1236 kcal, P: 36.0g, F: 52.3g, C: 156.7g

**差分 (Pipeline - Label)**

- カロリー: +453.5 kcal (+57.9%)
- タンパク質: -0.5g (-1.4%)
- 脂質: +18.1g (+52.9%)
- 炭水化物: +69.9g (+80.5%)

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

合計: 662 kcal, P: 29.8g, F: 26.0g, C: 79.4g

**差分 (Pipeline - Label)**

- カロリー: +116.4 kcal (+21.3%)
- タンパク質: +7.0g (+30.7%)
- 脂質: +9.0g (+52.9%)
- 炭水化物: +7.6g (+10.6%)

---

### test_food49.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | cheese pizza | 220g | 585 | 24.2g | 22.0g | 72.6g |
| extra | black olives | 15g | 17 | 0.1g | 1.6g | 0.9g |
| **合計** | - | - | **602** | **24.3g** | **23.6g** | **73.5g** |

**Pipeline栄養素**

合計: 588 kcal, P: 23.3g, F: 22.6g, C: 73.0g

**差分 (Pipeline - Label)**

- カロリー: -14.4 kcal (-2.4%)
- タンパク質: -1.0g (-4.1%)
- 脂質: -1.0g (-4.2%)
- 炭水化物: -0.5g (-0.7%)

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

合計: 554 kcal, P: 67.1g, F: 12.1g, C: 44.7g

**差分 (Pipeline - Label)**

- カロリー: +24.9 kcal (+4.7%)
- タンパク質: +16.3g (+32.1%)
- 脂質: -6.0g (-33.1%)
- 炭水化物: +3.1g (+7.5%)

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

合計: 642 kcal, P: 30.3g, F: 24.2g, C: 79.7g

**差分 (Pipeline - Label)**

- カロリー: -91.4 kcal (-12.5%)
- タンパク質: +1.4g (+4.8%)
- 脂質: -16.5g (-40.5%)
- 炭水化物: +10.5g (+15.2%)

---

### test_food6.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | cream of chicken soup with vegetables | 400g | 280 | 18.0g | 14.0g | 24.0g |
| main_food | dinner roll | 80g | 224 | 7.2g | 3.6g | 41.6g |
| **合計** | - | - | **504** | **25.2g** | **17.6g** | **65.6g** |

**Pipeline栄養素**

合計: 810 kcal, P: 30.4g, F: 34.6g, C: 97.4g

**差分 (Pipeline - Label)**

- カロリー: +306.2 kcal (+60.8%)
- タンパク質: +5.2g (+20.6%)
- 脂質: +17.0g (+96.6%)
- 炭水化物: +31.8g (+48.5%)

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

合計: 701 kcal, P: 67.5g, F: 29.0g, C: 37.8g

**差分 (Pipeline - Label)**

- カロリー: -21.0 kcal (-2.9%)
- タンパク質: +16.6g (+32.6%)
- 脂質: -15.4g (-34.7%)
- 炭水化物: +3.7g (+10.9%)

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

合計: 410 kcal, P: 43.0g, F: 8.9g, C: 36.9g

**差分 (Pipeline - Label)**

- カロリー: -223.3 kcal (-35.2%)
- タンパク質: +2.2g (+5.4%)
- 脂質: -8.3g (-48.3%)
- 炭水化物: -47.6g (-56.3%)

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

合計: 729 kcal, P: 48.6g, F: 30.4g, C: 68.3g

**差分 (Pipeline - Label)**

- カロリー: -42.0 kcal (-5.4%)
- タンパク質: +2.4g (+5.2%)
- 脂質: -18.8g (-38.2%)
- 炭水化物: +22.8g (+50.1%)

---
