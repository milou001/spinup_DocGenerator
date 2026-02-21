"""FastAPI main application entry point."""

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import tempfile
import json

from app.ingest import PDFIngestionPipeline

app = FastAPI(
    title="DocGenerator API",
    description="Technical Report Document Search & Generation",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    """Request model for search endpoint."""
    query: str
    top_n: int = 5
    year_filter: int = None


class GenerateRequest(BaseModel):
    """Request model for generate endpoint."""
    brief: str
    search_results: int = 5
    output_format: str = "json"


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}


@app.get("/api/status")
async def status():
    """Get database and ingestion status."""
    try:
        pipeline = PDFIngestionPipeline()
        status = pipeline.get_ingestion_status()
        pipeline.close()
        return {"status": "ok", "database": status}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/ingest/single")
async def ingest_single(file: UploadFile = File(...)):
    """
    Ingest a single PDF file.
    
    Args:
        file: PDF file to ingest
    
    Returns:
        Ingestion result with report ID and chunk count
    """
    try:
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Ingest
        pipeline = PDFIngestionPipeline()
        result = pipeline.ingest_pdf(tmp_path)
        pipeline.close()
        
        # Clean up
        Path(tmp_path).unlink()
        
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/ingest/batch")
async def ingest_batch(directory: str):
    """
    Ingest all PDFs from a directory.
    
    Args:
        directory: Path to directory containing PDFs
    
    Returns:
        Batch ingestion results
    """
    try:
        pipeline = PDFIngestionPipeline()
        results = pipeline.ingest_batch(directory)
        pipeline.close()
        return results
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "total": 0,
            "success": 0,
            "errors": 1
        }


@app.post("/api/search")
async def search(request: SearchRequest):
    """
    Task 1: Semantic search for similar documents.
    
    Args:
        request: SearchRequest with query, top_n, optional year_filter
    
    Returns:
        List of matching documents with similarity scores
    """
    # TODO: Implement embedding search
    return {
        "status": "not_implemented",
        "query": request.query,
        "top_n": request.top_n,
        "results": []
    }


@app.post("/api/generate")
async def generate(request: GenerateRequest):
    """
    Task 2: Generate new report from search results.
    
    Args:
        request: GenerateRequest with brief and parameters
    
    Returns:
        Generated report (PDF or JSON)
    """
    # TODO: Implement document generation
    return {
        "status": "not_implemented",
        "brief": request.brief,
        "search_results": request.search_results
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
