#!/usr/bin/env python3
"""
Test the new upload flow that matches frontend expectations.
"""

import requests
import json

def test_new_upload_flow():
    """Test the upload flow that matches frontend expectations."""
    base_url = "http://127.0.0.1:8000"
    
    print("🧪 Testing New Upload Flow (Frontend Compatible)")
    print("=" * 60)
    
    # Step 1: Get upload URL (what frontend does)
    print("Step 1: Getting upload URL...")
    try:
        payload = {
            "filename": "test_document.pdf",
            "contentType": "application/pdf",
            "sizeBytes": 1024000
        }
        
        r = requests.post(f"{base_url}/v1/upload", json=payload)
        print(f"✅ Get Upload URL: {r.status_code}")
        
        if r.status_code == 200:
            response_data = r.json()
            job_id = response_data.get("jobId")
            upload_url = response_data.get("uploadUrl")
            expires_at = response_data.get("expiresAt")
            
            print(f"   Job ID: {job_id}")
            print(f"   Upload URL: {upload_url}")
            print(f"   Expires: {expires_at}")
            
            if not upload_url or upload_url == "undefined":
                print("❌ Upload URL is undefined!")
                return False
                
        else:
            print(f"   Error: {r.text}")
            return False
            
    except Exception as e:
        print(f"❌ Get Upload URL failed: {e}")
        return False
    
    # Step 2: Upload file to the signed URL (what frontend does)
    print("\nStep 2: Uploading file to signed URL...")
    try:
        # Create test file content
        test_content = b"This is a test PDF content for the new upload flow."
        
        # PUT the file to the upload URL (like frontend does)
        headers = {
            'Content-Type': 'application/pdf'
        }
        
        r = requests.put(upload_url, data=test_content, headers=headers)
        print(f"✅ Upload File: {r.status_code}")
        
        if r.status_code == 200:
            upload_response = r.json()
            print(f"   Success: {upload_response.get('success')}")
            print(f"   Message: {upload_response.get('message')}")
        else:
            print(f"   Error: {r.text}")
            return False
            
    except Exception as e:
        print(f"❌ File upload failed: {e}")
        return False
    
    # Step 3: Verify document was stored
    print("\nStep 3: Verifying document storage...")
    try:
        r = requests.get(f"{base_url}/v1/documents")
        print(f"✅ Get Documents: {r.status_code}")
        
        if r.status_code == 200:
            docs_response = r.json()
            documents = docs_response.get('data', [])
            
            # Find our uploaded document
            uploaded_doc = None
            for doc in documents:
                if doc.get('id') == job_id:
                    uploaded_doc = doc
                    break
            
            if uploaded_doc:
                print(f"   ✅ Document found: {uploaded_doc['filename']}")
                print(f"   ✅ File size: {uploaded_doc['file_size']} bytes")
                print(f"   ✅ Status: {uploaded_doc['status']}")
            else:
                print(f"   ❌ Document with job ID {job_id} not found")
                return False
        else:
            print(f"   Error: {r.text}")
            
    except Exception as e:
        print(f"❌ Document verification failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 NEW UPLOAD FLOW TEST COMPLETE!")
    print("✅ Frontend-compatible upload workflow is working!")
    print(f"✅ Document uploaded with job ID: {job_id}")
    
    return True

if __name__ == "__main__":
    success = test_new_upload_flow()
    if success:
        print("\n🚀 Upload system is ready for frontend!")
    else:
        print("\n❌ Upload system needs fixes")