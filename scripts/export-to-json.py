#!/usr/bin/env python3
"""
Export SQLite database to JSON for Vercel Blob Storage
This script runs locally to convert the courses.db to JSON format
"""

import sqlite3
import json
import pickle
import os

def export_courses_to_json():
    # Path to the SQLite database
    db_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'courses.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
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
        print("No courses found in database")
        return
    
    courses = []
    
    for row in rows:
        course_id, subject, level, title, credit_amount, credit_min, credit_max, last_taught, description, embedding_bytes = row
        
        # Deserialize the embedding
        embedding_array = pickle.loads(embedding_bytes)
        embedding = embedding_array.tolist()
        
        # Create course object
        course = {
            'id': course_id,
            'subject': subject,
            'level': level,
            'title': title,
            'credit_amount': credit_amount,
            'credit_min': credit_min,
            'credit_max': credit_max,
            'last_taught': last_taught,
            'description': description,
            'embedding': embedding
        }
        
        courses.append(course)
    
    # Write to JSON file
    output_path = os.path.join(os.path.dirname(__file__), '..', 'courses.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(courses, f, ensure_ascii=False, indent=2)
    
    print(f"Exported {len(courses)} courses to {output_path}")
    print(f"File size: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB")

if __name__ == '__main__':
    export_courses_to_json()