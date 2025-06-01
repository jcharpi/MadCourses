#!/usr/bin/env python3
"""
skill_matcher.py – Query UW‑Madison courses by semantic similarity.

This version pushes *all* filtering into the Postgres function
`match_courses` (updated with extra parameters) and calls it via
Supabase RPC.  Compatible with supabase‑py v2.
"""

from __future__ import annotations

import argparse
import os
from typing import List, Optional

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from supabase import Client, create_client

# ─── ENV & CONSTANTS ────────────────────────────────────────────────────
load_dotenv()
SUPABASE_URL: str = os.environ["SUPABASE_URL"]
SUPABASE_KEY: str = os.environ["SUPABASE_ANON_PUBLIC_KEY"]
TOP_K_SQL_DEFAULT: int = int(os.getenv("TOP_K", 5))

# ─── GLOBALS ────────────────────────────────────────────────────────────
sb: Client = create_client(SUPABASE_URL, SUPABASE_KEY)  # supabase‑py v2
model: SentenceTransformer = SentenceTransformer("all-mpnet-base-v2")

# ─── EMBEDDING ──────────────────────────────────────────────────────────
def get_skill_embeddings(skills: List[str]) -> List[list[float]]:
    """Return 768‑float, unit‑norm vectors for each skill string."""
    print(model.encode(skills, normalize_embeddings=True).tolist())
    return model.encode(skills, normalize_embeddings=True).tolist()

# ─── RPC CALL ───────────────────────────────────────────────────────────
def match_courses_rpc(
    vector: list[float],
    *,
    k: int = TOP_K_SQL_DEFAULT,
    subject_contains: Optional[str] = None,
    level_min: Optional[int] = None,
    level_max: Optional[int] = None,
    credit_min: Optional[float] = None,
    credit_max: Optional[float] = None,
    last_taught_ge: Optional[str] = None,
) -> list[dict]:
    """Invoke the `match_courses` SQL function via Supabase RPC."""
    payload = {
        "skill": vector,
        "k": k,
        **{
            key: value
            for key, value in {
                "subject_contains": subject_contains,
                "level_min": level_min,
                "level_max": level_max,
                "credit_min": credit_min,
                "credit_max": credit_max,
                "last_taught_ge": last_taught_ge,
            }.items()
            if value is not None
        },
    }

    try:
        resp = sb.rpc("match_courses", payload).execute()  # SingleAPIResponse
    except Exception as exc:  # httpx.HTTPStatusError or connection issues
        raise RuntimeError(f"Supabase RPC failed: {exc}") from exc
    return resp.data or []

# ─── CLI PARSING ────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Return the courses most similar to each SKILL phrase."
    )
    p.add_argument("skills", nargs="+", help="Skill phrases to search for")
    p.add_argument("--k", type=int, default=TOP_K_SQL_DEFAULT, help="Top‑k rows")

    p.add_argument("--subject-contains", dest="subject_contains")
    p.add_argument("--level-min", type=int, dest="level_min")
    p.add_argument("--level-max", type=int, dest="level_max")
    p.add_argument("--credit-min", type=float, dest="credit_min")
    p.add_argument("--credit-max", type=float, dest="credit_max")
    p.add_argument(
        "--last-taught",
        dest="last_taught",
        help="Semester code like F23, S24, U24 (≥ filter)",
    )
    return p.parse_args()

# ─── MAIN ───────────────────────────────────────────────────────────────
def main() -> None:
    args = parse_args()
    vectors = get_skill_embeddings(args.skills)

    for skill, vec in zip(args.skills, vectors):
        print(f"\n🔍 Best matches for “{skill}” (Top {args.k})")
        rows = match_courses_rpc(
            vec,
            k=args.k,
            subject_contains=args.subject_contains,
            level_min=args.level_min,
            level_max=args.level_max,
            credit_min=args.credit_min,
            credit_max=args.credit_max,
            last_taught_ge=args.last_taught,
        )

        if not rows:
            print("No courses met your criteria.")
            continue

        for r in rows:
            print(
                f"{r['subject']} {r['level']} — {r['title']} | "
                f"Credits: {r['credit_amount']}, Last taught: {r['last_taught']} | "
                f"{r['similarity']:.3f}"
            )

if __name__ == "__main__":
    main()
