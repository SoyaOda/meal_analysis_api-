#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DeepInfra API test for reranker
"""

import os
import requests
import json

DEEPINFRA_API_KEY = os.getenv("DEEPINFRA_API_KEY")

# Test API directly
url = "https://api.deepinfra.com/v1/inference/Qwen/Qwen3-Reranker-8B"
headers = {
    "Authorization": f"Bearer {DEEPINFRA_API_KEY}",
    "Content-Type": "application/json"
}

query = "name: chicken breast\ndescription: grilled"
documents = [
    "name: Chicken breast\ndescription: NS as to cooking method, skin not eaten",
    "name: Chicken breast\ndescription: baked or broiled, skin not eaten",
    "name: Chicken breast\ndescription: grilled, skin not eaten"
]

payload = {
    "queries": [query],
    "documents": documents,
    "instruction": "Match food descriptions for nutrition database"
}

print("🔍 Testing DeepInfra Qwen3-Reranker-8B API...")
print(f"Query: {query}")
print(f"Documents: {len(documents)}")

response = requests.post(url, headers=headers, json=payload, timeout=60)

print(f"\nStatus: {response.status_code}")
print(f"Response:\n{json.dumps(response.json(), indent=2)}")
