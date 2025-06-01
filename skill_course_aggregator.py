#!/usr/bin/env python3
"""
skill_course_aggregator.py
==========================
Pick the best courses for a handful of skill words.

Key ideas -----------------------------------------------------
• “Embedding model” = a neural net that turns any sentence into a **vector**
  (a long list of numbers, here 768‑long).  Similar meaning between course description vector and skill vector → vectors that closely resemble each other.

• All vectors are **normalised to length 1**, so a dot‑product of two vectors
  is the same as cosine‑similarity (1 ≈ exact match, 0 ≈ unrelated).

• The `@` operator is NumPy’s “matrix multiply”.  With vectors that means:
      a @ b.T   →   dot‑product between a and b.

• We cache course‑embeddings to disk the first time; later runs reload in ms.

Tables to keep in mind
----------------------
row = skill   ·  column = course   →  cell = similarity score (1,000ths).
"""

from pathlib import Path
import csv
import numpy as np
from sentence_transformers import SentenceTransformer

# ── tweak me ────────────────────────────────────────────────────────────────
CSV_PATH   = Path("./courses.csv")
SKILLS     = ["Building athlete analytics dashboards and user interfaces",
"Implementing real-time data processing pipelines",
"Developing RESTful APIs and database schemas",
"Working with sports performance and social media metrics"]
TOP_K      = 5
MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"
# ────────────────────────────────────────────────────────────────────────────


# --------------------------------------------------------------------------- #
# 1) Load titles + descriptions from CSV                                      #
# --------------------------------------------------------------------------- #
def load_courses(csv_path: Path):
    titles, desc = [], []
    with csv_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            titles.append(row["Title"])
            desc.append(row["Description"])
    return titles, desc


# --------------------------------------------------------------------------- #
# 2) Embedding helpers                                                        #
# --------------------------------------------------------------------------- #
def embed(texts, model):
    """Text → unit‑length float32 vectors (shape = (len(texts), 768))."""
    vecs = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    return vecs.astype(np.float32, copy=False)


def cached_course_vecs(desc, model, cache_path: Path):
    """Reuse .npy cache if present, else build once and store."""
    if cache_path.exists():
        return np.load(cache_path)
    vecs = embed(desc, model)
    np.save(cache_path, vecs)
    return vecs


# --------------------------------------------------------------------------- #
# 3) Ranking utilities                                                        #
# --------------------------------------------------------------------------- #
def top_k_per_skill(skill_vecs, course_vecs, k):
    """
    similarities = skill_vecs @ course_vecs.T
      rows   = skills
      cols   = courses
      cells  = cosine similarities

    Return two (n_skill × k) arrays: scores and their course indices.
    """
    sims = skill_vecs @ course_vecs.T
    idx  = np.argpartition(-sims, k - 1, axis=1)[:, :k] # grab k biggest cols
    row  = np.arange(sims.shape[0])[:, None]
    idx  = idx[row, np.argsort(-sims[row, idx])] # order by score
    scr  = sims[row, idx]
    return scr, idx


def rank_by_centroid(skill_vecs, course_vecs):
    """Average all skills → one ‘desired profile’; rank every course vs it."""
    centroid = skill_vecs.mean(axis=0, keepdims=True)
    centroid /= np.linalg.norm(centroid) + 1e-12
    scores   = (centroid @ course_vecs.T)[0]
    return scores.argsort()[::-1], scores


# --------------------------------------------------------------------------- #
# 4) Glue code                                                                #
# --------------------------------------------------------------------------- #
def main():
    titles, descriptions = load_courses(CSV_PATH)

    model       = SentenceTransformer(MODEL_NAME) # download on first run
    course_vecs = cached_course_vecs(
        descriptions, model, CSV_PATH.with_suffix(".npy")
    )
    skill_vecs  = embed(SKILLS, model)

    # A) best courses for each skill separately
    scr, idx = top_k_per_skill(skill_vecs, course_vecs, TOP_K)
    for i, skill in enumerate(SKILLS):
        print(f"\nSkill: {skill!r}")
        for p in range(TOP_K):
            j = int(idx[i, p])
            print(f"  → {titles[j]}  (score {scr[i, p]:.3f})")

    # B) best courses overall (all skills combined)
    order, agg = rank_by_centroid(skill_vecs, course_vecs)
    print(f"\nTop {TOP_K} courses overall:")
    for r in range(TOP_K):
        j = int(order[r])
        print(f"  → {titles[j]}  (centroid_score {agg[j]:.3f})")


if __name__ == "__main__":
    main()
