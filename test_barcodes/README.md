# Test Barcodes for Barcode Scanner

North American products verified on OpenFoodFacts and USDA FoodData Central.

## OpenFoodFacts Products (5)

| File | Barcode | Product | Brand |
|------|---------|---------|-------|
| OFF_coca_cola_zero_049000042566.png | 049000042566 | Zero Calorie Cola | Coca-Cola |
| OFF_pringles_original_038000138416.png | 038000138416 | Pringles Original | Pringles |
| OFF_cheerios_016000275287.png | 016000275287 | Cheerios | General Mills |
| OFF_rold_gold_pretzels_028400047685.png | 028400047685 | Tiny Twists Original | Rold Gold |
| OFF_jack_links_jerky_017082879004.png | 017082879004 | Flame Grilled Jerky | Jack Link's |

## USDA FoodData Central Products (5)

| File | Barcode | Product | Brand |
|------|---------|---------|-------|
| USDA_quaker_real_medleys_030000315507.png | 030000315507 | Real Medleys Apple Walnut | Quaker |
| USDA_wishbone_dressing_041000006067.png | 041000006067 | Chunky Blue Cheese Dressing | Wish-Bone |
| USDA_yoplait_oui_blueberry_070470496535.png | 070470496535 | Oui Blueberry Yogurt | Yoplait |
| USDA_sunshine_crackers_024100122264.png | 024100122264 | Baked Snack Crackers | Sunshine |
| USDA_rodoula_kataifi_041318430028.png | 041318430028 | Kataifi Greek Sweets | RODOULA |

## How to Test

### Physical Device
1. Display barcode image on a monitor or print it
2. Point your phone's camera at the barcode
3. The app should detect and search for the product

## API Verification

```bash
# Test OpenFoodFacts API directly
curl "https://world.openfoodfacts.org/api/v2/product/049000042566"
```
