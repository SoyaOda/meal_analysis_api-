#!/bin/bash

# Elasticsearch VM セットアップスクリプト
# Google Cloud VM でElasticsearchサーバーを構築

set -e

echo "🚀 Elasticsearch VM セットアップ開始..."

# 1. Compute Engine VMインスタンス作成
echo "📦 Compute Engine VMインスタンスを作成中..."
gcloud compute instances create elasticsearch-vm \
    --zone=us-central1-a \
    --machine-type=e2-standard-2 \
    --boot-disk-size=30GB \
    --boot-disk-type=pd-standard \
    --image-family=debian-11 \
    --image-project=debian-cloud \
    --tags=elasticsearch-server \
    --metadata=startup-script='#!/bin/bash
# Elasticsearch自動インストールスクリプト

# Java 11インストール
apt-get update
apt-get install -y openjdk-11-jdk wget gnupg

# Elasticsearchリポジトリ追加
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | apt-key add -
echo "deb https://artifacts.elastic.co/packages/8.x/apt stable main" > /etc/apt/sources.list.d/elastic-8.x.list

# Elasticsearchインストール
apt-get update
apt-get install -y elasticsearch

# Elasticsearch設定
cat > /etc/elasticsearch/elasticsearch.yml << EOF
cluster.name: nutrition-search-cluster
node.name: nutrition-node-1
network.host: 0.0.0.0
http.port: 9200
discovery.type: single-node

# セキュリティ設定（開発用）
xpack.security.enabled: false
xpack.security.enrollment.enabled: false
xpack.security.http.ssl.enabled: false
xpack.security.transport.ssl.enabled: false

# メモリ設定
bootstrap.memory_lock: false
EOF

# JVMヒープサイズ設定
cat > /etc/elasticsearch/jvm.options.d/heap.options << EOF
-Xms1g
-Xmx1g
EOF

# Elasticsearchサービス開始
systemctl daemon-reload
systemctl enable elasticsearch
systemctl start elasticsearch

# ヘルスチェック用ログ
echo "Elasticsearch setup completed at $(date)" >> /var/log/elasticsearch-setup.log
'

echo "✅ VM作成コマンド実行完了"

# 2. ファイアウォールルール作成（内部ネットワーク用）
echo "🔥 ファイアウォールルール作成中..."
gcloud compute firewall-rules create elasticsearch-internal-allow \
    --allow tcp:9200 \
    --source-ranges 10.128.0.0/9 \
    --target-tags elasticsearch-server \
    --description="Allow Elasticsearch access from internal GCP networks"

echo "✅ ファイアウォールルール作成完了"

# 3. VMの内部IPアドレス取得待機
echo "⏳ VMの起動とElasticsearchインストールを待機中..."
sleep 60

# VMの内部IPアドレス取得
INTERNAL_IP=$(gcloud compute instances describe elasticsearch-vm \
    --zone=us-central1-a \
    --format="value(networkInterfaces[0].networkIP)")

echo "📍 VM内部IPアドレス: $INTERNAL_IP"

# 4. Elasticsearch接続テスト
echo "🔍 Elasticsearch接続テスト中..."
for i in {1..10}; do
    echo "テスト試行 $i/10..."
    if curl -f http://$INTERNAL_IP:9200 >/dev/null 2>&1; then
        echo "✅ Elasticsearch接続成功!"
        break
    else
        echo "⏳ Elasticsearchの起動を待機中... (30秒)"
        sleep 30
    fi
    
    if [ $i -eq 10 ]; then
        echo "❌ Elasticsearch接続に失敗しました"
        echo "📋 VM状態確認:"
        gcloud compute instances describe elasticsearch-vm --zone=us-central1-a --format="value(status)"
        echo "🔧 手動で以下コマンドで確認してください:"
        echo "gcloud compute ssh elasticsearch-vm --zone=us-central1-a --command='sudo systemctl status elasticsearch'"
        exit 1
    fi
done

echo ""
echo "🎉 Elasticsearch VM セットアップ完了!"
echo "📍 内部IPアドレス: $INTERNAL_IP"
echo "🔗 Elasticsearch URL: http://$INTERNAL_IP:9200"
echo ""
echo "📝 次のステップ:"
echo "1. Cloud Runの環境変数に ELASTIC_HOST=http://$INTERNAL_IP:9200 を設定"
echo "2. 栄養データベースインデックス作成"
echo "3. APIの再デプロイとテスト"
echo ""
echo "🛠 VM管理コマンド:"
echo "  VM接続: gcloud compute ssh elasticsearch-vm --zone=us-central1-a"
echo "  VM停止: gcloud compute instances stop elasticsearch-vm --zone=us-central1-a"  
echo "  VM開始: gcloud compute instances start elasticsearch-vm --zone=us-central1-a"
echo "  VM削除: gcloud compute instances delete elasticsearch-vm --zone=us-central1-a"