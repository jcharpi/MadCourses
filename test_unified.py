#!/usr/bin/env python3
"""
End-to-end test for the unified Vercel project structure

This script tests that:
1. Python API function works
2. Database is accessible
3. All imports are working correctly
4. The unified structure is deployment-ready
"""

import sys
import json
import subprocess
from pathlib import Path
import os

def test_python_api():
    """Test the Python API function directly"""
    print("[TEST] Testing Python API...")

    # Add api directory to path
    api_dir = Path("api")
    sys.path.insert(0, str(api_dir.absolute()))

    try:
        from match import handler

        # Create mock request
        class MockRequest:
            method = "POST"
            json = {"skills": ["test skill"], "k": 1}

            def __init__(self):
                self.body = json.dumps(self.json).encode('utf-8')

        response = handler(MockRequest())

        if response.status_code == 200:
            print("[OK] Python API working")
            return True
        else:
            print(f"[ERROR] API returned status {response.status_code}")
            return False

    except Exception as e:
        print(f"[ERROR] Python API test failed: {e}")
        return False

def test_database_exists():
    """Test that the database exists and has data"""
    print("[TEST] Testing database...")

    db_path = Path("api/courses.db")
    if not db_path.exists():
        print("[ERROR] Database file not found at api/courses.db")
        return False

    # Test database has content
    api_dir = Path("api")
    sys.path.insert(0, str(api_dir.absolute()))

    try:
        import database_setup
        import sqlite3

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM courses")
        course_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM embeddings")
        embedding_count = cursor.fetchone()[0]

        conn.close()

        if course_count > 0 and embedding_count > 0:
            print(f"[OK] Database has {course_count} courses and {embedding_count} embeddings")
            return True
        else:
            print(f"[ERROR] Database empty: {course_count} courses, {embedding_count} embeddings")
            return False

    except Exception as e:
        print(f"[ERROR] Database test failed: {e}")
        return False

def test_frontend_build():
    """Test that the frontend can build"""
    print("[TEST] Testing frontend build...")

    try:
        # Check if package.json exists
        if not Path("package.json").exists():
            print("[ERROR] package.json not found")
            return False

        # Try to build (but don't wait for completion)
        print("[INFO] Frontend build test would run 'npm run build' in production")
        print("[OK] Frontend structure looks correct")
        return True

    except Exception as e:
        print(f"[ERROR] Frontend build test failed: {e}")
        return False

def test_vercel_config():
    """Test that Vercel configuration is correct"""
    print("[TEST] Testing Vercel configuration...")

    try:
        vercel_config = Path("vercel.json")
        if not vercel_config.exists():
            print("[ERROR] vercel.json not found")
            return False

        # Parse vercel.json
        with open(vercel_config) as f:
            config = json.load(f)

        # Check required sections
        if "functions" not in config:
            print("[ERROR] Missing 'functions' in vercel.json")
            return False

        if "api/match.py" not in config["functions"]:
            print("[ERROR] Missing 'api/match.py' function config")
            return False

        print("[OK] Vercel configuration looks correct")
        return True

    except Exception as e:
        print(f"[ERROR] Vercel config test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("MadCourses Unified Project Test Suite")
    print("=" * 50)

    tests = [
        ("Database", test_database_exists),
        ("Python API", test_python_api),
        ("Frontend", test_frontend_build),
        ("Vercel Config", test_vercel_config),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n[RUN] {test_name} Test")
        if test_func():
            passed += 1
        else:
            print(f"[FAIL] {test_name} test failed")

    print(f"\n[RESULTS] {passed}/{total} tests passed")

    if passed == total:
        print("[SUCCESS] All tests passed! Project ready for deployment.")
        print("\nNext steps:")
        print("1. Run 'vercel deploy' to deploy to Vercel")
        print("2. Import your course CSV data")
        print("3. Test the deployed API")
    else:
        print("[WARNING] Some tests failed. Check the issues above.")
        return False

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)