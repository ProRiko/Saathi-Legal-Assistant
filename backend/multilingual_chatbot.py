# multilingual_chatbot.py
import requests
import json
import logging
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultilingualSaathiChatbot:
    def __init__(self):
        self.conversation_history = [
            {"role": "system", "content": Config.LEGAL_ASSISTANT_PROMPT}
        ]
        self.api_configured = Config.is_api_configured()
        
        # Language mappings
        self.language_prompts = {
            'english': 'Respond in English only.',
            'hindi': 'Provide your response in both Hindi and English. Format: **Hindi:** [response in Hindi] **English:** [response in English]',
            'marathi': 'Provide your response in both Marathi and English. Format: **मराठी:** [response in Marathi] **English:** [response in English]',
            'tamil': 'Provide your response in both Tamil and English. Format: **தமிழ்:** [response in Tamil] **English:** [response in English]',
            'telugu': 'Provide your response in both Telugu and English. Format: **తెలుగు:** [response in Telugu] **English:** [response in English]',
            'gujarati': 'Provide your response in both Gujarati and English. Format: **ગુજરાતી:** [response in Gujarati] **English:** [response in English]',
            'bengali': 'Provide your response in both Bengali and English. Format: **বাংলা:** [response in Bengali] **English:** [response in English]',
            'kannada': 'Provide your response in both Kannada and English. Format: **ಕನ್ನಡ:** [response in Kannada] **English:** [response in English]',
            'punjabi': 'Provide your response in both Punjabi and English. Format: **ਪੰਜਾਬੀ:** [response in Punjabi] **English:** [response in English]'
        }
        
        if not self.api_configured:
            logger.warning("OpenRouter API key not configured properly")
    
    def get_response(self, user_input, user_language='english', reset_conversation=False):
        """Get response from the chatbot in specified language"""
        
        # Check if API is configured
        if not self.api_configured:
            return self._get_fallback_response(user_input, user_language)
        
        try:
            # Reset conversation if requested
            if reset_conversation:
                self.reset_conversation()
            
            # Add language instruction to the user input
            language_instruction = self.language_prompts.get(user_language, self.language_prompts['english'])
            enhanced_input = f"{user_input}\n\nIMPORTANT: {language_instruction}"
            
            # Add user message to conversation
            self.conversation_history.append({"role": "user", "content": enhanced_input})
            
            # Prepare API request
            headers = {
                "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://openrouter.ai",
                "X-Title": Config.APP_NAME,
                "Content-Type": "application/json"
            }
            
            data = {
                "model": Config.DEFAULT_MODEL,
                "messages": self.conversation_history,
                "max_tokens": Config.MAX_TOKENS,
                "temperature": Config.TEMPERATURE
            }
            
            logger.info(f"Making multilingual API request with language: {user_language}")
            
            # Make API request
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions", 
                headers=headers, 
                json=data,
                timeout=Config.API_TIMEOUT
            )
            
            # Handle different response codes
            if response.status_code == 200:
                result = response.json()
                
                if "choices" in result and len(result["choices"]) > 0:
                    reply = result["choices"][0]["message"]["content"].strip()
                    
                    # Add assistant response to conversation
                    self.conversation_history.append({"role": "assistant", "content": reply})
                    
                    # Log usage if available
                    if "usage" in result:
                        logger.info(f"Token usage: {result['usage']}")
                    
                    return {
                        "reply": reply,
                        "language": user_language,
                        "intent": self._detect_intent(user_input),
                        "status": "success"
                    }
                else:
                    logger.error("Unexpected API response format")
                    return self._get_fallback_response(user_input, user_language, "UNEXPECTED_RESPONSE_FORMAT")
            
            elif response.status_code == 401:
                logger.error("API authentication failed")
                return self._get_fallback_response(user_input, user_language, "AUTHENTICATION_FAILED")
            
            elif response.status_code == 429:
                logger.warning("Rate limit exceeded")
                return self._get_fallback_response(user_input, user_language, "RATE_LIMIT_EXCEEDED")
            
            else:
                logger.error(f"API request failed with status code: {response.status_code}")
                return self._get_fallback_response(user_input, user_language, "API_REQUEST_FAILED")
        
        except requests.RequestException as e:
            logger.error(f"Network error: {str(e)}")
            return self._get_fallback_response(user_input, user_language, "NETWORK_ERROR")
        
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return self._get_fallback_response(user_input, user_language, "UNEXPECTED_ERROR")
    
    def _get_fallback_response(self, user_input, language='english', error_type=None):
        """Provide fallback responses in multiple languages"""
        
        fallback_responses = {
            'english': {
                'default': "I'm sorry, I'm having trouble processing your request right now. For urgent legal matters, please consult a qualified attorney.",
                'api_error': "I'm experiencing technical difficulties. Please try again in a few moments.",
                'rate_limit': "I'm receiving too many requests right now. Please wait a moment and try again."
            },
            'hindi': {
                'default': "**Hindi:** मुझे खुशी है कि आपने सवाल पूछा। कृपया एक योग्य वकील से सलाह लें। **English:** I'm sorry, I'm having trouble processing your request right now. For urgent legal matters, please consult a qualified attorney.",
                'api_error': "**Hindi:** मुझे तकनीकी समस्या हो रही है। कृपया कुछ देर बाद पुनः प्रयास करें। **English:** I'm experiencing technical difficulties. Please try again in a few moments.",
                'rate_limit': "**Hindi:** अभी बहुत सारे अनुरोध आ रहे हैं। कृपया थोड़ा इंतजार करें। **English:** I'm receiving too many requests right now. Please wait a moment and try again."
            },
            'marathi': {
                'default': "**मराठी:** मला खुशी आहे की तुम्ही प्रश्न विचारला. कृपया एका पात्र वकीलाचा सल्ला घ्या. **English:** I'm sorry, I'm having trouble processing your request right now. For urgent legal matters, please consult a qualified attorney.",
                'api_error': "**मराठी:** मला तांत्रिक अडचणी येत आहेत. कृपया काही क्षणानंतर पुन्हा प्रयत्न करा. **English:** I'm experiencing technical difficulties. Please try again in a few moments.",
                'rate_limit': "**मराठी:** सध्या खूप विनंत्या येत आहेत. कृपया थोडी वाट पाहा. **English:** I'm receiving too many requests right now. Please wait a moment and try again."
            },
            'tamil': {
                'default': "**தமிழ்:** நீங்கள் கேள்வி கேட்டதில் மகிழ்ச்சி. தயவு செய்து ஒரு தகுதியான வழக்குரைஞரை அணுகவும். **English:** I'm sorry, I'm having trouble processing your request right now. For urgent legal matters, please consult a qualified attorney.",
                'api_error': "**தமிழ்:** எனக்கு தொழில்நுட்ப சிக்கல்கள் ஏற்பட்டுள்ளன. சிறிது நேரத்தில் மீண்டும் முயற்சி செய்யுங்கள். **English:** I'm experiencing technical difficulties. Please try again in a few moments.",
                'rate_limit': "**தமிழ்:** இப்போது நிறைய கோரிக்கைகள் வருகின்றன. சிறிது காத்திருந்து முயற்சி செய்யுங்கள். **English:** I'm receiving too many requests right now. Please wait a moment and try again."
            }
        }
        
        # Get appropriate response
        lang_responses = fallback_responses.get(language, fallback_responses['english'])
        
        if error_type == "RATE_LIMIT_EXCEEDED":
            response_text = lang_responses.get('rate_limit', lang_responses['default'])
        elif error_type in ["API_REQUEST_FAILED", "AUTHENTICATION_FAILED", "NETWORK_ERROR"]:
            response_text = lang_responses.get('api_error', lang_responses['default'])
        else:
            response_text = lang_responses['default']
        
        return {
            "reply": response_text,
            "language": language,
            "intent": self._detect_intent(user_input),
            "status": "fallback",
            "error": error_type
        }
    
    def _detect_intent(self, user_input):
        """Simple intent detection based on keywords"""
        user_input_lower = user_input.lower()
        
        legal_keywords = {
            'document': ['document', 'agreement', 'contract', 'notice', 'template', 'दस्तावेज', 'करार'],
            'rights': ['rights', 'entitlement', 'gratuity', 'pf', 'provident', 'अधिकार', 'हक'],
            'court': ['court', 'case', 'judge', 'hearing', 'न्यायालय', 'मामला'],
            'family': ['marriage', 'divorce', 'custody', 'property', 'inheritance', 'शादी', 'तलाक'],
            'criminal': ['fir', 'police', 'bail', 'arrest', 'crime', 'एफआईआर', 'पुलिस'],
            'labor': ['salary', 'job', 'employment', 'termination', 'workplace', 'नौकरी', 'वेतन'],
            'property': ['property', 'rent', 'landlord', 'tenant', 'संपत्ति', 'किराया']
        }
        
        for intent, keywords in legal_keywords.items():
            if any(keyword in user_input_lower for keyword in keywords):
                return intent
        
        return 'general'
    
    def reset_conversation(self):
        """Reset the conversation history"""
        self.conversation_history = [
            {"role": "system", "content": Config.LEGAL_ASSISTANT_PROMPT}
        ]
        logger.info("Conversation history reset")
    
    def get_conversation_history(self):
        """Get the current conversation history"""
        return self.conversation_history
    
    def set_language_preference(self, language):
        """Set user's language preference"""
        if language in self.language_prompts:
            return True
        return False
