#!/usr/bin/env python3
"""
Test the live deployment of Saathi Legal Assistant
"""
import requests
import json

def test_deployment():
    base_url = "https://web-production-62a3.up.railway.app"
    
    print("Testing Saathi Legal Assistant Live Deployment")
    print("=" * 50)
    
    # Test 1: Health Check
    print("\n1. Testing Health Endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"App: {health_data.get('app')}")
            print(f"Provider: {health_data.get('provider')}")
            print(f"Model: {health_data.get('model')}")
            print(f"API Configured: {health_data.get('api_configured')}")
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.text}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test 2: Root endpoint (what frontend checks)
    print("\n2. Testing Root Endpoint (Frontend Check)...")
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("✅ Root endpoint accessible")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
    
    # Test 3: Chat Functionality
    print("\n3. Testing Chat Functionality...")
    try:
        test_query = "My landlord is not returning my security deposit. What can I do?"
        payload = {
            "query": test_query,
            "lang": "en"
        }
        
        response = requests.post(
            f"{base_url}/chat", 
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Intent: {data.get('intent')}")
            print(f"Provider: {data.get('provider')}")
            print(f"Model: {data.get('model')}")
            print(f"Response: {data.get('reply')[:200]}...")
            print("✅ Chat functionality working")
        else:
            print(f"❌ Chat failed: {response.text}")
    except Exception as e:
        print(f"❌ Chat error: {e}")

if __name__ == "__main__":
    test_deployment()
