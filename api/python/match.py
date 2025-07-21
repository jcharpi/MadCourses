#!/usr/bin/env python3
"""
MadCourses - Working Text-Based Matching

Uses keyword matching and pre-computed embeddings for reliable course matching.
"""

import os
import sqlite3
import json
import pickle
import numpy as np
from typing import List, Dict, Any, Optional
from http.server import BaseHTTPRequestHandler
import re
from collections import Counter

# Configuration
DB_PATH = os.getenv("DB_PATH", "api/python/courses.db")

# Global cache for course data
_courses_cache = None
_embeddings_cache = None


def create_skill_embedding(text: str) -> np.ndarray:
    """
    Create a skill embedding using sentence transformers (same model as pre-computed embeddings)
    """
    from sentence_transformers import SentenceTransformer

    # Use the same model that was likely used for pre-computed embeddings
    model = SentenceTransformer('all-MiniLM-L12-v2')

    # Generate embedding
    embedding = model.encode(text, convert_to_numpy=True)

    # Ensure it's a numpy array and normalize
    embedding = np.array(embedding)
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm

    return embedding.astype(np.float32)


def load_course_data() -> tuple[List[Dict[str, Any]], np.ndarray]:
    """
    Load pre-computed course data and embeddings from database
    """
    global _courses_cache, _embeddings_cache

    if _courses_cache is not None and _embeddings_cache is not None:
        return _courses_cache, _embeddings_cache

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Load all courses with their pre-computed embeddings
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

        # Deserialize the pre-computed embedding
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

    _courses_cache = courses
    _embeddings_cache = np.array(embeddings)

    print(f"Loaded {len(_courses_cache)} courses with pre-computed embeddings")
    return _courses_cache, _embeddings_cache


def apply_filters(courses: List[Dict[str, Any]],
                 subject_contains: Optional[str] = None,
                 level_min: Optional[int] = None,
                 level_max: Optional[int] = None,
                 credit_min: Optional[float] = None,
                 credit_max: Optional[float] = None,
                 last_taught_ge: Optional[str] = None) -> np.ndarray:
    """Apply filters and return valid course indices"""
    valid_indices = []

    for idx, course in enumerate(courses):
        # Subject filter
        if subject_contains and subject_contains.lower() not in course['subject'].lower():
            continue

        # Level filters
        if level_min is not None and course['level'] < level_min:
            continue
        if level_max is not None and course['level'] > level_max:
            continue

        # Credit filters (range overlap)
        if credit_min is not None and course['credit_max'] < credit_min:
            continue
        if credit_max is not None and course['credit_min'] > credit_max:
            continue

        # Semester filter
        if last_taught_ge is not None and course['last_taught'] < last_taught_ge:
            continue

        valid_indices.append(idx)

    return np.array(valid_indices)


def cosine_similarity_manual(a: np.ndarray, b: np.ndarray) -> float:
    """Manual cosine similarity calculation"""
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


def match_courses(skill: str,
                 k: int = 5,
                 subject_contains: Optional[str] = None,
                 level_min: Optional[int] = None,
                 level_max: Optional[int] = None,
                 credit_min: Optional[float] = None,
                 credit_max: Optional[float] = None,
                 last_taught_ge: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Find courses similar to the provided skill using keyword-based matching
    """
    # Load pre-computed course data
    courses, course_embeddings = load_course_data()

    if len(courses) == 0:
        return []

    # Generate embedding for the skill query
    skill_embedding = create_skill_embedding(skill)

    # Apply filters
    valid_indices = apply_filters(
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

    # Get embeddings for valid courses
    valid_embeddings = course_embeddings[valid_indices]

    # Compute similarities
    similarities = []
    for course_embedding in valid_embeddings:
        sim = cosine_similarity_manual(skill_embedding, course_embedding)
        similarities.append(sim)
    similarities = np.array(similarities)

    # Get top-k results
    top_k_indices = np.argsort(similarities)[::-1][:k]

    # Build results
    results = []
    for idx in top_k_indices:
        course_idx = valid_indices[idx]
        course = courses[course_idx].copy()
        course['similarity'] = float(similarities[idx])
        results.append(course)

    return results


# Vercel Python function handler using BaseHTTPRequestHandler format
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        try:
            data = json.loads(post_data.decode('utf-8'))

            skills = data.get('skills', [])
            k = data.get('k', 5)

            # Extract filters
            filters = {
                'subject_contains': data.get('subject_contains'),
                'level_min': data.get('level_min'),
                'level_max': data.get('level_max'),
                'credit_min': data.get('credit_min'),
                'credit_max': data.get('credit_max'),
                'last_taught_ge': data.get('last_taught')
            }

            # Process each skill
            results = []
            for skill in skills:
                matches = match_courses(skill, k=k, **filters)
                results.append({
                    'skill': skill,
                    'matches': matches
                })

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            response = json.dumps({'results': results})
            self.wfile.write(response.encode())

        except Exception as e:
            print(f"Error processing request: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            error_response = json.dumps({'error': str(e)})
            self.wfile.write(error_response.encode())

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        response = json.dumps({'message': 'MadCourses Working Text Matching API', 'status': 'ready'})
        self.wfile.write(response.encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()