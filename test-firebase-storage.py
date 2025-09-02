#!/usr/bin/env python3
"""
Test Firebase Storage configuration
"""

import os
import sys
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError

def test_firebase_storage():
    """Test Firebase Storage configuration"""
    
    # Set up environment
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './backend/service-account-key.json'
    os.environ['GOOGLE_CLOUD_PROJECT'] = 'kiro-hackathon23'
    
    bucket_name = 'kiro-hackathon23.firebasestorage.app'
    
    try:
        print(f"🔍 Testing Firebase Storage configuration...")
        print(f"📦 Project: kiro-hackathon23")
        print(f"🪣 Bucket: {bucket_name}")
        
        # Initialize storage client
        client = storage.Client()
        print("✅ Storage client initialized")
        
        # Try to get the bucket
        bucket = client.bucket(bucket_name)
        print("✅ Bucket reference created")
        
        # Check if bucket exists
        if bucket.exists():
            print("✅ Bucket exists and is accessible")
            
            # Try to list some objects (just to test permissions)
            blobs = list(bucket.list_blobs(max_results=1))
            print(f"✅ Bucket listing successful (found {len(blobs)} objects)")
            
        else:
            print("❌ Bucket does not exist or is not accessible")
            print("💡 Make sure Firebase Storage is enabled in your Firebase Console")
            print("💡 Go to: https://console.firebase.google.com/project/kiro-hackathon23/storage")
            return False
            
    except GoogleCloudError as e:
        print(f"❌ Google Cloud error: {e}")
        if "does not exist" in str(e).lower():
            print("💡 The storage bucket doesn't exist. You need to enable Firebase Storage.")
            print("💡 Go to: https://console.firebase.google.com/project/kiro-hackathon23/storage")
            print("💡 Click 'Get started' to enable Firebase Storage")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    print("🎉 Firebase Storage is properly configured!")
    return True

if __name__ == "__main__":
    success = test_firebase_storage()
    sys.exit(0 if success else 1)