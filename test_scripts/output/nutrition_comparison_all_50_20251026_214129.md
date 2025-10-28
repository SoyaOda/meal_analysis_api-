# Pipeline vs VLM Label 栄養素比較レポート

生成日時: 2025-10-26 21:41:29

対象画像数: 50

## サマリー

### 平均差分（Pipeline - Label）

| 栄養素 | 平均差分 (%) |
|--------|--------------|
| カロリー | +3.2% |
| タンパク質 | +14.2% |
| 脂質 | -6.8% |
| 炭水化物 | +7.0% |

## 詳細比較表

| 画像 | Label Cal | Pipeline Cal | 差分 | Label P | Pipeline P | 差分 | Label F | Pipeline F | 差分 | Label C | Pipeline C | 差分 |
|------|-----------|--------------|------|---------|------------|------|---------|------------|------|---------|------------|------|
| test_food1.jpg | 891 | 528 | -40.7% | 58.9 | 67.0 | +13.8% | 53.8 | 15.0 | -72.1% | 50.9 | 33.7 | -33.8% |
| test_food10.jpg | 854 | 962 | +12.7% | 59.5 | 87.2 | +46.6% | 48.1 | 42.3 | -12.1% | 53.4 | 52.6 | -1.5% |
| test_food11.jpg | 499 | 401 | -19.7% | 27.4 | 19.3 | -29.6% | 27.4 | 19.2 | -29.9% | 40.2 | 47.1 | +17.2% |
| test_food12.jpg | 441 | 309 | -30.0% | 24.6 | 21.4 | -13.0% | 28.0 | 19.3 | -31.1% | 25.6 | 14.3 | -44.1% |
| test_food13.jpg | 643 | 894 | +39.0% | 31.0 | 40.3 | +30.0% | 26.3 | 42.4 | +61.2% | 80.0 | 93.0 | +16.2% |
| test_food14.jpg | 749 | 567 | -24.3% | 45.8 | 55.2 | +20.5% | 26.9 | 11.6 | -56.9% | 81.0 | 59.5 | -26.5% |
| test_food15.jpg | 488 | 733 | +50.4% | 25.9 | 45.1 | +74.1% | 24.1 | 39.0 | +61.8% | 46.0 | 51.0 | +10.9% |
| test_food16.jpg | 855 | 938 | +9.7% | 58.0 | 59.9 | +3.3% | 42.6 | 45.0 | +5.6% | 62.1 | 70.3 | +13.2% |
| test_food17.jpg | 746 | 893 | +19.7% | 25.7 | 35.9 | +39.7% | 34.7 | 42.9 | +23.6% | 85.4 | 89.6 | +4.9% |
| test_food18.jpg | 582 | 572 | -1.7% | 43.6 | 26.6 | -39.0% | 14.8 | 22.0 | +48.6% | 70.8 | 68.1 | -3.8% |
| test_food19.jpg | 599 | 575 | -4.0% | 52.1 | 56.8 | +9.0% | 16.2 | 11.4 | -29.6% | 60.5 | 59.7 | -1.3% |
| test_food2.jpg | 684 | 819 | +19.7% | 63.9 | 61.8 | -3.3% | 23.8 | 22.5 | -5.5% | 57.6 | 65.8 | +14.2% |
| test_food20.jpg | 519 | 677 | +30.4% | 32.6 | 51.0 | +56.4% | 24.8 | 31.7 | +27.8% | 45.0 | 47.0 | +4.4% |
| test_food21.jpg | 725 | 1000 | +37.8% | 46.5 | 65.1 | +40.0% | 41.7 | 52.6 | +26.1% | 43.0 | 63.9 | +48.6% |
| test_food22.jpg | 646 | 569 | -11.9% | 31.4 | 20.4 | -35.0% | 28.2 | 0.6 | -97.9% | 69.8 | 120.4 | +72.5% |
| test_food23.jpg | 706 | 698 | -1.1% | 24.5 | 29.7 | +21.2% | 40.9 | 30.9 | -24.4% | 64.6 | 74.9 | +15.9% |
| test_food24.jpg | 370 | 366 | -1.3% | 47.1 | 35.9 | -23.8% | 12.7 | 18.4 | +44.9% | 15.6 | 14.6 | -6.4% |
| test_food25.jpg | 748 | 780 | +4.3% | 27.6 | 32.7 | +18.5% | 43.2 | 45.4 | +5.1% | 61.6 | 64.5 | +4.7% |
| test_food26.jpg | 786 | 551 | -29.9% | 32.2 | 20.0 | -37.9% | 36.9 | 29.2 | -20.9% | 80.4 | 51.3 | -36.2% |
| test_food27.jpg | 1069 | 642 | -39.9% | 50.8 | 51.0 | +0.4% | 54.3 | 17.2 | -68.3% | 85.5 | 68.7 | -19.6% |
| test_food28.jpg | 944 | 917 | -2.8% | 36.0 | 39.1 | +8.6% | 40.5 | 38.1 | -5.9% | 107.6 | 104.6 | -2.8% |
| test_food29.jpg | 769 | 764 | -0.7% | 62.7 | 29.2 | -53.4% | 28.3 | 40.1 | +41.7% | 70.2 | 77.4 | +10.3% |
| test_food3.jpg | 1000 | 931 | -6.9% | 56.7 | 44.0 | -22.4% | 60.4 | 59.3 | -1.8% | 68.7 | 55.0 | -19.9% |
| test_food30.jpg | 714 | 921 | +29.0% | 41.5 | 57.2 | +37.8% | 39.3 | 21.0 | -46.6% | 56.2 | 123.7 | +120.1% |
| test_food31.jpg | 609 | 277 | -54.6% | 40.9 | 30.3 | -25.9% | 29.9 | 12.4 | -58.5% | 46.0 | 45.1 | -2.0% |
| test_food32.jpg | 677 | 691 | +2.1% | 32.2 | 46.5 | +44.4% | 32.2 | 42.1 | +30.7% | 66.1 | 32.8 | -50.4% |
| test_food33.jpg | 572 | 591 | +3.4% | 31.5 | 45.2 | +43.5% | 26.2 | 16.4 | -37.4% | 48.7 | 62.9 | +29.2% |
| test_food34.jpg | 672 | 612 | -9.0% | 30.1 | 36.5 | +21.3% | 36.5 | 28.8 | -21.1% | 57.3 | 51.2 | -10.6% |
| test_food35.jpg | 856 | 964 | +12.6% | 47.9 | 74.7 | +55.9% | 40.5 | 21.1 | -47.9% | 85.5 | 113.7 | +33.0% |
| test_food36.jpg | 607 | 698 | +15.0% | 36.7 | 89.5 | +143.9% | 28.5 | 12.1 | -57.5% | 49.5 | 56.2 | +13.5% |
| test_food37.jpg | 980 | 1735 | +76.9% | 39.5 | 67.1 | +69.9% | 59.8 | 139.1 | +132.6% | 74.2 | 50.1 | -32.5% |
| test_food38.jpg | 681 | 414 | -39.2% | 34.6 | 26.4 | -23.7% | 41.1 | 23.5 | -42.8% | 45.7 | 25.1 | -45.1% |
| test_food39.jpg | 696 | 385 | -44.7% | 25.5 | 23.6 | -7.5% | 32.3 | 20.1 | -37.8% | 82.3 | 30.1 | -63.4% |
| test_food4.jpg | 702 | 667 | -4.9% | 53.0 | 60.5 | +14.2% | 36.3 | 21.2 | -41.6% | 46.4 | 60.5 | +30.4% |
| test_food40.jpg | 974 | 885 | -9.2% | 36.7 | 41.6 | +13.4% | 49.1 | 33.1 | -32.6% | 96.8 | 105.9 | +9.4% |
| test_food41.jpg | 682 | 1105 | +61.9% | 50.2 | 73.3 | +46.0% | 33.8 | 51.1 | +51.2% | 43.9 | 82.1 | +87.0% |
| test_food42.jpg | 786 | 892 | +13.5% | 49.4 | 74.1 | +50.0% | 31.8 | 25.5 | -19.8% | 83.7 | 88.8 | +6.1% |
| test_food43.jpg | 566 | 639 | +12.9% | 54.4 | 60.7 | +11.6% | 20.7 | 15.8 | -23.7% | 41.6 | 62.6 | +50.5% |
| test_food44.jpg | 518 | 547 | +5.6% | 21.9 | 21.3 | -2.7% | 17.8 | 3.5 | -80.3% | 75.2 | 110.8 | +47.3% |
| test_food45.jpg | 791 | 522 | -34.1% | 29.5 | 31.0 | +5.1% | 40.0 | 16.7 | -58.2% | 80.1 | 63.0 | -21.3% |
| test_food46.jpg | 677 | 614 | -9.3% | 31.2 | 17.7 | -43.3% | 29.5 | 35.0 | +18.6% | 74.9 | 58.1 | -22.4% |
| test_food47.jpg | 783 | 836 | +6.9% | 36.5 | 34.8 | -4.7% | 34.2 | 35.2 | +2.9% | 86.8 | 96.7 | +11.4% |
| test_food48.jpg | 546 | 616 | +12.9% | 22.8 | 26.8 | +17.5% | 17.0 | 23.6 | +38.8% | 71.8 | 74.1 | +3.2% |
| test_food49.jpg | 602 | 588 | -2.4% | 24.3 | 23.3 | -4.1% | 23.6 | 22.6 | -4.2% | 73.5 | 73.0 | -0.7% |
| test_food5.jpg | 530 | 501 | -5.5% | 50.8 | 58.6 | +15.4% | 18.1 | 11.3 | -37.6% | 41.6 | 42.3 | +1.7% |
| test_food50.jpg | 733 | 727 | -0.8% | 28.9 | 31.5 | +9.0% | 40.7 | 31.8 | -21.9% | 69.2 | 82.4 | +19.1% |
| test_food6.jpg | 504 | 935 | +85.6% | 25.2 | 36.0 | +42.9% | 17.6 | 42.4 | +140.9% | 65.6 | 106.1 | +61.7% |
| test_food7.jpg | 722 | 654 | -9.4% | 50.9 | 66.3 | +30.3% | 44.4 | 30.6 | -31.1% | 34.1 | 24.6 | -27.9% |
| test_food8.jpg | 634 | 799 | +26.2% | 40.8 | 39.5 | -3.2% | 17.2 | 31.1 | +80.8% | 84.5 | 90.4 | +7.0% |
| test_food9.jpg | 771 | 850 | +10.2% | 46.2 | 58.9 | +27.5% | 49.2 | 37.1 | -24.6% | 45.5 | 71.8 | +57.8% |

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

合計: 528 kcal, P: 67.0g, F: 15.0g, C: 33.7g

**差分 (Pipeline - Label)**

- カロリー: -362.6 kcal (-40.7%)
- タンパク質: +8.1g (+13.8%)
- 脂質: -38.8g (-72.1%)
- 炭水化物: -17.2g (-33.8%)

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

合計: 401 kcal, P: 19.3g, F: 19.2g, C: 47.1g

**差分 (Pipeline - Label)**

- カロリー: -98.4 kcal (-19.7%)
- タンパク質: -8.1g (-29.6%)
- 脂質: -8.2g (-29.9%)
- 炭水化物: +6.9g (+17.2%)

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

合計: 309 kcal, P: 21.4g, F: 19.3g, C: 14.3g

**差分 (Pipeline - Label)**

- カロリー: -132.2 kcal (-30.0%)
- タンパク質: -3.2g (-13.0%)
- 脂質: -8.7g (-31.1%)
- 炭水化物: -11.3g (-44.1%)

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

合計: 894 kcal, P: 40.3g, F: 42.4g, C: 93.0g

**差分 (Pipeline - Label)**

- カロリー: +250.8 kcal (+39.0%)
- タンパク質: +9.3g (+30.0%)
- 脂質: +16.1g (+61.2%)
- 炭水化物: +13.0g (+16.2%)

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

合計: 567 kcal, P: 55.2g, F: 11.6g, C: 59.5g

**差分 (Pipeline - Label)**

- カロリー: -182.1 kcal (-24.3%)
- タンパク質: +9.4g (+20.5%)
- 脂質: -15.3g (-56.9%)
- 炭水化物: -21.5g (-26.5%)

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

合計: 733 kcal, P: 45.1g, F: 39.0g, C: 51.0g

**差分 (Pipeline - Label)**

- カロリー: +245.9 kcal (+50.4%)
- タンパク質: +19.2g (+74.1%)
- 脂質: +14.9g (+61.8%)
- 炭水化物: +5.0g (+10.9%)

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

合計: 938 kcal, P: 59.9g, F: 45.0g, C: 70.3g

**差分 (Pipeline - Label)**

- カロリー: +83.0 kcal (+9.7%)
- タンパク質: +1.9g (+3.3%)
- 脂質: +2.4g (+5.6%)
- 炭水化物: +8.2g (+13.2%)

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

合計: 893 kcal, P: 35.9g, F: 42.9g, C: 89.6g

**差分 (Pipeline - Label)**

- カロリー: +147.2 kcal (+19.7%)
- タンパク質: +10.2g (+39.7%)
- 脂質: +8.2g (+23.6%)
- 炭水化物: +4.2g (+4.9%)

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

合計: 572 kcal, P: 26.6g, F: 22.0g, C: 68.1g

**差分 (Pipeline - Label)**

- カロリー: -10.0 kcal (-1.7%)
- タンパク質: -17.0g (-39.0%)
- 脂質: +7.2g (+48.6%)
- 炭水化物: -2.7g (-3.8%)

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

合計: 575 kcal, P: 56.8g, F: 11.4g, C: 59.7g

**差分 (Pipeline - Label)**

- カロリー: -23.8 kcal (-4.0%)
- タンパク質: +4.7g (+9.0%)
- 脂質: -4.8g (-29.6%)
- 炭水化物: -0.8g (-1.3%)

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

合計: 819 kcal, P: 61.8g, F: 22.5g, C: 65.8g

**差分 (Pipeline - Label)**

- カロリー: +134.6 kcal (+19.7%)
- タンパク質: -2.1g (-3.3%)
- 脂質: -1.3g (-5.5%)
- 炭水化物: +8.2g (+14.2%)

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

合計: 677 kcal, P: 51.0g, F: 31.7g, C: 47.0g

**差分 (Pipeline - Label)**

- カロリー: +157.8 kcal (+30.4%)
- タンパク質: +18.4g (+56.4%)
- 脂質: +6.9g (+27.8%)
- 炭水化物: +2.0g (+4.4%)

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

合計: 1000 kcal, P: 65.1g, F: 52.6g, C: 63.9g

**差分 (Pipeline - Label)**

- カロリー: +274.2 kcal (+37.8%)
- タンパク質: +18.6g (+40.0%)
- 脂質: +10.9g (+26.1%)
- 炭水化物: +20.9g (+48.6%)

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

合計: 569 kcal, P: 20.4g, F: 0.6g, C: 120.4g

**差分 (Pipeline - Label)**

- カロリー: -76.6 kcal (-11.9%)
- タンパク質: -11.0g (-35.0%)
- 脂質: -27.6g (-97.9%)
- 炭水化物: +50.6g (+72.5%)

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

合計: 698 kcal, P: 29.7g, F: 30.9g, C: 74.9g

**差分 (Pipeline - Label)**

- カロリー: -7.8 kcal (-1.1%)
- タンパク質: +5.2g (+21.2%)
- 脂質: -10.0g (-24.4%)
- 炭水化物: +10.3g (+15.9%)

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

合計: 366 kcal, P: 35.9g, F: 18.4g, C: 14.6g

**差分 (Pipeline - Label)**

- カロリー: -4.9 kcal (-1.3%)
- タンパク質: -11.2g (-23.8%)
- 脂質: +5.7g (+44.9%)
- 炭水化物: -1.0g (-6.4%)

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

合計: 780 kcal, P: 32.7g, F: 45.4g, C: 64.5g

**差分 (Pipeline - Label)**

- カロリー: +32.0 kcal (+4.3%)
- タンパク質: +5.1g (+18.5%)
- 脂質: +2.2g (+5.1%)
- 炭水化物: +2.9g (+4.7%)

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

合計: 551 kcal, P: 20.0g, F: 29.2g, C: 51.3g

**差分 (Pipeline - Label)**

- カロリー: -235.4 kcal (-29.9%)
- タンパク質: -12.2g (-37.9%)
- 脂質: -7.7g (-20.9%)
- 炭水化物: -29.1g (-36.2%)

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

合計: 642 kcal, P: 51.0g, F: 17.2g, C: 68.7g

**差分 (Pipeline - Label)**

- カロリー: -426.8 kcal (-39.9%)
- タンパク質: +0.2g (+0.4%)
- 脂質: -37.1g (-68.3%)
- 炭水化物: -16.8g (-19.6%)

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

合計: 917 kcal, P: 39.1g, F: 38.1g, C: 104.6g

**差分 (Pipeline - Label)**

- カロリー: -26.8 kcal (-2.8%)
- タンパク質: +3.1g (+8.6%)
- 脂質: -2.4g (-5.9%)
- 炭水化物: -3.0g (-2.8%)

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

合計: 764 kcal, P: 29.2g, F: 40.1g, C: 77.4g

**差分 (Pipeline - Label)**

- カロリー: -5.2 kcal (-0.7%)
- タンパク質: -33.5g (-53.4%)
- 脂質: +11.8g (+41.7%)
- 炭水化物: +7.2g (+10.3%)

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

合計: 931 kcal, P: 44.0g, F: 59.3g, C: 55.0g

**差分 (Pipeline - Label)**

- カロリー: -69.2 kcal (-6.9%)
- タンパク質: -12.7g (-22.4%)
- 脂質: -1.1g (-1.8%)
- 炭水化物: -13.7g (-19.9%)

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

合計: 921 kcal, P: 57.2g, F: 21.0g, C: 123.7g

**差分 (Pipeline - Label)**

- カロリー: +207.0 kcal (+29.0%)
- タンパク質: +15.7g (+37.8%)
- 脂質: -18.3g (-46.6%)
- 炭水化物: +67.5g (+120.1%)

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

合計: 277 kcal, P: 30.3g, F: 12.4g, C: 45.1g

**差分 (Pipeline - Label)**

- カロリー: -332.0 kcal (-54.6%)
- タンパク質: -10.6g (-25.9%)
- 脂質: -17.5g (-58.5%)
- 炭水化物: -0.9g (-2.0%)

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

合計: 691 kcal, P: 46.5g, F: 42.1g, C: 32.8g

**差分 (Pipeline - Label)**

- カロリー: +14.0 kcal (+2.1%)
- タンパク質: +14.3g (+44.4%)
- 脂質: +9.9g (+30.7%)
- 炭水化物: -33.3g (-50.4%)

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

合計: 591 kcal, P: 45.2g, F: 16.4g, C: 62.9g

**差分 (Pipeline - Label)**

- カロリー: +19.7 kcal (+3.4%)
- タンパク質: +13.7g (+43.5%)
- 脂質: -9.8g (-37.4%)
- 炭水化物: +14.2g (+29.2%)

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

合計: 612 kcal, P: 36.5g, F: 28.8g, C: 51.2g

**差分 (Pipeline - Label)**

- カロリー: -60.8 kcal (-9.0%)
- タンパク質: +6.4g (+21.3%)
- 脂質: -7.7g (-21.1%)
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

合計: 964 kcal, P: 74.7g, F: 21.1g, C: 113.7g

**差分 (Pipeline - Label)**

- カロリー: +108.2 kcal (+12.6%)
- タンパク質: +26.8g (+55.9%)
- 脂質: -19.4g (-47.9%)
- 炭水化物: +28.2g (+33.0%)

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

合計: 698 kcal, P: 89.5g, F: 12.1g, C: 56.2g

**差分 (Pipeline - Label)**

- カロリー: +90.8 kcal (+15.0%)
- タンパク質: +52.8g (+143.9%)
- 脂質: -16.4g (-57.5%)
- 炭水化物: +6.7g (+13.5%)

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

合計: 1735 kcal, P: 67.1g, F: 139.1g, C: 50.1g

**差分 (Pipeline - Label)**

- カロリー: +754.3 kcal (+76.9%)
- タンパク質: +27.6g (+69.9%)
- 脂質: +79.3g (+132.6%)
- 炭水化物: -24.1g (-32.5%)

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

合計: 414 kcal, P: 26.4g, F: 23.5g, C: 25.1g

**差分 (Pipeline - Label)**

- カロリー: -266.9 kcal (-39.2%)
- タンパク質: -8.2g (-23.7%)
- 脂質: -17.6g (-42.8%)
- 炭水化物: -20.6g (-45.1%)

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

合計: 385 kcal, P: 23.6g, F: 20.1g, C: 30.1g

**差分 (Pipeline - Label)**

- カロリー: -311.4 kcal (-44.7%)
- タンパク質: -1.9g (-7.5%)
- 脂質: -12.2g (-37.8%)
- 炭水化物: -52.2g (-63.4%)

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

合計: 667 kcal, P: 60.5g, F: 21.2g, C: 60.5g

**差分 (Pipeline - Label)**

- カロリー: -34.6 kcal (-4.9%)
- タンパク質: +7.5g (+14.2%)
- 脂質: -15.1g (-41.6%)
- 炭水化物: +14.1g (+30.4%)

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

合計: 885 kcal, P: 41.6g, F: 33.1g, C: 105.9g

**差分 (Pipeline - Label)**

- カロリー: -89.2 kcal (-9.2%)
- タンパク質: +4.9g (+13.4%)
- 脂質: -16.0g (-32.6%)
- 炭水化物: +9.1g (+9.4%)

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

合計: 1105 kcal, P: 73.3g, F: 51.1g, C: 82.1g

**差分 (Pipeline - Label)**

- カロリー: +422.3 kcal (+61.9%)
- タンパク質: +23.1g (+46.0%)
- 脂質: +17.3g (+51.2%)
- 炭水化物: +38.2g (+87.0%)

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

合計: 892 kcal, P: 74.1g, F: 25.5g, C: 88.8g

**差分 (Pipeline - Label)**

- カロリー: +106.1 kcal (+13.5%)
- タンパク質: +24.7g (+50.0%)
- 脂質: -6.3g (-19.8%)
- 炭水化物: +5.1g (+6.1%)

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

合計: 639 kcal, P: 60.7g, F: 15.8g, C: 62.6g

**差分 (Pipeline - Label)**

- カロリー: +73.1 kcal (+12.9%)
- タンパク質: +6.3g (+11.6%)
- 脂質: -4.9g (-23.7%)
- 炭水化物: +21.0g (+50.5%)

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

合計: 547 kcal, P: 21.3g, F: 3.5g, C: 110.8g

**差分 (Pipeline - Label)**

- カロリー: +28.8 kcal (+5.6%)
- タンパク質: -0.6g (-2.7%)
- 脂質: -14.3g (-80.3%)
- 炭水化物: +35.6g (+47.3%)

---

### test_food45.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | prosciutto and mozzarella sandwich | 220g | 550 | 26.4g | 24.2g | 57.2g |
| main_food | potato chips | 45g | 241 | 3.1g | 15.8g | 22.9g |
| **合計** | - | - | **791** | **29.5g** | **40.0g** | **80.1g** |

**Pipeline栄養素**

合計: 522 kcal, P: 31.0g, F: 16.7g, C: 63.0g

**差分 (Pipeline - Label)**

- カロリー: -269.7 kcal (-34.1%)
- タンパク質: +1.5g (+5.1%)
- 脂質: -23.3g (-58.2%)
- 炭水化物: -17.1g (-21.3%)

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

合計: 614 kcal, P: 17.7g, F: 35.0g, C: 58.1g

**差分 (Pipeline - Label)**

- カロリー: -62.6 kcal (-9.3%)
- タンパク質: -13.5g (-43.3%)
- 脂質: +5.5g (+18.6%)
- 炭水化物: -16.8g (-22.4%)

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

合計: 836 kcal, P: 34.8g, F: 35.2g, C: 96.7g

**差分 (Pipeline - Label)**

- カロリー: +53.8 kcal (+6.9%)
- タンパク質: -1.7g (-4.7%)
- 脂質: +1.0g (+2.9%)
- 炭水化物: +9.9g (+11.4%)

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

合計: 616 kcal, P: 26.8g, F: 23.6g, C: 74.1g

**差分 (Pipeline - Label)**

- カロリー: +70.2 kcal (+12.9%)
- タンパク質: +4.0g (+17.5%)
- 脂質: +6.6g (+38.8%)
- 炭水化物: +2.3g (+3.2%)

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

合計: 501 kcal, P: 58.6g, F: 11.3g, C: 42.3g

**差分 (Pipeline - Label)**

- カロリー: -28.9 kcal (-5.5%)
- タンパク質: +7.8g (+15.4%)
- 脂質: -6.8g (-37.6%)
- 炭水化物: +0.7g (+1.7%)

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

合計: 727 kcal, P: 31.5g, F: 31.8g, C: 82.4g

**差分 (Pipeline - Label)**

- カロリー: -6.2 kcal (-0.8%)
- タンパク質: +2.6g (+9.0%)
- 脂質: -8.9g (-21.9%)
- 炭水化物: +13.2g (+19.1%)

---

### test_food6.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | cream of chicken soup with vegetables | 400g | 280 | 18.0g | 14.0g | 24.0g |
| main_food | dinner roll | 80g | 224 | 7.2g | 3.6g | 41.6g |
| **合計** | - | - | **504** | **25.2g** | **17.6g** | **65.6g** |

**Pipeline栄養素**

合計: 935 kcal, P: 36.0g, F: 42.4g, C: 106.1g

**差分 (Pipeline - Label)**

- カロリー: +431.3 kcal (+85.6%)
- タンパク質: +10.8g (+42.9%)
- 脂質: +24.8g (+140.9%)
- 炭水化物: +40.5g (+61.7%)

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

合計: 654 kcal, P: 66.3g, F: 30.6g, C: 24.6g

**差分 (Pipeline - Label)**

- カロリー: -67.8 kcal (-9.4%)
- タンパク質: +15.4g (+30.3%)
- 脂質: -13.8g (-31.1%)
- 炭水化物: -9.5g (-27.9%)

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

合計: 799 kcal, P: 39.5g, F: 31.1g, C: 90.4g

**差分 (Pipeline - Label)**

- カロリー: +165.7 kcal (+26.2%)
- タンパク質: -1.3g (-3.2%)
- 脂質: +13.9g (+80.8%)
- 炭水化物: +5.9g (+7.0%)

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

合計: 850 kcal, P: 58.9g, F: 37.1g, C: 71.8g

**差分 (Pipeline - Label)**

- カロリー: +78.8 kcal (+10.2%)
- タンパク質: +12.7g (+27.5%)
- 脂質: -12.1g (-24.6%)
- 炭水化物: +26.3g (+57.8%)

---
