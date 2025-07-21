# MadCourses - UW-Madison Course Search

**Semantic course search with SvelteKit frontend + Python RAG backend using PyTorch and sentence-transformers.**

## 🚀 Quick Start

```bash
# 1. Set up Python environment
python -m venv venv
venv\Scripts\activate
pip install -r api\python\requirements.txt

# 2. Start Python RAG server
python local_server.py

# 3. Start frontend (in new terminal)
npm run dev
```

Open http://localhost:5173 to use the app!

## 📁 Project Structure

```
MadCourses/
├── src/                           # SvelteKit frontend
│   ├── routes/+page.svelte       # Main search interface
│   └── routes/api/match/+server.ts # API proxy to Python server
├── api/python/                    # Python RAG implementation
│   ├── match.py                  # Core RAG with sentence-transformers
│   ├── requirements.txt          # PyTorch + sentence-transformers
│   └── courses.db               # SQLite with 10,005 courses + embeddings
├── local_server.py               # Local Python API server
├── test_rag_local.py            # Test RAG functionality
├── test_api_client.py           # Test API client
├── venv/                        # Python virtual environment
└── package.json                 # Frontend dependencies
```

## 🔧 How It Works

### Request Flow
```
User → SvelteKit Frontend → Python RAG Server → sentence-transformers → SQLite Database
```

### Technology Stack
- **Frontend**: SvelteKit + TypeScript + Tailwind CSS
- **Backend**: Python + PyTorch + sentence-transformers 2.7.0
- **RAG**: Local embeddings with pre-computed course vectors
- **Database**: SQLite with 10,005 courses and 384D embeddings
- **Model**: all-MiniLM-L12-v2 (384 dimensions)

## 🧪 Testing

### Test RAG Functions
```bash
venv\Scripts\activate
python test_rag_local.py
```

### Test API Server
```bash
# Terminal 1: Start server
venv\Scripts\activate
python local_server.py

# Terminal 2: Test client
venv\Scripts\activate
python test_api_client.py
```

### Test Full Stack
```bash
# Terminal 1: Python server
venv\Scripts\activate
python local_server.py

# Terminal 2: Frontend
npm run dev
```

## 🔍 RAG Performance

- **10,005 courses** with semantic embeddings
- **First search**: Shows "Caching..." (model loads ~10s)
- **Subsequent searches**: Show "Searching..." (~1s)
- **High similarity scores**: 0.74+ for exact matches

## 🛠️ Development

### Core Files
- `api/python/match.py` - RAG implementation with sentence-transformers
- `local_server.py` - HTTP server for local development  
- `src/routes/+page.svelte` - Search interface with filters
- `src/routes/api/match/+server.ts` - Proxy to Python server

### Key Features
- **Semantic Search**: Uses sentence-transformers for intelligent matching
- **Advanced Filtering**: Subject, level, credits, semester
- **Local Development**: No external APIs required
- **Smart Caching**: Model loads once, stays in memory

## 📊 Database

- **10,005 courses** with full metadata
- **10,005 embeddings** (384D vectors)
- **Pre-computed**: Ready for instant similarity search
- **Subjects**: All UW-Madison departments

Ready for local development with PyTorch and sentence-transformers! 🚀