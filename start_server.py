#!/usr/bin/env python3
"""
Saathi Legal Assistant Server Startup Script
"""
import os
import sys
import subprocess

def main():
    """Start the Saathi Legal Assistant server"""
    print("🏛️ Starting Saathi Legal Assistant Server...")
    print("💼 Features: Chat, Legal Document Generation, PDF Creation")
    print("=" * 60)
    
    # Check if environment variables are set
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("⚠️  WARNING: GOOGLE_API_KEY environment variable not set!")
        print("   Chat functionality will be limited without API key.")
        print("   Document generation will still work.")
    else:
        print("✅ Google API Key found")
    
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🐍 Python version: {sys.version}")
    
    # Check dependencies
    try:
        import flask
        import reportlab
        print("✅ All dependencies available")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return 1
    
    print("=" * 60)
    print("🚀 Starting server...")
    print("📝 Chat API: http://localhost:5000/chat")
    print("📄 Letter Generation: http://localhost:5000/generate-letter") 
    print("📋 Form Generation: http://localhost:5000/generate-form/<form_type>")
    print("🌐 Test Interface: http://localhost:5000 or open test_documents.html")
    print("=" * 60)
    print("Press Ctrl+C to stop the server")
    
    # Start the Flask app
    try:
        from app_gemini import app
        app.run(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
