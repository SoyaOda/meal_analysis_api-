# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🚀 Quick Setup - Google Cloud SDK

**ローカルGoogle Cloud SDK パス**: `/Users/odasoya/google-cloud-sdk/bin/gcloud`

```bash
# 迷った時の確認コマンド
/Users/odasoya/google-cloud-sdk/bin/gcloud config get-value project  # => new-snap-calorie
/Users/odasoya/google-cloud-sdk/bin/gcloud config get-value account  # => odssuu@gmail.com

# PATHに追加する場合
export PATH="$PATH:/Users/odasoya/google-cloud-sdk/bin"
gcloud config get-value project  # => new-snap-calorie
```

## Project Overview

必ず serena MCP が日本語で対応すること！
日本語で応答すること！

[Instruction]
MEAL_ANALYSIS_API_README.md と app_v2 内の該当ファイルを参考にして、現状の API の実装を把握すること。

[命令]
md_files/deepresearch_voice_record.md の該当部分（API 実装に関わる部分）を参考に、現存の meal analysis api 修正して音声入力に対応させたい。
既存の実装を利用しつつ、音声入力特有の Google Cloud Speech-to-Text v2 や NLU 処理 (DeepInfra LLM)はコンポーネントにしつつ実装してほしい。
一期にたくさんの機能を実装しないこと。細かな機能単位ごとに機能の Test をして実装した内容がきちんと動くことを確認して次の機能の実装に移ること。
テスト用のデータは test-audio/breakfast_detailed.mp3 に存在するので利用すること。
こちらで作業する必要がある部分や必要な情報があれば、その都度どのようにしたらいいか教えて。
