#!/usr/bin/env python3
"""
Simple test of Google Cloud services without Unicode characters.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_services():
    """Test Google Cloud services."""
    print("Testing Google Cloud Services...")
    print("=" * 40)
    
    try:
        # Test Google Cloud Storage
        from google.cloud import storage
        storage_client = storage.Client()
        
        bucket_name = os.getenv("STORAGE_BUCKET_NAME")
        if bucket_name:
            bucket = storage_client.bucket(bucket_name)
            bucket.reload()
            print("Cloud Storage: Connected to", bucket_name)
        
        # Test Translation API
        from google.cloud import translate_v2 as translate
        translate_client = translate.Client()
        
        result = translate_client.translate("Hello", target_language="es")
        if result and "translatedText" in result:
            print("Translation API: Working -", result['translatedText'])
        
        # Test Document AI
        processor_id = os.getenv("DOCUMENT_AI_PROCESSOR_ID")
        if processor_id and processor_id != "your-processor-id-here":
            from google.cloud import documentai
            client = documentai.DocumentProcessorServiceClient()
            
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
            location = os.getenv("DOCUMENT_AI_LOCATION", "us")
            processor_name = f"projects/{project_id}/locations/{location}/processors/{processor_id}"
            
            processor = client.get_processor(name=processor_name)
            print("Document AI: Connected to", processor.display_name)
        else:
            print("⚠️  Document AI: Processor not configured")
        
        print("Google Cloud services are ready!")
        return True
        
    except Exception as e:
        print("Error:", str(e))
        return False

if __name__ == "__main__":
    test_services()