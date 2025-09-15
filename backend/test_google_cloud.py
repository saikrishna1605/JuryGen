#!/usr/bin/env python3
"""
Quick test script to verify Google Cloud services are working.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_google_cloud_services():
    """Test Google Cloud services."""
    print("🧪 Testing Google Cloud Services...")
    print("=" * 50)
    
    # Check environment variables
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    print(f"✅ Project ID: {project_id}")
    print(f"✅ Credentials: {credentials_path}")
    
    try:
        # Test Google Cloud Storage
        from google.cloud import storage
        storage_client = storage.Client()
        
        bucket_name = os.getenv("STORAGE_BUCKET_NAME")
        if bucket_name:
            try:
                bucket = storage_client.bucket(bucket_name)
                bucket.reload()
                print(f"✅ Cloud Storage: Connected to '{bucket_name}'")
            except Exception as e:
                print(f"❌ Cloud Storage: {e}")
        
        # Test Translation API
        from google.cloud import translate_v2 as translate
        translate_client = translate.Client()
        
        try:
            result = translate_client.translate("Hello World", target_language="es")
            if result and "translatedText" in result:
                print(f"✅ Translation API: '{result['translatedText']}'")
        except Exception as e:
            print(f"❌ Translation API: {e}")
        
        # Test Document AI (if processor ID is set)
        processor_id = os.getenv("DOCUMENT_AI_PROCESSOR_ID")
        if processor_id and processor_id != "your-processor-id-here":
            from google.cloud import documentai
            client = documentai.DocumentProcessorServiceClient()
            
            location = os.getenv("DOCUMENT_AI_LOCATION", "us")
            processor_name = f"projects/{project_id}/locations/{location}/processors/{processor_id}"
            
            try:
                processor = client.get_processor(name=processor_name)
                print(f"✅ Document AI: Connected to '{processor.display_name}'")
            except Exception as e:
                print(f"❌ Document AI: {e}")
        else:
            print("⚠️  Document AI: Processor not configured")
        
        print("\n🎉 Google Cloud services are ready!")
        return True
        
    except ImportError as e:
        print(f"❌ Missing Google Cloud libraries: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_google_cloud_services()