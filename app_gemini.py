"""
Saathi Legal Assistant - Gemini AI Powered
Railway.app deployment ready with Google Gemini API
"""
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import logging
from datetime import datetime
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration from environment variables
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'your-gemini-api-key-here')
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-1.5-flash')
MAX_TOKENS = int(os.environ.get('MAX_TOKENS', '500'))
TEMPERATURE = float(os.environ.get('TEMPERATURE', '0.7'))

# System prompt for legal assistant
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
9. Provide relevant Indian law references when possible
10. Be culturally sensitive to Indian legal context

Remember: You provide information, not legal advice. Always encourage users to seek professional legal counsel for their specific situations."""

# Global conversation history
conversation_history = []

def is_api_configured():
    """Check if Gemini API key is configured"""
    return GEMINI_API_KEY != 'your-gemini-api-key-here' and GEMINI_API_KEY.strip() != ''

def detect_intent(user_input):
    """Simple intent detection for legal queries"""
    user_input_lower = user_input.lower()
    
    intents = {
        "property_law": ["property", "real estate", "landlord", "tenant", "rent", "deposit", "lease", "eviction", "housing"],
        "employment_law": ["job", "employment", "salary", "workplace", "fired", "resignation", "termination", "labor"],
        "family_law": ["marriage", "divorce", "custody", "alimony", "domestic", "family", "dowry", "maintenance"],
        "criminal_law": ["police", "arrest", "crime", "criminal", "theft", "assault", "bail", "fir", "complaint"],
        "consumer_law": ["consumer", "refund", "warranty", "defective", "fraud", "complaint", "product", "service"],
        "contract_law": ["contract", "agreement", "breach", "terms", "conditions", "violation", "business"],
        "civil_law": ["civil", "damages", "compensation", "negligence", "liability", "tort", "injury"],
        "tax_law": ["tax", "income tax", "gst", "tds", "return", "penalty", "assessment"],
        "constitutional_law": ["constitutional", "fundamental rights", "petition", "writ", "supreme court", "high court"]
    }
    
    for intent, keywords in intents.items():
        if any(keyword in user_input_lower for keyword in keywords):
            return intent
    
    return "general_legal"

def call_gemini_api(messages):
    """Call Google Gemini API"""
    try:
        # Prepare the request for Gemini API
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
        headers = {
            "Content-Type": "application/json"
        }
        
        # Convert messages to Gemini format
        prompt_parts = []
        
        # Add system prompt first
        prompt_parts.append({
            "text": SYSTEM_PROMPT + "\n\nConversation:\n"
        })
        
        # Add conversation history
        for msg in messages:
            role_text = f"{msg['role'].title()}: {msg['content']}\n"
            prompt_parts.append({"text": role_text})
        
        # Add instruction for assistant response
        prompt_parts.append({"text": "Assistant: "})
        
        data = {
            "contents": [{
                "parts": prompt_parts
            }],
            "generationConfig": {
                "temperature": TEMPERATURE,
                "maxOutputTokens": MAX_TOKENS,
            }
        }
        
        # Make API request
        response = requests.post(
            f"{url}?key={GEMINI_API_KEY}",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                content = result['candidates'][0]['content']['parts'][0]['text']
                return content.strip()
            else:
                logger.error(f"No candidates in Gemini response: {result}")
                return None
        else:
            logger.error(f"Gemini API error {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error calling Gemini API: {str(e)}")
        return None

@app.route('/')
def home():
    """Serve the web interface"""
    try:
        with open('web_interface.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return jsonify({
            "status": "healthy",
            "app": "Saathi Legal Assistant - Gemini Powered",
            "version": "2.0.0",
            "message": "API is running. Web interface not found.",
            "api_configured": is_api_configured(),
            "timestamp": datetime.utcnow().isoformat()
        })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "app": "Saathi Legal Assistant - Gemini Powered",
        "version": "2.0.0",
        "api_configured": is_api_configured(),
        "model": GEMINI_MODEL,
        "provider": "Google Gemini",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint using Gemini API"""
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
        
        # Keep conversation history manageable (last 10 exchanges)
        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]
        
        logger.info(f"Processing query: {user_input[:50]}...")
        
        # Call Gemini API
        reply = call_gemini_api(conversation_history)
        
        if reply:
            # Add assistant response to conversation
            conversation_history.append({"role": "assistant", "content": reply})
            
            # Detect intent
            intent = detect_intent(user_input)
            
            return jsonify({
                "reply": reply,
                "intent": intent,
                "status": "success",
                "provider": "Google Gemini",
                "model": GEMINI_MODEL,
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            return jsonify({
                "reply": "I'm having trouble connecting to my knowledge base. Please try again later.",
                "intent": None,
                "error": "GEMINI_API_ERROR",
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
        conversation_history = []
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
        "version": "2.0.0",
        "model": GEMINI_MODEL,
        "provider": "Google Gemini",
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
    
    print(f"🚀 Starting Saathi Legal Assistant - Gemini Powered")
    print(f"🤖 Model: {GEMINI_MODEL}")
    print(f"🔑 API Configured: {is_api_configured()}")
    print(f"🌐 Running on {host}:{port}")
    
    app.run(host=host, port=port, debug=False)
