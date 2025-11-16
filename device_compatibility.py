"""
Device Compatibility Helper for Saathi Legal Assistant
Handles cross-device access issues, CORS, headers, and mobile compatibility
"""

from flask import Flask, request
from flask_cors import CORS
from functools import wraps
import logging

class DeviceCompatibilityHandler:
    """Handles device compatibility and access issues"""
    
    def __init__(self, app: Flask):
        self.app = app
        self.setup_cors()
        self.setup_headers()
        self.setup_mobile_headers()
        self.logger = logging.getLogger(__name__)
    
    def setup_cors(self):
        """Configure comprehensive CORS for all devices AND automated requests"""
        CORS(self.app, 
             origins=['*'],  # Allow all origins including bots
             methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'HEAD'],
             allow_headers=[
                'Content-Type', 
                'Authorization', 
                'Access-Control-Allow-Credentials',
                'Access-Control-Allow-Origin',
                'X-Requested-With',
                'Accept',
                'Accept-Version',
                'Accept-Encoding',
                'Accept-Language',
                'Content-Length',
                'Content-MD5',
                'Date',
                'X-Api-Version',
                'X-CSRF-Token',
                'User-Agent',
                'X-Forwarded-For',
                'X-Real-IP'
             ],
             supports_credentials=True,
             expose_headers=['Content-Range', 'X-Content-Range'],
             max_age=3600  # Cache preflight for 1 hour
        )
    
    def setup_headers(self):
        """Add comprehensive headers for device compatibility AND bot access"""
        @self.app.after_request
        def after_request(response):
            # CORS headers for all devices and bots
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With,Accept,Accept-Version,Accept-Encoding,Accept-Language,Content-Length,Content-MD5,Date,X-Api-Version,X-CSRF-Token,User-Agent')
            response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS,HEAD')
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            
            # Security headers that don't block bots
            response.headers.add('X-Content-Type-Options', 'nosniff')
            response.headers.add('Referrer-Policy', 'no-referrer-when-downgrade')
            
            # Bot-friendly caching
            response.headers.add('Cache-Control', 'public, max-age=300')  # 5 minutes cache
            
            # Remove restrictive headers for bots
            if 'bot' in request.headers.get('User-Agent', '').lower() or 'crawler' in request.headers.get('User-Agent', '').lower():
                response.headers.pop('X-Frame-Options', None)
                response.headers.pop('Content-Security-Policy', None)
            
            return response
    
    def setup_mobile_headers(self):
        """Special headers for mobile device compatibility"""
        @self.app.before_request
        def before_request():
            # Handle preflight requests for all devices
            if request.method == 'OPTIONS':
                response = self.app.make_default_options_response()
                headers = response.headers
                headers['Access-Control-Allow-Origin'] = '*'
                headers['Access-Control-Allow-Methods'] = 'DELETE, GET, POST, PUT'
                headers['Access-Control-Allow-Headers'] = request.headers.get('Access-Control-Request-Headers', '')
                return response
    
    def device_compatible_response(self, data, status_code=200):
        """Create a response that works across all devices"""
        from flask import jsonify, make_response
        
        response = make_response(jsonify(data), status_code)
        
        # Additional headers for problematic devices
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        # Mobile-specific headers
        user_agent = request.headers.get('User-Agent', '').lower()
        
        if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
            response.headers['X-Mobile-Device'] = 'true'
            response.headers['Cache-Control'] = 'no-cache'
        
        return response

def device_compatible_endpoint(f):
    """Decorator to make endpoints compatible with all devices"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Log device information for debugging
        user_agent = request.headers.get('User-Agent', 'Unknown')
        origin = request.headers.get('Origin', 'Unknown')
        
        logging.info(f"Device Access - UA: {user_agent[:100]}, Origin: {origin}")
        
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logging.error(f"Device compatibility error: {str(e)}")
            # Return error in a format that works on all devices
            from flask import jsonify
            return jsonify({
                "error": "Device compatibility issue. Please try refreshing the page.",
                "status": "error",
                "details": str(e)
            }), 500
    
    return decorated_function

def get_device_info():
    """Extract device information for debugging"""
    user_agent = request.headers.get('User-Agent', '')
    
    device_info = {
        'user_agent': user_agent,
        'is_mobile': any(mobile in user_agent.lower() for mobile in ['mobile', 'android', 'iphone', 'ipad']),
        'is_android': 'android' in user_agent.lower(),
        'is_ios': any(ios in user_agent.lower() for ios in ['iphone', 'ipad', 'ipod']),
        'is_chrome': 'chrome' in user_agent.lower(),
        'is_safari': 'safari' in user_agent.lower() and 'chrome' not in user_agent.lower(),
        'is_firefox': 'firefox' in user_agent.lower(),
        'origin': request.headers.get('Origin', ''),
        'host': request.headers.get('Host', ''),
        'referer': request.headers.get('Referer', '')
    }
    
    return device_info
