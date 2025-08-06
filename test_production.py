import os
import sys

# Set environment variable for testing
os.environ['OPENROUTER_API_KEY'] = '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'
os.environ['PORT'] = '5001'  # Different port to avoid conflicts

# Import and run the production app
if __name__ == '__main__':
    print("🧪 Testing Production App Locally")
    print("=" * 40)
    
    try:
        from app_production import app
        print("✅ Production app imported successfully")
        print("🚀 Starting test server on http://127.0.0.1:5001")
        print("Press Ctrl+C to stop")
        
        app.run(host='127.0.0.1', port=5001, debug=False)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)
