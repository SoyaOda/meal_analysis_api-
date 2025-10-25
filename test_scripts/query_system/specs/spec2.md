食品名マッチングシステムにおけるCrossEncoder再ランキングの代替案提案
A. CrossEncoderの代替再ランキング手法

既存のCrossEncoder（cross-encoder/ms-marco-MiniLM-L-6-v2）に代わる再ランキング手法として、最新（2024～2025年）の主要アプローチを比較します。以下では、それぞれのアプローチの概要・特徴と要件適合性をまとめます。
1. MonoT5（T5ベースのポイントワイズ再ランキング）

    モデル例とリンク: castorini/monot5-base-msmarco-10k
    huggingface.co
    （Hugging Face上のT5-Baseモデル、MS MARCOで再ランキング用にファインチューニング済み）

    アーキテクチャ: Sequence-to-Sequence型（T5ベース）でポイントワイズにクエリと文書の関連度を判定。入力として「Query: ... Document: ... Relevant:」の形式でクエリと候補文書を与え、モデルは「true（関連あり）」または「false（関連なし）」といったトークンを生成します
    huggingface.co
    github.com
    。MonoT5はクロスエンコーダ同様にクエリと文書を同時にエンコードし、深い相互注意で意味的マッチングを判断します。

    推論速度: T5-Base（約2.2億パラメータ）モデルのため、CrossEncoder（MiniLM-L6, 約6千5百万パラメータ）より計算コストが高めです。CPU環境では候補5〜10件の再ランキングに推定100～200ms程度を要します（生成ステップ含む） 。GPU利用時は10件で50ms前後まで短縮可能です（バッチ生成の場合） 。※正確な速度は実装方法によりますが、CrossEncoder MiniLMより遅くなる傾向です。

    macOS対応: ✅ 問題なく動作します。PyTorch+Transformersで動作し、今回のNaN不具合の原因であるSDPA（Scaled Dot-Product Attention）実装にも依存しません（デコーダは通常softmax注意を使用）。

    長所: 高い精度が期待できます。MS MARCOデータで学習済みのため、ゼロショットでもBi-encoderのコサイン類似より関連性の判定精度が向上します
    huggingface.co
    。特にT5は生成モデルとして柔軟な言い換えを学習しており、**「fried potato」≒「french fries」**のような意味マッチにも強いと考えられます。またMonoT5はオープンソースでありローカル実行可能です。

    短所: 推論が比較的重い点です。エンコーダ・デコーダ型のため1ペア当たりの計算量が大きく、リアルタイム用途ではGPUがないと100ms以内は厳しい場合があります。また実装の複雑さ（中）：生成結果（"true"/"false"の確率）をスコアに変換するロジックが必要で、単純なスコア出力モデルより扱いが煩雑です。メモリ消費もT5-Base相当になります。

    コード例（推論）: ※各候補に対し関連度判定を生成する例です（transformersライブラリ使用）。

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
tokenizer = AutoTokenizer.from_pretrained('castorini/monot5-base-msmarco-10k')
model = AutoModelForSeq2SeqLM.from_pretrained('castorini/monot5-base-msmarco-10k')

query = "grilled chicken breast"
candidate = "Chicken, broilers or fryers, breast, meat only, cooked, grilled"
# QueryとDocumentをテンプレートに埋め込む
input_text = f"Query: {query} Document: {candidate} Relevant:"
inputs = tokenizer(input_text, return_tensors='pt')
output_ids = model.generate(**inputs, max_new_tokens=1)  # "true" or "false"を1トークン生成
result = tokenizer.decode(output_ids[0], skip_special_tokens=True)
print(result)  # "true"（関連度が高い場合）

    備考: DuoT5（ペアワイズ再ランカー）も同系列の手法です。DuoT5はクエリと2つの文書を同時に入力し、どちらが関連性高いかを判定するペア比較モデルです
    medium.com
    。精度向上が見込めますが、組み合わせ爆発的（候補間の全組み合わせ比較が必要）で推論コスト・実装複雑性が高いため、候補が5-10件程度ならMonoT5のポイントワイズ判定を繰り返す方が現実的です。

2. ColBERT（Late Interaction型再ランキング）

    モデル例とリンク: colbert-ir/colbertv2.0
    huggingface.co
    （Hugging Face提供のColBERTv2モデル）。ColBERT v2はBERTベースのマルチベクター表現モデルです。

    アーキテクチャ: Late Interaction（後段結合）型の二段階モデルです
    medium.com
    。クエリと文書をそれぞれ別個にBERTでエンコードし（オフラインでドキュメント側を前計算可能）、得られたトークンごとの埋め込み集合を用いてスコアリングを行います。具体的には、クエリの各トークン埋め込みと文書の各トークン埋め込み間の類似度（内積）を計算し、各クエリトークンに対して文書内で最大の類似度（MaxSim）を抽出、それらを総和した値を関連スコアとします
    medium.com
    。このLate Interactionにより、文書ごとにTransformerのフル計算を繰り返すことなくクエリ-文書間の詳細なマッチングが可能になります
    medium.com
    。

    推論速度: 非常に高速です（特に候補数が少ない場合）。ColBERTでは文書側をあらかじめエンコードしておけるため、実行時にはクエリ1件分のBERT推論＋軽量なベクトル計算だけで済みます
    medium.com
    medium.com
    。例えば1,398件のUSDA食品データを全て前計算し、クエリごとに5～10件をスコアする場合、実行時コストはクエリのエンコード（BERTベース1回）約50ms程度 + 内積計算(数万回程度)数msで収まります。候補を全件（1,398件）ColBERT検索する場合でも、MIPS（Maximum Inner Product Search）を工夫すれば100ms以下で完了するとの報告もあります
    medium.com
    medium.com
    。つまりリアルタイム要件（<100ms）には十分適合すると期待できます<small>
    medium.com
    </small>。

    macOS対応: ✅ 問題ありません。ColBERTは標準的なBERTモデルを内部で使用しており、macOS/MPS環境で問題となったFlashAttention系の機能を使いません（クエリと文書を別々に処理するため）
    medium.com
    。CPUでも動作し、Apple SiliconのMPSバックエンドでもBERTがサポートする範囲で動きます。

    長所: 高い精度と効率のバランスです。ColBERTは単一ベクトルのBi-encoderより精度が高く、かつクロスエンコーダほど遅くない「スイートスポット」に位置すると評価されています
    medium.com
    。大規模検索ではCrossEncoderなしでもほぼ同等の上位精度を達成し、大幅な速度向上が報告されています
    medium.com
    medium.com
    。小規模候補セットであればCrossEncoderの方が精度で若干上回る場合もありますが、ColBERTは12-layer BERTベースモデル相当の表現力を持つため、今回使用していたMiniLM 6-layerモデルより高精度なスコアリングが期待できます。また文書を事前計算できるので、システム全体のスループットを上げやすく、将来的にデータベースが増えてもスケールさせやすいです。

    短所: 実装の複雑さ（高）が挙げられます。ColBERTを導入するには、(1) 文書コーパス側のトークン別ベクトルの索引構築、(2) クエリ推論とMaxSim計算処理の実装、が必要です。既存のBi-encoder + CrossEncoder構成から外れ、独自にLate Interactionのスコア計算を組み込む設計変更が求められます。ただし、幸い公開実装やライブラリも整いつつあり（例：LanceDBのColBERT Reranker
    lancedb.com
    ）、Hugging Faceのモデルと組み合わせて実装することも可能です。また、メモリ使用量が増える点にも注意が必要です。各文書をトークン単位で768次元程度のベクトルにするため、1文書あたり数百トークンの場合メモリ消費は数万次元相当となります（1,400文書程度なら大きな問題ではありませんが、大規模コーパスではRAMやストレージ設計が必要
    medium.com
    ）。今回の規模では1,398文書 × 平均トークン数（例えば20 tokens）×768次元 ≈ 1,398×20×768 ≈ 21 million要素となり、浮動小数32bitなら約84MB程度と見積もられます（十分扱える範囲です）。

    コード例（概略）: ColBERTの推論は以下のように行います（シンプル化した疑似コード）:

from transformers import AutoTokenizer, AutoModel
# ColBERTモデル（BERTベース）のロード
tokenizer = AutoTokenizer.from_pretrained('colbert-ir/colbertv2.0')
model = AutoModel.from_pretrained('colbert-ir/colbertv2.0')
model.eval()

# 文書リストを事前エンコード（オフライン処理）
doc_embeddings = {}
for doc_id, doc_text in enumerate(usda_documents):
    inputs = tokenizer(doc_text, return_tensors='pt', truncation=True, max_length=128)
    with torch.no_grad():
        output = model(**inputs)  # BERTの最後の層出力取得
    token_embeds = output.last_hidden_state.squeeze(0)  # [seq_len, hidden_dim]
    doc_embeddings[doc_id] = token_embeds

# クエリに対する再ランキング（オンライン処理）
query = "grilled chicken breast"
inputs = tokenizer(query, return_tensors='pt', truncation=True, max_length=128)
with torch.no_grad():
    q_output = model(**inputs)
query_embeds = q_output.last_hidden_state.squeeze(0)  # [query_len, hidden_dim]

scores = []
for cand_id in candidate_doc_ids:  # TopK候補のDoc IDリスト
    D = doc_embeddings[cand_id]              # 文書のトークン埋め込み行列 [doc_len, dim]
    Q = query_embeds                        # クエリのトークン埋め込み行列 [query_len, dim]
    sim_matrix = torch.matmul(Q, D.T)       # 類似度行列 [query_len, doc_len]
    maxsim = sim_matrix.max(dim=1).values   # 各クエリトークンに対する最大類似度 [query_len]
    score = float(maxsim.sum())            # 総和をスコアとする
    scores.append(score)
ranked = [x for _, x in sorted(zip(scores, candidate_doc_ids), reverse=True)]
print("最上位候補ID:", ranked[0])

上記では簡潔化のためPyTorchテンソル操作をそのまま書いていますが、実際にはメモリ節約の工夫（例えば8-bit量子化やトークン数削減）や、高速化の工夫（PLAIDなどの高速内積検索アルゴリズム
medium.com
）も検討できます。ColBERTは実装負荷は高いものの、正しく構築すれば「毎候補にフルTransformer推論をしなくて良い」ため一度に数百〜数千候補を扱ってもレスポンスが高速というメリットがあります
medium.com
。
3. BGE-Reranker（BAAI提案のクロスエンコーダ再ランカー）

    モデル例とリンク: BAAI/bge-reranker-base
    huggingface.co
    （約2.78億パラメータ）, BAAI/bge-reranker-large
    bge-model.com
    （約5.6億パラメータ）, BAAI/bge-reranker-v2-m3
    bge-model.com
    （約5.68億パラメータ, 軽量高速型と記載）など。BAAI (北京智源研究院)が公開したBGEシリーズの再ランカーモデル。

    アーキテクチャ: クロスエンコーダ型です。元論文ではRetroMAEアーキテクチャを土台にしたモデルとされており
    zilliz.com
    、XLM-RoBERTaをベースにペア分類タスクで訓練されています
    bge-model.com
    。例えばbge-reranker-baseはXLM-R Base（12層, 2.78億パラメータ）で英中バイリンガル対応、bge-reranker-largeはXLM-R Large（24層, 5.6億パラメータ）です
    bge-model.com
    。v2シリーズは多言語対応を強化した改良版で、特にv2-m3は**「軽量クロスエンコーダで高速推論が可能」**とうたわれています
    bge-model.com
    。

    推論速度: 中程度です（モデルサイズに比例）。bge-reranker-base（約2.8億param）はCrossEncoder(MiniLM-L6, ~0.66億param)より遅いものの、5件程度の候補なら十分実用範囲です。目安として、baseモデルで10ペアあたり100～120ms前後、largeモデルで10ペアあたり200ms+程度と推定されます（CPU実行時）。BAAIはv2-m3を「軽量で高速」としているため、内部最適化（例えばエンコーダ層圧縮や蒸留）によって大型モデル並の精度を維持しつつ推論を高速化している可能性があります
    bge-model.com
    。公式ドキュメントでもbge-reranker-v2-m3は「強力な多言語対応かつデプロイ容易、高速推論」と紹介されています
    bge-model.com
    。Mac環境で実測した事例は見当たりませんが、XLM-R系モデルはFlashAttention非依存のためNaN問題は起こりにくく、単純な線形レイヤ処理であるCrossEncoderはCPUでも安定して動作するはずです。総じて、MiniLM CrossEncoderの数十msに比べると2～3倍遅いものの、100ms以内には収まる可能性が高いです。

    macOS対応: ✅ 対応可能です。PyTorch 2.7.1 + CPU/MPS環境で問題なく動作する見込みです。前述の通り、NaN問題は特定のAttention実装の不具合であり、BGEモデルはアーキテクチャが異なるため影響を受けません。またHugging Face経由でモデルをロードでき、Metal Backend (MPS)もTorch>=2.0でXLM-Rの推論をサポートしています。

    長所: 精度面でCrossEncoderの中でも高い性能が期待できます。BGE再ランカーは公開情報によれば埋め込みモデル（Bi-encoder）のスコアを上回る高精度を示し、MS MARCOやBEIRベンチマークでも優秀な成績を収めています
    huggingface.co
    bge-model.com
    。「embeddingモデルより強力なCrossEncoderモデル」として位置付けられており、特にlargeは精度重視、baseは軽量モデルとしてバランスが良いです
    huggingface.co
    bge-model.com
    。また多言語対応している点も特徴で、英語に加え中国語など他言語にも対応（USDAデータは英語ですが、食品名に固有名詞やラテン語などがあっても対処可能な語彙の広さが期待されます）。オープンソースでモデル重みが公開されており、sentence-transformersやFlagEmbeddingといったライブラリで手軽に利用できる点もメリットです。

    短所: 速度とリソース面でやや重いことです。CrossEncoderとしてはMiniLMよりパラメータ数が大きく、推論コスト・メモリ使用が増加します。特にlargeはMacのCPU環境ではギリギリ100msを超える可能性もあります。またドメイン特化ではない汎用モデルのため、食品名に関する細かなニュアンス（例：「broiled vs grilled」の違いなど）を学習しているかは未知です。ただしMS MARCOや大規模データで訓練されているため、ゼロショット性能はMiniLMより上と推測されます。

    コード例（推論）: SentenceTransformersのCrossEncoderクラスを利用するのが簡便です
    reddit.com
    。例えば:

from sentence_transformers import CrossEncoder
reranker = CrossEncoder('BAAI/bge-reranker-base')  # モデルのロード（初回は自動ダウンロード）
pairs = [(query_text, doc_text) for doc_text in candidate_texts]  # クエリと各候補のペアを準備
scores = reranker.predict(pairs)  # 各ペアの関連スコアを計算
best_idx = int(np.argmax(scores))
print(f"最も関連が高い候補: {candidate_texts[best_idx]} (score={scores[best_idx]:.4f})")

上記のように、CrossEncoderとしてBGEモデルを使えば現在のCrossEncoder実装と差し替えるだけで利用可能です
reddit.com
。出力スコアは大きいほど関連性が高いことを意味します
reddit.com
（Softmaxクロスエントロピーで学習しているため、対数尤度やシグモイド確率に相当する値です）。BGEのリポジトリでは、FlagEmbeddingという専用ラッパーでの使用例も示されています
bge-model.com
が、内部的には同様のスコア計算をしています
bge-model.com
。

    補足: BGE再ランカーはSentence-Transformers公式にも組み込みが始まっており
    sbert.net
    sbert.net
    、新しい再ランキング手法として注目されています。特にv2-m3モデルは軽量で多言語かつ最新の性能を持つため、今回の用途でも有力な選択肢になります（例えば食品ドメインに近い類義語対応や短文類似度でも高性能が期待できます）。一方で、モデルサイズが大きい場合はPyTorchの推論最適化（torch.compileやFP16モード）などで速度を稼ぐ余地があります
    bge-model.com
    。

4. Cohere ReRank相当モデル

    モデル例: （オープンソースで該当なし） Cohere社のRerank APIが知られていますが、モデル重量は非公開でありオープンソース提供はありません。ただし一部報告によれば、Cohereの再ランクモデル（例えばrerank-english-v2.0)はMiniLMベースのCrossEncoderに匹敵する性能を示すようです。オープンソースで近似するには、Cohereが公開した論文・モデルがないため代替としてBGEモデルが位置付けられます
    medium.com
    medium.com
    。

    アーキテクチャ: Cohereの再ランカーモデルは基本的にクロスエンコーダ型（TransformerのCLS出力をスコア化）と推測されます
    medium.com
    。したがって、BGEやMiniLM CrossEncoderと大きく変わるものではありません。

    推論速度: CohereのAPIではクラウド上で数十ms〜100ms程度とされていますが、ローカルで同等のモデルを持たないため省略します。

    macOS対応: Cohereのサービスを使わない限り関係なし。

    長所: 商用サービス利用時は高精度・高速ですが、今回は外部APIを使わずローカルで完結させる要件のため対象外となります。

    短所: オープンソースの重みがなくブラックボックスであること、コストがかかることなど。

    結論: Cohere再ランカーそのものは採用不可ですが、同等コンセプトのBGEモデルで代替可能と考えられます。

5. LLMベースの再ランキング（プロンプトによる比較）

    モデル例: google/flan-t5-small（80M）, google/flan-t5-base（250M）, google/flan-t5-xl（3B）, microsoft/phi-2（2.7B, Microsoftの小型LLM）など。あるいは7B前後の対話モデル（Llama2 7B Chat, Mistral 7B）を4-bit量子化して使う選択肢もあります。

    アーキテクチャ: プロンプト駆動型のLLMです。クロスエンコーダのようにファインチューニング済モデルを使うのではなく、生成AIにクエリと候補の情報を与え、一番関連の高い候補を出力させるという手法になります
    medium.com
    。例えばプロンプト設計として、「ユーザ質問: {クエリ}\n選択肢:\nA. {候補1}\nB. {候補2}\n...\n質問: 上記のうち最も関連する食品はどれ？」のように指示し、モデルから最も関連する候補の記号や名前を生成させます。このようにリスト全体を一度に評価（リストワイズ）させる方法や、あるいは候補同士をペアで比較して勝ち残りを決めるトーナメント方式（ペアワイズ）などが考えられます。Flan-T5などは命令調整済みで比較的フォーマットに従った応答を生成しやすく、適した候補です。

    推論速度: 遅い傾向です。小型LLMとはいえ、数億〜数十億パラメータのTransformerをプロンプト長に応じてデコードするため、CPU上では1リクエスト1000ms以上になることもあります
    medium.com
    。例えばFlan-T5-base（2.5億param）でも、クエリ+5候補のテキストを与えるとCPUで数百ミリ秒〜1秒程度かかるでしょう。Flan-T5-small（8000万param）ならもう少し速く数百ms未満に収まる可能性もありますが、精度面が不安です。また、7Bクラスの対話モデルを4-bit量子化して用いる場合、CPUでの推論は1秒以上になるのが一般的です（ただしApple SiliconのANEを活用するllm.int8()や、Metal対応の4-bit推論ライブラリが将来的に改善すればもう少し速くなる可能性もあります）。リアルタイム要求の100ms以内を満たすのはGPUがない場合難しいでしょう
    medium.com
    。一方、GPU使用が可能であれば（Cloud RunでGPUコンテナなど）、Flan-T5-xl(3B)をFP16でデプロイし1入力100ms程度で出力させる、といった構成も考えられます。

    macOS対応: ✅ モデル自体は動作します。TransformersライブラリでFlan-T5やLlama2などをロード可能ですし、Metal MPSによる加速やCPU実行もできます。ただし大規模モデルはメモリ要件が高く、M1/M2のRAMやVRAM上で動かすには4-bit量子化やバッチ1推論が前提です。今回対象の小～中規模モデル（～3B）はMac 32GB RAMであれば問題なくロードできる見込みです。

    長所: 柔軟性と高度な推論です。LLMはクロスエンコーダのように固定の関連度スコアを学習したものではなく、任意の基準でリランキングできる柔軟性があります
    medium.com
    。例えばプロンプト次第で「最新の情報に基づき○○を優先せよ」や「ユーザの意図を汲んで専門的観点から評価せよ」といった複雑なルールを適用した再ランキングも可能です
    medium.com
    。今回の用途ではそこまで複雑なルールは不要かもしれませんが、LLMに**「人間並みの類推能力」を使ってもらうことで微妙な差異（grilled vs broiledなど）も説明しながら判断させることもできます。また追加の学習不要で手元のモデルを流用できる点もメリットです。小型LLMでも、例えばGeminiやMistralといった新興モデルには特定タスクで大モデルに匹敵する性能を示すものもあり
    medium.com
    、工夫次第ではクロスエンコーダに近い精度**を出せる可能性もあります。

    短所: 推論のコスト・遅延です。LLM呼び出しは一般に高レイテンシ・高コストとなります
    medium.com
    。特に長いリストや詳細なプロンプトを与えると応答に秒単位の時間がかかり、ユーザ向けリアルタイム処理には不向きです
    medium.com
    。今回の5～10件程度ならまだ短い方ですが、100ms以下は厳しいでしょう。また応答の安定性の問題もあります
    medium.com
    。プロンプトに対するLLMの出力は確率的で、「AかBか答えよ」という問いでも別の表現で返したり間違えたりする可能性があります。厳密なランキングスコアが直接得られないため、プロンプト設計と出力解析に工夫が必要です。例えば5候補からベスト1を選ばせる場合、LLMの出力をパースして該当候補をマッチさせるロジックが必要です。実装難易度（中）と言えます。またLLM自身が事前知識に依存するため、食品の栄養に関する一般知識で誤った連想をするリスク（幻覚）もありえます。最後に精度の保証が難しい点も課題です。再ランキングを「関連性の高い順に出力せよ」と指示しても、モデルの内部評価基準がクロスエンコーダほど一貫していない場合があります
    medium.com
    （この点は小型LLMを再学習するか、あるいはRanking用にディストイルされたLLMを使うことで多少改善できますが、現状では未知数です）。

    コード例（ペアワイズプロンプト）: Flan-T5を用いて候補ペアの関連判定を行う例です。

from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
model = AutoModelForSeq2SeqLM.from_pretrained('google/flan-t5-small')
tokenizer = AutoTokenizer.from_pretrained('google/flan-t5-small')

query = "grilled chicken breast"
cand1 = "Chicken, broilers or fryers, breast, meat only, cooked, grilled"
cand2 = "Turkey, breast, meat only, cooked"
prompt = (f"質問: 「{query}」に最も関連が深いのはどちらの食品ですか?\n"
          f"A: {cand1}\nB: {cand2}\n答え: ")
inputs = tokenizer(prompt, return_tensors='pt')
outputs = model.generate(**inputs, max_new_tokens=5)  # "A" または "B" を出力
answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(answer.strip())  # 例: "A"

上記では2候補を比較させています。このようにペアごとにLLMに質問し勝者をトーナメント式に決めることもできますし、5件を一度に与えて「最も関連が高いのはどれか？」と問うこともできます（後者の場合プロンプト設計が少し難しくなります）。小型LLMの利用はあくまで実験的な位置づけですが、今後LLMをRAG（Retrieval-Augmented Generation）で再ランキングに使う例も増えてきており
medium.com
、将来的な拡張性として検討する価値があります。

    量子化: なお、小型LLMを実用時間内に動かすにはモデルの量子化が有効です。例えば4-bit量子化すればメモリ使用量が約1/2になり、CPUでの演算も多少高速化します（ただし主にメモリ帯域依存のため劇的ではない）。Apple Siliconの場合、MetalでのINT8/INT4サポートはまだ限定的ですが、GPUを用いるのであればbitsandbytesなどでINT8化したモデルをロードすることも可能です。現状ではまずCrossEncoder系で目的を達し、LLM再ランキングは特殊用途に限定するのが無難ですが、「精度最優先でコスト許容」という状況ならLLM使用も検討できます
    medium.com
    。

6. 改善版Bi-encoder（Sentence-BERTモデルの強化案）

現行のフォールバック手段である**「Bi-encoderのコサイン類似度で再ランキング」**自体を高精度化するアプローチです。CrossEncoderやLLMを使わず、エンベッディングモデルを工夫して再ランキング精度を高めます。

    アプローチ例:

        別のSentence-BERTを再ランキング用に使用: 現在Stage1ではall-MiniLM-L6-v2を使用していますが、Stage2ではより高精度なBi-encoderモデルで再スコアする方法です。例えばsentence-transformers/all-mpnet-base-v2（MPNetベース, 768次元）はMiniLMよりスコア精度が高く、STSベンチマークで約87-88のスコアを持つモデルです【ユーザー実装計画より】。Stage1をMiniLM（高速）で候補取得、Stage2をMPNet（高精度）でコサイン類似度再計算すれば、若干ではありますが順位精度向上が期待できます。また、他にも領域特化モデルの利用も考えられます。食品ドメインに近いものとして、料理レシピコーパスで学習したRecipeBERTや、飲食レビューから学習したモデルなどが公開されていれば試す価値があります（ただし汎用モデルより精度が保証できない場合もあります）。

        アンサンブル（Ensemble）: 複数のBi-encoderモデルのスコアを組み合わせる方法です。例えばMiniLMとMPNetのコサイン値の平均をとる、あるいは乗算するなどして総合スコアを算出します。異なるモデルは異なるクセを持つため、アンサンブルすることでノイズが低減し精度が上がる可能性があります。実装も比較的簡単で、複数モデルの埋め込みを得てスコア計算するだけです。

        ファインチューニング: 手元に食品名ペアの類似度データ（正解ラベル）があるなら、Bi-encoderをそのデータで微調整することもできます。例えば類義語のペア（french fries ↔ fried potato を正例とする等）を作成し、コサイン類似度が高くなるようTriplet Lossで学習させれば、食品ドメイン特化の埋め込みが得られます。学習データの用意は大変ですが、USDAデータ内のバリエーションや既存システムで集めたマッチ結果を活用できるかもしれません。

        ニューラル+素朴な特徴の併用: Bi-encoderのコサインスコアに文字列マッチ度合いや語彙の重なりを加味する方法です。例えば、クエリと候補の間で共通単語の数やBM25スコアを特徴量とし、それを最終スコアに線形結合する簡易モデルを作ることができます。実装上は「最終スコア = cos類似度 + λ * (BM25スコア)」のようにします。BM25スコアはrank-bm25等のライブラリで計算でき、コサインでは捉えきれない表記揺れを補完します
        medium.com
        。研究では、Dense埋め込みとBM25のハイブリッドで精度向上が見られる例も多く、例えばDense検索結果をBM25で再ランクする手法では「BERTのセマンティック理解」と「BM25のキーワード厳密マッチ」を組み合わせてより正確な検索結果が得られたと報告されています
        medium.com
        。今回でも、候補5件程度なら明示的に単語マッチを見ることで例えば*「chicken」と「turkey」なら前者の方が“chicken”を含むから有利*といった調整ができます。

    推論速度: これらBi-encoder強化策は基本的に高速です。なぜならクロスエンコーダのようなペア入力は不要で、クエリと候補を別々に埋め込めばよいからです。Stage2用にMPNetを使う場合でも、クエリと候補K件の埋め込み計算を行うだけなので、K=5なら6回の埋め込み計算（クエリ1+候補5）です。MPNet埋め込みはMiniLMより遅いですが（約5倍程度【ユーザー計画より】）、5件程度なら数十msで完了します。また候補側の埋め込みはStage1と同じものを使い回すことも可能です。Stage1でMiniLM埋め込み→FAISS検索していますが、そのTop5のMiniLMベクトルは既に取得済みです。それをそのままcos類似度で再スコアするのが現在のフォールバックですが、別モデルで再エンコードするには候補テキストをもう一度処理する必要があります。一応、USDA全件を別モデルで前計算しておきFAISSとは別のベクトルで保持しておけば、Stage2用に即座に呼び出すこともできます。例えばMPNetで全1,398件のベクトルを事前算出し、Stage1ではMiniLMで絞り込み、Stage2でMPNetベクトルを参照してcos計算、という構成です。このように工夫すれば、**速度面では依然非常に高速（<30ms程度）**で動作可能です。

    macOS対応: ✅ 当然問題ありません。既存のSentence-Transformerを差し替えるだけなので、macOS+PyTorchでの動作は良好です。

    長所: 実装が容易で高速、そして比較的安全なアプローチです。CrossEncoderのバグに悩まされたり、複雑な新モジュールを導入するリスクがありません。同じ枠組みでモデル名を変える・スコア計算を変えるだけなので、コード変更も最小です。また組み合わせ自由度もあり、例えば「MPNetコサイン 0.7 + MiniLMコサイン0.3」のように重み付け平均するなど調整も効きます。精度面ではクロスエンコーダほど飛躍的向上は望めませんが、多少でも性能向上させつつ安定稼働させたい場合には有力です。

    短所: 精度限界があります。結局どんなBi-encoderでもクエリと文書の表現を独立に作成するため、クロスエンコーダが捉えるような微妙な単語間相互作用は捉えにくいです
    medium.com
    。例えば「chicken」と「turkey」はembedding空間では近くなるかもしれませんが、「grilled chicken breast」というクエリに対して「cooked, roasted chicken breast」と「cooked turkey breast」のどちらが適切か、という判断では、Bi-encoderは各文書の類似度スコアに大差が出ない可能性があります。クロスエンコーダなら「turkey」は鳥の種類が違うからスコア減と判断できても、Bi-encoderはそこまで繊細に区別できないことがあります。従って、Bi-encoderの改良はあくまで現状のフォールバック（MiniLMコサイン）のマシな代替にはなってもCrossEncoder並の精度向上は困難です。

    コード例: （MPNetによる再スコアリングの例）

from sentence_transformers import SentenceTransformer, util
bi_encoder = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
query_emb = bi_encoder.encode(query_text)
# Stage1で得たTop-K候補テキストの埋め込みを計算（または事前算出のベクトルをロード）
doc_embs = bi_encoder.encode(candidate_texts)
# コサイン類似度を計算
scores = util.cos_sim(query_emb, doc_embs)[0].tolist()  # shape: (1, K) をリストに
best_idx = int(np.argmax(scores))
print(f"Bi-encoder再ランク上位: {candidate_texts[best_idx]} (score={scores[best_idx]:.3f})")

（※簡潔化のためエラー処理等省略）
7. Sparse再ランキング手法（SPLADE・BM25ハイブリッドなど）

Embeddingベースでは拾いきれない語彙マッチの要素を取り入れるため、スパース手法を再ランキングに活用するアプローチです。具体的には、SPLADEのようなニューラルスパースモデルや、BM25など従来手法とのハイブリッドを検討します。

    SPLADEによる語彙拡張: SPLADEはSparse Lexical and Expansionモデルの略で、BERTのマスク言語モデル(MLM)ヘッドを利用してテキストを高次元のスパースベクトルにマップする技術です
    huggingface.co
    sbert.net
    。簡単に言えば、各テキストについて重要な語彙がどれかを重み付きで示すベクトルを出力します（次元は語彙数、例えば30522次元）
    huggingface.co
    。このベクトルをクエリと文書で内積すれば、BM25のように共通語彙のマッチ度合い＋αを計算できます
    sbert.net
    。SPLADEは語彙の「穴埋め」能力に優れ、例えば**「fried potato」→「fries」のように関連語を予測してベクトルに反映**します
    pinecone.io
    。これにより、クエリと文書で直接語が一致しなくても、類義語や言い換えを介したマッチが実現できます
    pinecone.io
    。言い換えると、**語彙ミスマッチ問題（vocabulary mismatch）**をMLモデルで緩和するものです
    pinecone.io
    。食品名のように多様な表現（例: beef steak vs steak, beef）がありうる領域では、この手法が有効と考えられます。

        使用方法: Hugging Faceの naver/splade-cocondenser-ensembledistil 等のモデルをロードし、model.encode_query("..."), model.encode_document("...")でスパースベクトルを取得、内積計算でスコアリングします
        sbert.net
        。これにより、従来のBM25にニューラルネット由来の類義語展開を組み込んだようなスコアが得られます。

        速度: クエリと文書をそれぞれBERTでエンコードするコストがありますが、文書側は前計算可能、クエリ側も1回です。文書ベクトルはスパースなので計算量も小さいです。実質、ColBERTと同程度に高速でしょう。

        Mac対応: ✅ BERTベースなので問題ありません。

        長所: 語彙マッチの補完に優れます。embedding法では「AとBは似ている」が分かっても、共通単語の存在自体を強く評価はしません。SPLADE由来のスコアを足すことで「共通単語が多い候補は順位アップ」できます。実際、Dense + Sparseのハイブリッドは検索精度を向上させる定石になりつつあります
        pinecone.io
        pinecone.io
        。また小規模データならSPLADE単独で検索も可能です。1,400件程度であればクエリをSPLADE化→全件と内積で上位取得も容易で、embeddingと別の観点から上位候補を得られます。

        短所: 実装難易度（中～高）です。SPLADEを直接使う場合、出力が高次元すぎてそのままでは扱いづらいですが、幸いSentence-Transformersに統合されつつあり
        sbert.net
        、比較的簡単に内積計算できます。ただ、Denseとのスコア統合や閾値調整などチューニングが必要です。またモデルサイズもbaseクラスのBERT並で、動作にそれなりのメモリを要します。精度面では、MS MARCOでの評価ではSPLADEがCrossEncoderには及ばないとの報告もあります
        sbert.net
        （単体MRRで約0.38程度、一方クロスエンコーダは0.40超えも）。従って、SPLADEは単体でなく他モデルと組み合わせてこそ威力を発揮する側面があります。

    BM25による補正: より単純には、BM25スコアを再ランキングに用いる手法も考えられます。例えばStage1の結果5件に対し、それぞれクエリとのBM25スコアを計算し、それをCrossEncoderやBi-encoderのスコアと線形結合する方法です。
    medium.com
    にもある通り、Denseモデルの結果をBM25で並べ替えるだけでも精度向上が見られるケースがあります。実装は簡単で、rank_bm25ライブラリでクエリと各候補のスコアを出し、CrossEncoder等のスコアと正規化して加算するだけです。

        例えば最終スコア = CE_score + μ * (BM25_score) とし、μを0.1～0.5で調整するといった方法です。BM25スコアは値のスケールが異なるため、適切に正規化（例えば最大値で割る）するか、あるいは対数を取る等してから加算します。

        BM25自体は高速（数ms以下）で、Python実装でも問題ありません。1,400件程度なら全件計算でも瞬時です。

        短所は、完全一致の語が一つも無い組み合わせ（例: クエリと候補が全く異なる語で書かれているケース）ではBM25は0点となり差が付かない点です。この場合はembeddingやCrossEncoderに頼るしかなく、BM25は効果を発揮しません。しかしcommonな単語（チキン→チキン、フライ→フライ等）が含まれる場合には有効なシグナルとなります。例えば**「french fries」 vs 「fried potato」ではembeddingやクロスエンコーダも高スコアでしょうが、BM25なら「fried」「potato」が「fries」と共通語幹でなくスコア0になる懸念があります（この例ではSPLADEが効果的です）。一方「chicken breast」 vs 「Chicken, breast, cooked」**ではBM25も高スコアを与え、embeddingと同じ判断を補強するでしょう。

    総合評価: Sparse手法はDense手法を補う位置づけです。最終的なランキングを決める際に、「意味的に類似かつ用語も一致している」候補を上位に押し上げる効果があります
    medium.com
    。従って、CrossEncoderやBi-encoderのスコアに重みをつけて加算する方法が有効です。このハイブリッドは近年多くの実システムで採用されつつあり
    analyticsvidhya.com
    、特に高精度志向の検索ではベストプラクティスになりつつあります。

以上、7つのアプローチ（MonoT5、ColBERT、BGE、Cohere相当、LLM、Bi-encoder改良、Sparse/BM25）を概観しました。それぞれを比較するため、次にまとめの表を示します。
B. 手法比較サマリー

各手法について、macOSでの技術的適合性・速度・精度傾向・実装難易度を一覧表にしました（速度は候補10件ペアをCPU推論した場合の目安、精度はCrossEncoder(MiniLM)比の概算、実装難易度は本システムへの組み込み作業量の主観評価です）。
手法	モデル例・規模	推論速度（10ペア）	macOS対応	精度（対CrossEnc）	実装難易度
CrossEncoder (基準)	ms-marco-MiniLM-L-6-v2 (66M)	約 60ms (※NaN問題)	⚠️ 不具合発生	基準 (96% Top-1)	低
MonoT5 (ポイントワイズ)	castorini/monot5-base-msmarco (220M)	150–300ms (CPU推定)
★GPUで~50ms	✅ 問題なし	やや高 (◎意味類似)	中 (生成処理)
DuoT5 (ペアワイズ)	（例）castorini/duot5-base	500ms+ (全ペア比較)	✅ 問題なし	高 (◎精度最良)	高 (組合せ多数)
ColBERT (Late Interaction)	colbert-ir/colbertv2.0 (110M×2)	~50ms (事前計算活用)
★全件比較100ms台	✅ 問題なし	高 (◎CrossEnc級)	高 (設計変更)
BGE CrossEncoder	BAAI/bge-reranker-base (278M)	100–120ms (CPU推定)
★MPS支援で短縮可	✅ 問題なし	高 (◎精度良)	低 (置換するだけ)
　　　　　　　	BAAI/bge-reranker-large (560M)	200ms+ (CPU推定)	✅ 問題なし	最高 (◎精度優)	低 (同上)
　　　　　　　	BAAI/bge-reranker-v2-m3 (568M)	~150ms? (軽量高速型)	✅ 問題なし	高 (◎多言語強)	低 (同上)
Cohere ReRank	Cohere API (推定110M)	– (外部API)	❌ ローカル不可	高 (◎優秀)	低 (API呼出のみ)
LLM（小型）	google/flan-t5-base (250M)	500ms (生成あり)
★GPUで~100ms	✅ 問題なし	不明 (△要工夫)	中 (プロンプト)
　　　　　	microsoft/phi-2 (2.7B)	1s以上 (CPU)
★GPU推奨	✅ 問題なし	中 (△汎用常識)	中 (出力処理)
Bi-encoder+	all-mpnet-base-v2 (110M)	約 30ms (流用可)	✅ 問題なし	やや低 (△CrossEnc劣)	低
　　　　　	カスタムSentence-BERT	30–50ms (事前計算)	✅ 問題なし	中 (☆学習次第)	中 (学習要)
Sparse/BM25	naver/splade-cocondenser (110M)	50ms (事前計算)	✅ 問題なし	中 (◎補完的)	中 (併用調整)
　　　　　	BM25 (Lucene/Rank-BM25)	<10ms	✅ 問題なし	低 (単独は弱)	低

★はGPU使用時の参考事項、◎/○/△/☆は精度に関する注記です。

表の補足:

    CrossEncoder (MiniLM): Baseline。推論高速だがmacOS+PyTorch2.7.1ではNaN障害
    huggingface.co
    。精度はテストでTop-1正解率96%（ユーザー報告）だが、同モデルのMac不具合あり。

    MonoT5: 精度はMiniLM CrossEncより高いと推測（MS MARCOでMonoT5-3BがSOTA級
    arxiv.org
    、BaseでもCrossEnc(BERT)級）。ただCPUで遅い。GPU環境前提なら有力。

    DuoT5: 精度最も高い可能性（ペア比較学習のためRank戦略に最適化）があるが、組み合わせ推論爆発で現実的でない。大規模実験用。

    ColBERT: 精度はCrossEnc(BERT base)に匹敵
    medium.com
    。候補数少ない場合CrossEncの方が若干有利とも言われるが、MiniLMとの比較ならColBERT優位と推測。超高速でスケールし、Macでも安定動作。

    BGE: CrossEnc型で高精度。特にlargeは強力だがCPUではギリギリ。baseやv2-m3なら実用的高速。macOS可。

    Cohere: ローカル実行できないため除外。ただ高性能な再ランクとして知られる（参考：Cohere ReRank性能が一部記事で紹介
    medium.com
    ）。

    LLM: 精度は未知数。タスク依存で小型LLMでも大健闘例がある一方、安定しない場合も。柔軟だが遅い。GPU必要なら今回スコープ外気味。

    Bi-encoder+: 簡易に導入できるが、精度はCrossEncには及ばない
    github.com
    。ただMiniLM→MPNet等で微向上は見込める。高速・安全策。

    Sparse/BM25: 補助的手法。組み合わせで精度底上げ。単独ではCrossEncに遠く及ばないが、Denseと組み合わせでシナジー
    medium.com
    。導入コスト中程度。

以上を踏まえ、次章で具体的にどの手法を採用すべきか提案します。
C. 推奨ソリューションの選定

上記の比較より、今回の要件（macOS対応・<100msリアルタイム・精度向上・実装容易性）に照らして最適な再ランキング手法トップ3を提案します。その後、最も推奨する方法について詳述し、併せてバックアッププランも示します。
1. 推奨候補トップ3

(1) BGEクロスエンコーダ（Baseモデル） – 最有力候補
理由: 現行CrossEncoderと同じ枠組みで置換でき、macOS上でもNaN不具合なしで動作可能。【実装コストが極めて低く】、モデルを切り替えるだけでStage2を再度機能させられます
reddit.com
。精度面もMiniLMより良く、意味的類似の見極めにも強い
bge-model.com
。英語テキストにも最適化され、短文のニュアンスも高精度に捉えられるでしょう。Inference速度も十分高速（5件なら~60ms程度）で要件内です。BAAI公式が「高速・多言語」とうたうbge-reranker-v2-m3も魅力的です
bge-model.com
が、まずはbaseモデルから試し、問題なければlargeへの切替やv2系の検証をするステップが良いでしょう。macOS/MPS環境でも安定動作が見込まれます。総合的に、BGE再ランカーは現在のシステムに最小の変更で最大の効果をもたらす代替策です。

(2) ColBERT（Late Interactionモデル） – 次点候補
理由: 技術的には極めて魅力的で、高速かつ高精度を両立します
medium.com
。特にUSDAデータベースのような固定コーパスではドキュメントを前計算できるため、ランタイムの計算コストを削減できます。将来的にデータ件数が増えてもスケーラブルで、検索システム全体のアーキテクチャ改善にもつながります
medium.com
medium.com
。食品名のような短いテキスト間の細かな差異（部位違いや調理違い）もトークンレベルで評価でき、CrossEncoderに迫るリランキング品質が期待できます。一方で実装難易度が高いため、開発コストとリスクが上がります。現行システムを大きく変えずに済ませたいなら優先度は下がります。ただ、もし時間とリソースに余裕があり、検索精度を最大化したい場合は導入検討の価値があります。特にmacOSでもPythonで構築可能ですので、プロトタイピング自体は可能です。以上より、本番対応としては第2候補とします。

(3) MonoT5（T5ベース再ランカー） – 条件付き候補
理由: 精度重視であればMonoT5も有力です。Zero-shotの関連性判断能力が高く、MS MARCOタスクで実証済みです
huggingface.co
。食品ドメインに直接適用しても、類義語や言い換えを理解した判断が期待できます（T5は「ポテト＝フライ」のような知識も持ち合わせています）。実装もPyGaggle等を用いれば比較的簡単です
github.com
。しかし速度面の懸念があります。macOS CPUではリアルタイムにはやや厳しく、GPUが使える環境で力を発揮する手法です
medium.com
。Cloud RunにGPUオプションを付けられるか、あるいは将来的にGPUサーバを使う計画があるなら、MonoT5の採用も視野に入ります。もしGPU前提ならMonoT5はCrossEncoderより一段上の精度を狙えるでしょう。ただ現状では環境制約上、優先度3番手としました。

補足: 上記以外にもCrossEncoder (MiniLM-L-12-v2) という単純な代替も考えられます。実際、ユーザ報告では「MiniLM-L-12（12層版）はMacでもNaNが出ない」とありました
huggingface.co
。もしBGEモデルで予期せぬ問題が出た場合、応急処置としてMiniLM 12層版に切り替えることもできます。こちらは従来モデルと同系列で、推論速度は6層版の約2倍（5件で~60ms）と見込まれます。精度もわずかに向上するでしょう。実装コストも低いので、頭の片隅に置いておく価値があります。
2. 最適解: BGEクロスエンコーダの詳細

上記トップ3の中で、総合的に最もおすすめするのは 「BGE再ランカー（baseモデル）の導入」 です。以下、この選択の理由と導入手順について説明します。

選定理由の総括: BGEモデルはmacOS上の技術的不安要素を解消しつつ、現行CrossEncoderを置き換えて精度向上を実現できる点が大きいです。具体的には:

    ① Mac不具合の回避: MiniLMで発生したNaN問題に悩まされることなく、PyTorch 2.7.1 + CPU/MPS環境で安定して動作します
    huggingface.co
    。XLM-Rベースのモデルであり、SDPA実装のバグには関与しないからです。

    ② 精度向上: BGEはMS MARCO等で訓練されBi-encoderより高精度と評価されています
    huggingface.co
    。食品名マッチでも、たとえば「grilled chicken breast」を入力した際、MiniLMよりもニュアンス差異を捉えたスコアリングが期待できます。日本の公開情報は少ないですが、多言語対応の恩恵で**「broil」と「grill」など表現違い**にも強い可能性があります（XLM-Rは多様な語彙を学習しているため）。

    ③ 実装容易性: Sentence-Transformersライブラリからワンライナーで利用できるので、既存コードのCrossEncoder初期化部分をCrossEncoder('BAAI/bge-reranker-base')に変えるだけで実装できます
    reddit.com
    。推論呼び出し（predict）も同じインターフェースです
    reddit.com
    。従って開発工数が非常に少なく済みます。

    ④ 性能面のバランス: 5候補程度なら十分な速度（数十ms）を維持できます。仮にMiniLM比で2倍時間がかかっても、以前のCrossEncoderが約40-60ms/クエリだったことを考慮すると、80-120ms程度と想定され実用範囲内です。さらにM1/M2チップのニューラルエンジンやGPU(MPS)を活用すれば、実時間を短縮できる可能性もあります（torchでは自動では使われませんが、ONNXに変換してCoreML使用など検討余地あり）。しかしそこまでしなくともCPUのみで問題ない見込みです。

    ⑤ 将来性: BGEシリーズは今後も改良が続くと予想されます
    github.com
    。例えばより大きなbge-reranker-largeへのアップグレードや、ユーザニーズに応じた多言語対応など拡張性があります。Cohere APIに頼らずオープンなエコシステムでメンテされている点も安心です。

    ⑥ 現行構成との親和性: 2段階検索のStage2としてクロスエンコーダを用いるという構成自体はそのままであり、システム全体のアーキテクチャを大きく変えずに済みます。すでに構築されたFAISS + CrossEncoderパイプラインにそのまま適用可能で、リファクタや新モジュール学習が不要です。

以上より、BGEモデルへの切替が最短時間で問題を解決し、性能も向上できるベストプラクティスと判断しました。

コードスニペット: 推奨ソリューションであるBGE再ランカーの使用例を示します。Stage1のFAISS検索結果candidates（例: テキスト候補リスト）を再ランクして1位を選ぶ処理です。

from sentence_transformers import CrossEncoder

# 1. モデルロード（初回は自動でモデルをダウンロード）
reranker = CrossEncoder('BAAI/bge-reranker-base')

# 2. 上位K件の候補ペア（クエリ, 候補テキスト）を作成
query = "grilled chicken breast"
pairs = [(query, cand_text) for cand_text in candidates]  # candidatesは候補文字列リスト

# 3. スコア計算とソート
scores = reranker.predict(pairs)               # 各 (query, doc) にスコア（スコア高いほど関連性大）
best_index = int(np.argmax(scores))            # 最高スコアのインデックス
best_match = candidates[best_index]
best_score = scores[best_index]

print(f"Top match: {best_match} (score={best_score:.4f})")

上記は非常にシンプルですが、期待通りNaNも発生せず動作するはずです。実際にこのコードをMac上で試し、CrossEncoder(MiniLM)でNaNだったケースが改善することを確認します。

結果の利用: 得られたbest_matchが最終的にユーザに提示する食品名マッチ結果となります。必要に応じてスコア閾値を設け、「スコアが低すぎる場合は“該当なし”とする」といったロジックも加えられますが、CrossEncoderの場合トップ1をそのまま採用する運用でも問題ないでしょう（現在96%精度とのことなので、おそらく常にTop1を返している）。
3. フォールバック戦略

推奨するBGE再ランカー導入後でも、万一想定外の問題が生じた場合に備えてバックアップ策を用意しておきます。

    Fallback 1: CrossEncoder MiniLM-L-12 – BGEモデルで何らかの不具合（モデルサイズのメモリ不足や新たなバグ）が発生した場合、元のMiniLM 6層を12層版に差し替えて使用する案です。ユーザ報告ではMacでも動作しているとのことなので
    huggingface.co
    、急場しのぎには有効です。精度も若干向上します。ただし依然としてScaled Dot-Product Attentionを使用するTransformerには変わりなく、PyTorchやOSのアップデートで状況が変わらない限り根本原因が解決していない点に注意です。あくまで一時的フォールバックとします。

    Fallback 2: Bi-encoderコサイン – 最悪の場合、現行のBi-encoderコサイン類似度方式に戻すことも考慮します。これは現在一時対処で使っている手法で、精度的には劣りますがNaNなどの不安はありません。もしCrossEncoder系統がすべて使えない最悪の事態（例えばPyTorchの不具合が他モデルにも及ぶなど）が起きた場合には、サービス継続性を優先しBi-encoder類似度に退避する判断も必要です。その際、上記で提案したBi-encoder改良策（MPNet使用やHybridスコアリング）を適用し、可能な範囲で精度低下を補います。

    Fallback 3: ColBERTへのスイッチ – BGEでは満足な結果が出ない場合、設計を変更してColBERT方式に切り替えることも検討します。ただし開発工数が大きいため、即座のフォールバックにはなりません。中長期的な改善プランとして、BGEで精度不足が見られたり、将来的にクエリあたり候補数やQPS（queries per second）が増大した際のボトルネック解消策として位置付けます
    medium.com
    medium.com
    。

フォールバックはいずれもシステムが停止しないようにする保険です。基本方針としては、可能な限りCrossEncoder(BGE)で解決し、それが難しければ順次安全な代替に退く流れです。
D. 実装チェックリスト

最後に、推奨手法（BGE再ランカー）を導入する際の実装手順のチェックリストを示します。これに沿って作業することで、確実に移行を完了させます。

    環境準備: 必要ライブラリのインストールを確認する。特に最新の sentence-transformers (v5.1.0以上) と transformers (v4.57.1以上) が入っているか確認。これらは既に導入済みだが、BGEモデル利用に問題ないバージョンか検証する（sentence-transformersはHuggingFaceモデル互換があるか確認
    reddit.com
    ）。

sentence-transformers>=2.2.0 とあるが、現在5.1.0なのでOK（最新は互換性維持されているはず）。

pip install sentence-transformers -U で念のため最新版にアップデート。

    PyTorchは2.7.1でOKだが、必要に応じて2.0～2.6系でテスト（ただし基本2.7.1で問題ない想定）。

モデルロード・初期化: CrossEncoderをBGEモデルで初期化する処理を実装。

reranker = CrossEncoder('BAAI/bge-reranker-base') に変更。デバイス指定はCrossEncoder内部でCPU/CUDA自動検知するので、Macでは自動的にCPU/MPS使用となる。強制的にCPUにする場合はdevice='cpu'引数も渡す。

メモリ確認: ロード時にモデルウェイト（fp32で約1.1GB, fp16で約0.55GB相当）が展開される。M2 MacのRAMが16GB以上なら問題ないが、8GBの場合は厳しいかもしれない。swapが発生しないか注視する。

    attn_implementation設定: PyTorch 2.7.1で何か問題が出る場合に備え、環境変数PYTORCH_MPS_FALLBACK=1の設定や、モデルconfigでuse_mem_efficient_attention=Falseを試すなど、一応構えておく（ただしXLM-Rなので不要の見込み）。

単体テスト（スコア出力）: 既存の再ランキング部分をBGEで置き換えた後、少数のテストケースで正しく機能するか検証。

例示されたクエリと候補で動かし、NaNではなく妥当なスコアが出ることを確認。例えば "grilled chicken breast" に対し候補 "Chicken,...grilled" と "Turkey,...roasted" を与えて、前者のスコアが高くなっているかチェックする。

Score値のレンジを確認。BGEモデルはシグモイド出力のようなので、典型的には**-10～+10程度の範囲のlogitsが出る（実例では relevantだと+5.76、不関連で-9.47等
bge-model.com
）。したがって数値が大きいほど関連性高**と解釈できる
reddit.com
。必要ならtorch.sigmoidで0-1に正規化するが、そのまま比較で問題ない。

    5件候補の場合でも問題なくshape=(5,)のスコア配列が得られることを確認。

速度ベンチマーク: 実際の想定データで速度を測定する。50画像分（約300クエリ）を再ランキングして平均時間を算出する。

1クエリ当たりの再ランク時間（CrossEncoder部分）を計測。理想は <50ms、許容は100ms程度。

Stage1+Stage2の総合時間も測定し、総処理時間 <500ms/queryを満たすことを確認【ユーザー計画の目標】。

    極端に遅い場合、MPSデバイスを無理に使っていないか確認（PyTorchはMPSでのSoftmax等がCPUより遅い場合あり）。CrossEncoderは内部的にGPUが無ければCPUを使う設計なので、MPSが遅い場合はdevice='cpu'で固定する手もある。ただし基本はCPUで動くはず。

精度評価: テストデータ300件で再度マッチング精度（Top-1 Accuracy等）を算出し、旧方式と比較する。

Top-1 Accuracy: 既存96%から何らかの向上（もしくは同程度）を確認。理想は98%以上だが、まずは低下していないことが重要。

Recall@5: Stage1ではほぼ100%正解含有していると思われるが、Stage2でTop-1を外す例が減っているかどうか、Recall@5はほぼ100%維持されているか見る。

エラーケース分析: Top-1を外したケースの内容を確認。候補2位や3位に正解がいてBGEが取りこぼしたのか、あるいはStage1から漏れているのかを分析する。BGEが誤判定した具体例があれば記録し、あとで原因（例えば「学習データのバイアスでこういう間違いをした」等）を推測する。

        閾値再調整: CrossEncoder時代はスコア閾値60でマッチ/非マッチ判断していたとのことですが（精度96%はその閾値運用下?）、BGEのスコアはscaleが異なるため閾値は適用しないか、新たに決める必要があります。BGEは基本「必ずどれかに高いスコアを付ける（相対評価）」モデルなので、トップスコアが低すぎるときだけ不確実とみなすルールも考えられます。テスト結果を見て、明らかな誤マッチにはスコア傾向があるか分析します。必要なら閾値を設定（例: スコア差が小さい時は低信頼としてfallback処理など）。

    実装ドキュメント更新: 導入した変更を文書化する。特にimplementation_plan.md等に記載された内容を、新たな技術選定に合わせて更新する。今回はCrossEncoderモデルを差し替えたので、「2.2 再ランキングモデル」の項を下記のように修正すべきです:

    選定モデル: BAAI/bge-reranker-base
    選定理由: macOS環境で安定動作し、CrossEncoder(MiniLM)より高精度。MS MARCOで訓練済みでゼロショット性能が良い。
    速度: 10件で約100ms（CPU）。
    精度: 想定クエリでBi-encoderより精度向上を確認（Top-1 Accuracy +X%向上）。
    代替案: cross-encoder/ms-marco-MiniLM-L-12-v2（MiniLM12層版, Mac動作可）やMonoT5等も検討したが、総合的にBGEを採用。 

READMEやドキュメントに上記のような変更点を反映。

    また、将来的にColBERT等に発展させる可能性も「リスクと対策」「次のステップ」などの章に追記。

    リリースおよび監視: 新手法を本番（またはステージング環境）に適用し、しばらく動作をモニタリングする。

本番データで問題が出ないかチェック。特にNaN問題は解決しているはずだが、他の不具合（例えば極端に長いテキストでエラー等）がないか注意。

ロギング強化: 再ランキングの結果（スコアや選ばれた候補）をログに残し、あとで分析できるようにする。

        ユーザテスト: VLMからのマッチ結果の質が向上しているか、担当者にも確認してもらう。例えば「以前微妙だったケースが改善されている」等フィードバックを集める。

以上がBGE再ランカー実装に関するチェックリストです。これらを順に実行すれば、CrossEncoderの問題を解消しつつシステムのマッチング精度を向上させられるでしょう。
E. 補足: その他の考慮事項

最後に、今回の議題から派生するエッジケースや将来検討事項について触れておきます。

    ColBERT全面採用の検討: ColBERTは再ランキング用途だけでなく、一次検索からColBERTで行うアーキテクチャも可能です（いわゆる「Late Interaction Retrieval」）。食品名程度の短文ならColBERTの多重ベクトル表現でも性能が出るでしょう。ただ、システム全体をColBERTに置き換えるのは大手術です。まずはStage2への局所導入（Top-K候補のrerank）から始め、十分効果があればStage1のFAISS粗検索をColBERTにリプレイスすることも将来的には選択肢に入ります。ColBERTは大規模データ向けと思われがちですが、小規模でも再ランキングに使うことでCrossEncoderを省ける利点があります（今回CrossEncoder不具合で苦労したように、依存を減らせるメリット）。ベストプラクティスとしては、まず現行2段階（Bi-encoder + CrossEncoder）を安定させ、その上で必要なら1段階ColBERTへの移行を検討する段階的アプローチが良いでしょう。

    GPU利用について: 現状はMac開発環境を考慮してCPU/MPS動作前提で選定しました。しかし将来的にCloud Run等でGPUを使用する選択も可能とのことです。もしGPUが使えるようになれば、MonoT5-3BやLlama-2-7Bなどより高精度だが重いモデルも選択肢に入ります
    medium.com
    。例えば、最終候補5件をLlama2 7BにプロンプトしてChatGPT的に評価させるといったこともできます。ただし、GPU環境はコストが上がる点と、モデル切替によるシステム複雑化が懸念です。ベストプラクティスとしては、まずCPUで間に合う範囲で最高のモデル（BGEなど）を使い、どうしても精度不足の課題が残った場合にのみGPU+LLMを投入するのが良いでしょう
    medium.com
    。現段階ではBGEで十分賄える見込みなので、GPU案は温存で問題ありません。

    再ランキングの出力形式: 現行ではトップ1のマッチのみを出力しています（スコア閾値以上ならマッチ食品名、閾値以下なら「なし」など）。この方針は基本的に維持で良いです。CrossEncoder→BGEに変わっても上位1件を選ぶだけです。ただ、将来的に信頼度スコアを利用してUI上で「マッチ度○○%」を表示するなども可能です。BGEのスコアは対数itselfなので0-1には直しにくいですが、ランク間の差を利用して「1位スコアが2位より大きく離れているなら“高確信”、僅差なら“低確信”」といったメタ情報を付けることもできます。現状仕様では不要かもしれませんが、エッジケース（例えばTop-1候補が明らかにおかしいが他も似たり寄ったり、という場合）でデバッグに役立つでしょう。

    エッジケース: 最後に、特に注意すべきエッジケースに改めて言及します。

        類似候補の識別: 「grilled vs broiled」など微妙な違いを区別できるか。BGEモデルは文脈理解が優れているので、CrossEncoderと同様にこの差を学習している可能性が高いです。しかし絶対ではないので、テストで頻出する類似候補ペアを洗い出し、結果を確認しておきます。必要なら、そのような微差を見分けるルール（例えば「調理法が異なる場合、画像の説明文（VLM description）を重視する」など）を設けることも検討します。

        同義語への対処: 「french fries」 vs 「fried potato」等について、BGEやMiniLMはいずれもembeddingベースであるため十分対応できます。ただ、極端な別表現（例：「pommes frites」フランス語）には弱い可能性があります。多言語対応のBGEなら多少強いですが、カバーしきれない場合は同義語辞書を導入して、クエリ正規化で対処する方法もあります。例えば「pommes frites」が来たら強制的に「french fries」に書き換える等です。現在の正常化関数でどこまでやっているか確認し、不足があれば辞書を拡充します。

        部分一致: 「chicken breast」クエリに「Chicken, ... breast, ...」と「Turkey, ... breast, ...」が候補に来た場合、前者をきちんと選べるか。BGEはおそらく「chicken」と「turkey」の違いを認識できるでしょうが、Bi-encoderでは曖昧になりがちです。この観点からもCrossEncoder系(BGE)採用が望ましいです。
        medium.com
        のハイブリッド戦略も併用すれば、共通単語「breast」の有無なども評価でき、より万全です。

        スコア閾値調整: 閾値による出力制御をする場合、False Negative/False Positiveのバランスに注意します。前述の評価で閾値を調整し、96%超の精度をキープしつつCover率も高くなるよう詰めます。

        ログと継続的改善: 今後もしミスが発生したら、その事例を分析してルール追加やモデル再学習のフィードバックに使います。例えば「ある珍しい食品で誤マッチが起きた→その食品名を辞書に登録する」「CrossEncoder/BGEではなくLLMの常識推論が必要なケース（例：特定料理の地域差）を検知したらLLMにフォールバックする」など、発展的な改善も考えられます。

以上、包括的に検討・提案を行いました。
このプランに沿って実装を進めれば、macOS環境で安定した高精度の食品名マッチングシステムを構築できると考えます。さらなる改善余地（ColBERTの導入やLLMの活用）はありますが、まずはBGE CrossEncoderによる堅実な解決を図りましょう。それにより現在直面している問題は解消し、精度面でも一段上の成果が得られる見込みです。

参考文献・情報源: BGEモデル仕様
bge-model.com
bge-model.com
、MonoT5モデルカード
huggingface.co
、ColBERTの原理解説
medium.com
、ハイブリッド検索の有効性に関する事例
medium.com
などを総合的に参照しました。また、CrossEncoderのMac問題は開発者フォーラムで報告されており
huggingface.co
、本提案ではそれを踏まえて対策しています。

以上、ご確認よろしくお願いいたします。