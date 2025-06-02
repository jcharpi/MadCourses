#!/usr/bin/env python3
"""
API.PY - FastAPI Wrapper for Skill-to-Course Matching
─────────────────────────────────────────────────────
• Provides REST endpoint for course similarity search
• Leverages functionality from skill_matcher.py
• Returns structured JSON for frontend consumption

Local Execution:
    pip install fastapi uvicorn[standard] pydantic
    uvicorn api:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations
from typing import List, Optional

from fastapi import FastAPI, HTTPException # type: ignore
from pydantic import BaseModel, Field, validator

# ===== INTEGRATION WITH MATCHING LOGIC =====
from skill_matcher import get_skill_embeddings, match_courses_rpc

app = FastAPI(title="Skill‑to‑Course matcher", version="1.0")

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

# ===== API ENDPOINT =====
@app.post("/match", response_model=ResponseModel)
def match(payload: Query):
    """
    Endpoint Workflow:
    1. Convert skills → embedding vectors
    2. Query database with filters
    3. Format results for frontend
    """
    try:
        vectors = get_skill_embeddings(payload.skills)  # List[np.ndarray]
    except RuntimeError as e:  # Handle embedding failures
        raise HTTPException(status_code=500, detail=str(e))

    results: list[SkillMatchBlock] = []

    for skill, vec in zip(payload.skills, vectors, strict=True):
        rows = match_courses_rpc(
            vec,
            k=payload.k,
            subject_contains=payload.subject_contains,
            level_min=payload.level_min,
            level_max=payload.level_max,
            credit_min=payload.credit_min,
            credit_max=payload.credit_max,
            last_taught_ge=payload.last_taught,
        )
        results.append(SkillMatchBlock(skill=skill, matches=rows))

    return ResponseModel(results=results)