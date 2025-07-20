# MadCourses Backend - SQLite-based Course Search Engine

High-performance semantic search API for UW-Madison courses using SQLite and in-memory vector search.

## Features

- **Semantic Search**: Uses SentenceTransformer embeddings for intelligent course matching
- **Advanced Filtering**: Subject, level, credits, and semester filtering with proper range handling
- **Credit Range Support**: Courses with "1-6" credits properly match searches for 1, 3, or 6 credits
- **Fast In-Memory Search**: Pre-loaded embeddings for sub-second response times
- **Zero Database Costs**: SQLite-based with no external dependencies
- **Vercel-Ready**: Optimized for serverless deployment

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Create database schema
python database_setup.py

# Import your course data (replace with your CSV file)
python -c "
from database_setup import import_csv_to_database, generate_and_store_embeddings
import_csv_to_database('your_courses_25_26.csv')
generate_and_store_embeddings()
"
```

### 3. Local Development

```bash
# Start the backend server (runs on port 8001)
python start_backend.py

# Test the API
curl -X POST http://localhost:8001/match \
  -H "Content-Type: application/json" \
  -d '{"skills": ["machine learning"], "k": 3}'

# CLI search tool
python skill_matcher_sqlite.py "data analysis" --k 5 --subject-contains "STAT"
```

### 4. Deploy to Vercel

```bash
vercel deploy
```

## Architecture

```
Frontend (SvelteKit) → API Server (FastAPI) → SQLite Database + In-Memory Vector Search
```

**Key Components:**
- **SQLite Database**: Stores course metadata and serialized embeddings
- **SentenceTransformer**: Generates 384-dimensional embeddings for semantic search
- **In-Memory Search**: Pre-loaded embeddings for fast cosine similarity computation
- **Advanced Filtering**: Subject, level, credit range, and semester filtering

## File Structure

```
Backend/
├── api.py                     # FastAPI server with /match endpoint
├── skill_matcher_sqlite.py    # Core search engine with vector similarity
├── database_setup.py          # Database initialization and data import
├── start_backend.py           # Local development server launcher
├── requirements.txt           # Python dependencies
├── vercel.json               # Serverless deployment config
├── courses.db                # SQLite database (created after import)
└── README_SQLITE.md          # This documentation
```

## API Reference

### POST /match

Search for courses similar to provided skills.

**Request Body:**
```json
{
  "skills": ["machine learning", "data analysis"],
  "k": 5,
  "subject_contains": "COMP SCI",
  "level_min": 300,
  "level_max": 599,
  "credit_min": 3,
  "credit_max": 4,
  "last_taught": "F24"
}
```

**Response:**
```json
{
  "results": [
    {
      "skill": "machine learning",
      "matches": [
        {
          "id": 123,
          "subject": "COMP SCI",
          "level": 540,
          "title": "Introduction to Machine Learning",
          "credit_amount": "3",
          "credit_min": 3.0,
          "credit_max": 3.0,
          "last_taught": "F24",
          "description": "...",
          "similarity": 0.89
        }
      ]
    }
  ]
}
```

## CSV Data Format

Your course CSV should include these columns:

| Column | Description | Example |
|--------|-------------|---------|
| `subject` | Course subject code | "COMP SCI", "MATH", "STAT" |
| `level` | Course number | 101, 540, 799 |
| `title` | Course title | "Introduction to Programming" |
| `credit_amount` | Credits (supports ranges) | "3", "1-6", "3-4" |
| `last_taught` | Semester code | "F24", "S25", "U25" |
| `description` | Course description | "This course covers..." |

**Credit Range Handling:**
- Single credits: "3" → matches exactly 3 credit searches
- Ranges: "1-6" → matches searches for 1, 3, 6, or any credits in between
- Variable: "3-4" → matches searches for 3, 4, or 3.5 credits

## Environment Variables

Create `.env` file for customization:
```bash
# Model configuration
MODEL=all-MiniLM-L12-v2        # SentenceTransformer model name
TOP_K=5                        # Default number of results per skill
DB_PATH=courses.db             # SQLite database file path

# Cache directory (important for serverless)
HF_HOME=/tmp/cache
TRANSFORMERS_CACHE=/tmp/cache
```

## Local Development

```bash
# Start backend server on port 8001
python start_backend.py

# Test search via CLI
python skill_matcher_sqlite.py "programming" --k 3 --level-min 300

# Check database statistics
python -c "from database_setup import get_database_stats; get_database_stats()"
```

**Starting Frontend + Backend:**
1. Backend: `python start_backend.py` (port 8001)
2. Frontend: `cd ../Frontend/MadCourses && npm run dev` (port 5173)
3. Visit: http://localhost:5173

## Performance Optimizations

- **Global Caching**: Model and embeddings loaded once and cached in memory
- **Batch Processing**: Multiple skills processed in single API call
- **Efficient Storage**: Embeddings stored as pickled BLOBs in SQLite
- **Index Optimization**: Database indexes on commonly filtered columns
- **Serverless Ready**: /tmp cache directory for model storage

## Credit Range Logic

The system properly handles course credit ranges using overlap detection:

```python
# Course offers "1-6" credits (credit_min=1, credit_max=6)
# Search for 3 credits (credit_min=3, credit_max=3)
# Result: MATCH (overlap between [1,6] and [3,3])

# Course offers "3" credits (credit_min=3, credit_max=3) 
# Search for 1-2 credits (credit_min=1, credit_max=2)
# Result: NO MATCH (no overlap between [3,3] and [1,2])
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `No such file: courses.db` | Run `python database_setup.py` first |
| Empty search results | Check if embeddings were generated with `generate_and_store_embeddings()` |
| Port 8001 in use | Change port in `start_backend.py` or kill existing process |
| Model download fails | Check internet connection, model downloads ~23MB |
| Vercel timeout | Ensure database file is included in deployment |

## Migration from Supabase

Key improvements over the previous Supabase version:

1. **Zero Database Costs**: No external database fees
2. **Faster Cold Starts**: No network latency for database connections  
3. **Simplified Deployment**: Single SQLite file vs. external PostgreSQL
4. **Better Credit Handling**: Proper range overlap logic vs. averaging
5. **Improved Error Handling**: Comprehensive validation and error messages
6. **Enhanced Documentation**: Complete API reference and troubleshooting guide