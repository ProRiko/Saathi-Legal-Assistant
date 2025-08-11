# chatbot.py
import requests
import json
import logging
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SaathiChatbot:
    def __init__(self):
        self.conversation_history = [
            {"role": "system", "content": Config.LEGAL_ASSISTANT_PROMPT}
        ]
        self.api_configured = Config.is_api_configured()
        
        if not self.api_configured:
            logger.warning("OpenRouter API key not configured properly")
    
    def get_response(self, user_input, reset_conversation=False):
        """Get response from the chatbot"""
        
        # Check if API is configured
        if not self.api_configured:
            return {
                "reply": "Sorry, the chatbot is not properly configured. Please contact the administrator.",
                "intent": None,
                "error": "API_NOT_CONFIGURED"
            }
        
        try:
            # Reset conversation if requested
            if reset_conversation:
                self.reset_conversation()
            
            # Add user message to conversation
            self.conversation_history.append({"role": "user", "content": user_input})
            
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
            
            logger.info(f"Making API request to OpenRouter with model: {Config.DEFAULT_MODEL}")
            
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
                        "intent": self._detect_intent(user_input),
                        "status": "success"
                    }
                else:
                    logger.error("Unexpected API response format")
                    return {
                        "reply": "I received an unexpected response. Please try again.",
                        "intent": None,
                        "error": "UNEXPECTED_RESPONSE_FORMAT"
                    }
            
            elif response.status_code == 401:
                logger.error("API authentication failed")
                return {
                    "reply": "There's an issue with my authentication. Please contact support.",
                    "intent": None,
                    "error": "AUTHENTICATION_FAILED"
                }
            
            elif response.status_code == 429:
                logger.error("API rate limit exceeded")
                return {
                    "reply": "I'm currently receiving too many requests. Please try again in a moment.",
                    "intent": None,
                    "error": "RATE_LIMIT_EXCEEDED"
                }
            
            else:
                logger.error(f"API request failed with status {response.status_code}: {response.text}")
                return {
                    "reply": "I'm having trouble connecting to my knowledge base. Please try again later.",
                    "intent": None,
                    "error": f"API_ERROR_{response.status_code}"
                }
                
        except requests.exceptions.Timeout:
            logger.error("API request timed out")
            return {
                "reply": "My response is taking too long. Please try again with a simpler question.",
                "intent": None,
                "error": "TIMEOUT"
            }
            
        except requests.exceptions.ConnectionError:
            logger.error("Connection error while making API request")
            return {
                "reply": "I'm having trouble connecting to the internet. Please check your connection and try again.",
                "intent": None,
                "error": "CONNECTION_ERROR"
            }
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {
                "reply": "I encountered an unexpected error. Please try again later.",
                "intent": None,
                "error": "UNEXPECTED_ERROR"
            }
    
    def reset_conversation(self):
        """Reset the conversation history"""
        self.conversation_history = [
            {"role": "system", "content": Config.LEGAL_ASSISTANT_PROMPT}
        ]
        logger.info("Conversation history reset")
    
    def _detect_intent(self, user_input):
        """Simple intent detection based on keywords"""
        user_input_lower = user_input.lower()
        
        # Define intents and their keywords
        intents = {
            "property_law": ["property", "real estate", "landlord", "tenant", "rent", "deposit", "lease"],
            "family_law": ["marriage", "divorce", "custody", "alimony", "domestic", "family"],
            "criminal_law": ["police", "arrest", "crime", "criminal", "theft", "assault", "bail"],
            "consumer_law": ["consumer", "refund", "warranty", "defective", "fraud", "complaint"],
            "employment_law": ["job", "employment", "salary", "workplace", "fired", "resignation"],
            "contract_law": ["contract", "agreement", "breach", "terms", "conditions"],
            "civil_law": ["civil", "damages", "compensation", "negligence", "liability"]
        }
        
        for intent, keywords in intents.items():
            if any(keyword in user_input_lower for keyword in keywords):
                return intent
        
        return "general_legal"

# Create global chatbot instance
chatbot = SaathiChatbot()

def get_response(user_input, reset_conversation=False):
    """Wrapper function for backward compatibility"""
    return chatbot.get_response(user_input, reset_conversation)
