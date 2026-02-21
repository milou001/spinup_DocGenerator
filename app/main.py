"""FastAPI main application entry point."""

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
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
    allow_origins=[
        "http://localhost:8000",
        "http://localhost:3000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:3000",
        "*"  # Allow from any origin (configure per deployment)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Serve frontend HTML
frontend_html = Path(__file__).parent.parent / "frontend" / "index.html"

@app.get("/")
async def root():
    """Serve frontend HTML"""
    if frontend_html.exists():
        with open(frontend_html, "r") as f:
            return HTMLResponse(f.read())
    return {"error": "Frontend not found"}


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
    """Get database, ingestion and embedding status."""
    try:
        pipeline = PDFIngestionPipeline()
        db_status = pipeline.get_ingestion_status()
        pipeline.close()
        
        return {
            "status": "ok",
            "database": db_status,
            "embedding_status": {
                "total_chunks": db_status["total_chunks"],
                "embedded": db_status["embedded_chunks"],
                "pending": db_status["pending_embeddings"],
                "percentage_complete": round(100 * db_status["embedded_chunks"] / max(1, db_status["total_chunks"]), 1)
            }
        }
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
        List of matching chunks with similarity scores
    """
    from app.embedding import EmbeddingService
    
    try:
        service = EmbeddingService()
        results = service.similarity_search(
            query=request.query,
            top_k=request.top_n,
            year_filter=request.year_filter
        )
        service.close()
        
        return {
            "status": "success",
            "query": request.query,
            "results_count": len(results),
            "results": results
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "query": request.query,
            "results": []
        }


@app.post("/api/generate")
async def generate(request: GenerateRequest):
    """
    Task 2: Generate new report from search results + LLM synthesis.
    
    Args:
        request: GenerateRequest with brief and parameters
    
    Returns:
        Generated report metadata + PDF path
    """
    from app.embedding import EmbeddingService
    from app.generator import DocumentGenerator
    from app.pdf_generator import PDFGenerator
    
    try:
        # Step 1: Search for relevant documents
        search_service = EmbeddingService()
        search_results = search_service.similarity_search(
            query=request.brief,
            top_k=request.search_results
        )
        search_service.close()
        
        if not search_results:
            return {
                "status": "error",
                "message": f"No relevant documents found for brief: {request.brief}"
            }
        
        # Step 2: Generate report via LLM
        generator = DocumentGenerator(model="orca-mini")
        gen_result = generator.generate_report(
            brief=request.brief,
            search_results=search_results,
            num_results=request.search_results
        )
        
        if gen_result['status'] != 'success':
            return gen_result
        
        # Step 3: Create PDF
        if request.output_format == "pdf":
            pdf_gen = PDFGenerator()
            pdf_path = pdf_gen.generate_pdf(
                title=gen_result['report_title'],
                content=gen_result['report_content'],
                source_docs=gen_result['source_documents']
            )
            
            return {
                "status": "success",
                "brief": request.brief,
                "report_title": gen_result['report_title'],
                "pdf_path": pdf_path,
                "output_format": "pdf",
                "source_documents": gen_result['source_documents'],
                "num_sources": gen_result['num_sources'],
                "timestamp": gen_result['generation_timestamp']
            }
        else:
            # Return JSON
            return {
                "status": "success",
                "brief": request.brief,
                "report_title": gen_result['report_title'],
                "report_content": gen_result['report_content'],
                "output_format": "json",
                "source_documents": gen_result['source_documents'],
                "num_sources": gen_result['num_sources'],
                "timestamp": gen_result['generation_timestamp']
            }
    
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "brief": request.brief
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
