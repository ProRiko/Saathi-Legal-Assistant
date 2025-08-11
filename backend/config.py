import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # OpenRouter API Configuration
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', 'your-actual-api-key-here')
    DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'mistralai/mistral-7b-instruct:free')
    API_TIMEOUT = int(os.getenv('API_TIMEOUT', '30'))
    MAX_TOKENS = int(os.getenv('MAX_TOKENS', '500'))
    TEMPERATURE = float(os.getenv('TEMPERATURE', '0.7'))
    
    # Flask Configuration
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    FLASK_HOST = os.getenv('FLASK_HOST', '127.0.0.1')
    FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
    
    # Application Settings
    APP_NAME = os.getenv('APP_NAME', 'Saathi Legal Assistant')
    APP_VERSION = os.getenv('APP_VERSION', '1.0.0')
    
    # System prompt for the legal assistant
    LEGAL_ASSISTANT_PROMPT = """You are Saathi, a helpful legal assistant that provides general legal information for Indian law and common legal situations. 

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

    @staticmethod
    def is_api_configured():
        """Check if the API key is properly configured"""
        return Config.OPENROUTER_API_KEY != 'your-actual-api-key-here' and Config.OPENROUTER_API_KEY.strip() != ''
