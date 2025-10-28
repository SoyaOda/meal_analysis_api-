# Pipeline vs VLM Label 栄養素比較レポート

生成日時: 2025-10-26 18:07:34

対象画像数: 50

## サマリー

### 平均差分（Pipeline - Label）

| 栄養素 | 平均差分 (%) |
|--------|--------------|
| カロリー | +69.5% |
| タンパク質 | +111.0% |
| 脂質 | +55.0% |
| 炭水化物 | +53.8% |

## 詳細比較表

| 画像 | Label Cal | Pipeline Cal | 差分 | Label P | Pipeline P | 差分 | Label F | Pipeline F | 差分 | Label C | Pipeline C | 差分 |
|------|-----------|--------------|------|---------|------------|------|---------|------------|------|---------|------------|------|
| test_food1.jpg | 891 | 1735 | +94.7% | 58.9 | 147.2 | +149.9% | 53.8 | 95.0 | +76.6% | 50.9 | 66.4 | +30.5% |
| test_food10.jpg | 854 | 1886 | +120.8% | 59.5 | 132.0 | +121.8% | 48.1 | 88.5 | +84.0% | 53.4 | 137.1 | +156.7% |
| test_food11.jpg | 499 | 657 | +31.6% | 27.4 | 35.8 | +30.7% | 27.4 | 22.8 | -16.8% | 40.2 | 78.0 | +94.0% |
| test_food12.jpg | 441 | 420 | -4.8% | 24.6 | 36.4 | +48.0% | 28.0 | 19.8 | -29.3% | 25.6 | 25.7 | +0.4% |
| test_food13.jpg | 643 | 1295 | +101.4% | 31.0 | 74.7 | +141.0% | 26.3 | 66.1 | +151.3% | 80.0 | 107.4 | +34.3% |
| test_food14.jpg | 749 | 1216 | +62.2% | 45.8 | 123.1 | +168.8% | 26.9 | 32.8 | +21.9% | 81.0 | 98.6 | +21.7% |
| test_food15.jpg | 488 | 577 | +18.4% | 25.9 | 30.4 | +17.4% | 24.1 | 10.2 | -57.7% | 46.0 | 91.2 | +98.3% |
| test_food16.jpg | 855 | 2053 | +140.1% | 58.0 | 159.4 | +174.8% | 42.6 | 118.6 | +178.4% | 62.1 | 84.6 | +36.2% |
| test_food17.jpg | 746 | 1298 | +74.1% | 25.7 | 48.5 | +88.7% | 34.7 | 61.9 | +78.4% | 85.4 | 137.6 | +61.1% |
| test_food18.jpg | 582 | 1145 | +96.7% | 43.6 | 57.6 | +32.1% | 14.8 | 45.4 | +206.8% | 70.8 | 125.6 | +77.4% |
| test_food19.jpg | 599 | 1236 | +106.3% | 52.1 | 79.4 | +52.4% | 16.2 | 46.0 | +184.0% | 60.5 | 127.3 | +110.4% |
| test_food2.jpg | 684 | 1423 | +107.9% | 63.9 | 140.4 | +119.7% | 23.8 | 57.6 | +142.0% | 57.6 | 78.0 | +35.4% |
| test_food20.jpg | 519 | 630 | +21.3% | 32.6 | 28.7 | -12.0% | 24.8 | 33.0 | +33.1% | 45.0 | 56.9 | +26.4% |
| test_food21.jpg | 725 | 1204 | +66.0% | 46.5 | 72.5 | +55.9% | 41.7 | 69.6 | +66.9% | 43.0 | 71.7 | +66.7% |
| test_food22.jpg | 646 | 1016 | +57.3% | 31.4 | 33.2 | +5.7% | 28.2 | 47.7 | +69.1% | 69.8 | 111.9 | +60.3% |
| test_food23.jpg | 706 | 1053 | +49.1% | 24.5 | 42.4 | +73.1% | 40.9 | 55.7 | +36.2% | 64.6 | 98.0 | +51.7% |
| test_food24.jpg | 370 | 946 | +155.2% | 47.1 | 153.1 | +225.1% | 12.7 | 32.5 | +155.9% | 15.6 | 13.4 | -14.1% |
| test_food25.jpg | 748 | 1264 | +68.9% | 27.6 | 49.8 | +80.4% | 43.2 | 71.4 | +65.3% | 61.6 | 110.0 | +78.6% |
| test_food26.jpg | 786 | 1100 | +39.9% | 32.2 | 37.2 | +15.5% | 36.9 | 58.3 | +58.0% | 80.4 | 113.5 | +41.2% |
| test_food27.jpg | 1069 | 1341 | +25.4% | 50.8 | 109.2 | +115.0% | 54.3 | 43.3 | -20.3% | 85.5 | 131.0 | +53.2% |
| test_food28.jpg | 944 | 1198 | +27.0% | 36.0 | 45.8 | +27.2% | 40.5 | 49.3 | +21.7% | 107.6 | 142.8 | +32.7% |
| test_food29.jpg | 769 | 834 | +8.5% | 62.7 | 30.2 | -51.8% | 28.3 | 40.9 | +44.5% | 70.2 | 85.1 | +21.2% |
| test_food3.jpg | 1000 | 1471 | +47.0% | 56.7 | 180.5 | +218.3% | 60.4 | 55.4 | -8.3% | 68.7 | 65.4 | -4.8% |
| test_food30.jpg | 714 | 1119 | +56.8% | 41.5 | 93.0 | +124.1% | 39.3 | 24.1 | -38.7% | 56.2 | 124.4 | +121.4% |
| test_food31.jpg | 609 | 1199 | +97.0% | 40.9 | 160.2 | +291.7% | 29.9 | 30.0 | +0.3% | 46.0 | 61.6 | +33.9% |
| test_food32.jpg | 677 | 706 | +4.3% | 32.2 | 47.4 | +47.2% | 32.2 | 42.2 | +31.1% | 66.1 | 33.0 | -50.1% |
| test_food33.jpg | 572 | 934 | +63.4% | 31.5 | 96.7 | +207.0% | 26.2 | 28.9 | +10.3% | 48.7 | 64.7 | +32.9% |
| test_food34.jpg | 672 | 938 | +39.5% | 30.1 | 78.9 | +162.1% | 36.5 | 40.6 | +11.2% | 57.3 | 60.2 | +5.1% |
| test_food35.jpg | 856 | 2056 | +140.3% | 47.9 | 123.1 | +157.0% | 40.5 | 107.0 | +164.2% | 85.5 | 156.2 | +82.7% |
| test_food36.jpg | 607 | 1093 | +80.0% | 36.7 | 120.2 | +227.5% | 28.5 | 32.8 | +15.1% | 49.5 | 70.5 | +42.4% |
| test_food37.jpg | 980 | 1386 | +41.4% | 39.5 | 121.1 | +206.6% | 59.8 | 39.8 | -33.4% | 74.2 | 128.5 | +73.2% |
| test_food38.jpg | 681 | 716 | +5.1% | 34.6 | 43.7 | +26.3% | 41.1 | 42.6 | +3.6% | 45.7 | 40.2 | -12.0% |
| test_food39.jpg | 696 | 916 | +31.6% | 25.5 | 28.5 | +11.8% | 32.3 | 22.4 | -30.7% | 82.3 | 148.2 | +80.1% |
| test_food4.jpg | 702 | 1176 | +67.6% | 53.0 | 127.7 | +140.9% | 36.3 | 37.5 | +3.3% | 46.4 | 72.8 | +56.9% |
| test_food40.jpg | 974 | 958 | -1.6% | 36.7 | 127.1 | +246.3% | 49.1 | 42.5 | -13.4% | 96.8 | 9.5 | -90.2% |
| test_food41.jpg | 682 | 1741 | +155.1% | 50.2 | 179.3 | +257.2% | 33.8 | 75.9 | +124.6% | 43.9 | 73.3 | +67.0% |
| test_food42.jpg | 786 | 1320 | +68.0% | 49.4 | 120.7 | +144.3% | 31.8 | 39.3 | +23.6% | 83.7 | 113.0 | +35.0% |
| test_food43.jpg | 566 | 1212 | +114.2% | 54.4 | 127.9 | +135.1% | 20.7 | 39.9 | +92.8% | 41.6 | 77.2 | +85.6% |
| test_food44.jpg | 518 | 1286 | +148.1% | 21.9 | 48.4 | +121.0% | 17.8 | 7.8 | -56.2% | 75.2 | 256.9 | +241.6% |
| test_food45.jpg | 791 | 1072 | +35.5% | 29.5 | 65.9 | +123.4% | 40.0 | 32.9 | -17.8% | 80.1 | 130.4 | +62.8% |
| test_food46.jpg | 677 | 788 | +16.4% | 31.2 | 77.5 | +148.4% | 29.5 | 33.3 | +12.9% | 74.9 | 44.4 | -40.7% |
| test_food47.jpg | 783 | 1522 | +94.5% | 36.5 | 74.4 | +103.8% | 34.2 | 73.9 | +116.1% | 86.8 | 139.9 | +61.2% |
| test_food48.jpg | 546 | 699 | +28.0% | 22.8 | 26.7 | +17.1% | 17.0 | 32.4 | +90.6% | 71.8 | 73.3 | +2.1% |
| test_food49.jpg | 602 | 1470 | +144.0% | 24.3 | 58.6 | +141.2% | 23.6 | 56.5 | +139.4% | 73.5 | 184.3 | +150.7% |
| test_food5.jpg | 530 | 1100 | +107.8% | 50.8 | 114.4 | +125.2% | 18.1 | 39.3 | +117.1% | 41.6 | 66.2 | +59.1% |
| test_food50.jpg | 733 | 1437 | +96.0% | 28.9 | 60.2 | +108.3% | 40.7 | 60.4 | +48.4% | 69.2 | 168.9 | +144.1% |
| test_food6.jpg | 504 | 744 | +47.7% | 25.2 | 33.1 | +31.3% | 17.6 | 30.8 | +75.0% | 65.6 | 87.5 | +33.4% |
| test_food7.jpg | 722 | 1538 | +113.1% | 50.9 | 152.1 | +198.8% | 44.4 | 74.7 | +68.2% | 34.1 | 56.2 | +64.8% |
| test_food8.jpg | 634 | 1256 | +98.3% | 40.8 | 67.0 | +64.2% | 17.2 | 56.4 | +227.9% | 84.5 | 122.9 | +45.4% |
| test_food9.jpg | 771 | 1299 | +68.4% | 46.2 | 84.2 | +82.3% | 49.2 | 60.9 | +23.8% | 45.5 | 106.6 | +134.3% |

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

合計: 1735 kcal, P: 147.2g, F: 95.0g, C: 66.4g

**差分 (Pipeline - Label)**

- カロリー: +843.5 kcal (+94.7%)
- タンパク質: +88.3g (+149.9%)
- 脂質: +41.2g (+76.6%)
- 炭水化物: +15.5g (+30.5%)

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

合計: 1886 kcal, P: 132.0g, F: 88.5g, C: 137.1g

**差分 (Pipeline - Label)**

- カロリー: +1031.6 kcal (+120.8%)
- タンパク質: +72.5g (+121.8%)
- 脂質: +40.4g (+84.0%)
- 炭水化物: +83.7g (+156.7%)

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

合計: 657 kcal, P: 35.8g, F: 22.8g, C: 78.0g

**差分 (Pipeline - Label)**

- カロリー: +157.9 kcal (+31.6%)
- タンパク質: +8.4g (+30.7%)
- 脂質: -4.6g (-16.8%)
- 炭水化物: +37.8g (+94.0%)

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

合計: 420 kcal, P: 36.4g, F: 19.8g, C: 25.7g

**差分 (Pipeline - Label)**

- カロリー: -21.1 kcal (-4.8%)
- タンパク質: +11.8g (+48.0%)
- 脂質: -8.2g (-29.3%)
- 炭水化物: +0.1g (+0.4%)

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

合計: 1295 kcal, P: 74.7g, F: 66.1g, C: 107.4g

**差分 (Pipeline - Label)**

- カロリー: +651.9 kcal (+101.4%)
- タンパク質: +43.7g (+141.0%)
- 脂質: +39.8g (+151.3%)
- 炭水化物: +27.4g (+34.3%)

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

合計: 1216 kcal, P: 123.1g, F: 32.8g, C: 98.6g

**差分 (Pipeline - Label)**

- カロリー: +466.4 kcal (+62.2%)
- タンパク質: +77.3g (+168.8%)
- 脂質: +5.9g (+21.9%)
- 炭水化物: +17.6g (+21.7%)

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

合計: 577 kcal, P: 30.4g, F: 10.2g, C: 91.2g

**差分 (Pipeline - Label)**

- カロリー: +89.5 kcal (+18.4%)
- タンパク質: +4.5g (+17.4%)
- 脂質: -13.9g (-57.7%)
- 炭水化物: +45.2g (+98.3%)

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

合計: 2053 kcal, P: 159.4g, F: 118.6g, C: 84.6g

**差分 (Pipeline - Label)**

- カロリー: +1198.0 kcal (+140.1%)
- タンパク質: +101.4g (+174.8%)
- 脂質: +76.0g (+178.4%)
- 炭水化物: +22.5g (+36.2%)

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

合計: 1298 kcal, P: 48.5g, F: 61.9g, C: 137.6g

**差分 (Pipeline - Label)**

- カロリー: +552.4 kcal (+74.1%)
- タンパク質: +22.8g (+88.7%)
- 脂質: +27.2g (+78.4%)
- 炭水化物: +52.2g (+61.1%)

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

合計: 1145 kcal, P: 57.6g, F: 45.4g, C: 125.6g

**差分 (Pipeline - Label)**

- カロリー: +562.8 kcal (+96.7%)
- タンパク質: +14.0g (+32.1%)
- 脂質: +30.6g (+206.8%)
- 炭水化物: +54.8g (+77.4%)

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

合計: 1236 kcal, P: 79.4g, F: 46.0g, C: 127.3g

**差分 (Pipeline - Label)**

- カロリー: +636.7 kcal (+106.3%)
- タンパク質: +27.3g (+52.4%)
- 脂質: +29.8g (+184.0%)
- 炭水化物: +66.8g (+110.4%)

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

合計: 1423 kcal, P: 140.4g, F: 57.6g, C: 78.0g

**差分 (Pipeline - Label)**

- カロリー: +738.7 kcal (+107.9%)
- タンパク質: +76.5g (+119.7%)
- 脂質: +33.8g (+142.0%)
- 炭水化物: +20.4g (+35.4%)

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

合計: 630 kcal, P: 28.7g, F: 33.0g, C: 56.9g

**差分 (Pipeline - Label)**

- カロリー: +110.8 kcal (+21.3%)
- タンパク質: -3.9g (-12.0%)
- 脂質: +8.2g (+33.1%)
- 炭水化物: +11.9g (+26.4%)

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

合計: 1204 kcal, P: 72.5g, F: 69.6g, C: 71.7g

**差分 (Pipeline - Label)**

- カロリー: +478.7 kcal (+66.0%)
- タンパク質: +26.0g (+55.9%)
- 脂質: +27.9g (+66.9%)
- 炭水化物: +28.7g (+66.7%)

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

合計: 1016 kcal, P: 33.2g, F: 47.7g, C: 111.9g

**差分 (Pipeline - Label)**

- カロリー: +370.0 kcal (+57.3%)
- タンパク質: +1.8g (+5.7%)
- 脂質: +19.5g (+69.1%)
- 炭水化物: +42.1g (+60.3%)

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

合計: 1053 kcal, P: 42.4g, F: 55.7g, C: 98.0g

**差分 (Pipeline - Label)**

- カロリー: +346.8 kcal (+49.1%)
- タンパク質: +17.9g (+73.1%)
- 脂質: +14.8g (+36.2%)
- 炭水化物: +33.4g (+51.7%)

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

合計: 946 kcal, P: 153.1g, F: 32.5g, C: 13.4g

**差分 (Pipeline - Label)**

- カロリー: +575.1 kcal (+155.2%)
- タンパク質: +106.0g (+225.1%)
- 脂質: +19.8g (+155.9%)
- 炭水化物: -2.2g (-14.1%)

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

合計: 1264 kcal, P: 49.8g, F: 71.4g, C: 110.0g

**差分 (Pipeline - Label)**

- カロリー: +515.4 kcal (+68.9%)
- タンパク質: +22.2g (+80.4%)
- 脂質: +28.2g (+65.3%)
- 炭水化物: +48.4g (+78.6%)

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

合計: 1100 kcal, P: 37.2g, F: 58.3g, C: 113.5g

**差分 (Pipeline - Label)**

- カロリー: +313.8 kcal (+39.9%)
- タンパク質: +5.0g (+15.5%)
- 脂質: +21.4g (+58.0%)
- 炭水化物: +33.1g (+41.2%)

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

合計: 1341 kcal, P: 109.2g, F: 43.3g, C: 131.0g

**差分 (Pipeline - Label)**

- カロリー: +272.0 kcal (+25.4%)
- タンパク質: +58.4g (+115.0%)
- 脂質: -11.0g (-20.3%)
- 炭水化物: +45.5g (+53.2%)

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

合計: 1198 kcal, P: 45.8g, F: 49.3g, C: 142.8g

**差分 (Pipeline - Label)**

- カロリー: +254.9 kcal (+27.0%)
- タンパク質: +9.8g (+27.2%)
- 脂質: +8.8g (+21.7%)
- 炭水化物: +35.2g (+32.7%)

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

合計: 834 kcal, P: 30.2g, F: 40.9g, C: 85.1g

**差分 (Pipeline - Label)**

- カロリー: +65.0 kcal (+8.5%)
- タンパク質: -32.5g (-51.8%)
- 脂質: +12.6g (+44.5%)
- 炭水化物: +14.9g (+21.2%)

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

合計: 1471 kcal, P: 180.5g, F: 55.4g, C: 65.4g

**差分 (Pipeline - Label)**

- カロリー: +470.2 kcal (+47.0%)
- タンパク質: +123.8g (+218.3%)
- 脂質: -5.0g (-8.3%)
- 炭水化物: -3.3g (-4.8%)

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

合計: 1119 kcal, P: 93.0g, F: 24.1g, C: 124.4g

**差分 (Pipeline - Label)**

- カロリー: +405.4 kcal (+56.8%)
- タンパク質: +51.5g (+124.1%)
- 脂質: -15.2g (-38.7%)
- 炭水化物: +68.2g (+121.4%)

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

合計: 1199 kcal, P: 160.2g, F: 30.0g, C: 61.6g

**差分 (Pipeline - Label)**

- カロリー: +590.5 kcal (+97.0%)
- タンパク質: +119.3g (+291.7%)
- 脂質: +0.1g (+0.3%)
- 炭水化物: +15.6g (+33.9%)

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

合計: 706 kcal, P: 47.4g, F: 42.2g, C: 33.0g

**差分 (Pipeline - Label)**

- カロリー: +29.1 kcal (+4.3%)
- タンパク質: +15.2g (+47.2%)
- 脂質: +10.0g (+31.1%)
- 炭水化物: -33.1g (-50.1%)

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

合計: 934 kcal, P: 96.7g, F: 28.9g, C: 64.7g

**差分 (Pipeline - Label)**

- カロリー: +362.3 kcal (+63.4%)
- タンパク質: +65.2g (+207.0%)
- 脂質: +2.7g (+10.3%)
- 炭水化物: +16.0g (+32.9%)

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

合計: 938 kcal, P: 78.9g, F: 40.6g, C: 60.2g

**差分 (Pipeline - Label)**

- カロリー: +265.5 kcal (+39.5%)
- タンパク質: +48.8g (+162.1%)
- 脂質: +4.1g (+11.2%)
- 炭水化物: +2.9g (+5.1%)

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

合計: 2056 kcal, P: 123.1g, F: 107.0g, C: 156.2g

**差分 (Pipeline - Label)**

- カロリー: +1200.4 kcal (+140.3%)
- タンパク質: +75.2g (+157.0%)
- 脂質: +66.5g (+164.2%)
- 炭水化物: +70.7g (+82.7%)

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

合計: 1093 kcal, P: 120.2g, F: 32.8g, C: 70.5g

**差分 (Pipeline - Label)**

- カロリー: +485.9 kcal (+80.0%)
- タンパク質: +83.5g (+227.5%)
- 脂質: +4.3g (+15.1%)
- 炭水化物: +21.0g (+42.4%)

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

合計: 1386 kcal, P: 121.1g, F: 39.8g, C: 128.5g

**差分 (Pipeline - Label)**

- カロリー: +405.7 kcal (+41.4%)
- タンパク質: +81.6g (+206.6%)
- 脂質: -20.0g (-33.4%)
- 炭水化物: +54.3g (+73.2%)

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

合計: 716 kcal, P: 43.7g, F: 42.6g, C: 40.2g

**差分 (Pipeline - Label)**

- カロリー: +34.9 kcal (+5.1%)
- タンパク質: +9.1g (+26.3%)
- 脂質: +1.5g (+3.6%)
- 炭水化物: -5.5g (-12.0%)

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

合計: 916 kcal, P: 28.5g, F: 22.4g, C: 148.2g

**差分 (Pipeline - Label)**

- カロリー: +220.2 kcal (+31.6%)
- タンパク質: +3.0g (+11.8%)
- 脂質: -9.9g (-30.7%)
- 炭水化物: +65.9g (+80.1%)

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

合計: 1176 kcal, P: 127.7g, F: 37.5g, C: 72.8g

**差分 (Pipeline - Label)**

- カロリー: +474.5 kcal (+67.6%)
- タンパク質: +74.7g (+140.9%)
- 脂質: +1.2g (+3.3%)
- 炭水化物: +26.4g (+56.9%)

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

合計: 958 kcal, P: 127.1g, F: 42.5g, C: 9.5g

**差分 (Pipeline - Label)**

- カロリー: -15.6 kcal (-1.6%)
- タンパク質: +90.4g (+246.3%)
- 脂質: -6.6g (-13.4%)
- 炭水化物: -87.3g (-90.2%)

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

合計: 1741 kcal, P: 179.3g, F: 75.9g, C: 73.3g

**差分 (Pipeline - Label)**

- カロリー: +1058.4 kcal (+155.1%)
- タンパク質: +129.1g (+257.2%)
- 脂質: +42.1g (+124.6%)
- 炭水化物: +29.4g (+67.0%)

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

合計: 1320 kcal, P: 120.7g, F: 39.3g, C: 113.0g

**差分 (Pipeline - Label)**

- カロリー: +534.5 kcal (+68.0%)
- タンパク質: +71.3g (+144.3%)
- 脂質: +7.5g (+23.6%)
- 炭水化物: +29.3g (+35.0%)

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

合計: 1212 kcal, P: 127.9g, F: 39.9g, C: 77.2g

**差分 (Pipeline - Label)**

- カロリー: +646.4 kcal (+114.2%)
- タンパク質: +73.5g (+135.1%)
- 脂質: +19.2g (+92.8%)
- 炭水化物: +35.6g (+85.6%)

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

合計: 1286 kcal, P: 48.4g, F: 7.8g, C: 256.9g

**差分 (Pipeline - Label)**

- カロリー: +767.8 kcal (+148.1%)
- タンパク質: +26.5g (+121.0%)
- 脂質: -10.0g (-56.2%)
- 炭水化物: +181.7g (+241.6%)

---

### test_food45.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | prosciutto and mozzarella sandwich | 220g | 550 | 26.4g | 24.2g | 57.2g |
| main_food | potato chips | 45g | 241 | 3.1g | 15.8g | 22.9g |
| **合計** | - | - | **791** | **29.5g** | **40.0g** | **80.1g** |

**Pipeline栄養素**

合計: 1072 kcal, P: 65.9g, F: 32.9g, C: 130.4g

**差分 (Pipeline - Label)**

- カロリー: +280.7 kcal (+35.5%)
- タンパク質: +36.4g (+123.4%)
- 脂質: -7.1g (-17.8%)
- 炭水化物: +50.3g (+62.8%)

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

合計: 788 kcal, P: 77.5g, F: 33.3g, C: 44.4g

**差分 (Pipeline - Label)**

- カロリー: +111.1 kcal (+16.4%)
- タンパク質: +46.3g (+148.4%)
- 脂質: +3.8g (+12.9%)
- 炭水化物: -30.5g (-40.7%)

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

合計: 1522 kcal, P: 74.4g, F: 73.9g, C: 139.9g

**差分 (Pipeline - Label)**

- カロリー: +739.9 kcal (+94.5%)
- タンパク質: +37.9g (+103.8%)
- 脂質: +39.7g (+116.1%)
- 炭水化物: +53.1g (+61.2%)

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

合計: 699 kcal, P: 26.7g, F: 32.4g, C: 73.3g

**差分 (Pipeline - Label)**

- カロリー: +152.9 kcal (+28.0%)
- タンパク質: +3.9g (+17.1%)
- 脂質: +15.4g (+90.6%)
- 炭水化物: +1.5g (+2.1%)

---

### test_food49.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | cheese pizza | 220g | 585 | 24.2g | 22.0g | 72.6g |
| extra | black olives | 15g | 17 | 0.1g | 1.6g | 0.9g |
| **合計** | - | - | **602** | **24.3g** | **23.6g** | **73.5g** |

**Pipeline栄養素**

合計: 1470 kcal, P: 58.6g, F: 56.5g, C: 184.3g

**差分 (Pipeline - Label)**

- カロリー: +867.6 kcal (+144.0%)
- タンパク質: +34.3g (+141.2%)
- 脂質: +32.9g (+139.4%)
- 炭水化物: +110.8g (+150.7%)

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

合計: 1100 kcal, P: 114.4g, F: 39.3g, C: 66.2g

**差分 (Pipeline - Label)**

- カロリー: +570.9 kcal (+107.8%)
- タンパク質: +63.6g (+125.2%)
- 脂質: +21.2g (+117.1%)
- 炭水化物: +24.6g (+59.1%)

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

合計: 1437 kcal, P: 60.2g, F: 60.4g, C: 168.9g

**差分 (Pipeline - Label)**

- カロリー: +703.7 kcal (+96.0%)
- タンパク質: +31.3g (+108.3%)
- 脂質: +19.7g (+48.4%)
- 炭水化物: +99.7g (+144.1%)

---

### test_food6.jpg

**VLM Label栄養素**

| Type | Food | Weight | Cal | P | F | C |
|------|------|--------|-----|---|---|---|
| main_food | cream of chicken soup with vegetables | 400g | 280 | 18.0g | 14.0g | 24.0g |
| main_food | dinner roll | 80g | 224 | 7.2g | 3.6g | 41.6g |
| **合計** | - | - | **504** | **25.2g** | **17.6g** | **65.6g** |

**Pipeline栄養素**

合計: 744 kcal, P: 33.1g, F: 30.8g, C: 87.5g

**差分 (Pipeline - Label)**

- カロリー: +240.3 kcal (+47.7%)
- タンパク質: +7.9g (+31.3%)
- 脂質: +13.2g (+75.0%)
- 炭水化物: +21.9g (+33.4%)

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

合計: 1538 kcal, P: 152.1g, F: 74.7g, C: 56.2g

**差分 (Pipeline - Label)**

- カロリー: +816.3 kcal (+113.1%)
- タンパク質: +101.2g (+198.8%)
- 脂質: +30.3g (+68.2%)
- 炭水化物: +22.1g (+64.8%)

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

合計: 1256 kcal, P: 67.0g, F: 56.4g, C: 122.9g

**差分 (Pipeline - Label)**

- カロリー: +622.8 kcal (+98.3%)
- タンパク質: +26.2g (+64.2%)
- 脂質: +39.2g (+227.9%)
- 炭水化物: +38.4g (+45.4%)

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

合計: 1299 kcal, P: 84.2g, F: 60.9g, C: 106.6g

**差分 (Pipeline - Label)**

- カロリー: +527.8 kcal (+68.4%)
- タンパク質: +38.0g (+82.3%)
- 脂質: +11.7g (+23.8%)
- 炭水化物: +61.1g (+134.3%)

---
