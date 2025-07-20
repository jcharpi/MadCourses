#!/usr/bin/env python3
"""
Start the MadCourses backend API server for local development
"""

import uvicorn
import os
import sys
from pathlib import Path

def check_dependencies():
    """Check if all required files exist"""
    required_files = ["courses.db", "api.py", "skill_matcher_sqlite.py"]
    
    for file in required_files:
        if not Path(file).exists():
            print(f"Error: Required file '{file}' not found!")
            print("Make sure you're running this from the Backend directory.")
            return False
    
    return True

def main():
    print("=" * 50)
    print("MadCourses Backend Server")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not check_dependencies():
        sys.exit(1)
    
    # Set environment variables
    os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
    
    print("Starting server...")
    print("Server will be available at: http://localhost:8001")
    print("API Documentation: http://localhost:8001/docs")
    print("Health Check: http://localhost:8001/health")
    print("\nPress Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        uvicorn.run(
            "api:app",
            host="127.0.0.1",
            port=8001,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()