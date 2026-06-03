---
name: handoff
description: セッション終了時の引き継ぎ処理。作業中アプリの plans/current.md の進捗（Status）を更新し、Session Log に今回の作業内容を追記して、未完了タスクのメモを残す。セッションを終える前やコンテキストを引き継ぎたいときに使う。
when_to_use: ユーザーがセッションを終える、作業を区切る、引き継ぎ・ハンドオフを求めたとき。
argument-hint: "[アプリ名 or plans/current.md のパス（省略時は作業中のものを推定）]"
allowed-tools: Read, Edit, Bash
---

# Handoff — plans/current.md を更新

セッション間の引き継ぎSSOT（`plans/current.md`）を最新化する。

## 手順
1. 対象の `plans/current.md` を特定する（`$ARGUMENTS` 指定、無ければ今回触ったアプリ配下の `plans/current.md`。例: `apps/freeform_usda_meal_analysis_api/plans/current.md`）。
2. 今回の作業に基づき更新する:
   - **Progress** テーブルの Status を更新（pending → wip → done）。
   - **Session Log** に1行追記（日付 / セッション名 / 作業内容を簡潔に）。
   - 未完了タスク・既知の問題・次の一手があればメモを追記。
   - Exit Criteria の「現在」列を実態に合わせて更新。
3. 必要なら関連docの同期（例: traceability や baseline 更新の有無）を確認する。

## 原則
- 事実のみ記録する（未検証の「改善した」は書かない）。
- 次セッションが `plans/current.md` だけ読めば再開できる粒度にする。
- コミットはユーザーの明示指示があるまで行わない。
