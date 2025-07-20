#!/usr/bin/env python3
"""
MadCourses Unified Development Server

This script starts both the SvelteKit frontend and provides utilities for
the Python backend API when developing the unified Vercel project structure.

For local development:
1. Frontend runs on port 5173 (SvelteKit dev server)
2. Backend API available at /api/match (served by SvelteKit's dev server)
3. Python dependencies managed in ./api/ directory

Usage:
    python start_unified.py          # Start development server
    python start_unified.py --setup  # Setup database and dependencies
"""

import os
import sys
import subprocess
import argparse
import threading
import time
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    print("[INFO] Checking dependencies...")

    # Check Node.js dependencies
    if not Path("node_modules").exists():
        print("[INSTALL] Installing Node.js dependencies...")
        subprocess.run(["npm", "install"], check=True)
    else:
        print("[OK] Node.js dependencies found")

    # Check Python dependencies in api directory
    api_dir = Path("api")
    if api_dir.exists():
        # Check if we can import the required modules
        original_path = sys.path.copy()
        sys.path.insert(0, str(api_dir.absolute()))
        try:
            import sentence_transformers
            import sklearn
            import numpy
            # Test our custom modules too - use importlib for dynamic imports
            import importlib.util

            # Test skill_matcher_sqlite
            spec = importlib.util.spec_from_file_location(
                "skill_matcher_sqlite",
                api_dir / "skill_matcher_sqlite.py"
            )
            if spec and spec.loader:
                skill_matcher = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(skill_matcher)

            # Test database_setup
            spec = importlib.util.spec_from_file_location(
                "database_setup",
                api_dir / "database_setup.py"
            )
            if spec and spec.loader:
                db_setup = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(db_setup)

            print("[OK] Python dependencies found")
        except ImportError as e:
            print(f"[ERROR] Missing Python dependency: {e}")
            print("[TIP] Install with: pip install -r api/requirements.txt")
            return False
        finally:
            # Restore original path
            sys.path = original_path

    return True

def setup_database():
    """Setup the SQLite database with sample data"""
    print("[DATABASE] Setting up database...")

    api_dir = Path("api")
    if not api_dir.exists():
        print("[ERROR] API directory not found")
        return False

    # Add api directory to Python path
    sys.path.insert(0, str(api_dir.absolute()))

    try:
        # Import from the api directory using importlib
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "database_setup",
            api_dir / "database_setup.py"
        )
        if spec and spec.loader:
            database_setup = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(database_setup)

            create_database = database_setup.create_database
            get_database_stats = database_setup.get_database_stats
        else:
            raise ImportError("Could not load database_setup module")

        # Create database schema
        create_database()
        print("[OK] Database schema created")

        # Show stats
        get_database_stats()

        return True
    except Exception as e:
        print(f"[ERROR] Database setup failed: {e}")
        return False

def start_python_api():
    """Start the Python API server in a separate thread"""
    try:
        print("[API] Starting Python API server on http://localhost:8001...")
        if os.name == 'nt':  # Windows
            subprocess.run("python api_server.py", shell=True, check=True)
        else:  # Unix/Linux/Mac
            subprocess.run([sys.executable, "api_server.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Python API server failed: {e}")
    except KeyboardInterrupt:
        pass  # Exit gracefully when interrupted

def start_dev_server():
    """Start both Python API and SvelteKit development servers"""
    print("[START] Starting unified development server...")
    print("[INFO] Starting Python API server...")
    
    # Start Python API server in background thread
    api_thread = threading.Thread(target=start_python_api, daemon=True)
    api_thread.start()
    
    # Give API server time to start
    print("[INFO] Waiting for Python API server to start...")
    time.sleep(3)
    
    print("[URL] Frontend: http://localhost:5173 (or next available port)")
    print("[API] Python API: http://localhost:8001")
    print("[INFO] Frontend will proxy /api/match requests to Python API")
    print()
    print("Press Ctrl+C to stop both servers")
    print()

    try:
        # Start SvelteKit dev server
        if os.name == 'nt':  # Windows
            subprocess.run("npm run dev", shell=True, check=True)
        else:  # Unix/Linux/Mac
            subprocess.run(["npm", "run", "dev"], check=True)
    except KeyboardInterrupt:
        print("\n[STOP] Development servers stopped")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to start development server: {e}")
        print("[TIP] Try running 'npm run dev' directly in the terminal")

def main():
    parser = argparse.ArgumentParser(description="MadCourses unified development server")
    parser.add_argument("--setup", action="store_true", help="Setup database and check dependencies")
    parser.add_argument("--deps-only", action="store_true", help="Only check dependencies")

    args = parser.parse_args()

    print("MadCourses Unified Development Server")
    print("=" * 50)

    if args.setup or args.deps_only:
        if not check_dependencies():
            sys.exit(1)

        if args.deps_only:
            print("[OK] Dependency check complete")
            return

        if not setup_database():
            sys.exit(1)

        print("[OK] Setup complete!")
        print("[TIP] Run 'python start_unified.py' to start the development server")
        return

    # Normal startup
    if not check_dependencies():
        print("[ERROR] Dependencies missing. Run with --setup to install.")
        sys.exit(1)

    start_dev_server()

if __name__ == "__main__":
    main()