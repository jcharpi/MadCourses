#!/usr/bin/env python3
"""
api.py – Tiny FastAPI wrapper around skill_matcher.py
─────────────────────────────────────────────────────
• Accepts a POST /match request with a list of skill strings + optional filters
• Encodes each skill → vector (Sentence‑Transformers) **once, in memory**
• Calls the Supabase RPC (match_courses) for each vector
• Returns a clean JSON payload that your Svelte frontend can render

Run locally:
    pip install fastapi uvicorn[standard] pydantic           # (once)
    uvicorn api:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator

# ─── Re‑use functionality that already exists in skill_matcher.py ─────────────
#   • get_skill_embeddings(str | list[str]) → list[np.ndarray]
#   • match_courses_rpc(vec, k, subject_contains=…, level_min=…, …) → list[dict]
#     (You implemented these when you built the CLI tool.)
#   • They still open a Supabase client using env vars SUPABASE_URL / KEY.
# -----------------------------------------------------------------------------
from skill_matcher import get_skill_embeddings, match_courses_rpc

app = FastAPI(title="Skill‑to‑Course matcher", version="1.0")


# ────────────────────────────
# ↓  request/response schema  ↓
# ────────────────────────────
class Query(BaseModel):
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

    # sanity checks — make sure min ≤ max if both provided
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
    skill: str
    matches: list  # list[dict[str, Any]]  — straight rows from Supabase


class ResponseModel(BaseModel):
    results: List[SkillMatchBlock]


# ───────────────────────────
# ↓       endpoint         ↓
# ───────────────────────────
@app.post("/match", response_model=ResponseModel)
def match(payload: Query):
    """
    1. Turn each skill phrase → embedding vector.
    2. Query Supabase via RPC for that vector with user‑supplied filters.
    3. Bundle everything into a JSON response.
    """
    try:
        vectors = get_skill_embeddings(payload.skills)       # List[np.ndarray]
    except RuntimeError as e:                                 # e.g. model not found
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
