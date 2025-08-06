"""
Debug version to test Railway deployment
"""
import os
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>Saathi Debug</title></head>
    <body>
        <h1>🔧 Saathi Legal Assistant - Debug Mode</h1>
        <button onclick="testAPI()">Test API Connection</button>
        <div id="result"></div>
        <script>
        async function testAPI() {
            const result = document.getElementById('result');
            try {
                const response = await fetch('/test-api', {method: 'POST'});
                const data = await response.json();
                result.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
            } catch (error) {
                result.innerHTML = 'Error: ' + error.message;
            }
        }
        </script>
    </body>
    </html>
    '''

@app.route('/test-api', methods=['POST'])
def test_api():
    try:
        api_key = os.environ.get('OPENROUTER_API_KEY', 'NOT_SET')
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "mistralai/mistral-7b-instruct:free",
            "messages": [{"role": "user", "content": "Hello, test message"}],
            "max_tokens": 50
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=10
        )
        
        return jsonify({
            "api_key_set": api_key != 'NOT_SET' and len(api_key) > 10,
            "api_key_prefix": api_key[:20] + "..." if len(api_key) > 20 else api_key,
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else response.text
        })
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "api_key_set": os.environ.get('OPENROUTER_API_KEY', 'NOT_SET') != 'NOT_SET'
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
