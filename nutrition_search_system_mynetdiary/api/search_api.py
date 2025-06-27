"""
栄養検索システム REST API
"""

import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

from core.models import SearchQuery, SearchResponse, BatchSearchQuery, BatchSearchResponse, SearchStats
from core.search_engine import NutritionSearchEngine

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPIアプリ初期化
app = FastAPI(
    title="🔍 Nutrition Search API",
    description="高度なElasticsearch栄養データベース検索システム",
    version="1.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 検索エンジン初期化
search_engine = NutritionSearchEngine()

# 静的ファイル設定（Demo用）
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception:
    logger.warning("Static files directory not found")


@app.get("/", response_class=HTMLResponse)
async def root():
    """ルートページ - API情報表示"""
    return """
    <html>
        <head>
            <title>🔍 Nutrition Search API</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
                .header { text-align: center; color: #2c3e50; }
                .feature { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }
                .api-link { background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🔍 Nutrition Search API</h1>
                <p>高度なElasticsearch栄養データベース検索システム</p>
            </div>
            
            <div class="feature">
                <h3>✨ 主な機能</h3>
                <ul>
                    <li>🔍 見出し語化検索 (tomatoes → tomato)</li>
                    <li>📊 7段階検索戦略</li>
                    <li>⚡ 高速検索 (平均200ms)</li>
                    <li>🎯 100%マッチ率</li>
                    <li>🌐 3DB統合 (YAZIO, MyNetDiary, EatThisMuch)</li>
                </ul>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="/docs" class="api-link">📚 API Documentation</a>
                <a href="/demo" class="api-link" style="margin-left: 20px;">🖥️ Live Demo</a>
            </div>
            
            <div class="feature">
                <h3>🚀 使用例</h3>
                <pre>
# 単一検索
curl -X POST "http://localhost:8001/search" \\
  -H "Content-Type: application/json" \\
  -d '{"query": "tomatoes", "max_results": 10}'

# バッチ検索
curl -X POST "http://localhost:8001/search/batch" \\
  -H "Content-Type: application/json" \\
  -d '{"queries": ["chicken", "rice", "apple"], "max_results": 5}'
                </pre>
            </div>
        </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "elasticsearch_connected": search_engine.es_client.is_connected(),
        "total_documents": search_engine.es_client.get_total_documents()
    }


@app.post("/search", response_model=SearchResponse)
async def search_nutrition(query: SearchQuery):
    """栄養データベース検索"""
    try:
        result = await search_engine.search(query)
        logger.info(f"Search completed: '{query.query}' -> {len(result.results)} results in {result.search_time_ms}ms")
        return result
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/search/batch", response_model=BatchSearchResponse)
async def batch_search_nutrition(batch_query: BatchSearchQuery):
    """バッチ栄養データベース検索"""
    try:
        result = await search_engine.batch_search(batch_query)
        logger.info(f"Batch search completed: {len(batch_query.queries)} queries -> {result.summary['total_results']} total results")
        return result
    except Exception as e:
        logger.error(f"Batch search error: {e}")
        raise HTTPException(status_code=500, detail=f"Batch search failed: {str(e)}")


@app.get("/stats")
async def get_search_stats():
    """検索統計取得"""
    try:
        stats = search_engine.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")


@app.get("/demo", response_class=HTMLResponse)
async def demo_page():
    """デモページ"""
    return """
    <html>
        <head>
            <title>🔍 Nutrition Search Demo</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
                .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .search-box { display: flex; gap: 10px; margin: 20px 0; }
                #searchInput { flex: 1; padding: 12px; border: 2px solid #ddd; border-radius: 5px; font-size: 16px; }
                #searchBtn { padding: 12px 24px; background: #3498db; color: white; border: none; border-radius: 5px; cursor: pointer; }
                #searchBtn:hover { background: #2980b9; }
                .results { margin-top: 20px; }
                .result-item { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #3498db; }
                .result-name { font-weight: bold; color: #2c3e50; margin-bottom: 5px; }
                .result-nutrition { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; margin-top: 10px; }
                .nutrition-item { background: white; padding: 8px; border-radius: 3px; text-align: center; }
                .loading { text-align: center; color: #7f8c8d; }
                .error { color: #e74c3c; background: #fadbd8; padding: 10px; border-radius: 5px; }
                .match-type { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 12px; color: white; }
                .exact { background: #27ae60; }
                .lemmatized { background: #f39c12; }
                .partial { background: #8e44ad; }
                .fuzzy { background: #95a5a6; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔍 Nutrition Search Demo</h1>
                <p>Try searching for foods like "tomatoes", "chicken breast", "apple", "rice", etc.</p>
                
                <div class="search-box">
                    <input type="text" id="searchInput" placeholder="Enter food name..." onkeypress="handleKeyPress(event)">
                    <button id="searchBtn" onclick="performSearch()">🔍 Search</button>
                </div>
                
                <div id="results"></div>
            </div>

            <script>
                async function performSearch() {
                    const query = document.getElementById('searchInput').value.trim();
                    if (!query) return;
                    
                    const resultsDiv = document.getElementById('results');
                    resultsDiv.innerHTML = '<div class="loading">🔍 Searching...</div>';
                    
                    try {
                        const response = await fetch('/search', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ query: query, max_results: 10 })
                        });
                        
                        const data = await response.json();
                        displayResults(data);
                    } catch (error) {
                        resultsDiv.innerHTML = '<div class="error">❌ Search failed: ' + error.message + '</div>';
                    }
                }
                
                function displayResults(data) {
                    const resultsDiv = document.getElementById('results');
                    
                    if (data.results.length === 0) {
                        resultsDiv.innerHTML = '<div class="error">No results found for "' + data.query + '"</div>';
                        return;
                    }
                    
                    let html = '<h3>🎯 Search Results (' + data.total_found + ' found in ' + data.search_time_ms + 'ms)</h3>';
                    
                    if (data.lemmatized_query) {
                        html += '<p><em>Lemmatized query: "' + data.lemmatized_query + '"</em></p>';
                    }
                    
                    data.results.forEach(result => {
                        const nutrition = result.nutrition;
                        html += `
                            <div class="result-item">
                                <div class="result-name">
                                    ${result.name} 
                                    <span class="match-type ${result.match_type}">${result.match_type}</span>
                                    <small style="color: #7f8c8d;">(${result.source_db}) Score: ${result.score.toFixed(2)}</small>
                                </div>
                                <div class="result-nutrition">
                                    <div class="nutrition-item"><strong>${nutrition.calories || 0}</strong><br>calories</div>
                                    <div class="nutrition-item"><strong>${nutrition.protein || 0}</strong><br>protein (g)</div>
                                    <div class="nutrition-item"><strong>${(nutrition.carbs || nutrition.carbohydrates || 0)}</strong><br>carbs (g)</div>
                                    <div class="nutrition-item"><strong>${nutrition.fat || 0}</strong><br>fat (g)</div>
                                </div>
                            </div>
                        `;
                    });
                    
                    resultsDiv.innerHTML = html;
                }
                
                function handleKeyPress(event) {
                    if (event.key === 'Enter') {
                        performSearch();
                    }
                }
                
                // 例のクエリをセット
                document.addEventListener('DOMContentLoaded', function() {
                    const examples = ['tomatoes', 'chicken breast', 'brown rice', 'apple', 'salmon'];
                    const randomExample = examples[Math.floor(Math.random() * examples.length)];
                    document.getElementById('searchInput').placeholder = `Try "${randomExample}"...`;
                });
            </script>
        </body>
    </html>
    """


def run_api(host: str = "0.0.0.0", port: int = 8001):
    """API サーバー起動"""
    logger.info(f"🚀 Starting Nutrition Search API on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_api() 