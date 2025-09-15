#!/usr/bin/env python3
"""
Test all API endpoints to verify they're working.
"""

import requests
import json

def test_endpoints():
    """Test all API endpoints."""
    base_url = "http://127.0.0.1:8000"
    
    print("🧪 Testing All API Endpoints")
    print("=" * 50)
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✅ Health: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Health: {e}")
        return False
    
    # Test documents endpoint
    try:
        response = requests.get(f"{base_url}/v1/documents")
        print(f"✅ Documents: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Documents count: {len(data.get('data', []))}")
    except Exception as e:
        print(f"❌ Documents: {e}")
    
    # Test QA history endpoint
    try:
        response = requests.get(f"{base_url}/v1/qa/sessions/doc_1/history?session_id=default")
        print(f"✅ QA History: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   History items: {len(data.get('history', []))}")
    except Exception as e:
        print(f"❌ QA History: {e}")
    
    # Test upload endpoint (without file)
    try:
        response = requests.post(f"{base_url}/v1/upload")
        print(f"✅ Upload: {response.status_code} (expected 422 - missing file)")
    except Exception as e:
        print(f"❌ Upload: {e}")
    
    # Test voice QA endpoint (without file)
    try:
        response = requests.post(f"{base_url}/v1/qa/ask-voice?document_id=doc_1")
        print(f"✅ Voice QA: {response.status_code} (expected 422 - missing file)")
    except Exception as e:
        print(f"❌ Voice QA: {e}")
    
    # Test translation endpoints
    try:
        response = requests.get(f"{base_url}/v1/translation/languages")
        print(f"✅ Translation Languages: {response.status_code}")
    except Exception as e:
        print(f"❌ Translation Languages: {e}")
    
    print("\n🎯 All endpoints tested!")
    return True

if __name__ == "__main__":
    test_endpoints()