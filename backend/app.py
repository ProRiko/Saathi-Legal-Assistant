from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import logging
import os
from chatbot import get_response, chatbot
from config import Config
from rights_calculator import LegalRightsCalculator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize the rights calculator
rights_calc = LegalRightsCalculator()

# Configure Flask from config
app.config['DEBUG'] = Config.FLASK_DEBUG

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "app": Config.APP_NAME,
        "version": Config.APP_VERSION,
        "api_configured": Config.is_api_configured()
    })

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files from parent directory"""
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return send_from_directory(parent_dir, filename)

@app.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint"""
    try:
        data = request.json
        if not data:
            return jsonify({
                "error": "No JSON data provided",
                "status": "error"
            }), 400
        
        user_input = data.get('query', '').strip()
        lang = data.get('lang', 'en')  # For future multilingual support
        reset_conversation = data.get('reset', False)
        
        if not user_input:
            return jsonify({
                "error": "No query provided",
                "status": "error"
            }), 400
        
        logger.info(f"Received query: {user_input}")
        
        # Get response from chatbot
        response = get_response(user_input, reset_conversation)
        
        # Add metadata to response
        response['timestamp'] = request.environ.get('REQUEST_TIME', None)
        response['lang'] = lang
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            "reply": "I'm experiencing technical difficulties. Please try again later.",
            "intent": None,
            "error": "INTERNAL_SERVER_ERROR",
            "status": "error"
        }), 500

@app.route('/reset', methods=['POST'])
def reset_conversation():
    """Reset conversation history"""
    try:
        chatbot.reset_conversation()
        return jsonify({
            "message": "Conversation reset successfully",
            "status": "success"
        })
    except Exception as e:
        logger.error(f"Error resetting conversation: {str(e)}")
        return jsonify({
            "error": "Failed to reset conversation",
            "status": "error"
        }), 500

@app.route('/config', methods=['GET'])
def get_config():
    """Get public configuration information"""
    return jsonify({
        "app_name": Config.APP_NAME,
        "version": Config.APP_VERSION,
        "model": Config.DEFAULT_MODEL,
        "api_configured": Config.is_api_configured(),
        "max_tokens": Config.MAX_TOKENS
    })

@app.route('/api/rights-calculators', methods=['GET'])
def get_rights_calculators():
    """Get all available rights calculators"""
    try:
        calculators = rights_calc.get_calculators()
        return jsonify(calculators)
    except Exception as e:
        logger.error(f"Error getting calculators: {str(e)}")
        return jsonify({
            "error": "Failed to load calculators",
            "status": "error"
        }), 500

@app.route('/api/calculate-rights', methods=['POST'])
def calculate_rights():
    """Calculate legal rights based on provided data"""
    try:
        data = request.json
        if not data:
            return jsonify({
                "error": "No JSON data provided",
                "status": "error"
            }), 400
        
        calculator = data.get('calculator')
        category = data.get('category')
        calc_data = data.get('data', {})
        
        if not calculator or not category:
            return jsonify({
                "error": "Calculator and category are required",
                "status": "error"
            }), 400
        
        logger.info(f"Calculating rights for {category}.{calculator}")
        
        # Convert string values to appropriate types
        for key, value in calc_data.items():
            if isinstance(value, str) and value.isdigit():
                calc_data[key] = int(value)
            elif isinstance(value, str):
                try:
                    calc_data[key] = float(value)
                except ValueError:
                    pass  # Keep as string if not a number
        
        # Perform calculation
        result = rights_calc.calculate(category, calculator, calc_data)
        
        return jsonify({
            "success": True,
            "calculation": result
        })
        
    except Exception as e:
        logger.error(f"Error calculating rights: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "status": "error"
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "error": "Method not allowed",
        "status": "error"
    }), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal server error",
        "status": "error"
    }), 500

if __name__ == '__main__':
    # Check if API is configured before starting
    if not Config.is_api_configured():
        print("⚠️  WARNING: OpenRouter API key is not configured!")
        print("Please set up your .env file with a valid API key.")
        print("The server will start but chatbot functionality will be limited.")
    
    print(f"🚀 Starting {Config.APP_NAME} v{Config.APP_VERSION}")
    print(f"🤖 Using model: {Config.DEFAULT_MODEL}")
    print(f"🌐 Server will run on http://{Config.FLASK_HOST}:{Config.FLASK_PORT}")
    
    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG
    )
