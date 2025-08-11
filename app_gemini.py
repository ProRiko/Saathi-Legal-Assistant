"""
Saathi Legal Assistant - Gemini AI Powered
Railway.app deployment ready with Google Gemini API
Enhanced with Legal Document Generation and Rights Calculator
VERSION: 3.0.0 - FEATURE #3 LEGAL HELP DIRECTORY
"""
import os
from flask import Flask, request, jsonify, send_file, send_from_directory, make_response, render_template_string
from flask_cors import CORS
import requests
import logging
from datetime import datetime, timedelta
import json
from collections import defaultdict, deque
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import io
import tempfile

# Rights Calculator
try:
    from rights_calculator import LegalRightsCalculator
    rights_calc = LegalRightsCalculator()
    RIGHTS_CALC_AVAILABLE = True
except ImportError:
    RIGHTS_CALC_AVAILABLE = False
    print("Rights Calculator not available.")

# MongoDB imports (optional - will work without MongoDB)
try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    print("MongoDB not available. Conversation logging will be disabled.")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Static file serving routes
@app.route('/legal-help.html')
def serve_legal_help():
    """Serve the legal help directory page"""
    try:
        with open('legal_help.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Legal help directory not found", 404

@app.route('/calculator.html')
def serve_calculator():
    """Serve the simple calculator page"""
    try:
        with open('simple_calculator.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Calculator page not found", 404

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

@app.route('/manifest.json')
def serve_manifest():
    """Serve the PWA manifest file"""
    try:
        return send_file('manifest.json', mimetype='application/json')
    except FileNotFoundError:
        return "Manifest file not found", 404

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

@app.route('/debug/version')
def debug_version():
    """Debug endpoint to check deployment version"""
    return jsonify({
        "version": "rights_calculator_v2",
        "timestamp": datetime.now().isoformat(),
        "calculator_available": RIGHTS_CALC_AVAILABLE,
        "routes": [str(rule) for rule in app.url_map.iter_rules()],
        "message": "Rights Calculator deployment active"
    })

@app.route('/calculator.html')
def calculator_page():
    """Serve the rights calculator page"""
    try:
        with open('calculator.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return """
        <html>
        <body style="text-align: center; padding: 50px; font-family: Arial; background: #1a2332; color: #f4f1e8;">
            <h1>🧮 Calculator Not Available</h1>
            <p>Rights calculator page not found.</p>
            <a href="/" style="color: #8b4513;">Back to Home</a>
        </body>
        </html>
        """, 404

@app.route('/api/templates', methods=['GET'])
def get_templates():
    """Get available document templates"""
    try:
        from document_generator import DocumentGenerator
        generator = DocumentGenerator()
        templates = generator.get_available_templates()
        return jsonify(templates)
    except Exception as e:
        logger.error(f"Error getting templates: {str(e)}")
        return jsonify({"error": "Failed to load templates"}), 500

@app.route('/api/template-questions/<template_id>', methods=['GET'])
def get_template_questions(template_id):
    """Get questions for a specific template"""
    try:
        from document_generator import DocumentGenerator
        generator = DocumentGenerator()
        questions = generator.get_template_questions(template_id)
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
        
        from document_generator import DocumentGenerator
        generator = DocumentGenerator()
        document = generator.generate_document(template_id, user_data)
        
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

@app.route('/api/rights-calculators', methods=['GET'])
def get_rights_calculators():
    """Get all available rights calculators"""
    try:
        if not RIGHTS_CALC_AVAILABLE:
            return jsonify({"error": "Rights calculator not available"}), 503
            
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
        if not RIGHTS_CALC_AVAILABLE:
            return jsonify({"error": "Rights calculator not available"}), 503
            
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
        
        logger.info(f"Processing query: {user_input[:50]}...")
        
        # Call Gemini API
        reply = call_gemini_api(conversation_history)
        
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

# Version endpoint for deployment verification
@app.route('/version')
def version_check():
    """Simple version check endpoint"""
    return jsonify({
        "version": "3.0.0 - FEATURE #3 LEGAL HELP DIRECTORY",
        "status": "working",
        "timestamp": datetime.now().isoformat(),
        "features": ["Smart Templates", "Rights Calculator", "Legal Help Directory"]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    print(f"🚀 Starting Saathi Legal Assistant - Gemini Powered")
    print(f"🤖 Model: {GEMINI_MODEL}")
    print(f"🔑 API Configured: {is_api_configured()}")
    print(f"🌐 Running on {host}:{port}")
    
    app.run(host=host, port=port, debug=False)
