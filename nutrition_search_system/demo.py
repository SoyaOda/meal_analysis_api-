"""
栄養検索システム Webデモ（Flask版）
"""

import asyncio
import logging
from flask import Flask, render_template_string, request, jsonify
from core.search_engine import NutritionSearchEngine
from core.models import SearchQuery

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
search_engine = NutritionSearchEngine()

# HTMLテンプレート
DEMO_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>🔍 Nutrition Search Demo</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            background: white; 
            border-radius: 15px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header { 
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white; 
            padding: 40px; 
            text-align: center; 
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { font-size: 1.1em; opacity: 0.9; }
        .content { padding: 40px; }
        .search-section { margin-bottom: 40px; }
        .search-box { 
            display: flex; 
            gap: 15px; 
            margin: 30px 0;
            flex-wrap: wrap;
        }
        #searchInput { 
            flex: 1; 
            min-width: 300px;
            padding: 15px 20px; 
            border: 2px solid #e1e8ed; 
            border-radius: 10px; 
            font-size: 16px;
            transition: all 0.3s ease;
        }
        #searchInput:focus { 
            outline: none; 
            border-color: #4facfe; 
            box-shadow: 0 0 0 3px rgba(79, 172, 254, 0.1);
        }
        #searchBtn { 
            padding: 15px 30px; 
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white; 
            border: none; 
            border-radius: 10px; 
            cursor: pointer; 
            font-size: 16px;
            transition: all 0.3s ease;
        }
        #searchBtn:hover { 
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(79, 172, 254, 0.3);
        }
        .examples { 
            display: flex; 
            gap: 10px; 
            flex-wrap: wrap; 
            margin: 20px 0;
        }
        .example-btn { 
            padding: 8px 16px; 
            background: #f8f9fa; 
            border: 1px solid #e1e8ed; 
            border-radius: 20px; 
            cursor: pointer; 
            transition: all 0.3s ease;
            font-size: 14px;
        }
        .example-btn:hover { 
            background: #4facfe; 
            color: white; 
            border-color: #4facfe;
        }
        .stats { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 20px; 
            margin: 30px 0;
        }
        .stat-card { 
            background: #f8f9fa; 
            padding: 20px; 
            border-radius: 10px; 
            text-align: center;
        }
        .stat-number { 
            font-size: 2em; 
            font-weight: bold; 
            color: #4facfe; 
            margin-bottom: 5px;
        }
        .results { margin-top: 30px; }
        .result-item { 
            background: #f8f9fa; 
            padding: 20px; 
            margin: 15px 0; 
            border-radius: 10px; 
            border-left: 5px solid #4facfe;
            transition: all 0.3s ease;
        }
        .result-item:hover { 
            transform: translateX(5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .result-name { 
            font-weight: bold; 
            color: #2c3e50; 
            margin-bottom: 10px; 
            font-size: 1.1em;
        }
        .result-meta { 
            display: flex; 
            gap: 15px; 
            margin-bottom: 15px; 
            flex-wrap: wrap;
        }
        .match-type { 
            display: inline-block; 
            padding: 4px 12px; 
            border-radius: 15px; 
            font-size: 12px; 
            color: white; 
            font-weight: bold;
        }
        .exact { background: #27ae60; }
        .lemmatized { background: #f39c12; }
        .partial { background: #8e44ad; }
        .fuzzy { background: #95a5a6; }
        .result-nutrition { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); 
            gap: 15px; 
        }
        .nutrition-item { 
            background: white; 
            padding: 15px; 
            border-radius: 8px; 
            text-align: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        .nutrition-value { 
            font-size: 1.5em; 
            font-weight: bold; 
            color: #4facfe; 
            margin-bottom: 5px;
        }
        .nutrition-label { 
            font-size: 0.9em; 
            color: #7f8c8d;
        }
        .loading { 
            text-align: center; 
            color: #4facfe; 
            font-size: 1.1em; 
            padding: 40px;
        }
        .error { 
            color: #e74c3c; 
            background: #fadbd8; 
            padding: 20px; 
            border-radius: 10px; 
            border-left: 5px solid #e74c3c;
        }
        
        @media (max-width: 768px) {
            .header { padding: 20px; }
            .header h1 { font-size: 2em; }
            .content { padding: 20px; }
            .search-box { flex-direction: column; }
            #searchInput { min-width: 100%; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Nutrition Search</h1>
            <p>Advanced Elasticsearch-powered nutrition database with lemmatization</p>
        </div>
        
        <div class="content">
            <div class="search-section">
                <div class="search-box">
                    <input type="text" id="searchInput" placeholder="Enter food name (e.g., tomatoes, chicken breast, brown rice)..." onkeypress="handleKeyPress(event)">
                    <button id="searchBtn" onclick="performSearch()">🔍 Search</button>
                </div>
                
                <div class="examples">
                    <span style="color: #7f8c8d; margin-right: 10px;">Quick examples:</span>
                    <span class="example-btn" onclick="searchExample('tomatoes')">tomatoes</span>
                    <span class="example-btn" onclick="searchExample('chicken breast')">chicken breast</span>
                    <span class="example-btn" onclick="searchExample('brown rice')">brown rice</span>
                    <span class="example-btn" onclick="searchExample('apple')">apple</span>
                    <span class="example-btn" onclick="searchExample('salmon')">salmon</span>
                    <span class="example-btn" onclick="searchExample('eggs')">eggs</span>
                </div>
            </div>
            
            <div id="searchStats" class="stats" style="display: none;">
                <div class="stat-card">
                    <div class="stat-number" id="totalResults">-</div>
                    <div>Results Found</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="searchTime">-</div>
                    <div>Search Time (ms)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="matchType">-</div>
                    <div>Best Match Type</div>
                </div>
            </div>
            
            <div id="results"></div>
        </div>
    </div>

    <script>
        async function performSearch() {
            const query = document.getElementById('searchInput').value.trim();
            if (!query) return;
            
            const resultsDiv = document.getElementById('results');
            const statsDiv = document.getElementById('searchStats');
            
            resultsDiv.innerHTML = '<div class="loading">🔍 Searching nutrition database...</div>';
            statsDiv.style.display = 'none';
            
            try {
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: query, max_results: 10 })
                });
                
                const data = await response.json();
                displayResults(data);
            } catch (error) {
                resultsDiv.innerHTML = '<div class="error">❌ Search failed: ' + error.message + '</div>';
                statsDiv.style.display = 'none';
            }
        }
        
        function displayResults(data) {
            const resultsDiv = document.getElementById('results');
            const statsDiv = document.getElementById('searchStats');
            
            if (data.results.length === 0) {
                resultsDiv.innerHTML = '<div class="error">No results found for "' + data.query + '"</div>';
                statsDiv.style.display = 'none';
                return;
            }
            
            // 統計表示
            document.getElementById('totalResults').textContent = data.total_found;
            document.getElementById('searchTime').textContent = data.search_time_ms;
            document.getElementById('matchType').textContent = data.results[0].match_type;
            statsDiv.style.display = 'grid';
            
            let html = '<h3>🎯 Search Results</h3>';
            
            if (data.lemmatized_query) {
                html += '<p style="color: #7f8c8d; margin-bottom: 20px;"><em>Lemmatized: "' + data.query + '" → "' + data.lemmatized_query + '"</em></p>';
            }
            
            data.results.forEach(result => {
                const nutrition = result.nutrition;
                html += `
                    <div class="result-item">
                        <div class="result-name">${result.name}</div>
                        <div class="result-meta">
                            <span class="match-type ${result.match_type}">${result.match_type}</span>
                            <span style="color: #7f8c8d;">Source: ${result.source_db}</span>
                            <span style="color: #7f8c8d;">Score: ${result.score.toFixed(2)}</span>
                        </div>
                        <div class="result-nutrition">
                            <div class="nutrition-item">
                                <div class="nutrition-value">${nutrition.calories || 0}</div>
                                <div class="nutrition-label">calories</div>
                            </div>
                            <div class="nutrition-item">
                                <div class="nutrition-value">${nutrition.protein || 0}</div>
                                <div class="nutrition-label">protein (g)</div>
                            </div>
                            <div class="nutrition-item">
                                <div class="nutrition-value">${(nutrition.carbs || nutrition.carbohydrates || 0)}</div>
                                <div class="nutrition-label">carbs (g)</div>
                            </div>
                            <div class="nutrition-item">
                                <div class="nutrition-value">${nutrition.fat || 0}</div>
                                <div class="nutrition-label">fat (g)</div>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            resultsDiv.innerHTML = html;
        }
        
        function searchExample(query) {
            document.getElementById('searchInput').value = query;
            performSearch();
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                performSearch();
            }
        }
        
        // 初期化
        document.addEventListener('DOMContentLoaded', function() {
            const examples = ['tomatoes', 'chicken breast', 'brown rice', 'apple', 'salmon'];
            const randomExample = examples[Math.floor(Math.random() * examples.length)];
            document.getElementById('searchInput').placeholder = `Try "${randomExample}"...`;
        });
    </script>
</body>
</html>
"""


@app.route('/')
def home():
    """デモページ表示"""
    return render_template_string(DEMO_TEMPLATE)


@app.route('/api/search', methods=['POST'])
def api_search():
    """API検索エンドポイント"""
    try:
        data = request.get_json()
        query = SearchQuery(
            query=data.get('query', ''),
            max_results=data.get('max_results', 10)
        )
        
        # 非同期関数を同期的に実行
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(search_engine.search(query))
        loop.close()
        
        return jsonify(result.dict())
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/health')
def health():
    """ヘルスチェック"""
    return jsonify({
        "status": "healthy",
        "elasticsearch_connected": search_engine.es_client.is_connected(),
        "total_documents": search_engine.es_client.get_total_documents()
    })


def run_demo(host='0.0.0.0', port=5000, debug=False):
    """デモアプリ起動"""
    logger.info(f"🚀 Starting Nutrition Search Demo on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_demo(debug=True) 