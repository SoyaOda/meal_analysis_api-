# Lesson: model-refresh 第1サイクル（2026-06-11）— 新世代17候補スイープで flash に勝者なし。「モデル選択は天井」は 2026-06-11 時点でも有効。異種モデル ensemble も SC K=3 に優位なし。OpenRouter クレジット枯渇 402 → circuit breaker 連鎖で本番停止という運用事故も発生

- 日付: 2026-06-11
- 種別: did-not-work（モデル入れ替え）+ worked（仕組みの構築・検証）+ incident（クレジット枯渇）
- 関連 runs: `20260611_164346`（smoke5）/ `20260611_171546`（dev40 A）/ `20260611_171558`（dev40 B）/ `20260611_175340`（flash K3 vs K1）/ `20260611_181903`（sonnet rerun, 無効）
- prompt: v13_floor20（sha256 先頭 `0665ac4054c858dc`, len 2841, 本番同等）全候補同一。reranker_top_n=5（E7）, temp 0.3, reasoning medium, seed 1, K=1, cache=false
- 判定セット: dev40（スクリーニング段。rotation 昇格者なしのため Stage 2 は未実施）

## 背景
新モデル定期評価の仕組み（MODEL_REFRESH protocol）を構築し、第1サイクルを実走。
カタログ 338 モデル → image+reasoning+予算（≤10×baseline）で 75 件が未テスト → 新世代/フラッグシップ17件を選抜（Qwen3.5/3.6/3.7世代・grok-4.x・kimi-k2.6・claude-haiku-4.5/sonnet-4.6・gpt-5.2/5.4-mini・seed-2.0・minimax-m3・ernie-4.5-vl・step-3.7・nova-2・perceptron-mk1）。

## 結果（dev40, paired vs v13f_flash 同一run）

| candidate | MAE% | ΔMAE | paired BCa CI | lat(s) | $/img | verdict |
|---|---|---|---|---|---|---|
| v13f_flash (A/B/K3run) | 15.42 / 15.04 / 15.35 | — | — | ~16 | 0.0078 | **残留**（3draw std ~0.2 と極めて安定） |
| v13f_flash_k3 (K=3) | 14.22 | −1.13 | [−3.51,+1.25] | 19.3 | ~0.024実質 | 方向は pooled −2.5pt と整合 |
| gpt_52 | 17.31 | +1.90 | [−3.26,+6.35] | **13.6** | 0.0122 | reject（最接近・flashより高速だが点推定+1.9） |
| grok_43 | 18.71 | +3.30 | [−1.71,+8.79] | 27.1 | 0.0065 | reject |
| grok_420 | 20.36 | +4.94 | [−0.18,+10.46] | 24.2 | 0.0112 | reject |
| gpt54_mini | 20.53 | +5.11 | [−0.49,+11.01] | 18.3 | 0.0072 | reject |
| qwen35_397b | 20.04 | +4.99 | [−0.42,+13.00] | **67.5** | 0.0095 | reject（latency失格も） |
| qwen37_plus | 20.31 | +5.27 | [−0.26,+10.72] | **68.3** | 0.0061 | reject（同上） |
| kimi_k26 | 17.29 | +1.94 | [−3.07,+6.42] | **116.4** | 0.0160 | reject（latency 7×失格。fail15は402交絡） |
| step37_flash | 21.75 | +6.65 | **[+0.09,+12.39]** p=.047 | 37.2 | 0.0031 | reject（有意悪化） |
| minimax_m3 | 26.27 | +10.86 | **[+4.67,+17.47]** | 27.6 | 0.0015 | reject（有意悪化） |
| haiku_45 | 29.09 | +13.68 | **[+6.50,+22.40]** | 21.8 | 0.0135 | reject（有意悪化） |
| sonnet_46 | 29.44 | +14.05 | **[+7.44,+20.72]** p<.001 | 31.2 | 0.0294 | reject（チャージ後の再評価 run `20260611_183715` fail=0 で確定。signed +24.1 の系統過大＝haiku-4.5 と同パターンで Claude 系VLMはこのタスクで明確に劣後） |

smoke のみで脱落: qwen3.6-plus / qwen3.6-flash / seed-2.0-lite / ernie-4.5-vl-424b / nova-2-lite / perceptron-mk1（latency 30-128s and/or MAE 21-30）。

## 異種モデル ensemble PoC（オフライン・dev40 A素材・同一draw）
per-image 予測総kcalの median-of-3。最良 = flash+grok_43+gpt_52 → **13.71%**（flash単独15.42から−1.71pt）。
- ただし (a) 15組合せからの post-hoc 選択（selection bias）、(b) 同一モデル SC K=3 の実測 14.22 / pooled 期待 −2.5pt と同等以下、(c) コスト ~6.6× vs 3×、(d) server側未実装。
- **結論: HOLD（SC K=3 に対する clean 優位なし）**。再訪条件: flash 同等精度で誤差が脱相関した高速モデルが出たとき（gpt-5.2 系は素材として最有力だった）。

## worked（仕組み — 今後の正式運用ツール）
- `scripts/model_watch.py`: カタログ全量→未テスト×予算内の検知・config生成・pricing追記（実走済: 75件検知）
- `evals/knowledge/tested_models.json`: 既テスト集合レジストリ（39 entries・gitignore例外追加済み）
- `scripts/pool_paired_rotation.py`: pooled rotation 判定の正式実装（E1 v18 実データで正準値と完全一致・SET-SPECIFIC を正判定）
- `scripts/check_openrouter_credits.py`: 残高プリフライト（本事故からの再発防止）
- `docs/MODEL_REFRESH_PROTOCOL_20260611.md` + `/model-refresh` skill

## incident（運用事故・教訓）
1. **OpenRouter クレジット枯渇**: 残高低下に気づかず評価続行 → Group B 後半（kimi以降）で 402 連発 → **本番 Cloud Run も同一キーのため解析不能**（プローブで確認: "can only afford 2976 tokens"）。最終残高 −$0.16 / total $240。
2. **circuit breaker の候補間汚染**: 402 連発でサーバ内 OpenRouter breaker が開き、同一サーバプロセスを使う後続候補（sonnet）が即時全滅。**flaky な候補の後に走る候補の結果は breaker 汚染を疑うこと**。サーバ再起動で breaker はリセットされるが、根本は DEEP_REVIEW P1（breaker/retry stacking）。
3. 教訓→protocol 反映済み: 評価開始前に `check_openrouter_credits --min-usd <想定コスト×2>` を必須化。リスキーな候補（新規プロバイダ/重いモデル）は別 run に分離。

## 解釈
- 「モデル選択は天井」（2026-06-05 結論）は新世代（Qwen3.5-3.7 / grok-4.x / kimi-2.6 / claude-4.5-4.6 / gpt-5.2-5.4）に対しても成立。flash + v13_floor20 + E7 + SC K=3 が引き続き最良。
- dev40 GT は GPT-5-pro 推定だが、GPT系（gpt_52/gpt54_mini）が artifact 上振れし得る条件でも勝てなかった点はむしろ頑健な負け。
- 真の lever は引き続き E13（実測収集）→ E14（条件付き校正, in-domain で −18.5pt 実証済み）。

## 次サイクルへの引き継ぎ
- 再評価しない: 本 lesson の reject 全件（registry 記録済み）
- sonnet_46 はチャージ後（2026-06-11 同日）にクリーン再評価し reject 確定 → **17候補すべて決着・サイクル完全クローズ**
- watch トリガ: 月1 or メジャーリリース時 or baseline drift 時（protocol §3）
