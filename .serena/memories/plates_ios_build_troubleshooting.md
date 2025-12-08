# Plates iOS ビルドトラブルシューティング

## よくあるエラー: Bundle Identifier is missing

### エラーメッセージ
```
Bundle identifier is missing. Runner doesn't have a bundle identifier. 
Add a value for PRODUCT_BUNDLE_IDENTIFIER in the build settings editor.
```

### 原因
Xcodeプロジェクトの`PRODUCT_BUNDLE_IDENTIFIER`が`$(appId)$(appIdSuffix)`という変数参照になっており、
これらの変数は`--dart-define-from-file`で定義される。

変数なしでビルドすると、`ios/Flutter/Dart-Defines.xcconfig`が空になりエラーになる。

### 解決方法

1. **正しいビルドコマンドを使用:**
```bash
cd /Users/odasoya/plates
.fvm/flutter_sdk/bin/flutter build ios --debug --dart-define-from-file=lib/flavor/dev.json
```

2. **Xcodeから実行する場合:**
flutter cleanしてからflutter buildを上記コマンドで実行し、その後Xcodeを開く

3. **flutter runの場合:**
```bash
.fvm/flutter_sdk/bin/flutter run --dart-define-from-file=lib/flavor/dev.json
```

### Flavor設定ファイル

- **開発環境**: `lib/flavor/dev.json`
- **本番環境**: `lib/flavor/prod.json` (開発中は使用禁止)

dev.jsonの内容:
```json
{
  "flavor": "dev",
  "appName": "Plates",
  "appId": "com.openhealth.calcalai",
  "appIdSuffix": ""
}
```

### ビルド後のDart-Defines.xcconfig
正常にビルドされると以下のような内容になる:
```
flavor=dev
appName=Plates
appId=com.openhealth.calcalai
appIdSuffix=
```

### ブランチ切り替え後の注意
ブランチを切り替えた後は`flutter clean`されている可能性があるため、
必ず`--dart-define-from-file`付きでビルドすること。
