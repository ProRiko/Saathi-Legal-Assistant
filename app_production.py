"""
Saathi Legal Assistant - Gemini AI Powered
Railway.app deployment ready with Google Gemini API
Enhanced with Legal Document Generation - Production Ready
"""
import os
import re
import uuid
from typing import Any, Dict
from flask import Flask, request, jsonify, send_file, send_from_directory, make_response, render_template_string
from flask_cors import CORS
import requests
import logging
from datetime import datetime, timedelta, timezone
import json
from collections import defaultdict, deque
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import io
import tempfile
import time
import hashlib
from functools import wraps
from threading import Lock

# Production Security and Rate Limiting
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    from flask_talisman import Talisman
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False
    print("⚠️  Security packages not available. Installing security middleware...")

# MongoDB imports (optional - will work without MongoDB)
try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    print("MongoDB not available. Conversation logging will be disabled.")

# Set up logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('saathi.log') if os.path.exists('.') else logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONSENT_LOG_PATH = os.path.join(BASE_DIR, 'consent_logs.jsonl')
CONSENT_SCRIPT_TAG = '<script src="consent-modal.js" defer></script>'
TOOL_MANIFEST_PATH = os.path.join(BASE_DIR, 'tool_metadata.json')
TEMPLATE_MANIFEST_PATH = os.path.join(BASE_DIR, 'template_metadata.json')
CONSENT_NOSCRIPT_BLOCK = (
    '<noscript>'
    '<div class="no-js-consent-banner" role="alert">'
    'Saathi Legal Assistant needs JavaScript enabled to capture your consent. '
    'Please enable JavaScript and reload to use the tools.'
    '</div>'
    '</noscript>'
)
CONSENT_LOG_LOCK = Lock()
def load_tool_manifest(path: str = TOOL_MANIFEST_PATH) -> Dict[str, Any]:
    """Load structured metadata for tools, templates, and calculators."""
    try:
        with open(path, 'r', encoding='utf-8') as manifest_file:
            data = json.load(manifest_file)
            if isinstance(data, dict) and isinstance(data.get('tools'), list):
                return data
    except FileNotFoundError:
        logger.warning("Tool metadata manifest not found at %s", path)
    except json.JSONDecodeError as exc:
        logger.error("Unable to parse tool metadata manifest: %s", exc)
    return {"tools": []}


def load_template_manifest(path: str = TEMPLATE_MANIFEST_PATH) -> Dict[str, Any]:
    """Load manifest that drives template metadata, fields, and samples."""
    try:
        with open(path, 'r', encoding='utf-8') as manifest_file:
            data = json.load(manifest_file)
            if isinstance(data, dict) and isinstance(data.get('templates'), list):
                return data
    except FileNotFoundError:
        logger.warning("Template metadata manifest not found at %s", path)
    except json.JSONDecodeError as exc:
        logger.error("Unable to parse template metadata manifest: %s", exc)
    return {"templates": []}


TOOL_MANIFEST = load_tool_manifest()
TOOL_INDEX = {entry.get('slug'): entry for entry in TOOL_MANIFEST.get('tools', [])}
TEMPLATE_MANIFEST = load_template_manifest()
TEMPLATE_INDEX = {entry.get('slug'): entry for entry in TEMPLATE_MANIFEST.get('templates', []) if entry.get('slug')}


def build_category_metadata(category_key: str) -> Dict[str, Dict[str, str]]:
    """Derive review metadata for a given category from the manifest."""
    meta: Dict[str, Dict[str, str]] = {}
    for entry in TOOL_MANIFEST.get('tools', []):
        if entry.get('category') != category_key:
            continue
        slug = entry.get('slug')
        if not slug:
            continue
        meta[slug] = {
            "reviewed_on": entry.get('reviewed_on') or "Not reviewed yet",
            "reviewed_by": entry.get('reviewed_by') or "Not reviewed yet",
            "risk_level": (entry.get('risk_level') or "Unverified").lower(),
            "sample_preview": entry.get('sample_preview') or "Sample preview is coming soon.",
            "when_to_consult": entry.get('when_to_consult') or "Consult a lawyer if the dispute value exceeds ₹50,000 or if ownership is contested.",
        }
    return meta


def build_template_category_metadata(category_key: str) -> Dict[str, Dict[str, Any]]:
    """Build metadata map for templates from the template manifest."""
    meta: Dict[str, Dict[str, Any]] = {}
    for entry in TEMPLATE_MANIFEST.get('templates', []):
        if entry.get('category') != category_key:
            continue
        slug = entry.get('slug')
        if not slug:
            continue
        combined = REVIEW_METADATA_DEFAULT.copy()
        combined.update({
            "reviewed_on": entry.get('last_reviewed_date') or REVIEW_METADATA_DEFAULT["reviewed_on"],
            "reviewed_by": entry.get('reviewed_by') or REVIEW_METADATA_DEFAULT["reviewed_by"],
            "risk_level": (entry.get('risk_level') or REVIEW_METADATA_DEFAULT["risk_level"]).lower(),
            "display_name": entry.get('display_name'),
            "pdf_title": entry.get('pdf_title'),
            "sample_path": entry.get('sample_path'),
            "when_to_consult_list": entry.get('when_to_consult_lawyer') or [],
            "prefill_fields": entry.get('prefill_fields') or {},
        })
        if not combined.get('when_to_consult_list'):
            combined['when_to_consult_list'] = [combined['when_to_consult']]
        combined['when_to_consult'] = (entry.get('when_to_consult_lawyer') or [combined['when_to_consult']])[0]
        meta[slug] = combined
    return meta


def get_tool_entry(slug: str) -> Dict[str, Any]:
    return TOOL_INDEX.get(slug, {})


def get_template_entry(slug: str) -> Dict[str, Any]:
    return TEMPLATE_INDEX.get(slug, {})



def parse_allowed_origins() -> list[str]:
    """Read ALLOWED_ORIGINS env var (comma-separated) for flexible deployments."""
    raw = os.getenv('ALLOWED_ORIGINS', '*')
    if not raw:
        return ['*']
    if raw.strip() == '*':
        return ['*']
    origins = [origin.strip() for origin in raw.split(',') if origin.strip()]
    return origins or ['*']


ALLOWED_ORIGINS = parse_allowed_origins()
ALLOW_WILDCARD = ALLOWED_ORIGINS == ['*']
CORS_ORIGIN = '*' if ALLOW_WILDCARD else ALLOWED_ORIGINS
CORS_CREDENTIALS = not ALLOW_WILDCARD

CORS(app,
     origins=CORS_ORIGIN,
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     supports_credentials=CORS_CREDENTIALS)

# Initialize security middleware
if SECURITY_AVAILABLE:
    # Rate limiting
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour", "10 per minute"],
        storage_uri="memory://",
        headers_enabled=True,
    )
    
    # Security headers
    Talisman(
        app,
        force_https=True if os.environ.get('RAILWAY_ENVIRONMENT_NAME') == 'production' else False,
        strict_transport_security=True,
        content_security_policy={
            'default-src': "'self'",
            'script-src': "'self' 'unsafe-inline' 'unsafe-eval'",
            'style-src': "'self' 'unsafe-inline'",
            'img-src': "'self' data: https:",
            'font-src': "'self'",
            'connect-src': "'self'",
        }
    )
else:
    # Fallback rate limiting without flask-limiter
    request_counts = defaultdict(lambda: {'count': 0, 'reset_time': time.time() + 3600})
    
    def simple_rate_limit(max_requests=50, window=3600):
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ['REMOTE_ADDR'])
                current_time = time.time()
                
                if current_time > request_counts[client_ip]['reset_time']:
                    request_counts[client_ip] = {'count': 0, 'reset_time': current_time + window}
                
                if request_counts[client_ip]['count'] >= max_requests:
                    return jsonify({
                        "error": "Rate limit exceeded. Please try again later.",
                        "status": "error"
                    }), 429
                
                request_counts[client_ip]['count'] += 1
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    # Apply simple rate limiting to chat endpoint
    limiter = None

# Production-ready error handling and monitoring
error_counts = defaultdict(int)
uptime_start = time.time()

@app.errorhandler(Exception)
def handle_exception(e):
    error_counts['total'] += 1
    error_type = type(e).__name__
    error_counts[error_type] += 1
    
    logger.error(f"Unhandled exception [{error_type}]: {str(e)}")
    
    # Don't expose internal errors in production
    if os.environ.get('RAILWAY_ENVIRONMENT_NAME') == 'production':
        return jsonify({
            "error": "Internal server error", 
            "status": "error",
            "message": "Please try again or contact support",
            "error_id": hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        }), 500
    else:
        return jsonify({
            "error": "Internal server error", 
            "status": "error",
            "message": str(e),
            "type": error_type
        }), 500

@app.errorhandler(404)
def not_found(error):
    error_counts['404'] += 1
    return jsonify({"error": "Endpoint not found", "status": "error"}), 404

@app.errorhandler(429)
def rate_limit_exceeded(error):
    error_counts['429'] += 1
    return jsonify({
        "error": "Rate limit exceeded", 
        "status": "error",
        "message": "Please wait before making more requests"
    }), 429

@app.errorhandler(500)
def internal_error(error):
    error_counts['500'] += 1
    return jsonify({
        "error": "Internal server error", 
        "status": "error",
        "message": "Please try again later"
    }), 500

# Static file serving routes
@app.route('/styles.css')
def serve_styles():
    """Serve the main CSS file"""
    try:
        return send_file('styles.css', mimetype='text/css')
    except FileNotFoundError:
        return "CSS file not found", 404

@app.route('/chat-styles.css')
def serve_chat_styles():
    """Serve the chat CSS file"""
    try:
        return send_file('chat-styles.css', mimetype='text/css')
    except FileNotFoundError:
        return "CSS file not found", 404

@app.route('/enhanced-ux.css')
def serve_enhanced_ux_styles():
    """Serve the enhanced UX CSS file"""
    try:
        return send_file('enhanced-ux.css', mimetype='text/css')
    except FileNotFoundError:
        return "Enhanced UX CSS file not found", 404

@app.route('/enhanced-ux.js')
def serve_enhanced_ux_js():
    """Serve the enhanced UX JavaScript file"""
    try:
        return send_file('enhanced-ux.js', mimetype='application/javascript')
    except FileNotFoundError:
        return "Enhanced UX JS file not found", 404


@app.route('/consent-modal.js')
def serve_consent_script():
    """Serve the global consent modal script"""
    try:
        return send_file('consent-modal.js', mimetype='application/javascript')
    except FileNotFoundError:
        return "Consent script not found", 404


def inject_consent_modal(html: str) -> str:
    """Ensure every rendered HTML page loads the consent modal script and fallback banner."""
    needs_script = 'consent-modal.js' not in html
    needs_noscript = 'no-js-consent-banner' not in html

    if needs_script:
        if '</body>' in html:
            html = html.replace('</body>', f"{CONSENT_SCRIPT_TAG}\n</body>")
        else:
            html = f"{html}{CONSENT_SCRIPT_TAG}"

    if needs_noscript:
        if '</body>' in html:
            html = html.replace('</body>', f"{CONSENT_NOSCRIPT_BLOCK}\n</body>")
        else:
            html = f"{html}{CONSENT_NOSCRIPT_BLOCK}"

    return html


def render_html_with_consent(filename: str, missing_message: str = "Page not found"):
    """Read an HTML file, inject consent script, and handle missing files gracefully."""
    try:
        with open(filename, 'r', encoding='utf-8') as file_handle:
            return inject_consent_modal(file_handle.read())
    except FileNotFoundError:
        return missing_message, 404

# Root route - simple and reliable
@app.route('/')
def home():
    """Main landing page"""
    try:
        return render_html_with_consent('landing.html')
    except FileNotFoundError:
        # Fallback HTML for emergencies
        fallback = '''<!DOCTYPE html>
<html>
<head><title>Saathi Legal Assistant</title></head>
<body>
    <h1>🏛️ Saathi Legal Assistant</h1>
    <p>Your AI-powered legal companion is running!</p>
    <p>Status: Server Online ✅</p>
    <a href="/test">Test Minimal Version</a>
</body>
</html>'''
        return inject_consent_modal(fallback), 200

@app.route('/test')
def test_page():
    """Test minimal page to troubleshoot issues"""
    try:
        return render_html_with_consent('test_minimal.html')
    except FileNotFoundError:
        fallback = '''<!DOCTYPE html>
<html><head><title>Test</title></head>
<body><h1>Test page - Server is working ✅</h1></body></html>'''
        return inject_consent_modal(fallback), 200

@app.route('/manifest.json')
def serve_manifest():
    """Serve the PWA manifest file"""
    try:
        return send_file('manifest.json', mimetype='application/json')
    except FileNotFoundError:
        return "Manifest file not found", 404

# New Feature Routes
@app.route('/case-tracker.html')
@app.route('/case_tracker.html')
def serve_case_tracker():
    """Serve the legal case tracker page"""
    return render_html_with_consent('case_tracker.html', 'Case tracker not found')

@app.route('/legal-help.html')
def serve_legal_help():
    """Serve the legal help directory page"""
    return render_html_with_consent('legal_help.html', 'Legal help directory not found')

@app.route('/legal-notices.html')
def serve_legal_notices():
    """Serve the legal notices landing page"""
    return render_html_with_consent('legal_notices.html', 'Legal notices page not found')

@app.route('/agreement-templates.html')
def serve_agreement_templates():
    """Serve the agreement templates landing page"""
    return render_html_with_consent('agreement_templates.html', 'Agreement templates page not found')

@app.route('/legal-calculators.html')
def serve_legal_calculators():
    """Serve the advanced legal calculators page"""
    return render_html_with_consent('legal_calculators.html', 'Legal calculators page not found')

@app.route('/language-selection.html')
@app.route('/language_selection.html')
def serve_language_selection():
    """Serve the language selection page"""
    return render_html_with_consent('language_selection.html', 'Language selection page not found')


@app.route('/privacy.html')
def serve_privacy_policy():
    """Serve the privacy policy page"""
    return render_html_with_consent('privacy.html', 'Privacy policy not found')


@app.route('/consent-required.html')
def serve_consent_required():
    """Explain why consent is mandatory when a user declines."""
    return render_html_with_consent('consent_required.html', 'Consent information not found')


@app.route('/tools.html')
def serve_tools_dashboard():
    """Serve the central tools discovery page."""
    return render_html_with_consent('tools.html', 'Tools page not found')

@app.route('/calculator.html') 
def serve_calculator():
    """Serve the simple calculator page"""
    return render_html_with_consent('simple_calculator.html', 'Calculator page not found')

@app.route('/version')
def version_check():
    """Simple version check endpoint"""
    return jsonify({
        "version": "5.0.0 - FEATURE #5 MULTI-LANGUAGE SUPPORT",
        "status": "working", 
        "timestamp": datetime.now().isoformat(),
        "features": ["Smart Templates", "Rights Calculator", "Legal Help Directory", "Legal Case Tracker"]
    })

# MongoDB Configuration
MONGO_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'saathi_legal_assistant')

# Initialize MongoDB connection
mongo_client = None
db = None

if MONGODB_AVAILABLE:
    try:
        mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Test connection
        mongo_client.admin.command('ismaster')
        db = mongo_client[DATABASE_NAME]
        logger.info("✅ MongoDB connected successfully")
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.warning(f"⚠️ MongoDB connection failed: {e}")
        logger.warning("📝 Conversation logging will be disabled")
        mongo_client = None
        db = None
else:
    logger.warning("📦 pymongo not installed. Install with: pip install pymongo")

# Configuration from environment variables
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'your-gemini-api-key-here')
GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-1.5-flash')
MAX_TOKENS = int(os.environ.get('MAX_TOKENS', '500'))
TEMPERATURE = float(os.environ.get('TEMPERATURE', '0.7'))

# Rate limiting configuration
RATE_LIMIT_REQUESTS = 3  # Maximum requests per minute
RATE_LIMIT_WINDOW = 60   # Time window in seconds (1 minute)

# In-memory rate limiting store (for production, consider using Redis)
rate_limit_store = defaultdict(deque)

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

def get_client_identifier(request):
    """Get a unique identifier for the client (IP address)"""
    # Try to get the real IP address from various headers (for proxies/load balancers)
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip
    
    return request.remote_addr or 'unknown'

def is_rate_limited(client_id):
    """Check if client has exceeded rate limit"""
    now = datetime.now()
    client_requests = rate_limit_store[client_id]
    
    # Remove old requests outside the time window
    cutoff_time = now - timedelta(seconds=RATE_LIMIT_WINDOW)
    while client_requests and client_requests[0] < cutoff_time:
        client_requests.popleft()
    
    # Check if client has exceeded the limit
    if len(client_requests) >= RATE_LIMIT_REQUESTS:
        return True, len(client_requests)
    
    # Add current request timestamp
    client_requests.append(now)
    return False, len(client_requests)

def get_rate_limit_reset_time(client_id):
    """Get the time when the rate limit will reset for the client"""
    client_requests = rate_limit_store[client_id]
    if not client_requests:
        return 0
    
    oldest_request = client_requests[0]
    reset_time = oldest_request + timedelta(seconds=RATE_LIMIT_WINDOW)
    now = datetime.now()
    
    if reset_time > now:
        return int((reset_time - now).total_seconds())
    return 0

# Legal Document Generation Functions
def generate_legal_letter(letter_type, user_data):
    """Generate a legal letter based on type and user data"""
    
    templates = {
        "demand_notice": {
            "title": "LEGAL DEMAND NOTICE",
            "content": """
LEGAL DEMAND NOTICE

To: {recipient_name}
{recipient_address}

Date: {date}

Subject: Legal Demand Notice - {subject}

Dear {recipient_name},

This is a LEGAL DEMAND NOTICE served upon you under the provisions of Indian law.

FACTS:
{facts}

DEMAND:
You are hereby demanded to {demand_action} within {time_period} days from the receipt of this notice, failing which legal action will be initiated against you without further notice.

LEGAL CONSEQUENCES:
Please note that non-compliance with this demand notice may result in:
1. Filing of appropriate legal proceedings against you
2. Claiming damages and compensation
3. Any other relief as deemed fit by the Court

This notice is served upon you to avoid unnecessary litigation. You are advised to comply with the above demand to avoid legal consequences.

Yours faithfully,
{sender_name}
{sender_address}
{sender_phone}
{sender_email}

---
IMPORTANT: This is a legal document. Please consult with a qualified attorney for legal advice.
Generated by Saathi Legal Assistant - For reference only.
            """
        },
        "rent_notice": {
            "title": "RENT DEMAND NOTICE TO TENANT",
            "content": """
NOTICE TO PAY RENT OR QUIT PREMISES

To: {tenant_name}
{property_address}

Date: {date}

YOU ARE HEREBY NOTIFIED that the rent for the above-mentioned premises occupied by you is due and unpaid.

RENT DETAILS:
Monthly Rent: ₹{monthly_rent}
Due Period: {due_period}
Amount Due: ₹{amount_due}
Late Fees: ₹{late_fees}
Total Amount Due: ₹{total_amount}

You are required to pay the said amount within {notice_period} days from the service of this notice, or quit and surrender the premises to the undersigned.

In case of failure to pay the rent or quit the premises within the stipulated time, legal proceedings will be instituted against you to recover the rent, damages, and possession of the premises.

Please note that this notice is served under Section 106 of the Transfer of Property Act, 1882 and relevant provisions of applicable State Rent Control Act.

Landlord/Agent: {landlord_name}
Address: {landlord_address}
Contact: {landlord_contact}

---
IMPORTANT: This is a legal document. Consult with a qualified attorney for legal advice.
Generated by Saathi Legal Assistant - For reference only.
            """
        },
        "consumer_complaint": {
            "title": "CONSUMER COMPLAINT LETTER",
            "content": """
CONSUMER COMPLAINT

To: {company_name}
{company_address}

Date: {date}

Subject: Complaint regarding {product_service} - Consumer Protection Act, 2019

Dear Sir/Madam,

I am writing to formally complain about {product_service} that I purchased/availed from your company.

PURCHASE DETAILS:
Purchase Date: {purchase_date}
Invoice/Bill Number: {invoice_number}
Amount Paid: ₹{amount_paid}
Product/Service: {product_service}

COMPLAINT:
{complaint_details}

CONSUMER RIGHTS UNDER CONSUMER PROTECTION ACT, 2019:
As per the Consumer Protection Act, 2019, I have the right to:
1. Protection against goods/services which are hazardous
2. Information about quality, quantity, potency, purity, and standard
3. Assured access to goods and services at competitive prices
4. Compensation for damages caused by defective goods/services

DEMAND:
I hereby demand:
{demand_details}

If this matter is not resolved within {resolution_period} days, I will be constrained to file a complaint with the appropriate Consumer Forum under the Consumer Protection Act, 2019.

I look forward to your immediate response and satisfactory resolution.

Yours faithfully,
{consumer_name}
{consumer_address}
{consumer_contact}

Attachments: {attachments}

---
IMPORTANT: This is a legal document template. Consult with a qualified attorney for legal advice.
Generated by Saathi Legal Assistant - For reference only.
            """
        }
    }
    
    if letter_type not in templates:
        return None
    
    template = templates[letter_type]
    
    # Format the content with user data
    try:
        content = template["content"].format(**user_data)
        return {
            "title": template["title"],
            "content": content
        }
    except KeyError as e:
        return {"error": f"Missing required field: {e}"}

def create_pdf_document(title, content, filename):
    """Create a PDF document from text content"""
    try:
        # Create a bytes buffer
        buffer = io.BytesIO()
        
        # Create the PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=1*inch,
            leftMargin=1*inch,
            topMargin=1*inch,
            bottomMargin=1*inch
        )
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            alignment=1,  # Center alignment
            textColor=colors.darkblue
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            leading=14
        )
        
        # Build the document
        story = []
        
        # Add title
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 20))
        
        # Add content (split by lines and convert to paragraphs)
        for line in content.split('\n'):
            if line.strip():
                story.append(Paragraph(line.strip(), normal_style))
            else:
                story.append(Spacer(1, 6))
        
        # Build PDF
        doc.build(story)
        
        # Get the PDF data
        pdf_data = buffer.getvalue()
        buffer.close()
        
        return pdf_data
        
    except Exception as e:
        logger.error(f"Error creating PDF: {str(e)}")
        return None

"""Pre-generated Legal Notice Templates"""
LEGAL_NOTICE_TEMPLATES = {
    "salary-not-paid": {
        "title": "LEGAL NOTICE FOR NON-PAYMENT OF SALARY",
        "description": "Formally demand pending salary payments from an employer with statutory references.",
        "tags": ["employment", "salary", "wages"],
        "content": """
LEGAL NOTICE FOR NON-PAYMENT OF SALARY

To,
[Employer Name]
[Company Name]
[Company Address]

Date: [Current Date]

Subject: Demand for Release of Pending Salary

Sir/Madam,

1. I was employed with your organization as [Designation] from [Start Date] to [Last Working Day].
2. Salary for the months of [Pending Months] amounting to ₹[Amount] remains unpaid despite repeated reminders.
3. Non-payment of salary violates Section 5 of the Payment of Wages Act, 1936 and relevant provisions of the Shops & Establishments Act.

DEMAND:
Release the entire pending salary with statutory interest within seven (7) days of receiving this notice. Failing compliance, I shall be constrained to initiate legal proceedings before the Labour Commissioner/appropriate court at your cost.

Yours faithfully,
[Employee Name]
[Employee Address]
[Employee Phone]
[Employee Email]

*This template is for informational purposes only. Consult a licensed advocate before issuing any legal notice.*
        """,
    },
    "rent-default": {
        "title": "NOTICE TO TENANT FOR RENT DEFAULT",
        "description": "Ask a tenant to clear outstanding rent or vacate the premises within a statutory window.",
        "tags": ["property", "landlord", "rent"],
        "content": """
NOTICE TO TENANT FOR RENT DEFAULT

To,
[Tenant Name]
[Property Address]

Date: [Notice Date]

Subject: Demand for Payment of Outstanding Rent & Possession

Sir/Madam,

1. You occupy the above premises as a tenant under Rent Agreement dated [Agreement Date] at a monthly rent of ₹[Monthly Rent].
2. Rent for the period [Pending Period] amounting to ₹[Outstanding Amount] is unpaid.
3. Under Section 106 of the Transfer of Property Act, 1882, you are hereby called upon to pay the entire arrears within fifteen (15) days OR vacate and hand over peaceful possession of the premises.

In case of failure, eviction proceedings and recovery of damages will be initiated without further notice.

Sincerely,
[Landlord Name]
[Landlord Address]
[Landlord Phone]

*This template is for informational purposes only. Consult a licensed advocate before issuing any legal notice.*
        """,
    },
    "consumer-complaint": {
        "title": "LEGAL NOTICE UNDER CONSUMER PROTECTION ACT, 2019",
        "description": "Alert a seller/service provider about deficiency and demand redressal before filing a consumer case.",
        "tags": ["consumer", "refund", "product"],
        "content": """
LEGAL NOTICE UNDER CONSUMER PROTECTION ACT, 2019

To,
[Company Name]
[Company Address]

Date: [Notice Date]

Subject: Deficiency in Service / Defective Goods

Dear Sir/Madam,

1. I purchased/availed [Product Service Description] on [Purchase Date] for ₹[Invoice Amount] evidenced by Invoice No. [Invoice Number].
2. The product/service is defective / deficient because [Issue Description].
3. Under Sections 2(11) & 2(47) of the Consumer Protection Act, 2019, you are liable to rectify the defect, replace the product, or refund the consideration with compensation.

DEMAND:
Kindly resolve the issue by [Desired Remedy] within fifteen (15) days failing which I shall file a complaint before the appropriate Consumer Disputes Redressal Commission seeking compensation, litigation costs, and punitive damages.

Sincerely,
[Consumer Name]
[Consumer Address]
[Consumer Contact]

*This template is for informational purposes only. Consult a licensed advocate before issuing any legal notice.*
        """,
    },
    "cheque-bounce": {
        "title": "SECTION 138 NI ACT NOTICE FOR DISHONOURED CHEQUE",
        "description": "Serve a statutory notice within 30 days of cheque return demanding payment under Section 138.",
        "tags": ["banking", "cheque", "ni-act"],
        "content": """
NOTICE UNDER SECTION 138 OF THE NEGOTIABLE INSTRUMENTS ACT, 1881

To,
[Drawer Name]
[Drawer Address]

Date: [Notice Date]

Subject: Demand notice for dishonoured cheque

Sir/Madam,

1. You issued Cheque No. [Cheque Number] dated [Cheque Date] for ₹[Cheque Amount] drawn on [Bank Name].
2. The cheque was presented within its validity but returned unpaid on [Return Date] with remark "[Return Reason]".
3. You are hereby called upon under Section 138 to make payment of ₹[Cheque Amount] within fifteen (15) days from receipt of this notice.

Failure will compel me to initiate criminal prosecution punishable with imprisonment up to two years and/or fine up to twice the cheque amount, in addition to civil recovery.

Regards,
[Payee Name]
[Payee Address]
[Payee Phone]

*This template is for informational purposes only. Consult a licensed advocate before issuing any legal notice.*
        """,
    }
}

# Template review metadata is stored separately so content writers can update
# review dates and risk tags without digging through the full template text.
REVIEW_METADATA_DEFAULT = {
    "reviewed_on": "Not reviewed yet",
    "reviewed_by": "Not reviewed yet",
    "risk_level": "Unverified",
    "sample_preview": "Sample preview is coming soon.",
    "when_to_consult": "Consult a lawyer if the dispute value exceeds ₹50,000 or if ownership is contested."
}

LEGAL_NOTICE_METADATA = build_template_category_metadata('legal_notice')


def generate_notice_pdf(notice_key: str):
    """Create a PDF for a pre-defined legal notice template."""
    template = LEGAL_NOTICE_TEMPLATES.get(notice_key)
    if not template:
        return None
    return create_pdf_document(template["title"], template["content"], f"{notice_key}.pdf")


"""Pre-generated Agreement Templates"""
AGREEMENT_TEMPLATES = {
    "rent-agreement": {
        "title": "RESIDENTIAL RENT AGREEMENT",
        "description": "Standard 11-month rent agreement with clauses for deposit, maintenance, and termination.",
        "tags": ["property", "lease", "housing"],
        "content": """
RENT AGREEMENT

This Rent Agreement is executed on [Agreement Date] between:

LANDLORD: [Landlord Name], residing at [Landlord Address]
TENANT: [Tenant Name], residing at [Tenant Address]

1. PROPERTY: Residential premises at [Property Address].
2. TERM: 11 months commencing from [Start Date] to [End Date].
3. RENT: ₹[Monthly Rent] payable on or before the 5th of each month.
4. DEPOSIT: ₹[Security Deposit] refundable at the end of tenancy subject to deductions for damages/unpaid dues.
5. USAGE: Residential use only; no subletting without written consent.
6. MAINTENANCE: Minor repairs up to ₹1000/month by tenant; structural repairs by landlord.
7. TERMINATION: Either party may terminate with 30-day written notice.

Signed:
Landlord ____________________  Date: _______
Tenant   ____________________  Date: _______

Witness 1: __________________  Witness 2: __________________

*Template is for reference only. Consult an advocate for registration/stamping requirements.*
        """,
    },
    "freelance-contract": {
        "title": "FREELANCE SERVICES AGREEMENT",
        "description": "Defines scope, deliverables, payment, and IP ownership for freelancers.",
        "tags": ["services", "freelance", "contract"],
        "content": """
FREELANCE SERVICES AGREEMENT

This Agreement is made on [Agreement Date] between:

CLIENT: [Client Name], having office at [Client Address]
FREELANCER: [Freelancer Name], residing at [Freelancer Address]

1. PROJECT SCOPE: [Deliverables Description].
2. TIMELINE: Work begins on [Start Date] and completes by [End Date].
3. FEES: Fixed fee of ₹[Project Fee] payable [Payment Terms].
4. INTELLECTUAL PROPERTY: Upon full payment, all work product and IP transfer to Client; Freelancer may showcase work in portfolio unless NDA signed.
5. CONFIDENTIALITY: Parties agree not to disclose confidential information received during engagement.
6. TERMINATION: Either party may terminate with 7-day notice; Client pays for work completed till termination.
7. GOVERNING LAW: This agreement is governed by Indian law.

Signed:
Client __________________  Date: _______
Freelancer _____________  Date: _______

*Template is informational. Customize clauses for tax, GST, or jurisdictional needs.*
        """,
    },
    "employment-offer": {
        "title": "EMPLOYMENT OFFER LETTER",
        "description": "Issue a formal offer letter with role, salary, benefits, and joining requirements.",
        "tags": ["employment", "HR", "offer"],
        "content": """
EMPLOYMENT OFFER LETTER

Date: [Letter Date]

To,
[Candidate Name]
[Candidate Address]

Subject: Offer of Employment – [Role Name]

Dear [Candidate Preferred Name],

We are pleased to offer you the position of [Position Title] with [Company Name] effective [Joining Date]. Key terms:

• CTC: ₹[Annual CTC] per annum (breakup annexed)
• Probation: [Probation Months] months
• Working Hours: [Working Hours Summary]
• Leave: [Leave Summary]
• Benefits: [Benefits Summary]

Please report with originals of KYC, education, experience certificates. This offer is subject to background verification and acceptance of company policies.

Kindly sign and return a copy of this letter as acceptance.

For [Company Name]

________________________
[Authorized Signatory]

I accept the offer under the stated terms.

Signature: __________________ Date: ______

*Template for reference. Adapt to state-specific Shops & Establishments requirements.*
        """,
    },
    "nda": {
        "title": "MUTUAL NON-DISCLOSURE AGREEMENT (NDA)",
        "description": "Mutual confidentiality agreement for sharing sensitive business information.",
        "tags": ["confidentiality", "NDA", "business"],
        "content": """
MUTUAL NON-DISCLOSURE AGREEMENT

This NDA is made on [Agreement Date] between:

Party A: [Company A Name]
Party B: [Company B Name]

1. CONFIDENTIAL INFORMATION: Includes all non-public business, technical, or financial information disclosed orally or in writing.
2. PURPOSE: Parties intend to explore [Purpose Statement].
3. OBLIGATIONS: Recipients shall protect information with reasonable care, use solely for Purpose, and not disclose to third parties.
4. EXCLUSIONS: Information already known, publicly available, or independently developed is excluded.
5. TERM: Confidentiality obligations survive for three (3) years from date of disclosure.
6. GOVERNING LAW: Indian law; courts at [Jurisdiction City].

IN WITNESS WHEREOF, parties execute this NDA on the date first written.

Party A __________________   Party B __________________
Name: ____________________   Name: ____________________
Title: _____________________  Title: _____________________

*Template is informational. Consider stamping/registration per state laws.*
        """,
    },
    "sale-of-goods": {
        "title": "SALE OF GOODS AGREEMENT",
        "description": "Documents sale of goods between buyer and seller with warranties and delivery terms.",
        "tags": ["commerce", "goods", "sales"],
        "content": """
SALE OF GOODS AGREEMENT

This Agreement is dated [Agreement Date] between:

SELLER: [Seller Name], having office at [Seller Address]
BUYER: [Buyer Name], having office at [Buyer Address]

1. GOODS: Seller agrees to sell and Buyer agrees to purchase [Goods Description].
2. PRICE: Total consideration ₹[Total Amount], payable [Payment Terms].
3. DELIVERY: Goods shall be delivered on/before [Delivery Date] at [Delivery Location]. Risk passes upon delivery; title transfers upon full payment.
4. WARRANTY: Goods shall conform to specifications and be free from defects for [Warranty Period].
5. INDEMNITY: Buyer indemnifies Seller against misuse; Seller indemnifies Buyer against IP infringement.
6. GOVERNING LAW: Indian Contract Act, 1872; disputes at [Jurisdiction City].

Signed:
Seller __________________  Date: _______
Buyer  __________________  Date: _______

*Template for reference. Include GST/E-way bill clauses as needed.*
        """,
    }
}

AGREEMENT_TEMPLATE_METADATA = build_template_category_metadata('agreement')
CALCULATOR_METADATA = build_category_metadata('calculator')


def get_template_metadata(source: Dict[str, Dict[str, str]], slug: str) -> Dict[str, str]:
    """Merge defaults with per-template metadata so UI always has complete info."""
    merged = REVIEW_METADATA_DEFAULT.copy()
    merged.update(source.get(slug, {}))
    return merged


def generate_agreement_pdf(agreement_key: str):
    template = AGREEMENT_TEMPLATES.get(agreement_key)
    if not template:
        return None
    return create_pdf_document(template["title"], template["content"], f"{agreement_key}.pdf")


def _format_date(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value)
        return parsed.strftime('%d %B %Y')
    except ValueError:
        try:
            parsed = datetime.strptime(value, '%d-%m-%Y')
            return parsed.strftime('%d %B %Y')
        except ValueError:
            return value


def _format_number(value: float) -> str:
    if value.is_integer():
        return f"{int(value):,}"
    return f"{value:,.2f}"


def _normalize_field_value(field_def: Dict[str, Any], raw_value: Any) -> tuple[str | None, str | None]:
    validation = field_def.get('validation', {}) or {}
    field_type = (field_def.get('type') or 'text').lower()
    value = '' if raw_value is None else str(raw_value).strip()

    if not value:
        if validation.get('required'):
            return None, f"{field_def.get('label', 'This field')} is required"
        return '', None

    if validation.get('minLength') and len(value) < validation['minLength']:
        return None, f"{field_def.get('label', 'This field')} must be at least {validation['minLength']} characters"
    if validation.get('maxLength') and len(value) > validation['maxLength']:
        return None, f"{field_def.get('label', 'This field')} must be under {validation['maxLength']} characters"

    pattern = validation.get('pattern')
    if pattern:
        try:
            if not re.match(pattern, value):
                return None, validation.get('message') or f"{field_def.get('label', 'This field')} format looks invalid"
        except re.error:
            logger.warning('Invalid regex pattern configured for %s', field_def.get('id'))

    if field_type == 'date':
        return _format_date(value), None

    if field_type == 'number':
        sanitized = value.replace(',', '')
        try:
            number_value = float(sanitized)
        except ValueError:
            return None, f"Enter a numeric value for {field_def.get('label', 'this field')}"
        if validation.get('min') is not None and number_value < validation['min']:
            return None, f"{field_def.get('label', 'This field')} must be at least {validation['min']}"
        if validation.get('max') is not None and number_value > validation['max']:
            return None, f"{field_def.get('label', 'This field')} must be below {validation['max']}"
        return _format_number(number_value), None

    return value, None


def validate_template_fields(slug: str, raw_fields: Dict[str, Any]) -> tuple[Dict[str, str], list[str]]:
    entry = get_template_entry(slug)
    if not entry:
        return {}, ["Template not found"]
    cleaned: Dict[str, str] = {}
    errors: list[str] = []
    for field_def in entry.get('fields', []):
        field_id = field_def.get('id')
        if not field_id:
            continue
        value, error = _normalize_field_value(field_def, raw_fields.get(field_id))
        if error:
            errors.append(error)
            continue
        cleaned[field_id] = value or ''
    return cleaned, errors


def _get_template_document(slug: str) -> tuple[str | None, str | None]:
    if slug in LEGAL_NOTICE_TEMPLATES:
        data = LEGAL_NOTICE_TEMPLATES[slug]
        return data["content"], data["title"]
    if slug in AGREEMENT_TEMPLATES:
        data = AGREEMENT_TEMPLATES[slug]
        return data["content"], data["title"]
    return None, None


def render_template_body(slug: str, cleaned_fields: Dict[str, str]) -> str:
    content, _ = _get_template_document(slug)
    if not content:
        return ''
    entry = get_template_entry(slug)
    rendered = content
    for field_def in entry.get('fields', []):
        token = field_def.get('token')
        if not token:
            continue
        rendered = rendered.replace(token, cleaned_fields.get(field_def['id'], ''))
    return rendered.strip()


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int | None = None) -> int | None:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _calculator_error(message: str, status_code: int = 400):
    return jsonify({"status": "error", "message": message}), status_code


def log_consent_event(event: Dict[str, Any]) -> None:
    """Persist consent approvals for compliance tracking (DB first, file fallback)."""
    if db is not None:
        try:
            db['consent_logs'].insert_one(event)
            return
        except Exception as exc:
            logger.warning("Mongo consent logging failed, using file fallback: %s", exc)

    try:
        with CONSENT_LOG_LOCK:
            with open(CONSENT_LOG_PATH, 'a', encoding='utf-8') as log_file:
                log_file.write(json.dumps(event) + '\n')
    except Exception as exc:
        logger.error("Failed to persist consent event: %s", exc)
        raise


def calculate_notice_period(company_type: str, years_of_service: float) -> Dict[str, Any]:
    company_rules = {
        "it_services": {"base": 30, "per_year": 5, "cap": 90},
        "manufacturing": {"base": 15, "per_year": 4, "cap": 60},
        "startup": {"base": 14, "per_year": 3, "cap": 45},
        "government": {"base": 30, "per_year": 7, "cap": 120},
    }
    rules = company_rules.get(company_type, company_rules["it_services"])
    recommended = rules["base"] + max(0, years_of_service) * rules["per_year"]
    recommended = min(rules["cap"], round(recommended / 5) * 5)
    rationale = (
        "Recommendation derived from Shops & Establishments norms for "
        f"{company_type.replace('_', ' ').title()} and years of service." )
    return {
        "notice_days": int(max(rules["base"], recommended)),
        "statutory_min": rules["base"],
        "statutory_cap": rules["cap"],
        "rationale": rationale
    }


def calculate_work_hours(total_week_hours: float, hourly_rate: float) -> Dict[str, Any]:
    legal_limit = 48
    overtime_hours = max(0.0, total_week_hours - legal_limit)
    compliance = total_week_hours <= legal_limit
    overtime_pay = overtime_hours * hourly_rate * 2  # double rate per Factories Act guidance
    return {
        "total_week_hours": round(total_week_hours, 2),
        "legal_limit_hours": legal_limit,
        "overtime_hours": round(overtime_hours, 2),
        "overtime_pay": round(overtime_pay, 2),
        "compliant": compliance,
        "message": "Within prescribed limit" if compliance else "Overtime pay required"
    }


def calculate_maternity_benefit(days_worked: int, avg_daily_wage: float, children_count: int) -> Dict[str, Any]:
    eligible = days_worked >= 80
    if children_count <= 2:
        weeks = 26
    else:
        weeks = 12
    payable_days = weeks * 7
    total_benefit = avg_daily_wage * payable_days if eligible else 0
    return {
        "eligible": eligible,
        "required_days": 80,
        "payable_weeks": weeks,
        "payable_days": payable_days,
        "estimated_benefit": round(total_benefit, 2),
        "note": "Eligibility based on Maternity Benefit (Amendment) Act, 2017"
    }


def calculate_consumer_compensation(purchase_amount: float, issue_type: str, delay_days: int, out_of_pocket: float) -> Dict[str, Any]:
    issue_multiplier = {
        "defective_product": 0.1,
        "service_deficiency": 0.15,
        "refund_delay": 0.12,
    }
    multiplier = issue_multiplier.get(issue_type, 0.1)
    penalty = purchase_amount * multiplier
    delay_comp = max(0, delay_days) * 100
    total = purchase_amount + out_of_pocket + penalty + delay_comp
    return {
        "refundable_amount": round(purchase_amount, 2),
        "compensation_component": round(penalty, 2),
        "delay_compensation": round(delay_comp, 2),
        "out_of_pocket": round(out_of_pocket, 2),
        "recommended_total": round(total, 2),
        "note": "Indicative computation referencing Consumer Protection Act, 2019"
    }


@app.route('/api/calculators/notice-period', methods=['POST'])
def api_notice_period():
    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    company_raw = payload.get('companyType', 'it_services')
    company_type = str(company_raw or 'it_services').lower()
    years = _safe_float(payload.get('yearsOfService'), None)

    if years is None or years < 0:
        return _calculator_error("Please provide yearsOfService as a non-negative number.")

    allowed_company_types = {"it_services", "manufacturing", "startup", "government"}
    if company_type not in allowed_company_types:
        company_type = 'it_services'

    result = calculate_notice_period(company_type, years)
    return jsonify({
        "status": "success",
        "input": {
            "companyType": company_type,
            "yearsOfService": years
        },
        "result": result
    })


@app.route('/api/calculators/work-hours', methods=['POST'])
def api_work_hours():
    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    total_hours = _safe_float(payload.get('totalWeeklyHours'), None)
    hourly_rate = _safe_float(payload.get('hourlyRate'), None)

    if total_hours is None or total_hours < 0:
        return _calculator_error("Provide totalWeeklyHours as a non-negative number.")
    if hourly_rate is None or hourly_rate < 0:
        return _calculator_error("Provide hourlyRate as a non-negative number.")

    result = calculate_work_hours(total_hours, hourly_rate)
    return jsonify({
        "status": "success",
        "input": {
            "totalWeeklyHours": total_hours,
            "hourlyRate": hourly_rate
        },
        "result": result
    })


@app.route('/api/calculators/maternity-benefit', methods=['POST'])
def api_maternity_benefit():
    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    days_worked = _safe_int(payload.get('daysWorked'), None)
    avg_daily_wage = _safe_float(payload.get('averageDailyWage'), None)
    children_count = _safe_int(payload.get('childrenCount'), 1) or 1

    if days_worked is None or days_worked < 0:
        return _calculator_error("daysWorked must be 0 or more")
    if avg_daily_wage is None or avg_daily_wage <= 0:
        return _calculator_error("averageDailyWage must be greater than 0")
    if children_count < 1:
        children_count = 1

    result = calculate_maternity_benefit(days_worked, avg_daily_wage, children_count)
    return jsonify({
        "status": "success",
        "input": {
            "daysWorked": days_worked,
            "averageDailyWage": avg_daily_wage,
            "childrenCount": children_count
        },
        "result": result
    })


@app.route('/api/calculators/consumer-compensation', methods=['POST'])
def api_consumer_compensation():
    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    purchase_amount = _safe_float(payload.get('purchaseAmount'), None)
    issue_raw = payload.get('issueType', 'defective_product')
    issue_type = str(issue_raw or 'defective_product').lower()
    delay_days = _safe_int(payload.get('delayDays'), 0) or 0
    out_of_pocket = _safe_float(payload.get('outOfPocket'), 0.0) or 0.0

    if purchase_amount is None or purchase_amount <= 0:
        return _calculator_error("purchaseAmount must be greater than 0")
    if out_of_pocket < 0:
        return _calculator_error("outOfPocket cannot be negative")
    if delay_days < 0:
        delay_days = 0

    allowed_issue_types = {"defective_product", "service_deficiency", "refund_delay"}
    if issue_type not in allowed_issue_types:
        issue_type = 'defective_product'

    result = calculate_consumer_compensation(purchase_amount, issue_type, delay_days, out_of_pocket)
    return jsonify({
        "status": "success",
        "input": {
            "purchaseAmount": purchase_amount,
            "issueType": issue_type,
            "delayDays": delay_days,
            "outOfPocket": out_of_pocket
        },
        "result": result
    })


@app.route('/api/consent', methods=['POST'])
def record_consent():
    """Capture explicit consent decisions and persist them reliably."""
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400

    anon_id = str(payload.get('anon_id') or '').strip() or uuid.uuid4().hex
    user_id_raw = payload.get('user_id')
    user_id = None
    if user_id_raw is not None:
        user_id = str(user_id_raw).strip() or None

    scope_payload = payload.get('scope') or {}
    if not isinstance(scope_payload, dict):
        return jsonify({"status": "error", "message": "scope must be an object"}), 400

    normalized_scope = {}
    for key, value in scope_payload.items():
        normalized_scope[str(key)] = bool(value)

    normalized_scope.setdefault('store_messages', False)
    normalized_scope.setdefault('store_documents', False)

    event = {
        "anon_id": anon_id,
        "user_id": user_id,
        "scope": normalized_scope,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ip": request.remote_addr,
        "user_agent": request.headers.get('User-Agent', ''),
    }

    try:
        log_consent_event(event)
    except Exception:
        return jsonify({
            "status": "error",
            "message": "Unable to record consent at this time"
        }), 500

    return jsonify({"status": "ok"}), 201


@app.route('/api/agreements', methods=['GET'])
def list_agreements():
    agreements = []
    for key, data in AGREEMENT_TEMPLATES.items():
        meta = get_template_metadata(AGREEMENT_TEMPLATE_METADATA, key)
        agreements.append({
            "slug": key,
            "title": data["title"],
            "description": data["description"],
            "tags": data["tags"],
            "reviewed_on": meta["reviewed_on"],
            "reviewed_by": meta["reviewed_by"],
            "risk_level": meta["risk_level"],
            "sample_preview": meta["sample_preview"],
            "when_to_consult": meta.get("when_to_consult", REVIEW_METADATA_DEFAULT["when_to_consult"]),
            "when_to_consult_list": meta.get("when_to_consult_list", []),
            "sample_path": meta.get("sample_path"),
            "prefill_fields": meta.get("prefill_fields", {}),
        })
    return jsonify({
        "status": "success",
        "count": len(agreements),
        "agreements": agreements
    })


@app.route('/agreements/<agreement_key>', methods=['GET'])
def download_agreement_template(agreement_key: str):
    pdf_data = generate_agreement_pdf(agreement_key)
    if not pdf_data:
        return jsonify({
            "status": "error",
            "error": "AGREEMENT_NOT_FOUND",
            "message": "Agreement template not available"
        }), 404

    filename = f"{agreement_key}_{datetime.now().strftime('%Y%m%d')}.pdf"
    response = make_response(pdf_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@app.route('/api/legal-notices', methods=['GET'])
def list_legal_notices():
    """Return metadata for the available legal notice templates."""
    notices = []
    for key, data in LEGAL_NOTICE_TEMPLATES.items():
        meta = get_template_metadata(LEGAL_NOTICE_METADATA, key)
        notices.append({
            "slug": key,
            "title": data["title"],
            "description": data["description"],
            "tags": data["tags"],
            "reviewed_on": meta["reviewed_on"],
            "reviewed_by": meta["reviewed_by"],
            "risk_level": meta["risk_level"],
            "sample_preview": meta["sample_preview"],
            "when_to_consult": meta.get("when_to_consult", REVIEW_METADATA_DEFAULT["when_to_consult"]),
            "when_to_consult_list": meta.get("when_to_consult_list", []),
            "sample_path": meta.get("sample_path"),
            "prefill_fields": meta.get("prefill_fields", {}),
        })
    return jsonify({
        "status": "success",
        "count": len(notices),
        "notices": notices
    })


def _metadata_source_for_slug(slug: str) -> Dict[str, Dict[str, Any]]:
    if slug in LEGAL_NOTICE_METADATA:
        return LEGAL_NOTICE_METADATA
    if slug in AGREEMENT_TEMPLATE_METADATA:
        return AGREEMENT_TEMPLATE_METADATA
    return {}


@app.route('/api/templates/<slug>', methods=['GET'])
def api_template_detail(slug: str):
    entry = get_template_entry(slug)
    if not entry:
        return jsonify({"status": "error", "message": "Template not found"}), 404
    meta_source = _metadata_source_for_slug(slug)
    meta = get_template_metadata(meta_source, slug) if meta_source else REVIEW_METADATA_DEFAULT.copy()
    return jsonify({
        "status": "success",
        "template": {
            "slug": slug,
            "category": entry.get('category'),
            "document_type": entry.get('document_type'),
            "display_name": entry.get('display_name'),
            "pdf_title": entry.get('pdf_title'),
            "risk_level": meta.get('risk_level'),
            "reviewed_on": meta.get('reviewed_on'),
            "reviewed_by": meta.get('reviewed_by'),
            "when_to_consult": meta.get('when_to_consult'),
            "when_to_consult_list": meta.get('when_to_consult_list', []),
            "fields": entry.get('fields', []),
            "prefill_fields": entry.get('prefill_fields', {}),
            "sample_path": entry.get('sample_path')
        }
    })


@app.route('/api/templates/render', methods=['POST'])
def api_render_template():
    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    slug = str(payload.get('slug') or '').strip()
    entry = get_template_entry(slug)
    if not slug or not entry:
        return jsonify({"status": "error", "message": "Template not found"}), 404
    raw_fields = payload.get('fields') or {}
    cleaned, errors = validate_template_fields(slug, raw_fields)
    if errors:
        return jsonify({"status": "error", "errors": errors}), 400
    rendered_text = render_template_body(slug, cleaned)
    if not rendered_text:
        return jsonify({"status": "error", "message": "Unable to render template"}), 500
    title = entry.get('pdf_title') or _get_template_document(slug)[1] or entry.get('display_name') or slug
    return jsonify({
        "status": "success",
        "title": title,
        "rendered_text": rendered_text,
        "fields": cleaned
    })


@app.route('/api/templates/pdf', methods=['POST'])
def api_template_pdf():
    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    slug = str(payload.get('slug') or '').strip()
    entry = get_template_entry(slug)
    if not slug or not entry:
        return jsonify({"status": "error", "message": "Template not found"}), 404
    cleaned, errors = validate_template_fields(slug, payload.get('fields') or {})
    if errors:
        return jsonify({"status": "error", "errors": errors}), 400
    edited_text = str(payload.get('edited_text') or '').strip()
    rendered_text = str(payload.get('rendered_text') or '').strip()
    final_text = edited_text or rendered_text or render_template_body(slug, cleaned)
    if not final_text:
        return jsonify({"status": "error", "message": "Nothing to convert into PDF"}), 400
    title = payload.get('title') or entry.get('pdf_title') or _get_template_document(slug)[1] or entry.get('display_name') or slug
    pdf_data = create_pdf_document(title, final_text, f"{slug}.pdf")
    if not pdf_data:
        return jsonify({"status": "error", "message": "Failed to generate PDF"}), 500
    filename = f"{slug}_{datetime.now().strftime('%Y%m%d')}.pdf"
    response = make_response(pdf_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@app.route('/notices/<notice_key>', methods=['GET'])
def download_legal_notice(notice_key: str):
    """Stream the requested legal notice as a PDF download."""
    pdf_data = generate_notice_pdf(notice_key)
    if not pdf_data:
        return jsonify({
            "status": "error",
            "error": "NOTICE_NOT_FOUND",
            "message": "Notice template not available"
        }), 404

    filename = f"{notice_key}_{datetime.now().strftime('%Y%m%d')}.pdf"
    response = make_response(pdf_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@app.route('/api/tools', methods=['GET'])
def api_tools_catalog():
    """Expose all tools with metadata for the discovery dashboard."""
    ordered_tools = sorted(TOOL_MANIFEST.get('tools', []), key=lambda entry: entry.get('order', 999))
    tools: list[Dict[str, Any]] = []
    for entry in ordered_tools:
        enriched = dict(entry)
        slug = enriched.get('slug')
        category = enriched.get('category')
        if category in {'legal_notice', 'agreement'} and slug in TEMPLATE_INDEX:
            template_meta = TEMPLATE_INDEX[slug]
            bullets = template_meta.get('when_to_consult_lawyer') or []
            enriched['reviewed_on'] = template_meta.get('last_reviewed_date', enriched.get('reviewed_on'))
            enriched['reviewed_by'] = template_meta.get('reviewed_by', enriched.get('reviewed_by'))
            enriched['risk_level'] = template_meta.get('risk_level', enriched.get('risk_level'))
            enriched['when_to_consult'] = bullets[0] if bullets else enriched.get('when_to_consult')
            enriched['when_to_consult_list'] = bullets
            enriched['sample_path'] = template_meta.get('sample_path')
        tools.append(enriched)
    return jsonify({
        "status": "success",
        "count": len(tools),
        "tools": tools
    })

def call_gemini_api(messages, user_language='english'):
    """Call Google Gemini API with language support"""
    try:
        # Language prompts for multilingual support
        language_prompts = {
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
        
        # Get language instruction
        language_instruction = language_prompts.get(user_language, language_prompts['english'])
        
        # Prepare the request for Gemini API
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
        headers = {
            "Content-Type": "application/json"
        }
        
        # Convert messages to Gemini format
        prompt_parts = []
        
        # Add system prompt with language instruction
        enhanced_system_prompt = f"{SYSTEM_PROMPT}\n\nIMPORTANT LANGUAGE INSTRUCTION: {language_instruction}\n\nConversation:\n"
        prompt_parts.append({
            "text": enhanced_system_prompt
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

@app.route('/health')
def health_check():
    """Enhanced health check endpoint with production metrics"""
    try:
        current_time = time.time()
        uptime_seconds = current_time - uptime_start
        uptime_hours = uptime_seconds / 3600
        
        return jsonify({
            "status": "healthy",
            "app": "Saathi Legal Assistant - Gemini Powered",
            "version": "2.1.0-production",
            "api_configured": is_api_configured(),
            "model": GEMINI_MODEL,
            "provider": "Google Gemini",
            "timestamp": datetime.now().isoformat(),
            "uptime": {
                "seconds": round(uptime_seconds),
                "hours": round(uptime_hours, 2),
                "start_time": datetime.fromtimestamp(uptime_start).isoformat()
            },
            "metrics": {
                "total_errors": error_counts['total'],
                "error_404": error_counts['404'],
                "error_500": error_counts['500'],
                "error_429": error_counts['429']
            },
            "features": {
                "rate_limiting": SECURITY_AVAILABLE,
                "database_logging": MONGODB_AVAILABLE,
                "security_headers": SECURITY_AVAILABLE,
                "production_mode": os.environ.get('RAILWAY_ENVIRONMENT_NAME') == 'production'
            }
        })
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "Health check failed"
        }), 500

@app.route('/generate-letter', methods=['POST'])
def generate_letter():
    """Generate a legal letter based on user inputs"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided", "status": "error"}), 400
        
        letter_type = data.get('letter_type', '').strip()
        user_data = data.get('user_data', {})
        output_format = data.get('format', 'text')  # 'text' or 'pdf'
        
        if not letter_type:
            return jsonify({"error": "Letter type is required", "status": "error"}), 400
            
        if not user_data:
            return jsonify({"error": "User data is required", "status": "error"}), 400
        
        # Add current date if not provided
        if 'date' not in user_data:
            user_data['date'] = datetime.now().strftime("%B %d, %Y")
        
        # Generate the letter
        result = generate_legal_letter(letter_type, user_data)
        
        if not result:
            return jsonify({
                "error": "Invalid letter type or generation failed",
                "status": "error",
                "available_types": ["demand_notice", "rent_notice", "consumer_complaint"]
            }), 400
            
        if "error" in result:
            return jsonify({
                "error": result["error"],
                "status": "error"
            }), 400
        
        if output_format == 'pdf':
            # Generate PDF
            pdf_data = create_pdf_document(result['title'], result['content'], f"{letter_type}.pdf")
            
            if pdf_data:
                # Create response with PDF
                response = make_response(pdf_data)
                response.headers['Content-Type'] = 'application/pdf'
                response.headers['Content-Disposition'] = f'attachment; filename="{letter_type}_{datetime.now().strftime("%Y%m%d")}.pdf"'
                return response
            else:
                return jsonify({
                    "error": "Failed to generate PDF",
                    "status": "error"
                }), 500
        else:
            # Return text format
            return jsonify({
                "title": result['title'],
                "content": result['content'],
                "letter_type": letter_type,
                "generated_date": user_data['date'],
                "status": "success"
            })
            
    except Exception as e:
        logger.error(f"Error generating letter: {str(e)}")
        return jsonify({
            "error": "Failed to generate letter",
            "status": "error"
        }), 500

@app.route('/legal-forms', methods=['GET'])
def get_legal_forms():
    """Get available legal forms list"""
    forms = {
        "rent_agreement": {
            "name": "Rental Agreement",
            "description": "Standard rental/lease agreement for residential property",
            "category": "Property Law",
            "fields": ["landlord_name", "tenant_name", "property_address", "monthly_rent", "security_deposit", "lease_duration"]
        },
        "employment_contract": {
            "name": "Employment Contract",
            "description": "Basic employment agreement template",
            "category": "Employment Law",
            "fields": ["company_name", "employee_name", "position", "salary", "joining_date", "terms"]
        },
        "power_of_attorney": {
            "name": "Power of Attorney",
            "description": "General power of attorney document",
            "category": "General Legal",
            "fields": ["principal_name", "agent_name", "powers_granted", "effective_date", "witness_details"]
        },
        "sale_deed": {
            "name": "Sale Deed",
            "description": "Property sale deed template",
            "category": "Property Law",
            "fields": ["seller_name", "buyer_name", "property_details", "sale_amount", "registration_details"]
        }
    }
    
    return jsonify({
        "forms": forms,
        "status": "success",
        "total_forms": len(forms)
    })

@app.route('/generate-form/<form_type>', methods=['POST'])
def generate_form(form_type):
    """Generate a specific legal form"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided", "status": "error"}), 400
        
        user_data = data.get('form_data', {})
        output_format = data.get('format', 'pdf')  # Default to PDF for forms
        
        # Form templates (simplified versions)
        form_templates = {
            "rent_agreement": {
                "title": "RENTAL AGREEMENT",
                "content": """
RENTAL AGREEMENT

This Rental Agreement is entered into on {date} between:

LANDLORD: {landlord_name}
Address: {landlord_address}
Contact: {landlord_contact}

TENANT: {tenant_name}
Address: {tenant_address}
Contact: {tenant_contact}

PROPERTY DETAILS:
The landlord agrees to rent the following property:
Address: {property_address}
Type: {property_type}

TERMS AND CONDITIONS:

1. RENT: The monthly rent is ₹{monthly_rent} payable on or before {rent_due_date} of each month.

2. SECURITY DEPOSIT: The tenant has paid ₹{security_deposit} as security deposit.

3. DURATION: This agreement is for a period of {lease_duration} starting from {lease_start_date}.

4. UTILITIES: {utility_terms}

5. MAINTENANCE: {maintenance_terms}

6. TERMINATION: Either party may terminate this agreement by giving {notice_period} days written notice.

IN WITNESS WHEREOF, both parties have executed this agreement on the date first written above.

LANDLORD                    TENANT
{landlord_name}            {tenant_name}

Signature: ___________      Signature: ___________
Date: {date}               Date: {date}

WITNESSES:
1. Name: ___________  Signature: ___________
2. Name: ___________  Signature: ___________

---
IMPORTANT: This is a template document. Please consult with a qualified attorney before use.
Generated by Saathi Legal Assistant - For reference only.
                """
            }
        }
        
        if form_type not in form_templates:
            return jsonify({
                "error": f"Form type '{form_type}' not available",
                "status": "error",
                "available_forms": list(form_templates.keys())
            }), 400
        
        # Add current date if not provided
        if 'date' not in user_data:
            user_data['date'] = datetime.now().strftime("%B %d, %Y")
        
        template = form_templates[form_type]
        
        try:
            content = template["content"].format(**user_data)
        except KeyError as e:
            return jsonify({
                "error": f"Missing required field: {e}",
                "status": "error"
            }), 400
        
        if output_format == 'pdf':
            # Generate PDF
            pdf_data = create_pdf_document(template['title'], content, f"{form_type}.pdf")
            
            if pdf_data:
                response = make_response(pdf_data)
                response.headers['Content-Type'] = 'application/pdf'
                response.headers['Content-Disposition'] = f'attachment; filename="{form_type}_{datetime.now().strftime("%Y%m%d")}.pdf"'
                return response
            else:
                return jsonify({
                    "error": "Failed to generate PDF",
                    "status": "error"
                }), 500
        else:
            return jsonify({
                "title": template['title'],
                "content": content,
                "form_type": form_type,
                "generated_date": user_data['date'],
                "status": "success"
            })
            
    except Exception as e:
        logger.error(f"Error generating form: {str(e)}")
        return jsonify({
            "error": "Failed to generate form",
            "status": "error"
        }), 500


# MongoDB Helper Functions
def log_to_mongodb(collection_name, data):
    """Log data to MongoDB collection"""
    if db is not None:
        try:
            collection = db[collection_name]
            result = collection.insert_one(data)
            return result.inserted_id
        except Exception as e:
            logger.error(f"MongoDB logging error: {e}")
            return None
    return None

def get_user_conversations(user_name, limit=50):
    """Get user's conversation history from MongoDB"""
    if db is not None:
        try:
            collection = db['conversations']
            conversations = collection.find(
                {'user_name': user_name}
            ).sort('timestamp', -1).limit(limit)
            return list(conversations)
        except Exception as e:
            logger.error(f"MongoDB query error: {e}")
            return []
    return []

# Landing Page Route
@app.route('/')
def landing_page():
    """Serve the landing page with phone input and old money theme"""
    try:
        with open('landing.html', 'r', encoding='utf-8') as f:
            content = f.read()
            logger.info("✅ Successfully serving landing.html with new old money theme")
            return content
    except FileNotFoundError:
        logger.error("❌ landing.html file not found!")
        return """
        <html>
        <body style="text-align: center; padding: 50px; font-family: Arial; background: #1a2332; color: #f4f1e8;">
            <h1>🏛️ Saathi Legal Assistant</h1>
            <p>Landing page not found. Please ensure landing.html exists.</p>
            <a href="/chat.html">Go to Chat</a>
            <p><small>App Version: NEW_THEME_DEPLOYED</small></p>
        </body>
        </html>
        """, 404

@app.route('/templates.html')
def templates_page():
    """Serve the document templates page"""
    try:
        with open('templates.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return """
        <html>
        <body style="text-align: center; padding: 50px; font-family: Arial; background: #1a2332; color: #f4f1e8;">
            <h1>📄 Templates Not Available</h1>
            <p>Document templates page not found.</p>
            <a href="/" style="color: #8b4513;">Back to Home</a>
        </body>
        </html>
        """, 404

@app.route('/api/templates', methods=['GET'])
def get_templates():
    """Get available document templates"""
    try:
        # Temporary fallback - document generator not available
        templates = {
            "rent_agreement": {
                "name": "Rent Agreement",
                "description": "Standard residential rent agreement template",
                "fields": ["tenant_name", "landlord_name", "property_address", "monthly_rent"]
            },
            "employment_contract": {
                "name": "Employment Contract", 
                "description": "Basic employment contract template",
                "fields": ["employee_name", "employer_name", "position", "salary"]
            },
            "legal_notice": {
                "name": "Legal Notice",
                "description": "Formal legal notice template",
                "fields": ["recipient_name", "issue_description", "deadline"]
            }
        }
        return jsonify(templates)
    except Exception as e:
        logger.error(f"Error getting templates: {str(e)}")
        return jsonify({"error": "Failed to load templates"}), 500

@app.route('/api/template-questions/<template_id>', methods=['GET'])
def get_template_questions(template_id):
    """Get questions for a specific template"""
    try:
        # Temporary fallback - document generator not available
        template_questions = {
            "rent_agreement": [
                {"field": "tenant_name", "question": "What is the tenant's full name?", "type": "text"},
                {"field": "landlord_name", "question": "What is the landlord's full name?", "type": "text"},
                {"field": "property_address", "question": "What is the complete property address?", "type": "text"},
                {"field": "monthly_rent", "question": "What is the monthly rent amount?", "type": "number"}
            ],
            "employment_contract": [
                {"field": "employee_name", "question": "What is the employee's full name?", "type": "text"},
                {"field": "employer_name", "question": "What is the employer's company name?", "type": "text"},
                {"field": "position", "question": "What is the job position/title?", "type": "text"},
                {"field": "salary", "question": "What is the annual salary?", "type": "number"}
            ],
            "legal_notice": [
                {"field": "recipient_name", "question": "Who is the recipient of this notice?", "type": "text"},
                {"field": "issue_description", "question": "Describe the legal issue:", "type": "textarea"},
                {"field": "deadline", "question": "What is the response deadline?", "type": "date"}
            ]
        }
        
        questions = template_questions.get(template_id)
        if questions:
            return jsonify(questions)
        else:
            return jsonify({"error": "Template not found"}), 404
    except Exception as e:
        logger.error(f"Error getting template questions: {str(e)}")
        return jsonify({"error": "Failed to load template questions"}), 500

@app.route('/api/generate-document', methods=['POST'])
def generate_document_api():
    """Generate document from template and user data"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        template_id = data.get('template_id')
        user_data = data.get('data', {})
        
        if not template_id:
            return jsonify({"error": "Template ID required"}), 400
        
        # Temporary fallback - document generator not available
        document = {
            "content": f"Document template '{template_id}' with user data: {user_data}",
            "filename": f"{template_id}_document.txt",
            "type": "text/plain"
        }
        
        if document:
            # Log document generation
            log_data = {
                'template_id': template_id,
                'user_data': user_data,
                'timestamp': datetime.now().isoformat(),
                'ip_address': get_client_identifier(request)
            }
            log_to_mongodb('document_generations', log_data)
            
            return jsonify({
                "success": True,
                "document": document,
                "template_id": template_id
            })
        else:
            return jsonify({"error": "Failed to generate document"}), 500
            
    except Exception as e:
        logger.error(f"Error generating document: {str(e)}")
        return jsonify({"error": "Failed to generate document"}), 500

@app.route('/chat.html')
def chat_page():
    """Serve the chat page"""
    try:
        with open('chat.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return """
        <html>
        <body style="text-align: center; padding: 50px; font-family: Arial;">
            <h1>🏛️ Chat Not Available</h1>
            <p>Chat page not found. Please ensure chat.html exists.</p>
            <a href="/">Back to Home</a>
        </body>
        </html>
        """, 404

@app.route('/api/start-session', methods=['POST'])
def start_session():
    """Start a new consultation session"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided", "status": "error"}), 400
        
        user_name = data.get('user_name', 'Anonymous')
        user_phone = data.get('user_phone', '')
        session_id = data.get('session_id')
        timestamp = data.get('timestamp', datetime.now().isoformat())
        
        session_data = {
            'user_name': user_name,
            'user_phone': user_phone,
            'session_id': session_id,
            'start_time': timestamp,
            'status': 'active',
            'user_agent': request.headers.get('User-Agent', ''),
            'ip_address': get_client_identifier(request)
        }
        
        # Log session start to MongoDB
        session_id_db = log_to_mongodb('sessions', session_data)
        
        logger.info(f"Session started for user: {user_name} ({user_phone}), ID: {session_id}")
        
        return jsonify({
            "status": "success",
            "message": f"Session started for {user_name}",
            "session_id": session_id,
            "db_id": str(session_id_db) if session_id_db else None
        })
        
    except Exception as e:
        logger.error(f"Error starting session: {str(e)}")
        return jsonify({
            "error": "Failed to start session",
            "status": "error"
        }), 500

@app.route('/api/log-conversation', methods=['POST'])
def log_conversation():
    """Log conversation messages to MongoDB"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided", "status": "error"}), 400
        
        conversation_data = {
            'user_name': data.get('user_name', 'Anonymous'),
            'session_id': data.get('session_id'),
            'message': data.get('message', ''),
            'sender': data.get('sender', 'unknown'),  # 'user' or 'assistant'
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'ip_address': get_client_identifier(request),
            'message_length': len(data.get('message', '')),
            'response_time': data.get('response_time', 0)
        }
        
        # Log to MongoDB
        conversation_id = log_to_mongodb('conversations', conversation_data)
        
        return jsonify({
            "status": "success",
            "conversation_id": str(conversation_id) if conversation_id else None
        })
        
    except Exception as e:
        logger.error(f"Error logging conversation: {str(e)}")
        return jsonify({
            "error": "Failed to log conversation",
            "status": "error"
        }), 500

@app.route('/api/user-history/<user_name>')
def get_user_history(user_name):
    """Get conversation history for a user"""
    try:
        limit = request.args.get('limit', 50, type=int)
        conversations = get_user_conversations(user_name, limit)
        
        # Convert ObjectId to string for JSON serialization
        for conv in conversations:
            if '_id' in conv:
                conv['_id'] = str(conv['_id'])
        
        return jsonify({
            "status": "success",
            "user_name": user_name,
            "conversations": conversations,
            "count": len(conversations)
        })
        
    except Exception as e:
        logger.error(f"Error getting user history: {str(e)}")
        return jsonify({
            "error": "Failed to get conversation history",
            "status": "error"
        }), 500

@app.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint using Gemini API with rate limiting"""
    global conversation_history
    
    # Apply rate limiting if security packages not available
    if not SECURITY_AVAILABLE:
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ['REMOTE_ADDR'])
        current_time = time.time()
        
        if current_time > request_counts[client_ip]['reset_time']:
            request_counts[client_ip] = {'count': 0, 'reset_time': current_time + 3600}
        
        if request_counts[client_ip]['count'] >= 30:  # 30 requests per hour
            return jsonify({
                "reply": "Rate limit exceeded. Please wait before making more requests.",
                "error": "RATE_LIMIT_EXCEEDED",
                "status": "error"
            }), 429
        
        request_counts[client_ip]['count'] += 1
    
    if not is_api_configured():
        return jsonify({
            "reply": "Sorry, the chatbot is not properly configured. Please contact the administrator.",
            "intent": None,
            "error": "API_NOT_CONFIGURED",
            "status": "error"
        }), 500
    
    # Rate limiting check
    client_id = get_client_identifier(request)
    is_limited, request_count = is_rate_limited(client_id)
    
    if is_limited:
        reset_time = get_rate_limit_reset_time(client_id)
        logger.warning(f"Rate limit exceeded for client {client_id}")
        return jsonify({
            "reply": f"🚫 Rate limit exceeded. You can make {RATE_LIMIT_REQUESTS} requests per minute. Please wait {reset_time} seconds before trying again.",
            "intent": "rate_limit",
            "error": "RATE_LIMIT_EXCEEDED",
            "status": "error",
            "rate_limit": {
                "limit": RATE_LIMIT_REQUESTS,
                "remaining": 0,
                "reset_in": reset_time,
                "current_requests": request_count
            }
        }), 429

    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided", "status": "error"}), 400
            
        user_input = data.get('message', '').strip()  # Changed from 'query' to 'message'
        user_name = data.get('user_name', 'User')
        user_language = data.get('language', 'english')  # Get user's preferred language
        session_id = data.get('session_id', '')
        message_count = data.get('message_count', 0)
        
        if not user_input:
            return jsonify({"error": "No message provided", "status": "error"}), 400
        
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
        
        logger.info(f"Processing query: {user_input[:50]}... in {user_language}")
        
        # Call Gemini API with language support
        reply = call_gemini_api(conversation_history, user_language)
        
        if reply:
            # Add assistant response to conversation
            conversation_history.append({"role": "assistant", "content": reply})
            
            # Log conversation to MongoDB if user is named
            if user_name != 'User' and db is not None:
                log_to_mongodb('conversations', {
                    'user_name': user_name,
                    'session_id': session_id,
                    'user_message': user_input,
                    'assistant_response': reply,
                    'message_count': message_count,
                    'timestamp': datetime.now().isoformat(),
                    'ip_address': client_id,
                    'response_length': len(reply),
                    'user_message_length': len(user_input)
                })
            
            # Detect intent
            intent = detect_intent(user_input)
            
            # Calculate remaining requests for this client
            remaining_requests = max(0, RATE_LIMIT_REQUESTS - request_count)
            
            return jsonify({
                "reply": reply,
                "language": user_language,
                "intent": intent,
                "status": "success",
                "user_name": user_name,
                "session_id": session_id,
                "message_count": message_count,
                "provider": "Google Gemini",
                "model": GEMINI_MODEL,
                "timestamp": datetime.now().isoformat(),
                "rate_limit": {
                    "limit": RATE_LIMIT_REQUESTS,
                    "remaining": remaining_requests,
                    "reset_in": RATE_LIMIT_WINDOW
                }
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
            "timestamp": datetime.now().isoformat()
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
        "timestamp": datetime.now().isoformat()
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
    
    # For development only - Gunicorn will handle this in production
    app.run(host=host, port=port, debug=False)

# Ensure the app is available for WSGI servers like Gunicorn
if __name__ != '__main__':
    # Production startup logging
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Saathi Legal Assistant - Production Mode")
    print(f"🤖 Model: {GEMINI_MODEL}")
    print(f"🔑 API Configured: {is_api_configured()}")
    print(f"🌐 Production server on port {port}")
