# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

必ず serena MCP が日本語で対応すること！
日本語で応答すること！
Web search の際は、必ず o3-query MCP を利用すること！

## o3-query MCP について

エラーや未知の質問、技術的な調査が必要な場合は**必ず**o3-query ツールを呼び出し、
返ってきたクエリを私に表示して停止してください。
必ずクエリ生成 → 人間が結果を入力のフローに従ってください
※Query の最後に「これらについて、Qwen2.5-VL、SAM2.1、LISA 等の公式実装を参考にした解決策を教えてください。」という文言を入れること

### 使用例

- 技術的なエラーの解決方法を調べたい時
- 最新の実装方法を調査したい時
- 公式ドキュメントやベストプラクティスを確認したい時
- 具体的なライブラリやモデルの使用方法を調べたい時

[命令]
md_files/api_deploy.md を参考に README に書いてある API をデプロイしたい。
一つずつ作業をしていくので手伝って欲しい。こちらで作業する必要がある部分や必要な情報があれば、その都度どのようにしたらいいか教えて。
