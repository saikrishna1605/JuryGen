#!/usr/bin/env python3
"""
Start backend server immediately with all endpoints.
"""

import os
import sys
import subprocess
import time

def start_server():
    """Start the backend server."""
    print("🚀 Starting Legal Companion Backend Server...")
    print("=" * 50)
    
    # Change to backend/app directory
    os.chdir("backend/app")
    
    # Start uvicorn directly
    cmd = [
        sys.executable, "-m", "uvicorn",
        "main:app",
        "--reload",
        "--host", "127.0.0.1", 
        "--port", "8000",
        "--log-level", "info"
    ]
    
    print("Starting server with command:", " ".join(cmd))
    print("Server will be available at: http://127.0.0.1:8000")
    print("API Documentation: http://127.0.0.1:8000/docs")
    print("=" * 50)
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")

if __name__ == "__main__":
    start_server()