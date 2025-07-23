# MadCourses - UW-Madison Course Search

**Semantic course search with SvelteKit frontend using Hugging Face API and Vercel Blob Storage.**

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Set up environment variables
# Create .env.local with:
# HUGGINGFACE_API_KEY=your_key_here
# BLOB_READ_WRITE_TOKEN=your_token_here

# Start development server
npm run dev
```

Open http://localhost:8000 to use the app!

## 📁 Project Structure

```
MadCourses/
├── src/                           # SvelteKit frontend
│   ├── routes/+page.svelte       # Main search interface
│   ├── routes/api/match/+server.ts # Course matching API endpoint
│   └── lib/database.ts           # Vercel Blob data loading
├── scripts/                       # Build and utility scripts
│   ├── dev-server.ts             # Development server with graceful shutdown
│   └── upload-to-blob.ts         # Course data upload to Vercel Blob
├── static/                        # Static assets
├── courses.json                   # Course data for upload
└── package.json                  # Dependencies and scripts
```

## 🔧 How It Works

### Request Flow

```
User → SvelteKit Frontend → Hugging Face API → Vercel Blob Storage
```

### Technology Stack

- **Frontend**: SvelteKit + TypeScript + Tailwind CSS + Skeleton UI
- **API**: Hugging Face Inference API (sentence-transformers)
- **RAG**: Real-time embeddings with similarity search
- **Storage**: Vercel Blob for course data and embeddings
- **Model**: all-MiniLM-L12-v2 (384 dimensions)
- **Deployment**: Vercel with @sveltejs/adapter-vercel

## 🧪 Development

### Available Scripts

```bash
# Development server (port 8000)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Type checking
npm run check

# Linting and formatting
npm run lint
npm run format

# Upload course data to Vercel Blob
npm run upload-blob
```

## 🔍 Features

- **Semantic Search**: Uses Hugging Face sentence-transformers for intelligent matching
- **Advanced Filtering**: Subject, level, credits, semester, results count
- **Real-time Search**: API calls to Hugging Face for embeddings
- **Cloud Storage**: Course data stored in Vercel Blob
- **Responsive Design**: Mobile-friendly interface with Tailwind CSS

## 🛠️ Core Files

- `src/routes/+page.svelte` - Main search interface with filters and results
- `src/routes/api/match/+server.ts` - Course matching API endpoint
- `src/lib/database.ts` - Vercel Blob data loading utilities
- `scripts/dev-server.ts` - Development server with graceful shutdown
- `scripts/upload-to-blob.ts` - Data upload utility

## 📊 Data

- **10,005+ courses** from UW-Madison
- **Course metadata**: Subject, level, title, credits, last taught
- **Pre-computed embeddings**: 384D vectors stored in Vercel Blob
- **All subjects**: Complete UW-Madison course catalog

## 🚀 Deployment

Ready for deployment on Vercel with serverless functions and Blob storage!
