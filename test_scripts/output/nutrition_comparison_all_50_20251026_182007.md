# Pipeline vs VLM Label 栄養素比較レポート

生成日時: 2025-10-26 18:20:07

対象画像数: 50

## サマリー

### 平均差分（Pipeline - Label）

| 栄養素 | 平均差分 (%) |
|--------|--------------|
| カロリー | +11.6% |
| タンパク質 | +27.4% |
| 脂質 | +7.3% |
| 炭水化物 | +9.4% |

## 詳細比較表

| 画像 | Label Cal | Pipeline Cal | 差分 | Label P | Pipeline P | 差分 | Label F | Pipeline F | 差分 | Label C | Pipeline C | 差分 |
|------|-----------|--------------|------|---------|------------|------|---------|------------|------|---------|------------|------|
| test_food1.jpg | 891 | 834 | -6.4% | 58.9 | 69.8 | +18.5% | 53.8 | 40.9 | -24.0% | 50.9 | 44.4 | -12.8% |
| test_food10.jpg | 854 | 1043 | +22.1% | 59.5 | 94.8 | +59.3% | 48.1 | 51.6 | +7.3% | 53.4 | 46.9 | -12.2% |
| test_food11.jpg | 499 | 663 | +32.9% | 27.4 | 36.1 | +31.8% | 27.4 | 22.9 | -16.4% | 40.2 | 79.0 | +96.5% |
| test_food12.jpg | 441 | 374 | -15.2% | 24.6 | 29.2 | +18.7% | 28.0 | 22.1 | -21.1% | 25.6 | 17.9 | -30.1% |
| test_food13.jpg | 643 | 678 | +5.5% | 31.0 | 27.3 | -11.9% | 26.3 | 34.4 | +30.8% | 80.0 | 84.4 | +5.5% |
| test_food14.jpg | 749 | 704 | -6.0% | 45.8 | 61.7 | +34.7% | 26.9 | 18.4 | -31.6% | 81.0 | 68.7 | -15.2% |
| test_food15.jpg | 488 | 473 | -2.9% | 25.9 | 27.3 | +5.4% | 24.1 | 22.2 | -7.9% | 46.0 | 44.2 | -3.9% |
| test_food16.jpg | 855 | 1047 | +22.5% | 58.0 | 67.3 | +16.0% | 42.6 | 56.3 | +32.2% | 62.1 | 69.0 | +11.1% |
| test_food17.jpg | 746 | 830 | +11.4% | 25.7 | 29.8 | +16.0% | 34.7 | 46.8 | +34.9% | 85.4 | 74.5 | -12.8% |
| test_food18.jpg | 582 | 721 | +23.9% | 43.6 | 35.1 | -19.5% | 14.8 | 30.2 | +104.1% | 70.8 | 76.9 | +8.6% |
| test_food19.jpg | 599 | 628 | +4.9% | 52.1 | 39.5 | -24.2% | 16.2 | 23.6 | +45.7% | 60.5 | 70.1 | +15.9% |
| test_food2.jpg | 684 | 806 | +17.7% | 63.9 | 64.5 | +0.9% | 23.8 | 34.8 | +46.2% | 57.6 | 55.6 | -3.5% |
| test_food20.jpg | 519 | 668 | +28.6% | 32.6 | 34.4 | +5.5% | 24.8 | 34.8 | +40.3% | 45.0 | 56.1 | +24.7% |
| test_food21.jpg | 725 | 1116 | +53.9% | 46.5 | 66.7 | +43.4% | 41.7 | 67.2 | +61.2% | 43.0 | 60.8 | +41.4% |
| test_food22.jpg | 646 | 567 | -12.2% | 31.4 | 20.1 | -36.0% | 28.2 | 0.6 | -97.9% | 69.8 | 119.3 | +70.9% |
| test_food23.jpg | 706 | 789 | +11.7% | 24.5 | 33.6 | +37.1% | 40.9 | 34.6 | -15.4% | 64.6 | 88.0 | +36.2% |
| test_food24.jpg | 370 | 319 | -14.0% | 47.1 | 45.8 | -2.8% | 12.7 | 13.6 | +7.1% | 15.6 | 6.1 | -60.9% |
| test_food25.jpg | 748 | 921 | +23.1% | 27.6 | 36.1 | +30.8% | 43.2 | 54.5 | +26.2% | 61.6 | 75.6 | +22.7% |
| test_food26.jpg | 786 | 804 | +2.3% | 32.2 | 29.7 | -7.8% | 36.9 | 42.3 | +14.6% | 80.4 | 75.2 | -6.5% |
| test_food27.jpg | 1069 | 850 | -20.5% | 50.8 | 64.6 | +27.2% | 54.3 | 31.9 | -41.3% | 85.5 | 76.4 | -10.6% |
| test_food28.jpg | 944 | 901 | -4.5% | 36.0 | 35.9 | -0.3% | 40.5 | 33.3 | -17.8% | 107.6 | 114.7 | +6.6% |
| test_food29.jpg | 769 | 529 | -31.2% | 62.7 | 29.2 | -53.4% | 28.3 | 10.5 | -62.9% | 70.2 | 77.8 | +10.8% |
| test_food3.jpg | 1000 | 1051 | +5.0% | 56.7 | 53.1 | -6.3% | 60.4 | 69.8 | +15.6% | 68.7 | 51.8 | -24.6% |
| test_food30.jpg | 714 | 667 | -6.5% | 41.5 | 54.3 | +30.8% | 39.3 | 19.3 | -50.9% | 56.2 | 64.4 | +14.6% |
| test_food31.jpg | 609 | 471 | -22.6% | 40.9 | 57.5 | +40.6% | 29.9 | 10.8 | -63.9% | 46.0 | 33.0 | -28.3% |
| test_food32.jpg | 677 | 745 | +10.0% | 32.2 | 50.1 | +55.6% | 32.2 | 44.8 | +39.1% | 66.1 | 33.9 | -48.7% |
| test_food33.jpg | 572 | 698 | +22.2% | 31.5 | 75.7 | +140.3% | 26.2 | 23.1 | -11.8% | 48.7 | 41.6 | -14.6% |
| test_food34.jpg | 672 | 568 | -15.6% | 30.1 | 47.3 | +57.1% | 36.5 | 24.4 | -33.2% | 57.3 | 37.3 | -34.9% |
| test_food35.jpg | 856 | 1268 | +48.2% | 47.9 | 64.9 | +35.5% | 40.5 | 67.0 | +65.4% | 85.5 | 106.5 | +24.6% |
| test_food36.jpg | 607 | 698 | +14.9% | 36.7 | 69.8 | +90.2% | 28.5 | 25.6 | -10.2% | 49.5 | 45.1 | -8.9% |
| test_food37.jpg | 980 | 856 | -12.6% | 39.5 | 80.0 | +102.5% | 59.8 | 25.4 | -57.5% | 74.2 | 72.1 | -2.8% |
| test_food38.jpg | 681 | 575 | -15.6% | 34.6 | 15.2 | -56.1% | 41.1 | 23.6 | -42.6% | 45.7 | 79.5 | +74.0% |
| test_food39.jpg | 696 | 551 | -20.8% | 25.5 | 18.7 | -26.7% | 32.3 | 4.5 | -86.1% | 82.3 | 107.7 | +30.9% |
| test_food4.jpg | 702 | 839 | +19.6% | 53.0 | 74.4 | +40.4% | 36.3 | 33.3 | -8.3% | 46.4 | 55.9 | +20.5% |
| test_food40.jpg | 974 | 975 | +0.1% | 36.7 | 127.4 | +247.1% | 49.1 | 43.5 | -11.4% | 96.8 | 11.2 | -88.4% |
| test_food41.jpg | 682 | 780 | +14.3% | 50.2 | 57.6 | +14.7% | 33.8 | 31.1 | -8.0% | 43.9 | 67.8 | +54.4% |
| test_food42.jpg | 786 | 698 | -11.1% | 49.4 | 46.5 | -5.9% | 31.8 | 20.8 | -34.6% | 83.7 | 78.5 | -6.2% |
| test_food43.jpg | 566 | 881 | +55.7% | 54.4 | 74.8 | +37.5% | 20.7 | 36.5 | +76.3% | 41.6 | 62.6 | +50.5% |
| test_food44.jpg | 518 | 1034 | +99.4% | 21.9 | 41.9 | +91.3% | 17.8 | 47.7 | +168.0% | 75.2 | 118.6 | +57.7% |
| test_food45.jpg | 791 | 833 | +5.2% | 29.5 | 35.9 | +21.7% | 40.0 | 35.8 | -10.5% | 80.1 | 94.9 | +18.5% |
| test_food46.jpg | 677 | 715 | +5.6% | 31.2 | 53.9 | +72.8% | 29.5 | 33.0 | +11.9% | 74.9 | 50.9 | -32.0% |
| test_food47.jpg | 783 | 867 | +10.8% | 36.5 | 45.0 | +23.3% | 34.2 | 43.3 | +26.6% | 86.8 | 73.6 | -15.2% |
| test_food48.jpg | 546 | 695 | +27.3% | 22.8 | 29.0 | +27.2% | 17.0 | 25.2 | +48.2% | 71.8 | 86.5 | +20.5% |
| test_food49.jpg | 602 | 798 | +32.4% | 24.3 | 31.4 | +29.2% | 23.6 | 30.5 | +29.2% | 73.5 | 99.7 | +35.6% |
| test_food5.jpg | 530 | 588 | +11.0% | 50.8 | 66.6 | +31.1% | 18.1 | 12.3 | -32.0% | 41.6 | 50.4 | +21.2% |
| test_food50.jpg | 733 | 944 | +28.8% | 28.9 | 36.7 | +27.0% | 40.7 | 40.9 | +0.5% | 69.2 | 110.5 | +59.7% |
| test_food6.jpg | 504 | 987 | +95.8% | 25.2 | 30.0 | +19.0% | 17.6 | 51.1 | +190.3% | 65.6 | 103.7 | +58.1% |
| test_food7.jpg | 722 | 763 | +5.6% | 50.9 | 67.0 | +31.6% | 44.4 | 36.1 | -18.7% | 34.1 | 39.3 | +15.2% |
| test_food8.jpg | 634 | 742 | +17.2% | 40.8 | 36.8 | -9.8% | 17.2 | 31.5 | +83.1% | 84.5 | 81.2 | -3.9% |
| test_food9.jpg | 771 | 823 | +6.7% | 46.2 | 55.3 | +19.7% | 49.2 | 38.6 | -21.5% | 45.5 | 64.3 | +41.3% |

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

合計: 834 kcal, P: 69.8g, F: 40.9g, C: 44.4g

**差分 (Pipeline - Label)**

- カロリー: -57.4 kcal (-6.4%)
- タンパク質: +10.9g (+18.5%)
- 脂質: -12.9g (-24.0%)
- 炭水化物: -6.5g (-12.8%)

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

合計: 1043 kcal, P: 94.8g, F: 51.6g, C: 46.9g

**差分 (Pipeline - Label)**

- カロリー: +189.0 kcal (+22.1%)
- タンパク質: +35.3g (+59.3%)
- 脂質: +3.5g (+7.3%)
- 炭水化物: -6.5g (-12.2%)

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

合計: 663 kcal, P: 36.1g, F: 22.9g, C: 79.0g

**差分 (Pipeline - Label)**

- カロリー: +164.2 kcal (+32.9%)
- タンパク質: +8.7g (+31.8%)
- 脂質: -4.5g (-16.4%)
- 炭水化物: +38.8g (+96.5%)

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

合計: 374 kcal, P: 29.2g, F: 22.1g, C: 17.9g

**差分 (Pipeline - Label)**

- カロリー: -67.1 kcal (-15.2%)
- タンパク質: +4.6g (+18.7%)
- 脂質: -5.9g (-21.1%)
- 炭水化物: -7.7g (-30.1%)

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

合計: 678 kcal, P: 27.3g, F: 34.4g, C: 84.4g

**差分 (Pipeline - Label)**

- カロリー: +35.2 kcal (+5.5%)
- タンパク質: -3.7g (-11.9%)
- 脂質: +8.1g (+30.8%)
- 炭水化物: +4.4g (+5.5%)

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

合計: 704 kcal, P: 61.7g, F: 18.4g, C: 68.7g

**差分 (Pipeline - Label)**

- カロリー: -44.9 kcal (-6.0%)
- タンパク質: +15.9g (+34.7%)
- 脂質: -8.5g (-31.6%)
- 炭水化物: -12.3g (-15.2%)

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

合計: 473 kcal, P: 27.3g, F: 22.2g, C: 44.2g

**差分 (Pipeline - Label)**

- カロリー: -14.2 kcal (-2.9%)
- タンパク質: +1.4g (+5.4%)
- 脂質: -1.9g (-7.9%)
- 炭水化物: -1.8g (-3.9%)

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

合計: 1047 kcal, P: 67.3g, F: 56.3g, C: 69.0g

**差分 (Pipeline - Label)**

- カロリー: +192.1 kcal (+22.5%)
- タンパク質: +9.3g (+16.0%)
- 脂質: +13.7g (+32.2%)
- 炭水化物: +6.9g (+11.1%)

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

合計: 830 kcal, P: 29.8g, F: 46.8g, C: 74.5g

**差分 (Pipeline - Label)**

- カロリー: +85.0 kcal (+11.4%)
- タンパク質: +4.1g (+16.0%)
- 脂質: +12.1g (+34.9%)
- 炭水化物: -10.9g (-12.8%)

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

合計: 721 kcal, P: 35.1g, F: 30.2g, C: 76.9g

**差分 (Pipeline - Label)**

- カロリー: +138.9 kcal (+23.9%)
- タンパク質: -8.5g (-19.5%)
- 脂質: +15.4g (+104.1%)
- 炭水化物: +6.1g (+8.6%)

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

合計: 628 kcal, P: 39.5g, F: 23.6g, C: 70.1g

**差分 (Pipeline - Label)**

- カロリー: +29.5 kcal (+4.9%)
- タンパク質: -12.6g (-24.2%)
- 脂質: +7.4g (+45.7%)
- 炭水化物: +9.6g (+15.9%)

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

合計: 806 kcal, P: 64.5g, F: 34.8g, C: 55.6g

**差分 (Pipeline - Label)**

- カロリー: +121.4 kcal (+17.7%)
- タンパク質: +0.6g (+0.9%)
- 脂質: +11.0g (+46.2%)
- 炭水化物: -2.0g (-3.5%)

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

合計: 668 kcal, P: 34.4g, F: 34.8g, C: 56.1g

**差分 (Pipeline - Label)**

- カロリー: +148.5 kcal (+28.6%)
- タンパク質: +1.8g (+5.5%)
- 脂質: +10.0g (+40.3%)
- 炭水化物: +11.1g (+24.7%)

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

合計: 1116 kcal, P: 66.7g, F: 67.2g, C: 60.8g

**差分 (Pipeline - Label)**

- カロリー: +391.0 kcal (+53.9%)
- タンパク質: +20.2g (+43.4%)
- 脂質: +25.5g (+61.2%)
- 炭水化物: +17.8g (+41.4%)

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

合計: 567 kcal, P: 20.1g, F: 0.6g, C: 119.3g

**差分 (Pipeline - Label)**

- カロリー: -78.7 kcal (-12.2%)
- タンパク質: -11.3g (-36.0%)
- 脂質: -27.6g (-97.9%)
- 炭水化物: +49.5g (+70.9%)

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

合計: 789 kcal, P: 33.6g, F: 34.6g, C: 88.0g

**差分 (Pipeline - Label)**

- カロリー: +82.7 kcal (+11.7%)
- タンパク質: +9.1g (+37.1%)
- 脂質: -6.3g (-15.4%)
- 炭水化物: +23.4g (+36.2%)

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

合計: 921 kcal, P: 36.1g, F: 54.5g, C: 75.6g

**差分 (Pipeline - Label)**

- カロリー: +173.1 kcal (+23.1%)
- タンパク質: +8.5g (+30.8%)
- 脂質: +11.3g (+26.2%)
- 炭水化物: +14.0g (+22.7%)

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

合計: 804 kcal, P: 29.7g, F: 42.3g, C: 75.2g

**差分 (Pipeline - Label)**

- カロリー: +17.9 kcal (+2.3%)
- タンパク質: -2.5g (-7.8%)
- 脂質: +5.4g (+14.6%)
- 炭水化物: -5.2g (-6.5%)

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

合計: 850 kcal, P: 64.6g, F: 31.9g, C: 76.4g

**差分 (Pipeline - Label)**

- カロリー: -219.5 kcal (-20.5%)
- タンパク質: +13.8g (+27.2%)
- 脂質: -22.4g (-41.3%)
- 炭水化物: -9.1g (-10.6%)

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

合計: 901 kcal, P: 35.9g, F: 33.3g, C: 114.7g

**差分 (Pipeline - Label)**

- カロリー: -42.9 kcal (-4.5%)
- タンパク質: -0.1g (-0.3%)
- 脂質: -7.2g (-17.8%)
- 炭水化物: +7.1g (+6.6%)

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

合計: 529 kcal, P: 29.2g, F: 10.5g, C: 77.8g

**差分 (Pipeline - Label)**

- カロリー: -240.0 kcal (-31.2%)
- タンパク質: -33.5g (-53.4%)
- 脂質: -17.8g (-62.9%)
- 炭水化物: +7.6g (+10.8%)

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

合計: 1051 kcal, P: 53.1g, F: 69.8g, C: 51.8g

**差分 (Pipeline - Label)**

- カロリー: +50.1 kcal (+5.0%)
- タンパク質: -3.6g (-6.3%)
- 脂質: +9.4g (+15.6%)
- 炭水化物: -16.9g (-24.6%)

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

合計: 667 kcal, P: 54.3g, F: 19.3g, C: 64.4g

**差分 (Pipeline - Label)**

- カロリー: -46.5 kcal (-6.5%)
- タンパク質: +12.8g (+30.8%)
- 脂質: -20.0g (-50.9%)
- 炭水化物: +8.2g (+14.6%)

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

合計: 471 kcal, P: 57.5g, F: 10.8g, C: 33.0g

**差分 (Pipeline - Label)**

- カロリー: -137.8 kcal (-22.6%)
- タンパク質: +16.6g (+40.6%)
- 脂質: -19.1g (-63.9%)
- 炭水化物: -13.0g (-28.3%)

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

合計: 745 kcal, P: 50.1g, F: 44.8g, C: 33.9g

**差分 (Pipeline - Label)**

- カロリー: +67.8 kcal (+10.0%)
- タンパク質: +17.9g (+55.6%)
- 脂質: +12.6g (+39.1%)
- 炭水化物: -32.2g (-48.7%)

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

合計: 698 kcal, P: 75.7g, F: 23.1g, C: 41.6g

**差分 (Pipeline - Label)**

- カロリー: +126.7 kcal (+22.2%)
- タンパク質: +44.2g (+140.3%)
- 脂質: -3.1g (-11.8%)
- 炭水化物: -7.1g (-14.6%)

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

合計: 568 kcal, P: 47.3g, F: 24.4g, C: 37.3g

**差分 (Pipeline - Label)**

- カロリー: -104.7 kcal (-15.6%)
- タンパク質: +17.2g (+57.1%)
- 脂質: -12.1g (-33.2%)
- 炭水化物: -20.0g (-34.9%)

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

合計: 1268 kcal, P: 64.9g, F: 67.0g, C: 106.5g

**差分 (Pipeline - Label)**

- カロリー: +412.3 kcal (+48.2%)
- タンパク質: +17.0g (+35.5%)
- 脂質: +26.5g (+65.4%)
- 炭水化物: +21.0g (+24.6%)

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

合計: 698 kcal, P: 69.8g, F: 25.6g, C: 45.1g

**差分 (Pipeline - Label)**

- カロリー: +90.5 kcal (+14.9%)
- タンパク質: +33.1g (+90.2%)
- 脂質: -2.9g (-10.2%)
- 炭水化物: -4.4g (-8.9%)

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

合計: 856 kcal, P: 80.0g, F: 25.4g, C: 72.1g

**差分 (Pipeline - Label)**

- カロリー: -123.9 kcal (-12.6%)
- タンパク質: +40.5g (+102.5%)
- 脂質: -34.4g (-57.5%)
- 炭水化物: -2.1g (-2.8%)

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

合計: 575 kcal, P: 15.2g, F: 23.6g, C: 79.5g

**差分 (Pipeline - Label)**

- カロリー: -106.3 kcal (-15.6%)
- タンパク質: -19.4g (-56.1%)
- 脂質: -17.5g (-42.6%)
- 炭水化物: +33.8g (+74.0%)

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

合計: 551 kcal, P: 18.7g, F: 4.5g, C: 107.7g

**差分 (Pipeline - Label)**

- カロリー: -145.1 kcal (-20.8%)
- タンパク質: -6.8g (-26.7%)
- 脂質: -27.8g (-86.1%)
- 炭水化物: +25.4g (+30.9%)

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

合計: 839 kcal, P: 74.4g, F: 33.3g, C: 55.9g

**差分 (Pipeline - Label)**

- カロリー: +137.4 kcal (+19.6%)
- タンパク質: +21.4g (+40.4%)
- 脂質: -3.0g (-8.3%)
- 炭水化物: +9.5g (+20.5%)

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

合計: 975 kcal, P: 127.4g, F: 43.5g, C: 11.2g

**差分 (Pipeline - Label)**

- カロリー: +0.6 kcal (+0.1%)
- タンパク質: +90.7g (+247.1%)
- 脂質: -5.6g (-11.4%)
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

合計: 698 kcal, P: 46.5g, F: 20.8g, C: 78.5g

**差分 (Pipeline - Label)**

- カロリー: -87.1 kcal (-11.1%)
- タンパク質: -2.9g (-5.9%)
- 脂質: -11.0g (-34.6%)
- 炭水化物: -5.2g (-6.2%)

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

合計: 881 kcal, P: 74.8g, F: 36.5g, C: 62.6g

**差分 (Pipeline - Label)**

- カロリー: +315.0 kcal (+55.7%)
- タンパク質: +20.4g (+37.5%)
- 脂質: +15.8g (+76.3%)
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

合計: 1034 kcal, P: 41.9g, F: 47.7g, C: 118.6g

**差分 (Pipeline - Label)**

- カロリー: +515.1 kcal (+99.4%)
- タンパク質: +20.0g (+91.3%)
- 脂質: +29.9g (+168.0%)
- 炭水化物: +43.4g (+57.7%)

---

### test_food45.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | prosciutto and mozzarella sandwich | 220g | 550 | 26.4g | 24.2g | 57.2g |
| main_food | potato chips | 45g | 241 | 3.1g | 15.8g | 22.9g |
| **合計** | - | - | **791** | **29.5g** | **40.0g** | **80.1g** |

**Pipeline栄養素**

合計: 833 kcal, P: 35.9g, F: 35.8g, C: 94.9g

**差分 (Pipeline - Label)**

- カロリー: +41.4 kcal (+5.2%)
- タンパク質: +6.4g (+21.7%)
- 脂質: -4.2g (-10.5%)
- 炭水化物: +14.8g (+18.5%)

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

合計: 715 kcal, P: 53.9g, F: 33.0g, C: 50.9g

**差分 (Pipeline - Label)**

- カロリー: +37.9 kcal (+5.6%)
- タンパク質: +22.7g (+72.8%)
- 脂質: +3.5g (+11.9%)
- 炭水化物: -24.0g (-32.0%)

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

合計: 695 kcal, P: 29.0g, F: 25.2g, C: 86.5g

**差分 (Pipeline - Label)**

- カロリー: +148.8 kcal (+27.3%)
- タンパク質: +6.2g (+27.2%)
- 脂質: +8.2g (+48.2%)
- 炭水化物: +14.7g (+20.5%)

---

### test_food49.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | cheese pizza | 220g | 585 | 24.2g | 22.0g | 72.6g |
| extra | black olives | 15g | 17 | 0.1g | 1.6g | 0.9g |
| **合計** | - | - | **602** | **24.3g** | **23.6g** | **73.5g** |

**Pipeline栄養素**

合計: 798 kcal, P: 31.4g, F: 30.5g, C: 99.7g

**差分 (Pipeline - Label)**

- カロリー: +195.1 kcal (+32.4%)
- タンパク質: +7.1g (+29.2%)
- 脂質: +6.9g (+29.2%)
- 炭水化物: +26.2g (+35.6%)

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

合計: 588 kcal, P: 66.6g, F: 12.3g, C: 50.4g

**差分 (Pipeline - Label)**

- カロリー: +58.3 kcal (+11.0%)
- タンパク質: +15.8g (+31.1%)
- 脂質: -5.8g (-32.0%)
- 炭水化物: +8.8g (+21.2%)

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

合計: 944 kcal, P: 36.7g, F: 40.9g, C: 110.5g

**差分 (Pipeline - Label)**

- カロリー: +211.3 kcal (+28.8%)
- タンパク質: +7.8g (+27.0%)
- 脂質: +0.2g (+0.5%)
- 炭水化物: +41.3g (+59.7%)

---

### test_food6.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | cream of chicken soup with vegetables | 400g | 280 | 18.0g | 14.0g | 24.0g |
| main_food | dinner roll | 80g | 224 | 7.2g | 3.6g | 41.6g |
| **合計** | - | - | **504** | **25.2g** | **17.6g** | **65.6g** |

**Pipeline栄養素**

合計: 987 kcal, P: 30.0g, F: 51.1g, C: 103.7g

**差分 (Pipeline - Label)**

- カロリー: +483.0 kcal (+95.8%)
- タンパク質: +4.8g (+19.0%)
- 脂質: +33.5g (+190.3%)
- 炭水化物: +38.1g (+58.1%)

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

合計: 742 kcal, P: 36.8g, F: 31.5g, C: 81.2g

**差分 (Pipeline - Label)**

- カロリー: +108.7 kcal (+17.2%)
- タンパク質: -4.0g (-9.8%)
- 脂質: +14.3g (+83.1%)
- 炭水化物: -3.3g (-3.9%)

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

合計: 823 kcal, P: 55.3g, F: 38.6g, C: 64.3g

**差分 (Pipeline - Label)**

- カロリー: +51.3 kcal (+6.7%)
- タンパク質: +9.1g (+19.7%)
- 脂質: -10.6g (-21.5%)
- 炭水化物: +18.8g (+41.3%)

---
