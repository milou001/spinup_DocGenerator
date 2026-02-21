# DocGenerator: Technical Report Document Search & Generation System

A sophisticated system for semantic search and intelligent document generation based on ~3000 technical reports.

## Features

### Task 1: Semantic Search
- **Smart Similarity Search:** Find documents by meaning, not just keywords
  - Search: "Beule" → finds "Dellen", "Beschädigungen", etc.
- **Vector-based Retrieval:** Uses embeddings for semantic matching
- **Configurable Result Count:** Get top-N matches

### Task 2: Document Generation
- **Template-based Synthesis:** Generate new reports from search hits
- **LLM Adaptation:** Uses Ollama (local) to synthesize content
- **PDF Export:** Output formatted technical reports

## Tech Stack

- **Backend:** FastAPI (modern, async, auto-docs)
- **Database:** SQLite + json1 extension (local, archivable)
- **Frontend:** Vue 3 (lightweight, reactive)
- **LLM:** Ollama (100% local, no cloud)
- **PDF Generation:** ReportLab (pure Python)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Web Clients (Search + Generate UI)                    │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│  FastAPI Server (Task 1 & 2 Endpoints)                 │
└────────────────────┬────────────────────────────────────┘
                     │
      ┌──────────────┼──────────────┐
      ▼              ▼              ▼
   SQLite      Ollama LLM     PDF Generator
 (Embeddings) (Generation)   (ReportLab)
```

## Getting Started

### Prerequisites
- Python 3.9+
- SQLite 3.35+
- Ollama (running locally)

### Installation

```bash
# Clone repo
git clone https://github.com/milou001/spinup_DocGenerator.git
cd spinup_DocGenerator

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -m app.db init

# Run backend
uvicorn app.main:app --reload --port 8000

# Run frontend (separate terminal)
cd frontend
npm install
npm run dev
```

### Usage

**Search Endpoint:**
```bash
POST /api/search
{
  "query": "Bruch im Rahmen",
  "top_n": 5,
  "year_filter": 2023
}
```

**Generate Endpoint:**
```bash
POST /api/generate
{
  "brief": "Fahrzeug mit Rostschäden",
  "search_results": 5,
  "output_format": "pdf"
}
```

## Project Structure

```
spinup_DocGenerator/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── db.py                # SQLite + json1 schema
│   ├── embedding.py         # Vector generation & search
│   ├── pdf_parser.py        # PDF → chunks + metadata
│   ├── ollama_service.py    # LLM integration
│   ├── report_generator.py  # ReportLab PDF generation
│   └── api/
│       ├── search.py        # Task 1 endpoints
│       └── generate.py      # Task 2 endpoints
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── App.vue
│   └── package.json
├── data/
│   ├── archive/             # PDF storage
│   └── docgen.db            # SQLite database
├── requirements.txt
└── README.md
```

## Development Roadmap

**Phase 1A: Core Infrastructure**
- [ ] Database schema (SQLite + json1)
- [ ] PDF parser + TOC extraction
- [ ] API stubs (search, ingest, generate)

**Phase 1B: Frontend + Embedding**
- [ ] Vue search interface
- [ ] Embedding pipeline
- [ ] Vector similarity search

**Phase 2: LLM Integration**
- [ ] Ollama integration
- [ ] Document generation
- [ ] PDF export

**Phase 3: Bulk Ingest**
- [ ] Batch PDF import (3000 docs)
- [ ] Metadata extraction
- [ ] Embedding generation (overnight builds)

## Local Deployment

- **NAS Storage:** `/archive/` for PDFs
- **Database:** `docgen.db` (archivable)
- **API Server:** Local machine or VM
- **Clients:** Web browsers on network

## Testing

```bash
# Run tests
pytest tests/

# Test with 100-document subset
python scripts/test_ingest.py --count 100
```

## Author

Built by Ivy for Micha's technical document workflow.

## License

TBD
