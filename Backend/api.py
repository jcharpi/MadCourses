#!/usr/bin/env python3
"""
MadCourses API - FastAPI server for course similarity search

This API provides semantic search capabilities for UW-Madison courses using:
- SQLite database with pre-computed embeddings
- In-memory vector similarity search
- Advanced filtering (subject, level, credits, semester)
- Proper credit range handling (e.g., "1-6" credits matches both 1 and 6 credit searches)

Architecture:
    Frontend (SvelteKit) → API Server (FastAPI) → SQLite Database
    
Endpoints:
    GET  /health - Health check
    GET  /docs   - API documentation  
    POST /match  - Course similarity search

Local Development:
    python start_backend.py
    # Server runs on http://localhost:8001
"""

from __future__ import annotations
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator

# Import our custom search engine
from skill_matcher_sqlite import get_skill_embeddings, match_courses

# Initialize FastAPI application
app = FastAPI(
    title="MadCourses API",
    version="2.0", 
    description="UW-Madison Course Similarity Search with SQLite",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ===== REQUEST/RESPONSE SCHEMAS =====
class Query(BaseModel):
    """Request payload structure for /match endpoint"""
    skills: List[str] = Field(..., example=["data analysis", "creative writing"])
    k: int = Field(5, ge=1, le=10, description="Top‑k rows per skill (1-10)")
    subject_contains: Optional[str] = Field(
        None, example="ACCT", description="Case‑insensitive substring"
    )
    level_min: Optional[int] = Field(None, ge=0)
    level_max: Optional[int] = Field(None, ge=0)
    credit_min: Optional[float] = Field(None, ge=0)
    credit_max: Optional[float] = Field(None, ge=0)
    last_taught: Optional[str] = Field(
        None, pattern=r"^[FSU]\d{2}$", example="S25",
        description="Semester code: F, S, or U plus two‑digit year"
    )

    # Validation: ensure min ≤ max when both provided
    @validator("level_max")
    def _level_range(cls, v, values):
        if v is not None and values.get("level_min") is not None and v < values["level_min"]:
            raise ValueError("level_max must be ≥ level_min")
        return v

    @validator("credit_max")
    def _credit_range(cls, v, values):
        if v is not None and values.get("credit_min") is not None and v < values["credit_min"]:
            raise ValueError("credit_max must be ≥ credit_min")
        return v

class SkillMatchBlock(BaseModel):
    """Response block for a single skill's matches"""
    skill: str
    matches: list  # Raw course data from Supabase

class ResponseModel(BaseModel):
    """Top-level API response structure"""
    results: List[SkillMatchBlock]

# ===== API ENDPOINTS =====

@app.get("/health")
def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns:
        dict: Simple status message indicating the API is running
    """
    return {"status": "healthy", "message": "MadCourses API is running"}


@app.get("/")
def root():
    """
    Root endpoint that provides API information and navigation links.
    
    Returns:
        dict: API info with links to documentation and health check
    """
    return {
        "message": "MadCourses API", 
        "docs": "/docs", 
        "health": "/health",
        "version": "2.0"
    }


@app.post("/match", response_model=ResponseModel)
def match(payload: Query):
    """
    Find courses similar to the provided skills using semantic search.
    
    This endpoint performs vector similarity search against pre-computed course
    embeddings. It supports advanced filtering by subject, level, credits, and
    semester. Credit filtering properly handles course credit ranges (e.g., a 
    course offering "1-6" credits will match searches for 1, 3, or 6 credits).
    
    Process:
    1. Convert input skills to embedding vectors using SentenceTransformer
    2. Perform similarity search against stored course embeddings  
    3. Apply filters (subject, level, credits, semester)
    4. Return top-k matches per skill ranked by cosine similarity
    
    Args:
        payload (Query): Search parameters including skills and filters
        
    Returns:
        ResponseModel: Results containing matching courses for each skill
        
    Raises:
        HTTPException: 500 if embedding generation or search fails
    """
    # Step 1: Generate embeddings for all input skills
    try:
        vectors = get_skill_embeddings(payload.skills)
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate embeddings: {str(e)}"
        )

    # Step 2: Search for matches for each skill
    results: List[SkillMatchBlock] = []
    
    for skill, vector in zip(payload.skills, vectors, strict=True):
        try:
            # Perform similarity search with filtering
            matches = match_courses(
                vector.tolist(),
                k=payload.k,
                subject_contains=payload.subject_contains,
                level_min=payload.level_min,
                level_max=payload.level_max,
                credit_min=payload.credit_min,
                credit_max=payload.credit_max,
                last_taught_ge=payload.last_taught,
            )
            
            # Add results for this skill
            results.append(SkillMatchBlock(skill=skill, matches=matches))
            
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Search failed for skill '{skill}': {str(e)}"
            )

    return ResponseModel(results=results)