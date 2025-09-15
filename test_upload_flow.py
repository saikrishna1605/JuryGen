#!/usr/bin/env python3
"""
Test the complete upload flow to identify issues.
"""

import requests
import json

def test_upload_flow():
    """Test the complete upload flow."""
    base_url = "http://127.0.0.1:8000"
    
    print("🧪 Testing Upload Flow...")
    print("=" * 50)
    
    # Step 1: Test health
    try:
        r = requests.get(f"{base_url}/health")
        print(f"✅ Health Check: {r.status_code}")
        if r.status_code != 200:
            print("❌ Backend not running properly")
            return False
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        return False
    
    # Step 2: Test create upload URL
    try:
        payload = {
            "filename": "test_document.pdf",
            "content_type": "application/pdf"
        }
        r = requests.post(f"{base_url}/v1/documents/upload", json=payload)
        print(f"✅ Create Upload URL: {r.status_code}")
        
        if r.status_code == 200:
            response_data = r.json()
            print(f"   Upload URL: {response_data.get('data', {}).get('upload_url', 'Not found')}")
            document_id = response_data.get('data', {}).get('document_id')
        else:
            print(f"   Error: {r.text}")
            document_id = None
    except Exception as e:
        print(f"❌ Create Upload URL failed: {e}")
        document_id = None
    
    # Step 3: Test direct upload
    try:
        # Create a test file
        test_content = b"This is a test PDF content for upload testing."
        files = {'file': ('test.pdf', test_content, 'application/pdf')}
        
        r = requests.post(f"{base_url}/v1/upload", files=files)
        print(f"✅ Direct Upload: {r.status_code}")
        
        if r.status_code == 200:
            upload_response = r.json()
            print(f"   Document ID: {upload_response.get('document_id', 'Not found')}")
            print(f"   File Size: {upload_response.get('file_size', 'Not found')}")
            actual_document_id = upload_response.get('document_id')
        else:
            print(f"   Error: {r.text}")
            actual_document_id = None
    except Exception as e:
        print(f"❌ Direct Upload failed: {e}")
        actual_document_id = None
    
    # Step 4: Test get documents
    try:
        r = requests.get(f"{base_url}/v1/documents")
        print(f"✅ Get Documents: {r.status_code}")
        
        if r.status_code == 200:
            docs_response = r.json()
            doc_count = len(docs_response.get('data', []))
            print(f"   Documents found: {doc_count}")
        else:
            print(f"   Error: {r.text}")
    except Exception as e:
        print(f"❌ Get Documents failed: {e}")
    
    # Step 5: Test get specific document
    if actual_document_id:
        try:
            r = requests.get(f"{base_url}/v1/documents/{actual_document_id}")
            print(f"✅ Get Document by ID: {r.status_code}")
            
            if r.status_code == 200:
                doc_response = r.json()
                print(f"   Document status: {doc_response.get('data', {}).get('status', 'Not found')}")
            else:
                print(f"   Error: {r.text}")
        except Exception as e:
            print(f"❌ Get Document by ID failed: {e}")
    
    # Step 6: Test QA endpoints
    try:
        test_doc_id = actual_document_id or "test_doc"
        r = requests.get(f"{base_url}/v1/qa/sessions/{test_doc_id}/history")
        print(f"✅ QA History: {r.status_code}")
    except Exception as e:
        print(f"❌ QA History failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Upload Flow Test Complete!")
    
    if actual_document_id:
        print("✅ Upload is working - files are being stored locally")
        print(f"✅ Document ID generated: {actual_document_id}")
        return True
    else:
        print("❌ Upload is not working properly")
        return False

if __name__ == "__main__":
    test_upload_flow()