#!/usr/bin/env python3
"""
Vertex AI設定確認・セットアップスクリプト
"""
import os
import sys
import json
import subprocess
from pathlib import Path

def check_gcloud_installed():
    """gcloudがインストールされているか確認"""
    try:
        result = subprocess.run(['gcloud', '--version'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def get_current_gcloud_project():
    """現在のgcloudプロジェクトを取得"""
    try:
        result = subprocess.run(['gcloud', 'config', 'get-value', 'project'], 
                              capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else None
    except:
        return None

def check_application_default_credentials():
    """Application Default Credentialsが設定されているか確認"""
    adc_path = Path.home() / '.config' / 'gcloud' / 'application_default_credentials.json'
    return adc_path.exists()

def check_service_account_key(path="service-account-key.json"):
    """サービスアカウントキーファイルの存在確認"""
    return Path(path).exists()

def main():
    print("=== Vertex AI 設定確認 ===\n")
    
    # プロジェクト設定の確認
    PROJECT_ID = "recording-diet-ai-3e7cf"
    REGION = "us-central1"
    SERVICE_ACCOUNT_PATH = "service-account-key.json"
    
    print(f"プロジェクトID: {PROJECT_ID}")
    print(f"リージョン: {REGION}")
    print(f"サービスアカウントキーパス: {SERVICE_ACCOUNT_PATH}\n")
    
    # gcloudの確認
    if check_gcloud_installed():
        print("✅ gcloud CLIがインストールされています")
        current_project = get_current_gcloud_project()
        if current_project:
            print(f"   現在のプロジェクト: {current_project}")
            if current_project != PROJECT_ID:
                print(f"   ⚠️  プロジェクトが異なります。以下のコマンドで変更してください：")
                print(f"      gcloud config set project {PROJECT_ID}")
        else:
            print("   ⚠️  プロジェクトが設定されていません")
    else:
        print("❌ gcloud CLIがインストールされていません")
        print("   https://cloud.google.com/sdk/docs/install からインストールしてください")
    
    print("")
    
    # 認証方法の確認
    print("=== 認証設定 ===")
    
    # 方法1: サービスアカウントキー
    if check_service_account_key(SERVICE_ACCOUNT_PATH):
        print(f"✅ サービスアカウントキーファイルが見つかりました: {SERVICE_ACCOUNT_PATH}")
        print("   環境変数を設定してください：")
        print(f"   export GOOGLE_APPLICATION_CREDENTIALS=\"{os.path.abspath(SERVICE_ACCOUNT_PATH)}\"")
    else:
        print(f"❌ サービスアカウントキーファイルが見つかりません: {SERVICE_ACCOUNT_PATH}")
    
    print("")
    
    # 方法2: Application Default Credentials
    if check_application_default_credentials():
        print("✅ Application Default Credentialsが設定されています")
    else:
        print("❌ Application Default Credentialsが設定されていません")
        print("   以下のコマンドで設定してください：")
        print("   gcloud auth application-default login")
    
    print("")
    
    # 推奨される次のステップ
    print("=== 推奨される次のステップ ===")
    
    if not check_service_account_key(SERVICE_ACCOUNT_PATH) and not check_application_default_credentials():
        print("1. 以下のいずれかの方法で認証を設定してください：")
        print("   a) gcloud auth application-default login (開発環境推奨)")
        print(f"   b) サービスアカウントキーを {SERVICE_ACCOUNT_PATH} に配置")
        print("")
    
    print("2. Vertex AI APIが有効になっていることを確認：")
    print("   gcloud services enable aiplatform.googleapis.com")
    print("")
    
    print("3. APIサーバーを起動してテスト：")
    print("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print("   python test_api.py")
    
    # 環境変数の確認
    print("\n=== 環境変数の状態 ===")
    if os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        print(f"✅ GOOGLE_APPLICATION_CREDENTIALS: {os.environ['GOOGLE_APPLICATION_CREDENTIALS']}")
    else:
        print("❌ GOOGLE_APPLICATION_CREDENTIALSが設定されていません")

if __name__ == "__main__":
    main() 