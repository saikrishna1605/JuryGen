#!/usr/bin/env python3
"""
Simple server startup script without Unicode characters.
"""

import os
import sys
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def start_server():
    """Start the FastAPI server."""
    print("Starting Legal Companion Backend Server...")
    print("=" * 50)
    print("Real OCR processing (Google Document AI)")
    print("Real file storage (Google Cloud Storage)")  
    print("Real translation (Google Translate API)")
    print("No mock or demo functionality")
    print("=" * 50)
    
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
        
        print("Server starting at: http://127.0.0.1:8000")
        print("API Documentation: http://127.0.0.1:8000/docs")
        print("Alternative Docs: http://127.0.0.1:8000/redoc")
        print("")
        print("Press Ctrl+C to stop the server")
        print("=" * 50)
        
        # Start the server
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Failed to start server: {e}")

if __name__ == "__main__":
    start_server()