#!/usr/bin/env python3
"""
Production server startup script for Legal Companion.
Verifies all services are working before starting the server.
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def verify_services():
    """Verify all Google Cloud services are working."""
    print("🔍 Verifying Google Cloud services...")
    
    try:
        # Run the comprehensive test
        result = subprocess.run([sys.executable, "test_full_functionality.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0 and "🎉 ALL TESTS PASSED!" in result.stdout:
            print("✅ All Google Cloud services verified and working!")
            return True
        else:
            print("❌ Service verification failed:")
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error verifying services: {e}")
        return False

def start_server():
    """Start the FastAPI server."""
    print("\n🚀 Starting Legal Companion Production Server...")
    print("=" * 60)
    print("✅ Real OCR processing (Google Document AI)")
    print("✅ Real file storage (Google Cloud Storage)")  
    print("✅ Real translation (Google Translate API)")
    print("✅ No mock or demo functionality")
    print("=" * 60)
    
    try:
        # Change to app directory
        os.chdir("app")
        
        # Start uvicorn server
        cmd = [
            sys.executable, "-m", "uvicorn",
            "main:app",
            "--reload",
            "--host", "127.0.0.1",
            "--port", "8000",
            "--log-level", "info"
        ]
        
        print("🌐 Server starting at: http://127.0.0.1:8000")
        print("📚 API Documentation: http://127.0.0.1:8000/docs")
        print("📖 Alternative Docs: http://127.0.0.1:8000/redoc")
        print("\n⚡ Press Ctrl+C to stop the server")
        print("=" * 60)
        
        # Start the server
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")

def main():
    """Main function."""
    print("🚀 Legal Companion - Production Server Startup")
    print("=" * 60)
    
    # Verify all services are working
    if not verify_services():
        print("\n❌ Cannot start server - service verification failed")
        print("Please check your Google Cloud configuration and try again.")
        return
    
    # Start the server
    start_server()

if __name__ == "__main__":
    main()