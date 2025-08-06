"""
Saathi Legal Assistant - Production Flask App
Railway.app deployment ready
"""
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration from environment variables
API_KEY = os.environ.get('OPENROUTER_API_KEY', 'your-api-key-here')
MODEL = os.environ.get('DEFAULT_MODEL', 'mistralai/mistral-7b-instruct:free')
MAX_TOKENS = int(os.environ.get('MAX_TOKENS', '500'))
TEMPERATURE = float(os.environ.get('TEMPERATURE', '0.7'))

# System prompt
SYSTEM_PROMPT = """You are Saathi, a helpful legal assistant that provides general legal information for Indian law and common legal situations. 

Important guidelines:
1. Provide accurate, helpful legal information based on Indian laws
2. Always remind users that this is general information only
3. Advise users to consult with a qualified attorney for specific legal advice
4. Be empathetic and understanding in your responses
5. Provide practical next steps when possible
6. Focus on Indian legal system, laws, and procedures
7. If you're not sure about something, say so clearly
8. Use simple language that common people can understand

Remember: You provide information, not legal advice. Always encourage users to seek professional legal counsel for their specific situations."""

# Global conversation history
conversation_history = [{"role": "system", "content": SYSTEM_PROMPT}]

def is_api_configured():
    """Check if API key is configured"""
    return API_KEY != 'your-api-key-here' and API_KEY.strip() != ''

def detect_intent(user_input):
    """Simple intent detection"""
    user_input_lower = user_input.lower()
    
    intents = {
        "property_law": ["property", "real estate", "landlord", "tenant", "rent", "deposit", "lease"],
        "employment_law": ["job", "employment", "salary", "workplace", "fired", "resignation"],
        "family_law": ["marriage", "divorce", "custody", "alimony", "domestic", "family"],
        "criminal_law": ["police", "arrest", "crime", "criminal", "theft", "assault", "bail"],
        "consumer_law": ["consumer", "refund", "warranty", "defective", "fraud", "complaint"],
        "contract_law": ["contract", "agreement", "breach", "terms", "conditions"],
        "civil_law": ["civil", "damages", "compensation", "negligence", "liability"]
    }
    
    for intent, keywords in intents.items():
        if any(keyword in user_input_lower for keyword in keywords):
            return intent
    
    return "general_legal"

@app.route('/')
def home():
    """Serve the web interface"""
    try:
        with open('web_interface.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return jsonify({
            "status": "healthy",
            "app": "Saathi Legal Assistant",
            "version": "1.0.0",
            "message": "API is running. Web interface not found.",
            "api_configured": is_api_configured(),
            "timestamp": datetime.utcnow().isoformat()
        })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "app": "Saathi Legal Assistant",
        "version": "1.0.0",
        "api_configured": is_api_configured(),
        "model": MODEL,
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint"""
    global conversation_history
    
    if not is_api_configured():
        return jsonify({
            "reply": "Sorry, the chatbot is not properly configured. Please contact the administrator.",
            "intent": None,
            "error": "API_NOT_CONFIGURED",
            "status": "error"
        }), 500
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided", "status": "error"}), 400
        
        user_input = data.get('query', '').strip()
        if not user_input:
            return jsonify({"error": "No query provided", "status": "error"}), 400
        
        if len(user_input) > 1000:
            return jsonify({
                "error": "Query too long. Please keep it under 1000 characters.",
                "status": "error"
            }), 400
        
        # Add user message to conversation
        conversation_history.append({"role": "user", "content": user_input})
        
        # Prepare API request
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "HTTP-Referer": "https://openrouter.ai",
            "X-Title": "Saathi Legal Assistant",
            "Content-Type": "application/json"
        }
        
        api_data = {
            "model": MODEL,
            "messages": conversation_history,
            "max_tokens": MAX_TOKENS,
            "temperature": TEMPERATURE
        }
        
        logger.info(f"Processing query: {user_input[:50]}...")
        
        # Make API request
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=api_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                reply = result["choices"][0]["message"]["content"].strip()
                
                # Add assistant response to conversation
                conversation_history.append({"role": "assistant", "content": reply})
                
                # Detect intent
                intent = detect_intent(user_input)
                
                return jsonify({
                    "reply": reply,
                    "intent": intent,
                    "status": "success",
                    "timestamp": datetime.utcnow().isoformat()
                })
            else:
                return jsonify({
                    "reply": "I received an unexpected response. Please try again.",
                    "intent": None,
                    "error": "UNEXPECTED_RESPONSE_FORMAT",
                    "status": "error"
                }), 500
        else:
            logger.error(f"API request failed: {response.status_code}")
            error_msg = "I'm having trouble connecting to my knowledge base. Please try again later."
            
            if response.status_code == 401:
                error_msg = "Authentication issue. Please contact support."
            elif response.status_code == 429:
                error_msg = "I'm currently receiving too many requests. Please try again in a moment."
            
            return jsonify({
                "reply": error_msg,
                "intent": None,
                "error": f"API_ERROR_{response.status_code}",
                "status": "error"
            }), 500
            
    except requests.exceptions.Timeout:
        return jsonify({
            "reply": "My response is taking too long. Please try again with a simpler question.",
            "intent": None,
            "error": "TIMEOUT",
            "status": "error"
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            "reply": "I encountered an unexpected error. Please try again later.",
            "intent": None,
            "error": "UNEXPECTED_ERROR",
            "status": "error"
        }), 500

# Alternative endpoint for compatibility
@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Alternative chat endpoint for /api/chat calls"""
    return chat()

@app.route('/reset', methods=['POST'])
def reset_conversation():
    """Reset conversation history"""
    global conversation_history
    try:
        conversation_history = [{"role": "system", "content": SYSTEM_PROMPT}]
        return jsonify({
            "message": "Conversation reset successfully",
            "status": "success",
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error resetting conversation: {str(e)}")
        return jsonify({
            "error": "Failed to reset conversation",
            "status": "error"
        }), 500

@app.route('/config')
def get_config():
    """Get public configuration"""
    return jsonify({
        "app_name": "Saathi Legal Assistant",
        "version": "1.0.0",
        "model": MODEL,
        "api_configured": is_api_configured(),
        "max_tokens": MAX_TOKENS,
        "timestamp": datetime.utcnow().isoformat()
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found", "status": "error"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error", "status": "error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    print(f"🚀 Starting Saathi Legal Assistant")
    print(f"🤖 Model: {MODEL}")
    print(f"🔑 API Configured: {is_api_configured()}")
    print(f"🌐 Running on {host}:{port}")
    
    app.run(host=host, port=port, debug=False)
