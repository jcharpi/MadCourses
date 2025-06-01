#!/usr/bin/env python3
"""
Given any list of skill phrases, print the top‑K matching UW courses
based on cosine similarity of embeddings stored in Supabase.
"""

import os, sys
from typing import List
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client  # supabase‑py v2
from dotenv import load_dotenv

load_dotenv()

# ── config ────────────────────────────────────────────────────────────
SUPABASE_URL       = os.environ["SUPABASE_URL"]
SUPABASE_ANON_PUBLIC_KEY = os.environ["SUPABASE_ANON_PUBLIC_KEY"]
TOP_K              = int(os.getenv("TOP_K", 5))
MODEL_NAME         = "all-mpnet-base-v2"

# ── initialise ────────────────────────────────────────────────────────
sb: Client = create_client(SUPABASE_URL, SUPABASE_ANON_PUBLIC_KEY)
model      = SentenceTransformer(MODEL_NAME)

def get_skill_embeddings(skills: List[str]):
    """Return unit‑norm vectors (lists of floats) for each skill string."""
    return model.encode(skills, normalize_embeddings=True).tolist()

def match(skill: str, vector: list[float]):
    """Call the SQL function we created in step 2."""
    response = (
        sb.rpc("match_courses", {"skill": vector, "k": TOP_K})
          .execute()
    )
    return response.data  # list of rows

# ── main ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python skill_matcher.py \"data analysis\" \"cloud computing\" ...")
        sys.exit(1)

    skills = sys.argv[1:]
    vectors = get_skill_embeddings(skills)

    for skill, vec in zip(skills, vectors):
        print(f"\n🔍  Best courses for “{skill}”")
        for row in match(skill, vec):
            print(f"{row['subject']} {row['level']} - {row['title']} | {row['similarity']:.3f}")
