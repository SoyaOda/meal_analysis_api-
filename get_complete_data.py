import requests
import json

# 最初のスクロールから残りのデータを取得
with open('mynetdiary_list_support_db_data.json', 'r') as f:
    first_batch = json.load(f)

scroll_id = first_batch['_scroll_id']
total_docs = first_batch['hits']['total']['value']
print(f'Total documents: {total_docs}')

# 残りのデータを取得
all_hits = first_batch['hits']['hits']
while len(all_hits) < total_docs:
    response = requests.get('http://localhost:9200/_search/scroll',
                          json={'scroll': '1m', 'scroll_id': scroll_id})
    if response.status_code != 200:
        print(f'Error: {response.status_code} - {response.text}')
        break
    
    data = response.json()
    scroll_id = data['_scroll_id']
    hits = data['hits']['hits']
    
    if not hits:
        break
        
    all_hits.extend(hits)
    print(f'Retrieved {len(all_hits)}/{total_docs} documents')

# 完全なデータを保存
complete_data = {
    'hits': {
        'total': first_batch['hits']['total'],
        'hits': all_hits
    }
}

with open('mynetdiary_list_support_db_complete.json', 'w') as f:
    json.dump(complete_data, f)

print(f'Complete data saved: {len(all_hits)} documents')