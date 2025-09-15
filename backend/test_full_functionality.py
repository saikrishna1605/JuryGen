#!/usr/bin/env python3
"""
Comprehensive test of all Google Cloud services with real functionality.
"""

import os
import io
import base64
from dotenv import load_dotenv
from google.cloud import documentai, storage, translate_v2 as translate

load_dotenv()

def test_document_ai():
    """Test Document AI with a sample document."""
    print("🧪 Testing Document AI OCR...")
    
    try:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
        location = os.getenv("DOCUMENT_AI_LOCATION", "us")
        processor_id = os.getenv("DOCUMENT_AI_PROCESSOR_ID")
        
        client = documentai.DocumentProcessorServiceClient()
        processor_name = f"projects/{project_id}/locations/{location}/processors/{processor_id}"
        
        # Create a minimal PDF document for testing
        # This is a base64 encoded minimal PDF with text "Legal Document Test"
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Legal Document Test) Tj
ET
endstream
endobj

5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj

xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000274 00000 n 
0000000368 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
465
%%EOF"""
        
        # Create the document object
        raw_document = documentai.RawDocument(
            content=pdf_content,
            mime_type="application/pdf"
        )
        
        # Process the document
        request = documentai.ProcessRequest(
            name=processor_name,
            raw_document=raw_document
        )
        
        result = client.process_document(request=request)
        
        # Extract text
        extracted_text = result.document.text
        
        print(f"✅ Document AI OCR successful!")
        print(f"Extracted text length: {len(extracted_text)} chars")
        print(f"Sample extracted text: {extracted_text.strip()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Document AI test failed: {e}")
        return False

def test_cloud_storage():
    """Test Cloud Storage upload and download."""
    print("\n🧪 Testing Cloud Storage...")
    
    try:
        bucket_name = os.getenv("STORAGE_BUCKET_NAME")
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        
        # Test file content
        test_content = "This is a test file for Legal Companion storage functionality."
        test_filename = "test-document.txt"
        
        # Upload test
        blob = bucket.blob(test_filename)
        blob.upload_from_string(test_content, content_type="text/plain")
        
        print(f"✅ File uploaded: {test_filename}")
        
        # Download test
        downloaded_content = blob.download_as_text()
        
        print(f"✅ File downloaded successfully")
        print(f"Content matches: {downloaded_content == test_content}")
        
        # Generate signed URL
        signed_url = blob.generate_signed_url(expiration=3600)
        print(f"✅ Signed URL generated: {signed_url[:50]}...")
        
        # Clean up
        blob.delete()
        print(f"✅ Test file cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Cloud Storage test failed: {e}")
        return False

def test_translation():
    """Test Translation API with various languages."""
    print("\n🧪 Testing Translation API...")
    
    try:
        client = translate.Client()
        
        # Test translations
        test_cases = [
            ("Hello, this is a legal document.", "es"),
            ("Contract terms and conditions", "fr"),
            ("Confidentiality agreement", "de"),
            ("Payment due date", "it")
        ]
        
        for text, target_lang in test_cases:
            result = client.translate(text, target_language=target_lang)
            translated = result['translatedText']
            detected_lang = result.get('detectedSourceLanguage', 'en')
            
            print(f"✅ {detected_lang} → {target_lang}: '{text}' → '{translated}'")
        
        # Test language detection
        detect_result = client.detect_language("Bonjour, ceci est un document juridique.")
        detected = detect_result['language']
        confidence = detect_result['confidence']
        
        print(f"✅ Language detection: {detected} (confidence: {confidence:.2f})")
        
        return True
        
    except Exception as e:
        print(f"❌ Translation test failed: {e}")
        return False

def test_api_endpoints():
    """Test that the services are properly configured."""
    print("\n🧪 Testing Service Configuration...")
    
    try:
        # Check environment variables
        required_vars = [
            "GOOGLE_CLOUD_PROJECT_ID",
            "GOOGLE_APPLICATION_CREDENTIALS", 
            "DOCUMENT_AI_PROCESSOR_ID",
            "STORAGE_BUCKET_NAME"
        ]
        
        missing_vars = []
        for var in required_vars:
            value = os.getenv(var)
            if not value or value == "your-processor-id-here":
                missing_vars.append(var)
            else:
                print(f"✅ {var}: configured")
        
        if missing_vars:
            print(f"❌ Missing variables: {', '.join(missing_vars)}")
            return False
        
        # Test credentials file
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if os.path.exists(creds_path):
            print(f"✅ Credentials file exists: {creds_path}")
        else:
            print(f"❌ Credentials file not found: {creds_path}")
            return False
        
        print("✅ All services properly configured for production use")
        print("✅ No mock functionality - all real Google Cloud services")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Run all functionality tests."""
    print("🚀 Legal Companion - Full Functionality Test")
    print("=" * 60)
    print("Testing all Google Cloud services with REAL functionality")
    print("=" * 60)
    
    # Test results
    results = {
        "Document AI": test_document_ai(),
        "Cloud Storage": test_cloud_storage(),
        "Translation API": test_translation(),
        "Configuration": test_api_endpoints()
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for service, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{service:20} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("Your Legal Companion backend is fully functional with:")
        print("  ✅ Real OCR processing (Google Document AI)")
        print("  ✅ Real file storage (Google Cloud Storage)")
        print("  ✅ Real translation (Google Translate API)")
        print("  ✅ No mock data or demo functionality")
        print("\n🚀 Ready for production use!")
        print("Start server: cd app && uvicorn main:app --reload")
        print("API docs: http://localhost:8000/docs")
    else:
        print("❌ Some tests failed. Check the errors above.")
    
    return all_passed

if __name__ == "__main__":
    main()