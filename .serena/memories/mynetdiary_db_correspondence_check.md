# MyNetDiaryデータベース対応関係チェック

## 目的
- `db/mynetdiary_converted_tool_calls_list_stemmed.json`
- `MyNetDiary_json_builder/mynetdiary_db.json`

2つのDBで同じIDを持つレコードの`original_name`と`search_name`が対応しているかを確認する。

## 調査項目
1. 同一ID間での名前フィールドの一致性
2. 不一致がある場合の原因分析
3. データ変換過程での変更パターンの特定