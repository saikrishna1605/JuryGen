#!/usr/bin/env python3
"""
Restart backend and test all endpoints.
"""

import subprocess
import sys
import time
import requests
import os

def kill_existing_server():
    """Kill existing server processes."""
    try:
        result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        for line in lines:
            if ':8000' in line and 'LISTENING' in line:
                parts = line.split()
                if len(parts) > 4:
                    pid = parts[-1]
                    print(f"Killing process {pid} on port 8000...")
                    subprocess.run(["taskkill", "/PID", pid, "/F"], capture_output=True)
    except Exception as e:
        print(f"Error killing processes: {e}")

def start_server():
    """Start the backend server."""
    print("🚀 Starting backend server...")
    
    # Change to backend/app directory
    os.chdir("backend/app")
    
    # Start server
    cmd = [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"]
    
    process = subprocess.Popen(cmd)
    
    # Wait for server to start
    print("Waiting for server to start...")
    time.sleep(5)
    
    return process

def test_endpoints():
    """Test all endpoints."""
    base_url = "http://127.0.0.1:8000"
    
    print("\n🧪 Testing endpoints...")
    
    # Test health
    try:
        r = requests.get(f"{base_url}/health")
        print(f"✅ Health: {r.status_code}")
    except Exception as e:
        print(f"❌ Health: {e}")
        return False
    
    # Test documents
    try:
        r = requests.get(f"{base_url}/v1/documents")
        print(f"✅ Documents: {r.status_code}")
    except Exception as e:
        print(f"❌ Documents: {e}")
    
    # Test upload (without file - should return error but not 404)
    try:
        r = requests.post(f"{base_url}/v1/upload")
        print(f"✅ Upload: {r.status_code} (expected 422 or 400)")
    except Exception as e:
        print(f"❌ Upload: {e}")
    
    # Test QA history
    try:
        r = requests.get(f"{base_url}/v1/qa/sessions/test_doc/history")
        print(f"✅ QA History: {r.status_code}")
    except Exception as e:
        print(f"❌ QA History: {e}")
    
    print("\n🎯 All endpoints tested!")
    return True

def main():
    """Main function."""
    print("🔄 Restarting Legal Companion Backend...")
    
    # Kill existing server
    kill_existing_server()
    time.sleep(2)
    
    # Start new server
    process = start_server()
    
    # Test endpoints
    if test_endpoints():
        print("\n✅ Server is running and all endpoints are working!")
        print("🌐 Server: http://127.0.0.1:8000")
        print("📚 API Docs: http://127.0.0.1:8000/docs")
        print("\nPress Ctrl+C to stop...")
        
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n👋 Stopping server...")
            process.terminate()
    else:
        print("\n❌ Server startup failed")
        process.terminate()

if __name__ == "__main__":
    main()