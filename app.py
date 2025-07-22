# Added Streamlit for caching the search engine resource
from flask import Flask, render_template_string, request, jsonify
import os
import logging
import streamlit as st

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# נסה לייבא את מנוע החיפוש
try:
    # Alias for clarity with the cached loader below
    from semantic_search import AIToolsSemanticSearch as SearchEngine

    # Use Streamlit caching so the engine is constructed only once per session
    @st.cache_resource
    def get_search_engine():
        logger.info("Attempting to load search engine...")
        engine = SearchEngine()
        logger.info("Search engine loaded successfully!")
        return engine

    # Load the search engine using the cached function
    search_engine = get_search_engine()

    SEARCH_AVAILABLE = True
except Exception as e:
    logger.exception(f"Search engine unavailable: {e}")
    SEARCH_AVAILABLE = False
    search_engine = None

app = Flask(__name__)

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 חיפוש כלי AI - AIxploria Bot</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
            color: white;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.2rem;
            opacity: 0.9;
        }
        
        .search-section {
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
        }
        
        .search-box {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .search-input {
            flex: 1;
            padding: 15px 20px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 1.1rem;
            outline: none;
            transition: all 0.3s ease;
        }
        
        .search-input:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .search-btn {
            padding: 15px 30px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 25px;
            font-size: 1.1rem;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .search-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        .search-btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        
        .quick-actions {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            justify-content: center;
        }
        
        .quick-btn {
            padding: 8px 16px;
            background: #f8f9fa;
            border: 1px solid #e0e0e0;
            border-radius: 20px;
            color: #666;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 0.9rem;
        }
        
        .quick-btn:hover {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
        
        .loading {
            text-align: center;
            color: #667eea;
            font-size: 1.1rem;
            margin: 20px 0;
        }
        
        .results {
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }
        
        .result-item {
            padding: 25px;
            border-bottom: 1px solid #f0f0f0;
            transition: all 0.3s ease;
        }
        
        .result-item:hover {
            background: #f8f9fa;
            transform: translateX(-5px);
        }
        
        .result-item:last-child {
            border-bottom: none;
        }
        
        .result-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 15px;
        }
        
        .result-title {
            font-size: 1.4rem;
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
        
        .result-score {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.9rem;
            font-weight: bold;
        }
        
        .result-meta {
            display: flex;
            gap: 15px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }
        
        .meta-tag {
            padding: 4px 12px;
            background: #e3f2fd;
            color: #1976d2;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 500;
        }
        
        .meta-tag.category {
            background: #f3e5f5;
            color: #7b1fa2;
        }
        
        .meta-tag.pricing {
            background: #e8f5e8;
            color: #388e3c;
        }
        
        .meta-tag.popularity {
            background: #fff3e0;
            color: #f57c00;
        }
        
        .result-description {
            color: #666;
            line-height: 1.6;
            margin-bottom: 15px;
        }
        
        .result-link {
            display: inline-block;
            padding: 10px 20px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            text-decoration: none;
            border-radius: 20px;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        
        .result-link:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            color: white;
            text-decoration: none;
        }
        
        .error {
            background: #ffebee;
            color: #c62828;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin: 20px 0;
        }
        
        .stats {
            background: rgba(255,255,255,0.1);
            color: white;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 30px;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .search-section {
                padding: 20px;
            }
            
            .search-box {
                flex-direction: column;
            }
            
            .result-header {
                flex-direction: column;
                gap: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 בוט חיפוש כלי AI</h1>
            <p>מנוע חיפוש חכם למציאת כלי AI מתוך מאגר AIxploria</p>
        </div>
        
        {% if SEARCH_AVAILABLE %}
        <div class="stats">
            📊 המאגר מכיל {{ total_tools }} כלי AI איכותיים | 🔍 חיפוש סמנטי מתקדם
        </div>
        {% endif %}
        
        <div class="search-section">
            {% if not SEARCH_AVAILABLE %}
            <div class="error">
                ❌ מנוע החיפוש לא זמין כרגע<br>
                💡 ודא שקובץ ai_tools_full.db קיים וכולל נתונים
            </div>
            {% else %}
            <div class="search-box">
                <input 
                    type="text" 
                    id="searchInput" 
                    class="search-input" 
                    placeholder="תאר מה אתה מחפש... (למשל: 'כלי ליצירת וידאו', 'צ'אט בוט', 'עריכת תמונות')"
                    value="{{ query or '' }}"
                >
                <button id="searchBtn" class="search-btn">🔍 חפש</button>
            </div>
            
            <div class="quick-actions">
                <div class="quick-btn" data-query="כלי ליצירת תמונות">🎨 יצירת תמונות</div>
                <div class="quick-btn" data-query="צ'אט בוט AI">💬 צ'אט בוט</div>
                <div class="quick-btn" data-query="עריכת וידאו">🎬 עריכת וידאו</div>
                <div class="quick-btn" data-query="יצירת לוגו">🏷️ יצירת לוגו</div>
                <div class="quick-btn" data-query="תרגום שפות">🌐 תרגום</div>
                <div class="quick-btn" data-query="כתיבת קוד">💻 כתיבת קוד</div>
                <div class="quick-btn" data-query="כלים חינמיים">💰 חינמי</div>
                <div class="quick-btn" data-action="popular">⭐ פופולריים</div>
                <div class="quick-btn" data-action="random">🎲 אקראי</div>
            </div>
            {% endif %}
        </div>
        
        <div id="loading" class="loading" style="display: none;">
            🔄 מחפש כלים רלוונטיים...
        </div>
        
        <div id="results"></div>
        
        {% if results %}
        <div class="results">
            {% for tool in results %}
            <div class="result-item">
                <div class="result-header">
                    <div>
                        <div class="result-title">{{ tool.name }}</div>
                    </div>
                    {% if tool.final_score %}
                    <div class="result-score">{{ "%.0f"|format(tool.final_score * 100) }}%</div>
                    {% endif %}
                </div>
                
                <div class="result-meta">
                    {% if tool.category %}
                    <span class="meta-tag category">📂 {{ tool.category }}</span>
                    {% endif %}
                    
                    {% if tool.pricing %}
                    <span class="meta-tag pricing">
                        {% if tool.pricing == 'free' %}💚 חינמי
                        {% elif tool.pricing == 'freemium' %}💛 פרימיום חלקי
                        {% elif tool.pricing == 'paid' %}💳 בתשלום
                        {% else %}💰 {{ tool.pricing }}
                        {% endif %}
                    </span>
                    {% endif %}
                    
                    {% if tool.popularity %}
                    <span class="meta-tag popularity">👁️ {{ tool.popularity }} צפיות</span>
                    {% endif %}
                </div>
                
                <div class="result-description">
                    {{ tool.description[:200] }}{% if tool.description|length > 200 %}...{% endif %}
                </div>
                
                <a href="{{ tool.url }}" target="_blank" class="result-link">
                    🔗 לכלי באתר AIxploria
                </a>
            </div>
            {% endfor %}
        </div>
        {% endif %}
    </div>
    
    <script>
        const searchInput = document.getElementById('searchInput');
        const searchBtn = document.getElementById('searchBtn');
        const resultsDiv = document.getElementById('results');
        const loadingDiv = document.getElementById('loading');
        
        function performSearch(query, action = null) {
            if (!query.trim() && !action) return;
            
            loadingDiv.style.display = 'block';
            resultsDiv.innerHTML = '';
            searchBtn.disabled = true;
            searchBtn.textContent = '🔄 מחפש...';
            
            const params = new URLSearchParams();
            if (action) {
                params.append('action', action);
            } else {
                params.append('q', query);
            }
            
            fetch('/search?' + params.toString())
                .then(response => response.json())
                .then(data => {
                    loadingDiv.style.display = 'none';
                    searchBtn.disabled = false;
                    searchBtn.textContent = '🔍 חפש';
                    
                    if (data.results && data.results.length > 0) {
                        displayResults(data.results);
                    } else {
                        resultsDiv.innerHTML = '<div class="error">🤷‍♂️ לא נמצאו תוצאות. נסה חיפוש אחר.</div>';
                    }
                })
                .catch(error => {
                    loadingDiv.style.display = 'none';
                    searchBtn.disabled = false;
                    searchBtn.textContent = '🔍 חפש';
                    resultsDiv.innerHTML = '<div class="error">❌ שגיאה בחיפוש: ' + error.message + '</div>';
                });
        }
        
        function displayResults(results) {
            const resultsHTML = results.map(tool => `
                <div class="result-item">
                    <div class="result-header">
                        <div>
                            <div class="result-title">${tool.name}</div>
                        </div>
                        ${tool.final_score ? `<div class="result-score">${Math.round(tool.final_score * 100)}%</div>` : ''}
                    </div>
                    
                    <div class="result-meta">
                        ${tool.category ? `<span class="meta-tag category">📂 ${tool.category}</span>` : ''}
                        
                        ${tool.pricing ? `<span class="meta-tag pricing">
                            ${tool.pricing === 'free' ? '💚 חינמי' : 
                              tool.pricing === 'freemium' ? '💛 פרימיום חלקי' : 
                              tool.pricing === 'paid' ? '💳 בתשלום' : 
                              '💰 ' + tool.pricing}
                        </span>` : ''}
                        
                        ${tool.popularity ? `<span class="meta-tag popularity">👁️ ${tool.popularity} צפיות</span>` : ''}
                    </div>
                    
                    <div class="result-description">
                        ${tool.description.length > 200 ? tool.description.substring(0, 200) + '...' : tool.description}
                    </div>
                    
                    <a href="${tool.url}" target="_blank" class="result-link">
                        🔗 לכלי באתר AIxploria
                    </a>
                </div>
            `).join('');
            
            resultsDiv.innerHTML = `<div class="results">${resultsHTML}</div>`;
        }
        
        // אירועים
        searchBtn.addEventListener('click', () => {
            performSearch(searchInput.value);
        });
        
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                performSearch(searchInput.value);
            }
        });
        
        // לחצני חיפוש מהיר
        document.querySelectorAll('.quick-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const query = btn.getAttribute('data-query');
                const action = btn.getAttribute('data-action');
                
                if (query) {
                    searchInput.value = query;
                    performSearch(query);
                } else if (action) {
                    performSearch('', action);
                }
            });
        });
        
        // חיפוש ראשוני אם יש query
        {% if query %}
        performSearch('{{ query }}');
        {% endif %}
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """עמוד בית"""
    query = request.args.get('q', '')
    results = []
    total_tools = 0
    
    if SEARCH_AVAILABLE:
        total_tools = len(search_engine.tools_data)
        
        # אם יש שאלה, בצע חיפוש
        if query:
            try:
                results = search_engine.search(query, top_k=10)
            except Exception as e:
                print(f"שגיאה בחיפוש: {e}")
    
    return render_template_string(HTML_TEMPLATE, 
                                query=query, 
                                results=results,
                                total_tools=total_tools,
                                SEARCH_AVAILABLE=SEARCH_AVAILABLE)

@app.route('/search')
def search_api():
    """API לחיפוש"""
    if not SEARCH_AVAILABLE:
        return jsonify({'error': 'מנוע חיפוש לא זמין'}), 500
    
    query = request.args.get('q', '')
    action = request.args.get('action', '')
    
    try:
        if action == 'popular':
            results = search_engine.get_popular_tools(20)
        elif action == 'random':
            results = search_engine.get_random_tools(10)
        elif query:
            results = search_engine.search(query, top_k=15)
        else:
            results = search_engine.get_random_tools(10)
        
        return jsonify({'results': results})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/categories')
def categories_api():
    """API לקטגוריות"""
    if not SEARCH_AVAILABLE:
        return jsonify({'error': 'מנוע חיפוש לא זמין'}), 500
    
    try:
        categories = search_engine.get_categories()
        return jsonify({'categories': categories})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """בדיקת תקינות"""
    status = {
        'status': 'healthy' if SEARCH_AVAILABLE else 'limited',
        'search_available': SEARCH_AVAILABLE,
        'tools_count': len(search_engine.tools_data) if SEARCH_AVAILABLE else 0
    }
    return jsonify(status)

# if __name__ == '__main__':
#     # Start the Flask app
#     app.run(debug=False, port=5000)
