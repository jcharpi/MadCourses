#!/usr/bin/env python3
"""
Start both MadCourses backend and frontend for local development
"""

import subprocess
import sys
import time
import threading
import os
from pathlib import Path

def start_backend():
    """Start the backend server"""
    backend_dir = Path("Backend")
    if not backend_dir.exists():
        print("Error: Backend directory not found!")
        return
    
    os.chdir(backend_dir)
    try:
        print("Starting backend...")
        subprocess.run([sys.executable, "start_backend.py"], check=True)
    except Exception as e:
        print(f"Backend error: {e}")
    finally:
        os.chdir("..")

def start_frontend():
    """Start the frontend server"""
    frontend_dir = Path("Frontend/MadCourses")
    if not frontend_dir.exists():
        print("Error: Frontend directory not found!")
        return
    
    # Wait for backend to start
    time.sleep(3)
    
    os.chdir(frontend_dir)
    try:
        print("Starting frontend...")
        subprocess.run([sys.executable, "start_frontend.py"], check=True)
    except Exception as e:
        print(f"Frontend error: {e}")
    finally:
        os.chdir("../..")

def main():
    print("=" * 60)
    print("MadCourses Full Stack Local Development")
    print("=" * 60)
    print("This will start both backend and frontend servers")
    print("\nBackend: http://localhost:8001")
    print("Frontend: http://localhost:5173")
    print("API Docs: http://localhost:8001/docs")
    print("\nPress Ctrl+C to stop both servers")
    print("-" * 60)
    
    try:
        # Start backend in a separate thread
        backend_thread = threading.Thread(target=start_backend)
        backend_thread.daemon = True
        backend_thread.start()
        
        # Start frontend in main thread
        start_frontend()
        
    except KeyboardInterrupt:
        print("\nStopping servers...")
        sys.exit(0)

if __name__ == "__main__":
    main()