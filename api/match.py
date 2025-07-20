#!/usr/bin/env python3
"""
MadCourses Vercel API - Serverless function for course similarity search

This is a Vercel serverless function that provides the same functionality as
the standalone FastAPI server, but optimized for serverless deployment.

Vercel Function Signature:
    - Must have a handler function that accepts (request)
    - Returns a Response object
    - Automatically handles HTTP routing

Endpoint: POST /api/match
"""

from __future__ import annotations
import json
import os
import sys
from typing import List, Optional, Dict, Any

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure cache directory for serverless environment
CACHE_DIR = "/tmp/cache"
os.makedirs(CACHE_DIR, exist_ok=True)
os.environ["HF_HOME"] = CACHE_DIR
os.environ["TRANSFORMERS_CACHE"] = CACHE_DIR

try:
    from skill_matcher_sqlite import get_skill_embeddings, match_courses
except ImportError as e:
    print(f"Import error: {e}")
    # This will help debug import issues in Vercel logs
    raise

# ===== REQUEST VALIDATION =====

def validate_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and sanitize the incoming request data.

    Args:
        data: Raw request JSON data

    Returns:
        Validated and cleaned request parameters

    Raises:
        ValueError: If validation fails
    """
    # Required field
    if 'skills' not in data or not isinstance(data['skills'], list):
        raise ValueError("'skills' field is required and must be a list")

    if not data['skills']:
        raise ValueError("'skills' list cannot be empty")

    # Validate each skill is a string
    for skill in data['skills']:
        if not isinstance(skill, str) or not skill.strip():
            raise ValueError("All skills must be non-empty strings")

    # Optional parameters with defaults and validation
    k = data.get('k', 5)
    if not isinstance(k, int) or k < 1 or k > 10:
        raise ValueError("'k' must be an integer between 1 and 10")

    # Level filters
    level_min = data.get('level_min')
    level_max = data.get('level_max')
    if level_min is not None and (not isinstance(level_min, int) or level_min < 0):
        raise ValueError("'level_min' must be a non-negative integer")
    if level_max is not None and (not isinstance(level_max, int) or level_max < 0):
        raise ValueError("'level_max' must be a non-negative integer")
    if level_min is not None and level_max is not None and level_max < level_min:
        raise ValueError("'level_max' must be >= 'level_min'")

    # Credit filters
    credit_min = data.get('credit_min')
    credit_max = data.get('credit_max')
    if credit_min is not None and (not isinstance(credit_min, (int, float)) or credit_min < 0):
        raise ValueError("'credit_min' must be a non-negative number")
    if credit_max is not None and (not isinstance(credit_max, (int, float)) or credit_max < 0):
        raise ValueError("'credit_max' must be a non-negative number")
    if credit_min is not None and credit_max is not None and credit_max < credit_min:
        raise ValueError("'credit_max' must be >= 'credit_min'")

    # Subject filter
    subject_contains = data.get('subject_contains')
    if subject_contains is not None and not isinstance(subject_contains, str):
        raise ValueError("'subject_contains' must be a string")

    # Semester filter
    last_taught = data.get('last_taught')
    if last_taught is not None:
        if not isinstance(last_taught, str):
            raise ValueError("'last_taught' must be a string")
        # Basic format validation for semester codes like "F24", "S25"
        if len(last_taught) != 3 or last_taught[0] not in 'FSU' or not last_taught[1:].isdigit():
            raise ValueError("'last_taught' must follow format 'F24', 'S25', etc.")

    return {
        'skills': [skill.strip() for skill in data['skills']],
        'k': k,
        'subject_contains': subject_contains,
        'level_min': level_min,
        'level_max': level_max,
        'credit_min': credit_min,
        'credit_max': credit_max,
        'last_taught': last_taught
    }


def create_response(status_code: int, data: Any = None, error: Optional[str] = None):
    """
    Create a standardized HTTP response for Vercel.

    Args:
        status_code: HTTP status code
        data: Response data (for success responses)
        error: Error message (for error responses)

    Returns:
        Response object compatible with Vercel
    """
    from http import HTTPStatus

    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
    }

    if error:
        body = {'error': error}
    else:
        body = data or {}

    class VercelResponse:
        def __init__(self, status_code, headers, body):
            self.status_code = status_code
            self.headers = headers
            self.body = json.dumps(body)

    return VercelResponse(status_code, headers, body)


# ===== MAIN HANDLER FUNCTION =====

def handler(request):
    """
    Main Vercel serverless function handler.

    This function is called by Vercel for each HTTP request to /api/match.
    It processes the request, performs the course search, and returns results.

    Args:
        request: Vercel request object containing method, body, etc.

    Returns:
        Response object with status code, headers, and JSON body
    """

    # Handle CORS preflight requests
    if request.method == 'OPTIONS':
        return create_response(200)

    # Only accept POST requests
    if request.method != 'POST':
        return create_response(405, error="Method not allowed. Use POST.")

    try:
        # Parse request body
        try:
            if hasattr(request, 'json'):
                # Vercel provides parsed JSON
                data = request.json
            else:
                # Parse JSON from raw body
                body = request.body
                if isinstance(body, bytes):
                    body = body.decode('utf-8')
                data = json.loads(body)
        except json.JSONDecodeError:
            return create_response(400, error="Invalid JSON in request body")

        # Validate request parameters
        try:
            params = validate_request(data)
        except ValueError as e:
            return create_response(400, error=str(e))

        # Generate embeddings for input skills
        try:
            vectors = get_skill_embeddings(params['skills'])
        except Exception as e:
            return create_response(500, error=f"Failed to generate embeddings: {str(e)}")

        # Perform search for each skill
        results = []
        for skill, vector in zip(params['skills'], vectors):
            try:
                matches = match_courses(
                    vector.tolist(),
                    k=params['k'],
                    subject_contains=params['subject_contains'],
                    level_min=params['level_min'],
                    level_max=params['level_max'],
                    credit_min=params['credit_min'],
                    credit_max=params['credit_max'],
                    last_taught_ge=params['last_taught']
                )

                results.append({
                    'skill': skill,
                    'matches': matches
                })

            except Exception as e:
                return create_response(500, error=f"Search failed for skill '{skill}': {str(e)}")

        # Return successful response
        return create_response(200, {'results': results})

    except Exception as e:
        # Catch-all for unexpected errors
        return create_response(500, error=f"Internal server error: {str(e)}")


# ===== VERCEL ENTRY POINT =====

# Vercel automatically imports this file and calls the handler function
# The function name must match the filename (match.py -> handler function)