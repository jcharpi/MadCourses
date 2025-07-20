#!/usr/bin/env python3
"""
MadCourses Search Engine - SQLite-based semantic course search

This module provides semantic similarity search for UW-Madison courses using:
- SQLite database for course metadata and pre-computed embeddings
- SentenceTransformer for generating query embeddings
- In-memory vector search using cosine similarity
- Advanced filtering with proper credit range handling

Key Features:
- Supports courses with variable credit ranges (e.g., "1-6" credits)
- Fast in-memory similarity search after initial loading
- Comprehensive filtering by subject, level, credits, semester
- Optimized for both local development and serverless deployment

Architecture:
    User Query → Embedding Generation → Vector Similarity Search → Filtering → Results

Usage:
    # As a library (used by API)
    from skill_matcher_sqlite import get_skill_embeddings, match_courses

    # As a CLI tool
    python skill_matcher_sqlite.py "machine learning" --k 5 --subject-contains "COMP SCI"
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import numpy as np
import pickle
from typing import List, Optional, Dict, Any, Tuple

# Configure cache directory for ML models (important for serverless)
CACHE_DIR = "/tmp/cache"
os.makedirs(CACHE_DIR, exist_ok=True)
os.environ["HF_HOME"] = CACHE_DIR
os.environ["TRANSFORMERS_CACHE"] = CACHE_DIR

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# ===== CONFIGURATION =====
load_dotenv()
TOP_K_DEFAULT: int = int(os.getenv("TOP_K", 5))
MODEL_NAME: str = os.getenv("MODEL", "all-MiniLM-L12-v2")
DB_PATH: str = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "courses.db"))

# ===== GLOBAL STATE (for performance optimization) =====
# These are loaded once and cached in memory for fast access
_model: Optional[SentenceTransformer] = None
_courses: List[Dict[str, Any]] = []
_embeddings: Optional[np.ndarray] = None


def _load_model() -> SentenceTransformer:
    """Load and cache the SentenceTransformer model"""
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def _load_data() -> Tuple[List[Dict[str, Any]], np.ndarray]:
    """Load and cache course data and embeddings from SQLite database"""
    global _courses, _embeddings

    if not _courses:  # Only load if not already cached
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Load all courses with their embeddings
        cursor.execute("""
        SELECT c.id, c.subject, c.level, c.title, c.credit_amount,
               c.credit_min, c.credit_max, c.last_taught, c.description, e.embedding
        FROM courses c
        JOIN embeddings e ON c.id = e.course_id
        ORDER BY c.id
        """)

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return [], np.array([])

        courses = []
        embeddings = []

        for row in rows:
            course_id, subject, level, title, credit_amount, credit_min, credit_max, last_taught, description, embedding_bytes = row

            # Deserialize the stored embedding
            embedding = pickle.loads(embedding_bytes)

            # Store course metadata
            course_data = {
                'id': course_id,
                'subject': subject,
                'level': level,
                'title': title,
                'credit_amount': credit_amount,
                'credit_min': credit_min,
                'credit_max': credit_max,
                'last_taught': last_taught,
                'description': description
            }

            courses.append(course_data)
            embeddings.append(embedding)

        _courses = courses
        _embeddings = np.array(embeddings)

        print(f"Loaded {len(_courses)} courses with embeddings")

    # Type assertion: _embeddings is guaranteed to be non-None after the above logic
    assert _embeddings is not None, "Embeddings should be loaded at this point"
    return _courses, _embeddings


def get_skill_embeddings(skills: List[str]) -> List[np.ndarray]:
    """
    Generate embeddings for input skill strings.

    Args:
        skills: List of skill descriptions to convert to embeddings

    Returns:
        List of numpy arrays containing the normalized embeddings
    """
    model = _load_model()
    embeddings = model.encode(skills, normalize_embeddings=True)
    # Convert tensors to numpy arrays
    return [np.array(embedding, dtype=np.float32) for embedding in embeddings]


def _apply_filters(courses: List[Dict[str, Any]],
                  subject_contains: Optional[str] = None,
                  level_min: Optional[int] = None,
                  level_max: Optional[int] = None,
                  credit_min: Optional[float] = None,
                  credit_max: Optional[float] = None,
                  last_taught_ge: Optional[str] = None) -> np.ndarray:
    """
    Apply filters to course list and return indices of valid courses.

    Credit filtering uses range overlap logic:
    - A course with credits "1-6" matches searches for 1, 3, or 6 credits
    - A course with credits "3" only matches searches that include 3 credits

    Args:
        courses: List of course dictionaries
        subject_contains: Filter by subject code (case-insensitive substring)
        level_min: Minimum course level (inclusive)
        level_max: Maximum course level (inclusive)
        credit_min: Minimum credits (uses range overlap)
        credit_max: Maximum credits (uses range overlap)
        last_taught_ge: Minimum semester (e.g., "S25")

    Returns:
        Numpy array of valid course indices
    """
    valid_indices = []

    for idx, course in enumerate(courses):
        # Subject filter (case-insensitive substring match)
        if subject_contains and subject_contains.lower() not in course['subject'].lower():
            continue

        # Level filters (simple range check)
        if level_min is not None and course['level'] < level_min:
            continue
        if level_max is not None and course['level'] > level_max:
            continue

        # Credit filters (range overlap logic)
        # Course credit range: [credit_min, credit_max]
        # Search credit range: [credit_min_filter, credit_max_filter]
        # Overlap if: course_max >= search_min AND course_min <= search_max
        if credit_min is not None and course['credit_max'] < credit_min:
            continue  # Course's max credits are below the search minimum
        if credit_max is not None and course['credit_min'] > credit_max:
            continue  # Course's min credits are above the search maximum

        # Semester filter (string comparison works for format "S25", "F24", etc.)
        if last_taught_ge is not None and course['last_taught'] < last_taught_ge:
            continue

        valid_indices.append(idx)

    return np.array(valid_indices)


def match_courses(vector: List[float],
                 *,
                 k: int = TOP_K_DEFAULT,
                 subject_contains: Optional[str] = None,
                 level_min: Optional[int] = None,
                 level_max: Optional[int] = None,
                 credit_min: Optional[float] = None,
                 credit_max: Optional[float] = None,
                 last_taught_ge: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Find courses similar to the provided skill vector using semantic search.

    This function performs the core similarity search by:
    1. Loading course data and embeddings (cached after first call)
    2. Applying filters to get a subset of valid courses
    3. Computing cosine similarity between the query and valid course embeddings
    4. Returning the top-k matches ranked by similarity score

    Args:
        vector: Skill embedding as a list of floats
        k: Number of top results to return
        subject_contains: Filter by subject code (case-insensitive)
        level_min: Minimum course level (inclusive)
        level_max: Maximum course level (inclusive)
        credit_min: Minimum credits (uses range overlap)
        credit_max: Maximum credits (uses range overlap)
        last_taught_ge: Minimum semester taught

    Returns:
        List of course dictionaries with similarity scores, ranked by similarity
    """
    # Load data (cached after first call)
    courses, embeddings = _load_data()

    if len(courses) == 0:
        return []

    # Apply filters to get valid course indices
    valid_indices = _apply_filters(
        courses,
        subject_contains=subject_contains,
        level_min=level_min,
        level_max=level_max,
        credit_min=credit_min,
        credit_max=credit_max,
        last_taught_ge=last_taught_ge
    )

    if len(valid_indices) == 0:
        return []

    # Get embeddings for valid courses only
    valid_embeddings = embeddings[valid_indices]

    # Compute cosine similarities
    query_vector = np.array(vector).reshape(1, -1)
    similarities = cosine_similarity(query_vector, valid_embeddings)[0]

    # Get top-k results sorted by similarity (descending)
    top_k_indices = np.argsort(similarities)[::-1][:k]

    # Build result list with similarity scores
    results = []
    for idx in top_k_indices:
        course_idx = valid_indices[idx]
        course = courses[course_idx].copy()
        course['similarity'] = float(similarities[idx])
        results.append(course)

    return results


# ===== COMMAND LINE INTERFACE =====

def parse_args() -> argparse.Namespace:
    """Parse command line arguments for CLI usage"""
    parser = argparse.ArgumentParser(
        description="Search for courses similar to provided skills",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python skill_matcher_sqlite.py "machine learning"
  python skill_matcher_sqlite.py "data analysis" --k 3 --subject-contains "STAT"
  python skill_matcher_sqlite.py "programming" --level-min 300 --credit-min 3
        """
    )

    parser.add_argument("skills", nargs="+", help="Skill phrases to search for")
    parser.add_argument("--k", type=int, default=TOP_K_DEFAULT, help="Number of top results per skill")
    parser.add_argument("--subject-contains", help="Filter by subject code (case-insensitive)")
    parser.add_argument("--level-min", type=int, help="Minimum course level")
    parser.add_argument("--level-max", type=int, help="Maximum course level")
    parser.add_argument("--credit-min", type=float, help="Minimum credits")
    parser.add_argument("--credit-max", type=float, help="Maximum credits")
    parser.add_argument("--last-taught", help="Minimum semester (e.g., S25)")

    return parser.parse_args()


def main():
    """Main CLI entry point"""
    args = parse_args()

    # Generate embeddings for all input skills
    print("Generating embeddings...")
    vectors = get_skill_embeddings(args.skills)

    # Search for each skill
    for skill, vector in zip(args.skills, vectors):
        print(f"\nBest matches for '{skill}' (Top {args.k})")
        print("-" * 50)

        results = match_courses(
            vector.tolist(),
            k=args.k,
            subject_contains=args.subject_contains,
            level_min=args.level_min,
            level_max=args.level_max,
            credit_min=args.credit_min,
            credit_max=args.credit_max,
            last_taught_ge=args.last_taught,
        )

        if not results:
            print("No courses found matching your criteria.")
            continue

        for i, course in enumerate(results, 1):
            print(f"{i:2d}. {course['subject']} {course['level']} - {course['title']}")
            print(f"    Credits: {course['credit_amount']}, Last taught: {course['last_taught']}")
            print(f"    Similarity: {course['similarity']:.3f}")


if __name__ == "__main__":
    main()