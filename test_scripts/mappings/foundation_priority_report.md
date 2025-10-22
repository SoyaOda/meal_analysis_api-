# Foundation Food優先統合レポート（v3.0）

## 🎯 変更内容

Foundation Food（base_7）を優先するように統合戦略を変更しました。

## 📊 統合結果

### 数値サマリー

| 項目 | 数値 | 説明 |
|------|------|------|
| **総項目数** | 488 | ユニークな食品ID |
| **Foundation Food項目** | 107 | base_7由来（重複27件含む） |
| **Survey FNDDS専用** | 381 | base_1-6のみ |
| **Foundation優先置換** | 27 | Foundation版を優先採用 |

## 🔄 優先順位の変更

### Before（v2.0）
- Survey FNDDS優先
- Foundation Foodは補完情報

### After（v3.0）
- **Foundation Food優先**（より正確な栄養データ）
- Survey FNDDSは代替情報として保持

## 📝 重複項目の処理（27件）

### Foundation優先で置換された項目

| 食品ID | Foundation Food（優先） | Survey FNDDS（代替） |
|--------|------------------------|---------------------|
| apple | Apples, gala, with skin, raw | Apple, raw |
| banana | Bananas, ripe and slightly ripe, raw | Banana, raw |
| bacon | Pork, cured, bacon, cooked, restaurant | Bacon, NS as to type of meat, cooked |
| berries | Strawberries, raw | Berry, NFS |
| nuts | Nuts, almonds, whole, raw | Mixed nuts, NFS |
| oatmeal | Oats, whole grain, rolled, old fashioned | Oatmeal, cooked, NFS |

その他21項目も同様にFoundation Food版を優先

## 🔍 データ構造の例（apple）

```json
{
  "display_name": "Apple",
  "default_usda": {
    "name": "Apples, gala, with skin, raw",  // Foundation優先
    "database": "foundation"
  },
  "survey_alternative": {  // Survey版を代替として保持
    "name": "Apple, raw",
    "database": "survey_fndds",
    "reason": "Survey FNDDS alternative for broader compatibility"
  },
  "all_usda_mappings": [
    // Foundation項目を先頭に配置（5項目）
    "Apples, fuji, with skin, raw",
    "Apples, gala, with skin, raw",
    ...
    // Survey項目を後に追加（4項目）
    "Apple, raw",
    "Apple, baked",
    ...
  ],
  "is_merged": true,
  "merge_info": {
    "primary_database": "foundation"
  }
}
```

## ✅ Foundation Food優先のメリット

1. **より正確な栄養データ**
   - 具体的な品種・ブランドの栄養価
   - 最新の分析手法による測定値

2. **詳細な食品情報**
   - 品種指定（例: Gala apple vs 一般的なapple）
   - 調理法や部位の明確な記載

3. **科学的根拠**
   - USDAの最新研究に基づくデータ
   - サンプリング方法が明確

## ⚠️ 注意事項

1. **Survey FNDDSとの互換性**
   - 一部のアプリケーションはSurvey FNDDS名を期待する可能性
   - `survey_alternative`フィールドで対応可能

2. **汎用性の違い**
   - Foundation: 具体的だが限定的
   - Survey: 汎用的だが精度は劣る

3. **使い分けの指針**
   - 栄養計算の精度重視 → Foundation Food（default）
   - 幅広い互換性重視 → Survey FNDDS（alternative）

## 📁 生成ファイル

- **mappings.json** - Foundation優先統合版（v3.0）
- **mappings.json.backup_v3** - 前バージョンのバックアップ
- **foundation_priority_report.md** - このレポート

---
作成日: 2024-10-22
バージョン: 3.0
優先データベース: Foundation Food
