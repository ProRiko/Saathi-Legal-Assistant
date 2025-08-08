# 🏛️ Saathi Legal Assistant

A comprehensive AI-powered legal assistant that provides chat support and generates legal documents with PDF creation capabilities.

## ✨ Features

### 💬 AI Chat Support
- Google Gemini AI integration for legal queries
- Rate limiting (3 requests per minute) to prevent abuse
- Conversation history management
- Hindi and English language support

### 📝 Legal Document Generation
Generate professional legal letters in text or PDF format:

1. **Demand Notice** - For debt recovery and payment demands
2. **Rent Notice** - For rental/lease related issues
3. **Consumer Complaint** - For consumer protection matters

### 📋 Legal Form Generation
Create legal forms with PDF download:

1. **Rental Agreement** - Standard lease agreement template
2. **Employment Contract** - Basic employment agreement
3. **Power of Attorney** - General power of attorney document
4. **Sale Deed** - Property sale deed template

### 🔒 Security Features
- Rate limiting to prevent API abuse
- CORS protection
- Input validation and sanitization
- Error handling and logging

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Google Gemini API Key (optional, for chat features)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Saathi-Legal-Assistant
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables:**
   ```bash
   # Create .env file or set environment variable
   set GOOGLE_API_KEY=your_gemini_api_key_here
   ```

5. **Start the server:**
   ```bash
   python start_server.py
   ```

The server will start at `http://localhost:5000`

## 📖 API Documentation

### Chat Endpoint
```http
POST /chat
Content-Type: application/json

{
    "message": "What are my rights as a tenant?"
}
```

### Generate Legal Letter
```http
POST /generate-letter
Content-Type: application/json

{
    "letter_type": "demand_notice",
    "user_data": {
        "sender_name": "John Doe",
        "sender_address": "123 Main St, City",
        "recipient_name": "Jane Smith", 
        "recipient_address": "456 Oak Ave, Town",
        "amount_owed": "50000",
        "description": "Outstanding payment for services",
        "due_date": "2024-02-15"
    },
    "format": "pdf"  // or "text"
}
```

### Generate Legal Form
```http
POST /generate-form/rent_agreement
Content-Type: application/json

{
    "form_data": {
        "landlord_name": "Property Owner",
        "tenant_name": "Renter Name",
        "property_address": "Property Address",
        "monthly_rent": "25000",
        "security_deposit": "50000",
        "lease_start_date": "2024-01-01"
    },
    "format": "pdf"
}
```

### Available Letter Types
- `demand_notice` - Legal demand for payment
- `rent_notice` - Rental/lease notices  
- `consumer_complaint` - Consumer protection complaints

### Available Form Types
- `rent_agreement` - Rental agreement
- `employment_contract` - Employment contract
- `power_of_attorney` - Power of attorney
- `sale_deed` - Property sale deed

## 🌐 Web Interface

Open `test_documents.html` in your browser for a user-friendly interface to:
- Generate legal letters with form inputs
- Create legal documents with PDF download
- Test all document generation features

## 📁 Project Structure

```
Saathi-Legal-Assistant/
├── app_gemini.py          # Main Flask application
├── start_server.py        # Server startup script
├── test_documents.html    # Web interface for testing
├── requirements.txt       # Python dependencies
├── backend/
│   ├── app.py            # Original backend (legacy)
│   ├── chatbot.py        # Chat logic
│   └── pdf_generator.py  # PDF utilities
└── frontend/             # React Native mobile app
    ├── App.js
    └── screens/
```

## 🔧 Technical Details

### Dependencies
- **Flask 3.1.0** - Web framework
- **Google Generative AI** - Gemini API client
- **ReportLab 4.0.4** - PDF generation
- **Pillow 10.0.0** - Image processing
- **Flask-CORS** - Cross-origin requests

### Rate Limiting
- 3 requests per minute per IP address
- Automatic cleanup of expired requests
- HTTP 429 responses for exceeded limits
- Visual feedback in web interface

### PDF Generation
- Professional document formatting
- Indian law compliance notices
- Proper legal document structure
- Download-ready PDF files

## 🚀 Deployment

### Railway.app Deployment
1. Connect your GitHub repository to Railway
2. Set environment variables in Railway dashboard:
   - `GOOGLE_API_KEY=your_api_key`
3. Deploy automatically from main branch

### Environment Variables
- `GOOGLE_API_KEY` - Google Gemini API key (optional)
- `PORT` - Server port (default: 5000)

## ⚖️ Legal Disclaimer

**Important:** This application provides template legal documents and general legal information for reference purposes only. It does not constitute legal advice. Users should:

1. Consult qualified legal professionals before using any generated documents
2. Verify compliance with local laws and regulations
3. Review and customize documents for specific situations
4. Understand their legal rights and obligations

The developers are not responsible for the accuracy, completeness, or legal validity of generated documents.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and support:
1. Check the documentation
2. Review common errors in the code
3. Open an issue on GitHub
4. Contact the development team

---

**Made with ❤️ for the legal community**
