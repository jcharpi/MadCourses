#!/usr/bin/env python3
"""
Simple Python API server for local development

This runs a FastAPI server that SvelteKit can proxy to during development.
In production, Vercel handles the Python functions directly.
"""

import sys
import os
from pathlib import Path

# Add api directory to path
api_dir = Path(__file__).parent / "api"
sys.path.insert(0, str(api_dir.absolute()))

# Configure cache
CACHE_DIR = "/tmp/cache"
os.makedirs(CACHE_DIR, exist_ok=True)
os.environ["HF_HOME"] = CACHE_DIR

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

# Import our search functions
from skill_matcher_sqlite import get_skill_embeddings, match_courses

app = FastAPI(title="MadCourses Local API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    skills: List[str]
    k: int = 5
    subject_contains: Optional[str] = None
    level_min: Optional[int] = None
    level_max: Optional[int] = None
    credit_min: Optional[float] = None
    credit_max: Optional[float] = None
    last_taught: Optional[str] = None

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "Local API server running"}

@app.post("/match")
def match_endpoint(query: Query):
    """Course similarity search endpoint"""
    try:
        # Generate embeddings
        vectors = get_skill_embeddings(query.skills)

        # Search for each skill
        results = []
        for skill, vector in zip(query.skills, vectors):
            matches = match_courses(
                vector.tolist(),
                k=query.k,
                subject_contains=query.subject_contains,
                level_min=query.level_min,
                level_max=query.level_max,
                credit_min=query.credit_min,
                credit_max=query.credit_max,
                last_taught_ge=query.last_taught,
            )

            results.append({
                "skill": skill,
                "matches": matches
            })

        return {"results": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("Starting MadCourses Local API Server...")
    print("API available at: http://localhost:8001")
    print("Health check: http://localhost:8001/health")
    print("Search endpoint: http://localhost:8001/match")
    print()
    uvicorn.run(app, host="127.0.0.1", port=8001)