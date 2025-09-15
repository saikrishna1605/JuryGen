#!/usr/bin/env python3
"""
Comprehensive setup verification for Legal Companion.
"""

import os
import subprocess
import sys
from pathlib import Path

def check_backend_env():
    """Check backend environment variables."""
    print("Checking Backend Environment...")
    print("-" * 40)
    
    backend_env = Path("backend/.env")
    if not backend_env.exists():
        print("❌ Backend .env file not found")
        return False
    
    # Load backend env
    sys.path.append("backend")
    from dotenv import load_dotenv
    load_dotenv("backend/.env")
    
    required_vars = [
        "GOOGLE_CLOUD_PROJECT_ID",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "DOCUMENT_AI_PROCESSOR_ID",
        "STORAGE_BUCKET_NAME"
    ]
    
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or value == "your-processor-id-here":
            missing.append(var)
            print(f"❌ {var}: Not set")
        else:
            print(f"✅ {var}: Configured")
    
    if missing:
        print(f"❌ Missing backend variables: {', '.join(missing)}")
        return False
    
    # Check credentials file
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path and Path(f"backend/{creds_path}").exists():
        print("✅ Service account key file exists")
    else:
        print("❌ Service account key file not found")
        return False
    
    print("✅ Backend environment configured correctly")
    return True

def check_frontend_env():
    """Check frontend environment variables."""
    print("\nChecking Frontend Environment...")
    print("-" * 40)
    
    frontend_env = Path("frontend/.env")
    if not frontend_env.exists():
        print("❌ Frontend .env file not found")
        return False
    
    # Read frontend env file
    with open(frontend_env, 'r') as f:
        content = f.read()
    
    required_vars = [
        "VITE_FIREBASE_API_KEY",
        "VITE_FIREBASE_AUTH_DOMAIN",
        "VITE_FIREBASE_PROJECT_ID",
        "VITE_FIREBASE_STORAGE_BUCKET",
        "VITE_FIREBASE_MESSAGING_SENDER_ID",
        "VITE_FIREBASE_APP_ID"
    ]
    
    missing = []
    for var in required_vars:
        # Look for the variable in the content
        lines = content.split('\n')
        found = False
        for line in lines:
            line = line.strip()
            if line.startswith(f"{var}=") and not line.startswith('#'):
                value = line.split('=', 1)[1].strip()
                if value:
                    print(f"✅ {var}: Configured")
                    found = True
                    break
        
        if not found:
            missing.append(var)
            print(f"❌ {var}: Not found")
    
    if missing:
        print(f"❌ Missing frontend variables: {', '.join(missing)}")
        return False
    
    print("✅ Frontend environment configured correctly")
    return True

def test_backend_services():
    """Test backend Google Cloud services."""
    print("\nTesting Backend Services...")
    print("-" * 40)
    
    try:
        result = subprocess.run([
            sys.executable, "test_services_simple.py"
        ], capture_output=True, text=True, cwd="backend")
        
        if result.returncode == 0 and "Google Cloud services are ready!" in result.stdout:
            print("✅ All Google Cloud services working")
            return True
        else:
            print("❌ Google Cloud services test failed")
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error testing services: {e}")
        return False

def check_ports():
    """Check if required ports are available."""
    print("\nChecking Ports...")
    print("-" * 40)
    
    try:
        # Check port 8000 (backend)
        result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
        if ":8000" in result.stdout:
            print("⚠️  Port 8000 is in use (backend)")
            print("   You may need to stop the existing process")
        else:
            print("✅ Port 8000 available (backend)")
        
        # Check port 5173 (frontend)
        if ":5173" in result.stdout:
            print("⚠️  Port 5173 is in use (frontend)")
            print("   You may need to stop the existing process")
        else:
            print("✅ Port 5173 available (frontend)")
        
        return True
    except Exception as e:
        print(f"❌ Error checking ports: {e}")
        return False

def main():
    """Main verification function."""
    print("Legal Companion - Setup Verification")
    print("=" * 50)
    
    # Check all components
    backend_ok = check_backend_env()
    frontend_ok = check_frontend_env()
    services_ok = test_backend_services() if backend_ok else False
    ports_ok = check_ports()
    
    # Summary
    print("\n" + "=" * 50)
    print("VERIFICATION SUMMARY")
    print("=" * 50)
    
    print(f"Backend Environment:  {'✅ PASS' if backend_ok else '❌ FAIL'}")
    print(f"Frontend Environment: {'✅ PASS' if frontend_ok else '❌ FAIL'}")
    print(f"Google Cloud Services: {'✅ PASS' if services_ok else '❌ FAIL'}")
    print(f"Port Availability:    {'✅ PASS' if ports_ok else '❌ FAIL'}")
    
    if all([backend_ok, frontend_ok, services_ok]):
        print("\n🎉 ALL CHECKS PASSED!")
        print("\nReady to start:")
        print("1. Backend:  cd backend && python start_server_simple.py")
        print("2. Frontend: cd frontend && npm run dev")
        print("\nThen visit: http://localhost:5173")
    else:
        print("\n❌ Some checks failed. Please fix the issues above.")
    
    return all([backend_ok, frontend_ok, services_ok])

if __name__ == "__main__":
    main()