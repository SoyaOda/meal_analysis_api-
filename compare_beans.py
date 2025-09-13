import json
import subprocess

# ローカルのbeans検索結果を取得
local_result = subprocess.run(['curl', '-X', 'GET', 'localhost:9200/mynetdiary_list_support_db/_search?q=beans&size=100'], 
                             capture_output=True, text=True)
local_data = json.loads(local_result.stdout)
local_ids = set(hit['_id'] for hit in local_data['hits']['hits'])

# VMのbeans検索結果を取得
vm_cmd = ['gcloud', 'compute', 'ssh', 'elasticsearch-vm', '--zone=us-central1-a', 
          '--command=curl -X GET "localhost:9200/mynetdiary_list_support_db/_search?q=beans&size=100"']
vm_result = subprocess.run(vm_cmd, capture_output=True, text=True, 
                          env={'PATH': '/Users/odasoya/google-cloud-sdk/bin:' + subprocess.os.environ.get('PATH', '')})

# SSH出力から JSON 部分を抽出
vm_output_lines = vm_result.stdout.strip().split('\n')
vm_json_line = None
for line in vm_output_lines:
    if line.strip().startswith('{'):
        vm_json_line = line
        break

if vm_json_line:
    vm_data = json.loads(vm_json_line)
    vm_ids = set(hit['_id'] for hit in vm_data['hits']['hits'])
    
    print(f"ローカル: {len(local_ids)} 件")
    print(f"VM: {len(vm_ids)} 件")
    
    # 差分を確認
    missing_in_vm = local_ids - vm_ids
    missing_in_local = vm_ids - local_ids
    
    print(f"\nVMで欠けているID: {missing_in_vm}")
    print(f"ローカルで欠けているID: {missing_in_local}")
    
    # 欠けているドキュメントの詳細を確認
    if missing_in_vm:
        print("\nVMで欠けているドキュメントの詳細:")
        for doc_id in missing_in_vm:
            for hit in local_data['hits']['hits']:
                if hit['_id'] == doc_id:
                    print(f"ID: {doc_id}")
                    print(f"Name: {hit['_source'].get('original_name')}")
                    print(f"Search name: {hit['_source'].get('search_name')}")
                    print("---")
else:
    print("VM結果の解析に失敗")