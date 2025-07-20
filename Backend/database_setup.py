"""
MadCourses Database Setup - SQLite database initialization and data import

This module provides utilities for setting up the MadCourses SQLite database:
- Creates the database schema for courses and embeddings
- Imports course data from CSV files  
- Generates and stores vector embeddings for semantic search
- Handles credit ranges properly (e.g., "1-6" credits stored as min=1, max=6)

Key Features:
- Supports variable credit amounts and credit ranges
- Generates 384-dimensional embeddings using SentenceTransformer
- Optimized schema with indexes for fast querying
- Batch processing for efficient embedding generation

Usage:
    # Create database and import data
    python database_setup.py
    
    # Or programmatically
    from database_setup import create_database, import_csv_to_database
    create_database()
    import_csv_to_database("courses.csv")
"""

import sqlite3
import csv
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
import os
from typing import List, Dict, Any


def create_database(db_path: str = "courses.db"):
    """Create the SQLite database with the required schema"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create courses table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT NOT NULL,
        level INTEGER NOT NULL,
        title TEXT NOT NULL,
        credit_amount TEXT NOT NULL,  -- Store as text to preserve ranges like "1-6"
        credit_min REAL NOT NULL,     -- Minimum credits for filtering
        credit_max REAL NOT NULL,     -- Maximum credits for filtering
        last_taught TEXT NOT NULL,
        description TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create embeddings table (store as BLOB for efficiency)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS embeddings (
        course_id INTEGER PRIMARY KEY,
        embedding BLOB NOT NULL,
        FOREIGN KEY(course_id) REFERENCES courses(id)
    )
    """)
    
    # Create indexes for better query performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_subject ON courses(subject)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_level ON courses(level)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_last_taught ON courses(last_taught)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_credit_min ON courses(credit_min)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_credit_max ON courses(credit_max)")
    
    conn.commit()
    conn.close()
    print(f"Database created successfully at {db_path}")


def import_csv_to_database(csv_path: str, db_path: str = "courses.db"):
    """Import course data from CSV file to SQLite database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    with open(csv_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        
        courses_data = []
        for row in csv_reader:
            # Handle variable credit amounts properly
            credit_str = row.get('credit_amount', '0').strip()
            
            if '-' in credit_str:
                # Handle ranges like '1-6'
                try:
                    parts = credit_str.split('-')
                    credit_min = float(parts[0])
                    credit_max = float(parts[1])
                except:
                    credit_min = credit_max = 3.0  # Default
            else:
                try:
                    credit_amount = float(credit_str)
                    credit_min = credit_max = credit_amount
                except:
                    credit_min = credit_max = 3.0  # Default
            
            course_data = (
                row.get('subject', ''),
                int(row.get('level', 0)) if row.get('level') else 0,
                row.get('title', ''),
                credit_str,  # Store original string
                credit_min,  # Minimum for filtering
                credit_max,  # Maximum for filtering
                row.get('last_taught', ''),
                row.get('description', '')
            )
            courses_data.append(course_data)
    
    cursor.executemany("""
    INSERT INTO courses (subject, level, title, credit_amount, credit_min, credit_max, last_taught, description)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, courses_data)
    
    conn.commit()
    rows_inserted = cursor.rowcount
    conn.close()
    
    print(f"Successfully imported {rows_inserted} courses from {csv_path}")
    return rows_inserted


def generate_and_store_embeddings(db_path: str = "courses.db", model_name: str = "all-MiniLM-L12-v2"):
    """Generate embeddings for all courses and store them in the database"""
    print(f"Loading SentenceTransformer model: {model_name}")
    model = SentenceTransformer(model_name)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all courses
    cursor.execute("SELECT id, title, description FROM courses")
    courses = cursor.fetchall()
    
    print(f"Generating embeddings for {len(courses)} courses...")
    
    embeddings_data = []
    for course_id, title, description in courses:
        # Combine title and description for embedding
        text = f"{title}. {description}".strip()
        
        # Generate embedding
        embedding = model.encode(text, normalize_embeddings=True)
        
        # Convert to bytes for storage
        embedding_bytes = pickle.dumps(embedding.astype(np.float32))
        
        embeddings_data.append((course_id, embedding_bytes))
    
    # Store embeddings in database
    cursor.executemany("""
    INSERT OR REPLACE INTO embeddings (course_id, embedding)
    VALUES (?, ?)
    """, embeddings_data)
    
    conn.commit()
    conn.close()
    
    print(f"Successfully generated and stored embeddings for {len(courses)} courses")


def load_embeddings_from_database(db_path: str = "courses.db") -> tuple:
    """Load all embeddings from database for in-memory search"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT c.id, c.subject, c.level, c.title, c.credit_amount, c.credit_min, c.credit_max, c.last_taught, c.description, e.embedding
    FROM courses c
    JOIN embeddings e ON c.id = e.course_id
    ORDER BY c.id
    """)
    
    results = cursor.fetchall()
    conn.close()
    
    if not results:
        return [], np.array([])
    
    courses = []
    embeddings = []
    
    for row in results:
        course_id, subject, level, title, credit_amount, credit_min, credit_max, last_taught, description, embedding_bytes = row
        
        # Deserialize embedding
        embedding = pickle.loads(embedding_bytes)
        
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
    
    embeddings_array = np.array(embeddings)
    print(f"Loaded {len(courses)} courses with embeddings shape: {embeddings_array.shape}")
    
    return courses, embeddings_array


def get_database_stats(db_path: str = "courses.db"):
    """Print database statistics"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM courses")
    course_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM embeddings")
    embedding_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT DISTINCT subject FROM courses ORDER BY subject")
    subjects = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT MIN(level), MAX(level) FROM courses")
    level_range = cursor.fetchone()
    
    cursor.execute("SELECT DISTINCT last_taught FROM courses ORDER BY last_taught")
    semesters = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    
    print("\n=== Database Statistics ===")
    print(f"Total courses: {course_count}")
    print(f"Courses with embeddings: {embedding_count}")
    print(f"Subjects: {len(subjects)} ({', '.join(subjects[:10])}{'...' if len(subjects) > 10 else ''})")
    print(f"Level range: {level_range[0]} - {level_range[1]}")
    print(f"Semesters: {', '.join(semesters)}")


if __name__ == "__main__":
    # Example usage
    db_path = "courses.db"
    
    print("Creating database schema...")
    create_database(db_path)
    
    # Uncomment when you have your CSV file ready
    # print("Importing CSV data...")
    # import_csv_to_database("your_courses_25_26.csv", db_path)
    
    # print("Generating embeddings...")
    # generate_and_store_embeddings(db_path)
    
    print("Database setup complete!")
    get_database_stats(db_path)