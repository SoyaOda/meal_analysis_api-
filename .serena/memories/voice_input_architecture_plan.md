# 音声入力対応アーキテクチャ計画

## 現在のアーキテクチャ理解
- FastAPIベースのコンポーネント化パイプライン
- Phase1Component（画像分析）→AdvancedNutritionSearchComponent（栄養検索）→NutritionCalculationComponent（栄養計算）
- 3段階でMealAnalysisPipelineが統合管理

## 音声入力拡張方針
1. 既存Phase1Componentと並列する新規Phase1SpeechComponentを作成
2. 後段のAdvancedNutritionSearchComponent、NutritionCalculationComponentは再利用
3. 新エンドポイント /api/v1/meal-analyses/voice を追加

## 実装アプローチ
1. **Phase1SpeechComponent**: 音声→テキスト→料理・食材抽出
2. **SpeechService**: Google Cloud Speech-to-Text v2統合
3. **LLMService**: DeepInfra LLMでのNLU処理
4. **VoiceAnalysisEndpoint**: multipart/form-data音声受信

## データフロー設計
```
Input (Audio) 
    ↓
Phase1SpeechComponent (音声分析)
    ↓ Google STT
Text Recognition
    ↓ DeepInfra LLM
Food/Ingredient Extraction
    ↓
AdvancedNutritionSearchComponent (既存再利用)
    ↓
NutritionCalculationComponent (既存再利用)
    ↓
Output (Same as image analysis)
```

## テストファイル
- test-audio/breakfast_detailed.mp3 等 6ファイル存在