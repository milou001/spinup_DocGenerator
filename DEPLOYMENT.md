# DocGenerator - Deployment & Operations Guide

## Quick Start

```bash
# Initialize & start
./run.sh

# Or manually:
python3 scripts/init_db.py
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Frontend (Vue.js - frontend/index.html)            │
│  • Search Interface                                 │
│  • Report Generation                                │
│  • PDF Download                                     │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼ HTTP/JSON
┌─────────────────────────────────────────────────────┐
│  FastAPI Backend (app/main.py)                      │
│  • /api/search (semantic search)                    │
│  • /api/generate (report synthesis)                 │
│  • /api/ingest (batch PDF upload)                   │
│  • /api/status (system status)                      │
└────────────────┬────────────────────────────────────┘
                 │
        ┌────────┴────────┬─────────────────┐
        ▼                 ▼                 ▼
    SQLite DB        Ollama LLM      ReportLab
    (embeddings)     (generation)     (PDF export)
    (metadata)       (orca-mini)
    (chunks)
```

## Components

### 1. PDF Ingestion

```bash
# Single file
curl -X POST -F "file=@report.pdf" http://localhost:8000/api/ingest/single

# Batch directory
curl -X POST -d "directory=/path/to/pdfs" http://localhost:8000/api/ingest/batch
```

### 2. Semantic Search

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Fahrzeug Bruch Rahmen",
    "top_n": 5,
    "year_filter": null
  }'
```

### 3. Report Generation

```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "brief": "Analyse Fahrzeugrahmen unter Windbedingungen",
    "search_results": 3,
    "output_format": "pdf"
  }'
```

## System Requirements

### Minimum
- Python 3.9+
- 4 GB RAM
- 10 GB disk (for embeddings + PDFs)
- Ollama running (separate service)

### Recommended
- Python 3.13+ (Homebrew)
- 8+ GB RAM
- 50 GB+ disk (for 3000+ documents)
- Ollama with models: `nomic-embed-text`, `orca-mini`

## Installation

### 1. Clone & Setup

```bash
cd spinup_DocGenerator
python3 -m pip install -r requirements.txt
```

### 2. Initialize Database

```bash
python3 scripts/init_db.py
```

### 3. Load Ollama Models

```bash
# Embedding model (required)
curl -X POST http://localhost:11434/api/pull -d '{"name":"nomic-embed-text"}'

# LLM model (required for generation)
curl -X POST http://localhost:11434/api/pull -d '{"name":"orca-mini"}'
```

### 4. Start Server

```bash
./run.sh
# or
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 5. Open Frontend

```
http://localhost:8000/frontend/index.html
```

## API Reference

### GET /health
Health check.

**Response:**
```json
{"status": "ok", "version": "0.1.0"}
```

### GET /api/status
Database & embedding status.

**Response:**
```json
{
  "status": "ok",
  "database": {
    "total_reports": 14,
    "total_chunks": 342,
    "pending_embeddings": 0,
    "embedded_chunks": 342,
    "percentage_complete": 100.0
  }
}
```

### POST /api/search
Semantic search.

**Request:**
```json
{
  "query": "Bruch Rahmen",
  "top_n": 5,
  "year_filter": 2023
}
```

**Response:**
```json
{
  "status": "success",
  "results_count": 5,
  "results": [
    {
      "chunk_id": "001-0",
      "report_id": "001",
      "similarity_score": 0.68,
      "heading": "Beschreibung Objekte",
      "page_range": "1-3",
      "text": "..."
    }
  ]
}
```

### POST /api/generate
Generate report from brief.

**Request:**
```json
{
  "brief": "Fahrzeug Bruch Rahmen Wind",
  "search_results": 3,
  "output_format": "pdf"
}
```

**Response:**
```json
{
  "status": "success",
  "brief": "...",
  "report_title": "Synthesized Report: ...",
  "pdf_path": "/data/.../report.pdf",
  "output_format": "pdf",
  "num_sources": 3,
  "timestamp": "2026-02-21T..."
}
```

## Operations

### Monitor Status

```bash
# Real-time status
curl http://localhost:8000/api/status | jq

# Check Ollama models
curl http://localhost:11434/api/tags | jq
```

### Ingest PDFs

```bash
# Copy PDFs to data/samples
cp *.pdf data/samples/

# Batch ingest
curl -X POST \
  -d "directory=$(pwd)/data/samples" \
  http://localhost:8000/api/ingest/batch
```

### Database Backup

```bash
cp data/docgen.db data/docgen.db.backup.$(date +%s)
```

## Troubleshooting

### Ollama Connection Error
```
Error: HTTPConnectionPool(...:11434): Connection refused
```
**Solution:** Check Ollama is running
```bash
curl http://openclaw-8ola-ollama-1:11434/api/tags
# If no response, restart Ollama container
docker restart openclaw-8ola-ollama-1
```

### Model Not Found
```
Error: model 'orca-mini' not found
```
**Solution:** Pull the model
```bash
curl -X POST http://openclaw-8ola-ollama-1:11434/api/pull \
  -d '{"name":"orca-mini"}'
```

### Slow Search/Generation
- Increase RAM allocation to Ollama
- Use smaller models (`orca-mini` vs `neural-chat`)
- Run embedding batch at night

### Out of Disk Space
```bash
# Check usage
du -sh data/
# Archive old reports
tar -czf data/archive_2024.tar.gz data/docgen.db
```

## Performance Tuning

### Embedding Speed
```bash
# Larger batches (in scripts/embed_chunks.py)
embed_all_chunks(batch_size=50)
```

### Search Latency
- Pre-load Ollama embedding model
- Cache frequently used queries

### PDF Generation
- Use `orca-mini` for speed (trade-off: quality)
- Run generation jobs in background

## Security

### Production Deployment

1. **Frontend**: Serve via nginx/Caddy
```nginx
server {
    listen 80;
    root /data/.../frontend;
    index index.html;
}
```

2. **API**: Run behind reverse proxy
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
# Then proxy via nginx
```

3. **Database**: Backup regularly
```bash
# Daily backup to NAS
rsync -av data/docgen.db nas://backup/
```

4. **Ollama**: Only expose internally
```bash
# Don't expose port 11434 to internet
```

## Scaling to 3000+ Documents

1. **Initial Load** (one-time)
   ```bash
   # Copy all 3000 PDFs to data/samples/
   # Run batch ingest overnight
   python3 scripts/embed_chunks.py
   ```
   Time: ~10-20 hours depending on hardware

2. **Continuous Operation**
   - Ingest new PDFs via API `/api/ingest/single`
   - Run embedding batch jobs off-peak
   - Monitor disk space

3. **Optimization**
   - Use SSD storage
   - Allocate 8+ GB RAM to Ollama
   - Consider database indexing for 5000+ chunks

## Maintenance

### Weekly
- Check `/api/status` for health
- Monitor disk usage

### Monthly
- Backup `data/docgen.db`
- Review Ollama resource usage
- Clean old temp files

### Quarterly
- Reindex database (if >10k chunks)
- Update models (`ollama pull nomic-embed-text`)

## Support & Issues

- Check API docs: http://localhost:8000/docs
- GitHub: https://github.com/milou001/spinup_DocGenerator
- Logs: `uvicorn` console output

---

**Deployed & ready for 3000+ technical reports.** 🚀
