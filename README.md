# MadCourses - UW-Madison Course Search

**Semantic course search with SvelteKit frontend + Python API backend, deployed as a unified Vercel project.**

## 🚀 Quick Start

```bash
# Local development
python start_unified.py

# Deploy to Vercel
vercel deploy
```

## 📁 Project Structure

```
MadCourses/                         # Root project (deploy this to Vercel)
├── src/                            # SvelteKit frontend
│   ├── routes/+page.svelte        # Main search interface
│   └── routes/api/match/+server.ts # Development API proxy
├── api/                           # Python serverless functions
│   ├── match.py                   # Main API endpoint (/api/match)
│   ├── skill_matcher_sqlite.py    # Search engine with vector similarity
│   ├── database_setup.py          # Database utilities
│   ├── requirements.txt           # Python dependencies
│   └── courses.db                 # SQLite database with course data
├── static/                        # Static assets
├── package.json                   # Frontend dependencies
├── vercel.json                    # Vercel deployment configuration
├── start_unified.py               # Local development server
└── test_unified.py                # Comprehensive test suite
```

## 🔧 Local Development

### Setup

```bash
# Check dependencies and setup database
python start_unified.py --setup

# Or check dependencies only
python start_unified.py --deps-only
```

### Development Server

```bash
# Option 1: Simple NPM command (recommended)
npm run dev

# Option 2: Use Python script (may have Windows issues)
python start_unified.py

# Option 3: Windows batch file
start_dev.bat

# Server URL: http://localhost:5173 (or next available port)
# API URL: http://localhost:5173/api/match
```

### Testing

```bash
# Run comprehensive test suite
python test_unified.py

# Check code formatting
npm run check
npm run lint
```

## 🌐 Deployment

### Vercel Deployment

```bash
# Deploy to Vercel (first time)
vercel

# Redeploy
vercel deploy

# Production deployment
vercel --prod
```

### What Gets Deployed

- **Frontend**: SvelteKit app with search interface
- **API**: Python serverless functions for course matching
- **Database**: SQLite database with 10,000+ courses and embeddings
- **Static Assets**: Fonts, favicon, etc.

## 🔍 How It Works

### Request Flow

```
User Search → SvelteKit Frontend → /api/match → Python Function → SQLite Database
```

### Key Features

- **Semantic Search**: Uses SentenceTransformer embeddings for intelligent course matching
- **Advanced Filtering**: Subject, level, credits, semester with proper range handling
- **Credit Range Logic**: Courses with "1-6" credits match searches for 1, 3, or 6 credits
- **Fast Performance**: In-memory vector search with global caching
- **Single Deployment**: Frontend and backend in one Vercel project

## 📊 Database

### Current Data

- **10,005 courses** with full metadata
- **10,005 embeddings** for semantic search
- **1,558 subjects** across all departments
- **Levels**: 100-999 (undergraduate through PhD)
- **Semesters**: Historical data from 1989 to present

### Import New Data

```bash
python -c "
import sys; sys.path.append('api')
from database_setup import import_csv_to_database, generate_and_store_embeddings
import_csv_to_database('new_courses.csv')
generate_and_store_embeddings()
"
```

## 🧪 API Reference

### POST /api/match

**Request:**

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
					"similarity": 0.89
				}
			]
		}
	]
}
```

## 🛠️ Architecture

### Development Mode

```
Browser → SvelteKit Dev Server (5173) → Python API → SQLite Database
```

### Production Mode

```
Browser → Vercel Edge Network → SvelteKit + Python API → SQLite Database
```

### Technology Stack

- **Frontend**: SvelteKit, TypeScript, Tailwind CSS, Skeleton UI
- **Backend**: Python, FastAPI, SQLite, SentenceTransformers
- **Deployment**: Vercel with serverless functions
- **Search**: Vector similarity with cosine distance

## 🐛 Troubleshooting

### Common Issues

| Issue                        | Solution                                      |
| ---------------------------- | --------------------------------------------- |
| Dependencies missing         | Run `python start_unified.py --setup`         |
| Port 5173 in use             | Stop other dev servers or change port         |
| Database not found           | Run database setup with `--setup` flag        |
| Import errors in VS Code     | Restart VS Code (should auto-configure)       |
| API timeout on first request | Normal - model loading takes 10-20s initially |

### Debug Commands

```bash
# Test API directly
curl -X POST http://localhost:5173/api/match \
  -H "Content-Type: application/json" \
  -d '{"skills": ["programming"], "k": 2}'

# Check database
python -c "
import sys; sys.path.append('api')
from database_setup import get_database_stats
get_database_stats()
"
```

## 📚 Documentation

- **API Documentation**: Built-in at `/docs` when running locally
- **Database Schema**: See `api/database_setup.py`

## 🎯 Key Improvements

### From Previous Version

- ✅ **Credit Range Fix**: Proper overlap detection instead of averaging
- ✅ **Unified Deployment**: Single Vercel project instead of separate frontend/backend
- ✅ **Performance**: Global caching and in-memory vector search
- ✅ **Error Handling**: Comprehensive validation and user-friendly messages
- ✅ **Documentation**: Complete guides and API reference

### Architecture Benefits

- **Zero CORS Issues**: Same origin for frontend and API
- **Cost Effective**: Single Vercel project, no external database costs
- **Easy Debugging**: Everything in one repository
- **Scalable**: Vercel handles traffic scaling automatically

## 🎉 Success Metrics

- ✅ **All tests passing**: Database, API, Frontend, Vercel config
- ✅ **Clean structure**: Root directory ready for Vercel deployment
- ✅ **No import errors**: Proper Python path configuration
- ✅ **Credit logic working**: Range overlap detection implemented
- ✅ **Performance optimized**: Sub-second search responses after warmup

**Ready for production deployment! 🚀**

Run `vercel deploy` from this directory to deploy to production.
