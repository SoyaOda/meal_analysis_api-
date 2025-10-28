# Pipeline vs VLM Label 栄養素比較レポート

生成日時: 2025-10-26 17:51:45

対象画像数: 50

## サマリー

### 平均差分（Pipeline - Label）

| 栄養素 | 平均差分 (%) |
|--------|--------------|
| カロリー | +32.3% |
| タンパク質 | +51.1% |
| 脂質 | +17.9% |
| 炭水化物 | +36.0% |

## 詳細比較表

| 画像 | Label Cal | Pipeline Cal | 差分 | Label P | Pipeline P | 差分 | Label F | Pipeline F | 差分 | Label C | Pipeline C | 差分 |
|------|-----------|--------------|------|---------|------------|------|---------|------------|------|---------|------------|------|
| test_food1.jpg | 891 | 1366 | +53.3% | 58.9 | 107.6 | +82.7% | 53.8 | 71.0 | +32.0% | 50.9 | 69.8 | +37.1% |
| test_food10.jpg | 854 | 1437 | +68.2% | 59.5 | 98.9 | +66.2% | 48.1 | 66.4 | +38.0% | 53.4 | 107.3 | +100.9% |
| test_food11.jpg | 499 | 632 | +26.5% | 27.4 | 34.6 | +26.3% | 27.4 | 21.0 | -23.4% | 40.2 | 76.5 | +90.3% |
| test_food12.jpg | 441 | 453 | +2.6% | 24.6 | 26.5 | +7.7% | 28.0 | 30.1 | +7.5% | 25.6 | 20.4 | -20.3% |
| test_food13.jpg | 643 | 918 | +42.8% | 31.0 | 53.9 | +73.9% | 26.3 | 47.5 | +80.6% | 80.0 | 81.1 | +1.4% |
| test_food14.jpg | 749 | 772 | +3.0% | 45.8 | 80.6 | +76.0% | 26.9 | 20.7 | -23.0% | 81.0 | 59.9 | -26.0% |
| test_food15.jpg | 488 | 516 | +5.8% | 25.9 | 27.3 | +5.4% | 24.1 | 11.6 | -51.9% | 46.0 | 78.5 | +70.7% |
| test_food16.jpg | 855 | 1160 | +35.6% | 58.0 | 82.3 | +41.9% | 42.6 | 64.4 | +51.2% | 62.1 | 64.3 | +3.5% |
| test_food17.jpg | 746 | 959 | +28.6% | 25.7 | 33.4 | +30.0% | 34.7 | 48.3 | +39.2% | 85.4 | 97.3 | +13.9% |
| test_food18.jpg | 582 | 870 | +49.5% | 43.6 | 42.5 | -2.5% | 14.8 | 35.3 | +138.5% | 70.8 | 94.9 | +34.0% |
| test_food19.jpg | 599 | 917 | +53.2% | 52.1 | 54.6 | +4.8% | 16.2 | 37.3 | +130.2% | 60.5 | 95.3 | +57.5% |
| test_food2.jpg | 684 | 1028 | +50.2% | 63.9 | 85.5 | +33.8% | 23.8 | 43.2 | +81.5% | 57.6 | 69.3 | +20.3% |
| test_food20.jpg | 519 | 723 | +39.3% | 32.6 | 36.2 | +11.0% | 24.8 | 35.1 | +41.5% | 45.0 | 68.0 | +51.1% |
| test_food21.jpg | 725 | 858 | +18.3% | 46.5 | 50.6 | +8.8% | 41.7 | 51.6 | +23.7% | 43.0 | 47.3 | +10.0% |
| test_food22.jpg | 646 | 719 | +11.4% | 31.4 | 33.5 | +6.7% | 28.2 | 14.0 | -50.4% | 69.8 | 112.0 | +60.5% |
| test_food23.jpg | 706 | 879 | +24.5% | 24.5 | 36.5 | +49.0% | 40.9 | 39.4 | -3.7% | 64.6 | 96.9 | +50.0% |
| test_food24.jpg | 370 | 417 | +12.5% | 47.1 | 62.4 | +32.5% | 12.7 | 17.4 | +37.0% | 15.6 | 7.7 | -50.6% |
| test_food25.jpg | 748 | 847 | +13.2% | 27.6 | 37.1 | +34.4% | 43.2 | 50.7 | +17.4% | 61.6 | 61.2 | -0.6% |
| test_food26.jpg | 786 | 1159 | +47.4% | 32.2 | 42.3 | +31.4% | 36.9 | 59.4 | +61.0% | 80.4 | 111.8 | +39.1% |
| test_food27.jpg | 1069 | 889 | -16.9% | 50.8 | 67.8 | +33.5% | 54.3 | 32.2 | -40.7% | 85.5 | 82.2 | -3.9% |
| test_food28.jpg | 944 | 1351 | +43.1% | 36.0 | 51.9 | +44.2% | 40.5 | 55.1 | +36.0% | 107.6 | 161.5 | +50.1% |
| test_food29.jpg | 769 | 746 | -3.0% | 62.7 | 41.1 | -34.4% | 28.3 | 14.5 | -48.8% | 70.2 | 110.2 | +57.0% |
| test_food3.jpg | 1000 | 915 | -8.5% | 56.7 | 104.6 | +84.5% | 60.4 | 35.7 | -40.9% | 68.7 | 46.2 | -32.8% |
| test_food30.jpg | 714 | 945 | +32.4% | 41.5 | 74.4 | +79.3% | 39.3 | 27.5 | -30.0% | 56.2 | 93.3 | +66.0% |
| test_food31.jpg | 609 | 618 | +1.5% | 40.9 | 78.3 | +91.4% | 29.9 | 14.7 | -50.8% | 46.0 | 38.8 | -15.7% |
| test_food32.jpg | 677 | 917 | +35.4% | 32.2 | 57.3 | +78.0% | 32.2 | 56.8 | +76.4% | 66.1 | 42.5 | -35.7% |
| test_food33.jpg | 572 | 690 | +20.8% | 31.5 | 71.0 | +125.4% | 26.2 | 21.1 | -19.5% | 48.7 | 49.0 | +0.6% |
| test_food34.jpg | 672 | 682 | +1.4% | 30.1 | 63.2 | +110.0% | 36.5 | 30.3 | -17.0% | 57.3 | 35.3 | -38.4% |
| test_food35.jpg | 856 | 976 | +14.1% | 47.9 | 77.1 | +61.0% | 40.5 | 43.5 | +7.4% | 85.5 | 66.1 | -22.7% |
| test_food36.jpg | 607 | 699 | +15.1% | 36.7 | 71.4 | +94.6% | 28.5 | 23.4 | -17.9% | 49.5 | 45.7 | -7.7% |
| test_food37.jpg | 980 | 883 | -10.0% | 39.5 | 76.9 | +94.7% | 59.8 | 22.1 | -63.0% | 74.2 | 89.5 | +20.6% |
| test_food38.jpg | 681 | 586 | -13.9% | 34.6 | 16.6 | -52.0% | 41.1 | 28.4 | -30.9% | 45.7 | 85.9 | +88.0% |
| test_food39.jpg | 696 | 784 | +12.6% | 25.5 | 23.6 | -7.5% | 32.3 | 16.6 | -48.6% | 82.3 | 134.5 | +63.4% |
| test_food4.jpg | 702 | 1088 | +55.1% | 53.0 | 99.3 | +87.4% | 36.3 | 42.8 | +17.9% | 46.4 | 70.3 | +51.5% |
| test_food40.jpg | 974 | 773 | -20.7% | 36.7 | 94.1 | +156.4% | 49.1 | 35.6 | -27.5% | 96.8 | 14.8 | -84.7% |
| test_food41.jpg | 682 | 1070 | +56.8% | 50.2 | 77.9 | +55.2% | 33.8 | 42.9 | +26.9% | 43.9 | 89.0 | +102.7% |
| test_food42.jpg | 786 | 1259 | +60.2% | 49.4 | 68.3 | +38.3% | 31.8 | 35.6 | +11.9% | 83.7 | 161.1 | +92.5% |
| test_food43.jpg | 566 | 914 | +61.6% | 54.4 | 87.4 | +60.7% | 20.7 | 28.9 | +39.6% | 41.6 | 69.8 | +67.8% |
| test_food44.jpg | 518 | 1351 | +160.6% | 21.9 | 51.4 | +134.7% | 17.8 | 9.7 | -45.5% | 75.2 | 270.9 | +260.2% |
| test_food45.jpg | 791 | 887 | +12.1% | 29.5 | 51.9 | +75.9% | 40.0 | 29.0 | -27.5% | 80.1 | 106.8 | +33.3% |
| test_food46.jpg | 677 | 1138 | +68.2% | 31.2 | 80.6 | +158.3% | 29.5 | 37.7 | +27.8% | 74.9 | 118.8 | +58.6% |
| test_food47.jpg | 783 | 834 | +6.6% | 36.5 | 41.8 | +14.5% | 34.2 | 41.0 | +19.9% | 86.8 | 74.2 | -14.5% |
| test_food48.jpg | 546 | 891 | +63.2% | 22.8 | 32.8 | +43.9% | 17.0 | 25.3 | +48.8% | 71.8 | 131.6 | +83.3% |
| test_food49.jpg | 602 | 859 | +42.5% | 24.3 | 33.9 | +39.5% | 23.6 | 32.8 | +39.0% | 73.5 | 107.3 | +46.0% |
| test_food5.jpg | 530 | 1094 | +106.6% | 50.8 | 81.5 | +60.4% | 18.1 | 44.6 | +146.4% | 41.6 | 88.8 | +113.5% |
| test_food50.jpg | 733 | 1143 | +55.9% | 28.9 | 45.5 | +57.4% | 40.7 | 48.4 | +18.9% | 69.2 | 135.2 | +95.4% |
| test_food6.jpg | 504 | 840 | +66.7% | 25.2 | 30.2 | +19.8% | 17.6 | 38.2 | +117.0% | 65.6 | 95.9 | +46.2% |
| test_food7.jpg | 722 | 1011 | +40.0% | 50.9 | 91.3 | +79.4% | 44.4 | 48.4 | +9.0% | 34.1 | 47.8 | +40.2% |
| test_food8.jpg | 634 | 973 | +53.6% | 40.8 | 48.5 | +18.9% | 17.2 | 42.6 | +147.7% | 84.5 | 99.3 | +17.5% |
| test_food9.jpg | 771 | 906 | +17.5% | 46.2 | 60.4 | +30.7% | 49.2 | 41.8 | -15.0% | 45.5 | 72.9 | +60.2% |

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

合計: 1366 kcal, P: 107.6g, F: 71.0g, C: 69.8g

**差分 (Pipeline - Label)**

- カロリー: +474.8 kcal (+53.3%)
- タンパク質: +48.7g (+82.7%)
- 脂質: +17.2g (+32.0%)
- 炭水化物: +18.9g (+37.1%)

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

合計: 1437 kcal, P: 98.9g, F: 66.4g, C: 107.3g

**差分 (Pipeline - Label)**

- カロリー: +582.7 kcal (+68.2%)
- タンパク質: +39.4g (+66.2%)
- 脂質: +18.3g (+38.0%)
- 炭水化物: +53.9g (+100.9%)

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

合計: 632 kcal, P: 34.6g, F: 21.0g, C: 76.5g

**差分 (Pipeline - Label)**

- カロリー: +132.4 kcal (+26.5%)
- タンパク質: +7.2g (+26.3%)
- 脂質: -6.4g (-23.4%)
- 炭水化物: +36.3g (+90.3%)

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

合計: 453 kcal, P: 26.5g, F: 30.1g, C: 20.4g

**差分 (Pipeline - Label)**

- カロリー: +11.3 kcal (+2.6%)
- タンパク質: +1.9g (+7.7%)
- 脂質: +2.1g (+7.5%)
- 炭水化物: -5.2g (-20.3%)

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

合計: 918 kcal, P: 53.9g, F: 47.5g, C: 81.1g

**差分 (Pipeline - Label)**

- カロリー: +275.0 kcal (+42.8%)
- タンパク質: +22.9g (+73.9%)
- 脂質: +21.2g (+80.6%)
- 炭水化物: +1.1g (+1.4%)

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

合計: 772 kcal, P: 80.6g, F: 20.7g, C: 59.9g

**差分 (Pipeline - Label)**

- カロリー: +22.5 kcal (+3.0%)
- タンパク質: +34.8g (+76.0%)
- 脂質: -6.2g (-23.0%)
- 炭水化物: -21.1g (-26.0%)

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

合計: 516 kcal, P: 27.3g, F: 11.6g, C: 78.5g

**差分 (Pipeline - Label)**

- カロリー: +28.5 kcal (+5.8%)
- タンパク質: +1.4g (+5.4%)
- 脂質: -12.5g (-51.9%)
- 炭水化物: +32.5g (+70.7%)

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

合計: 1160 kcal, P: 82.3g, F: 64.4g, C: 64.3g

**差分 (Pipeline - Label)**

- カロリー: +304.9 kcal (+35.6%)
- タンパク質: +24.3g (+41.9%)
- 脂質: +21.8g (+51.2%)
- 炭水化物: +2.2g (+3.5%)

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

合計: 959 kcal, P: 33.4g, F: 48.3g, C: 97.3g

**差分 (Pipeline - Label)**

- カロリー: +213.3 kcal (+28.6%)
- タンパク質: +7.7g (+30.0%)
- 脂質: +13.6g (+39.2%)
- 炭水化物: +11.9g (+13.9%)

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

合計: 870 kcal, P: 42.5g, F: 35.3g, C: 94.9g

**差分 (Pipeline - Label)**

- カロリー: +288.2 kcal (+49.5%)
- タンパク質: -1.1g (-2.5%)
- 脂質: +20.5g (+138.5%)
- 炭水化物: +24.1g (+34.0%)

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

合計: 917 kcal, P: 54.6g, F: 37.3g, C: 95.3g

**差分 (Pipeline - Label)**

- カロリー: +318.4 kcal (+53.2%)
- タンパク質: +2.5g (+4.8%)
- 脂質: +21.1g (+130.2%)
- 炭水化物: +34.8g (+57.5%)

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

合計: 1028 kcal, P: 85.5g, F: 43.2g, C: 69.3g

**差分 (Pipeline - Label)**

- カロリー: +343.5 kcal (+50.2%)
- タンパク質: +21.6g (+33.8%)
- 脂質: +19.4g (+81.5%)
- 炭水化物: +11.7g (+20.3%)

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

合計: 723 kcal, P: 36.2g, F: 35.1g, C: 68.0g

**差分 (Pipeline - Label)**

- カロリー: +204.1 kcal (+39.3%)
- タンパク質: +3.6g (+11.0%)
- 脂質: +10.3g (+41.5%)
- 炭水化物: +23.0g (+51.1%)

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

合計: 858 kcal, P: 50.6g, F: 51.6g, C: 47.3g

**差分 (Pipeline - Label)**

- カロリー: +132.6 kcal (+18.3%)
- タンパク質: +4.1g (+8.8%)
- 脂質: +9.9g (+23.7%)
- 炭水化物: +4.3g (+10.0%)

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

合計: 719 kcal, P: 33.5g, F: 14.0g, C: 112.0g

**差分 (Pipeline - Label)**

- カロリー: +73.4 kcal (+11.4%)
- タンパク質: +2.1g (+6.7%)
- 脂質: -14.2g (-50.4%)
- 炭水化物: +42.2g (+60.5%)

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

合計: 879 kcal, P: 36.5g, F: 39.4g, C: 96.9g

**差分 (Pipeline - Label)**

- カロリー: +173.3 kcal (+24.5%)
- タンパク質: +12.0g (+49.0%)
- 脂質: -1.5g (-3.7%)
- 炭水化物: +32.3g (+50.0%)

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

合計: 417 kcal, P: 62.4g, F: 17.4g, C: 7.7g

**差分 (Pipeline - Label)**

- カロリー: +46.4 kcal (+12.5%)
- タンパク質: +15.3g (+32.5%)
- 脂質: +4.7g (+37.0%)
- 炭水化物: -7.9g (-50.6%)

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

合計: 847 kcal, P: 37.1g, F: 50.7g, C: 61.2g

**差分 (Pipeline - Label)**

- カロリー: +98.7 kcal (+13.2%)
- タンパク質: +9.5g (+34.4%)
- 脂質: +7.5g (+17.4%)
- 炭水化物: -0.4g (-0.6%)

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

合計: 1159 kcal, P: 42.3g, F: 59.4g, C: 111.8g

**差分 (Pipeline - Label)**

- カロリー: +373.0 kcal (+47.4%)
- タンパク質: +10.1g (+31.4%)
- 脂質: +22.5g (+61.0%)
- 炭水化物: +31.4g (+39.1%)

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

合計: 889 kcal, P: 67.8g, F: 32.2g, C: 82.2g

**差分 (Pipeline - Label)**

- カロリー: -180.4 kcal (-16.9%)
- タンパク質: +17.0g (+33.5%)
- 脂質: -22.1g (-40.7%)
- 炭水化物: -3.3g (-3.9%)

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

合計: 1351 kcal, P: 51.9g, F: 55.1g, C: 161.5g

**差分 (Pipeline - Label)**

- カロリー: +407.0 kcal (+43.1%)
- タンパク質: +15.9g (+44.2%)
- 脂質: +14.6g (+36.0%)
- 炭水化物: +53.9g (+50.1%)

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

合計: 746 kcal, P: 41.1g, F: 14.5g, C: 110.2g

**差分 (Pipeline - Label)**

- カロリー: -23.4 kcal (-3.0%)
- タンパク質: -21.6g (-34.4%)
- 脂質: -13.8g (-48.8%)
- 炭水化物: +40.0g (+57.0%)

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

合計: 915 kcal, P: 104.6g, F: 35.7g, C: 46.2g

**差分 (Pipeline - Label)**

- カロリー: -85.5 kcal (-8.5%)
- タンパク質: +47.9g (+84.5%)
- 脂質: -24.7g (-40.9%)
- 炭水化物: -22.5g (-32.8%)

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

合計: 945 kcal, P: 74.4g, F: 27.5g, C: 93.3g

**差分 (Pipeline - Label)**

- カロリー: +231.0 kcal (+32.4%)
- タンパク質: +32.9g (+79.3%)
- 脂質: -11.8g (-30.0%)
- 炭水化物: +37.1g (+66.0%)

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

合計: 618 kcal, P: 78.3g, F: 14.7g, C: 38.8g

**差分 (Pipeline - Label)**

- カロリー: +9.1 kcal (+1.5%)
- タンパク質: +37.4g (+91.4%)
- 脂質: -15.2g (-50.8%)
- 炭水化物: -7.2g (-15.7%)

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

合計: 917 kcal, P: 57.3g, F: 56.8g, C: 42.5g

**差分 (Pipeline - Label)**

- カロリー: +239.8 kcal (+35.4%)
- タンパク質: +25.1g (+78.0%)
- 脂質: +24.6g (+76.4%)
- 炭水化物: -23.6g (-35.7%)

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

合計: 690 kcal, P: 71.0g, F: 21.1g, C: 49.0g

**差分 (Pipeline - Label)**

- カロリー: +118.6 kcal (+20.8%)
- タンパク質: +39.5g (+125.4%)
- 脂質: -5.1g (-19.5%)
- 炭水化物: +0.3g (+0.6%)

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

合計: 682 kcal, P: 63.2g, F: 30.3g, C: 35.3g

**差分 (Pipeline - Label)**

- カロリー: +9.2 kcal (+1.4%)
- タンパク質: +33.1g (+110.0%)
- 脂質: -6.2g (-17.0%)
- 炭水化物: -22.0g (-38.4%)

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

合計: 976 kcal, P: 77.1g, F: 43.5g, C: 66.1g

**差分 (Pipeline - Label)**

- カロリー: +120.3 kcal (+14.1%)
- タンパク質: +29.2g (+61.0%)
- 脂質: +3.0g (+7.4%)
- 炭水化物: -19.4g (-22.7%)

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

合計: 699 kcal, P: 71.4g, F: 23.4g, C: 45.7g

**差分 (Pipeline - Label)**

- カロリー: +91.7 kcal (+15.1%)
- タンパク質: +34.7g (+94.6%)
- 脂質: -5.1g (-17.9%)
- 炭水化物: -3.8g (-7.7%)

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

合計: 883 kcal, P: 76.9g, F: 22.1g, C: 89.5g

**差分 (Pipeline - Label)**

- カロリー: -97.7 kcal (-10.0%)
- タンパク質: +37.4g (+94.7%)
- 脂質: -37.7g (-63.0%)
- 炭水化物: +15.3g (+20.6%)

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

合計: 586 kcal, P: 16.6g, F: 28.4g, C: 85.9g

**差分 (Pipeline - Label)**

- カロリー: -94.9 kcal (-13.9%)
- タンパク質: -18.0g (-52.0%)
- 脂質: -12.7g (-30.9%)
- 炭水化物: +40.2g (+88.0%)

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

合計: 784 kcal, P: 23.6g, F: 16.6g, C: 134.5g

**差分 (Pipeline - Label)**

- カロリー: +87.8 kcal (+12.6%)
- タンパク質: -1.9g (-7.5%)
- 脂質: -15.7g (-48.6%)
- 炭水化物: +52.2g (+63.4%)

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

合計: 1088 kcal, P: 99.3g, F: 42.8g, C: 70.3g

**差分 (Pipeline - Label)**

- カロリー: +386.7 kcal (+55.1%)
- タンパク質: +46.3g (+87.4%)
- 脂質: +6.5g (+17.9%)
- 炭水化物: +23.9g (+51.5%)

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

合計: 773 kcal, P: 94.1g, F: 35.6g, C: 14.8g

**差分 (Pipeline - Label)**

- カロリー: -201.5 kcal (-20.7%)
- タンパク質: +57.4g (+156.4%)
- 脂質: -13.5g (-27.5%)
- 炭水化物: -82.0g (-84.7%)

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

合計: 1070 kcal, P: 77.9g, F: 42.9g, C: 89.0g

**差分 (Pipeline - Label)**

- カロリー: +387.4 kcal (+56.8%)
- タンパク質: +27.7g (+55.2%)
- 脂質: +9.1g (+26.9%)
- 炭水化物: +45.1g (+102.7%)

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

合計: 1259 kcal, P: 68.3g, F: 35.6g, C: 161.1g

**差分 (Pipeline - Label)**

- カロリー: +473.2 kcal (+60.2%)
- タンパク質: +18.9g (+38.3%)
- 脂質: +3.8g (+11.9%)
- 炭水化物: +77.4g (+92.5%)

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

合計: 914 kcal, P: 87.4g, F: 28.9g, C: 69.8g

**差分 (Pipeline - Label)**

- カロリー: +348.3 kcal (+61.6%)
- タンパク質: +33.0g (+60.7%)
- 脂質: +8.2g (+39.6%)
- 炭水化物: +28.2g (+67.8%)

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

合計: 1351 kcal, P: 51.4g, F: 9.7g, C: 270.9g

**差分 (Pipeline - Label)**

- カロリー: +832.5 kcal (+160.6%)
- タンパク質: +29.5g (+134.7%)
- 脂質: -8.1g (-45.5%)
- 炭水化物: +195.7g (+260.2%)

---

### test_food45.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | prosciutto and mozzarella sandwich | 220g | 550 | 26.4g | 24.2g | 57.2g |
| main_food | potato chips | 45g | 241 | 3.1g | 15.8g | 22.9g |
| **合計** | - | - | **791** | **29.5g** | **40.0g** | **80.1g** |

**Pipeline栄養素**

合計: 887 kcal, P: 51.9g, F: 29.0g, C: 106.8g

**差分 (Pipeline - Label)**

- カロリー: +95.7 kcal (+12.1%)
- タンパク質: +22.4g (+75.9%)
- 脂質: -11.0g (-27.5%)
- 炭水化物: +26.7g (+33.3%)

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

合計: 1138 kcal, P: 80.6g, F: 37.7g, C: 118.8g

**差分 (Pipeline - Label)**

- カロリー: +461.6 kcal (+68.2%)
- タンパク質: +49.4g (+158.3%)
- 脂質: +8.2g (+27.8%)
- 炭水化物: +43.9g (+58.6%)

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

合計: 834 kcal, P: 41.8g, F: 41.0g, C: 74.2g

**差分 (Pipeline - Label)**

- カロリー: +51.4 kcal (+6.6%)
- タンパク質: +5.3g (+14.5%)
- 脂質: +6.8g (+19.9%)
- 炭水化物: -12.6g (-14.5%)

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

合計: 891 kcal, P: 32.8g, F: 25.3g, C: 131.6g

**差分 (Pipeline - Label)**

- カロリー: +345.3 kcal (+63.2%)
- タンパク質: +10.0g (+43.9%)
- 脂質: +8.3g (+48.8%)
- 炭水化物: +59.8g (+83.3%)

---

### test_food49.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | cheese pizza | 220g | 585 | 24.2g | 22.0g | 72.6g |
| extra | black olives | 15g | 17 | 0.1g | 1.6g | 0.9g |
| **合計** | - | - | **602** | **24.3g** | **23.6g** | **73.5g** |

**Pipeline栄養素**

合計: 859 kcal, P: 33.9g, F: 32.8g, C: 107.3g

**差分 (Pipeline - Label)**

- カロリー: +256.3 kcal (+42.5%)
- タンパク質: +9.6g (+39.5%)
- 脂質: +9.2g (+39.0%)
- 炭水化物: +33.8g (+46.0%)

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

合計: 1094 kcal, P: 81.5g, F: 44.6g, C: 88.8g

**差分 (Pipeline - Label)**

- カロリー: +564.6 kcal (+106.6%)
- タンパク質: +30.7g (+60.4%)
- 脂質: +26.5g (+146.4%)
- 炭水化物: +47.2g (+113.5%)

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

合計: 1143 kcal, P: 45.5g, F: 48.4g, C: 135.2g

**差分 (Pipeline - Label)**

- カロリー: +410.2 kcal (+55.9%)
- タンパク質: +16.6g (+57.4%)
- 脂質: +7.7g (+18.9%)
- 炭水化物: +66.0g (+95.4%)

---

### test_food6.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | cream of chicken soup with vegetables | 400g | 280 | 18.0g | 14.0g | 24.0g |
| main_food | dinner roll | 80g | 224 | 7.2g | 3.6g | 41.6g |
| **合計** | - | - | **504** | **25.2g** | **17.6g** | **65.6g** |

**Pipeline栄養素**

合計: 840 kcal, P: 30.2g, F: 38.2g, C: 95.9g

**差分 (Pipeline - Label)**

- カロリー: +336.0 kcal (+66.7%)
- タンパク質: +5.0g (+19.8%)
- 脂質: +20.6g (+117.0%)
- 炭水化物: +30.3g (+46.2%)

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

合計: 1011 kcal, P: 91.3g, F: 48.4g, C: 47.8g

**差分 (Pipeline - Label)**

- カロリー: +289.0 kcal (+40.0%)
- タンパク質: +40.4g (+79.4%)
- 脂質: +4.0g (+9.0%)
- 炭水化物: +13.7g (+40.2%)

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

合計: 973 kcal, P: 48.5g, F: 42.6g, C: 99.3g

**差分 (Pipeline - Label)**

- カロリー: +339.5 kcal (+53.6%)
- タンパク質: +7.7g (+18.9%)
- 脂質: +25.4g (+147.7%)
- 炭水化物: +14.8g (+17.5%)

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

合計: 906 kcal, P: 60.4g, F: 41.8g, C: 72.9g

**差分 (Pipeline - Label)**

- カロリー: +135.1 kcal (+17.5%)
- タンパク質: +14.2g (+30.7%)
- 脂質: -7.4g (-15.0%)
- 炭水化物: +27.4g (+60.2%)

---
