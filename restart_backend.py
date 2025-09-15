#!/usr/bin/env python3
"""
Restart backend server script.
"""

import subprocess
import sys
import time
import os

def restart_backend():
    """Restart the backend server."""
    print("🔄 Restarting backend server...")
    
    # Kill any existing processes on port 8000
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
    
    # Wait a moment
    time.sleep(2)
    
    # Start the server
    print("🚀 Starting backend server...")
    os.chdir("backend")
    
    try:
        subprocess.run([sys.executable, "start_server_simple.py"])
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")

if __name__ == "__main__":
    restart_backend()