#!/usr/bin/env python3
"""
Start the MadCourses frontend development server
"""

import subprocess
import sys
import os
from pathlib import Path

def check_dependencies():
    """Check if required files exist"""
    required_files = ["package.json", "svelte.config.js"]
    
    for file in required_files:
        if not Path(file).exists():
            print(f"Error: Required file '{file}' not found!")
            print("Make sure you're running this from the Frontend/MadCourses directory.")
            return False
    
    return True

def check_node_modules():
    """Check if node_modules exists"""
    if not Path("node_modules").exists():
        print("node_modules not found. Installing dependencies...")
        try:
            subprocess.run(["npm", "install"], check=True)
        except subprocess.CalledProcessError:
            print("Error: Failed to install dependencies. Make sure npm is installed.")
            return False
        except FileNotFoundError:
            print("Error: npm not found. Please install Node.js and npm.")
            return False
    
    return True

def main():
    print("=" * 50)
    print("MadCourses Frontend Development Server")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    if not check_node_modules():
        sys.exit(1)
    
    print("Starting SvelteKit development server...")
    print("Frontend will be available at: http://localhost:5173")
    print("Backend should be running at: http://localhost:8000")
    print("\nPress Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        subprocess.run(["npm", "run", "dev"], check=True)
    except KeyboardInterrupt:
        print("\nFrontend server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"Error starting frontend server: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: npm not found. Please install Node.js and npm.")
        sys.exit(1)

if __name__ == "__main__":
    main()