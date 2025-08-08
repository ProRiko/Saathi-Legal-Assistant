"""
Saathi Legal Assistant - Gemini AI Powered
Railway.app deployment ready with Google Gemini API
Enhanced with Legal Document Generation
"""
import os
from flask import Flask, request, jsonify, send_file, make_response
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
            
            # Calculate remaining requests for this client
            remaining_requests = max(0, RATE_LIMIT_REQUESTS - request_count)
            
            return jsonify({
                "reply": reply,
                "intent": intent,
                "status": "success",
                "provider": "Google Gemini",
                "model": GEMINI_MODEL,
                "timestamp": datetime.utcnow().isoformat(),
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    print(f"🚀 Starting Saathi Legal Assistant - Gemini Powered")
    print(f"🤖 Model: {GEMINI_MODEL}")
    print(f"🔑 API Configured: {is_api_configured()}")
    print(f"🌐 Running on {host}:{port}")
    
    app.run(host=host, port=port, debug=False)
