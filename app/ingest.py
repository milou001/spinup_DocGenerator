"""PDF ingestion pipeline: Parse PDFs and store in database."""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict

from app.pdf_parser import PDFParser
from app.db import get_db_connection


class PDFIngestionPipeline:
    """Manages PDF ingestion: parsing, chunking, and database storage."""
    
    def __init__(self):
        self.db = get_db_connection()
    
    def ingest_pdf(self, pdf_path: str) -> Dict:
        """
        Ingest a single PDF: parse it and store in database.
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            {
                'status': 'success' | 'error',
                'report_id': '001',
                'chunks_count': 5,
                'message': '...'
            }
        """
        try:
            # Parse PDF
            parser = PDFParser(pdf_path)
            metadata, chunks = parser.get_all_chunks()
            parser.close()
            
            # Store in database
            report_id = metadata['berichtsnummer']
            
            # Check if report already exists
            cursor = self.db.cursor()
            cursor.execute("SELECT report_id FROM reports WHERE report_id = ?", (report_id,))
            if cursor.fetchone():
                return {
                    'status': 'skipped',
                    'report_id': report_id,
                    'message': f'Report {report_id} already exists in database'
                }
            
            # Insert report metadata
            cursor.execute("""
                INSERT INTO reports (report_id, berichtsnummer, year, title, file_path, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                report_id,
                metadata['berichtsnummer'],
                metadata['year'],
                metadata['title'],
                pdf_path,
                json.dumps(metadata)
            ))
            
            # Insert chunks
            chunk_count = 0
            for chunk in chunks:
                chunk_id = f"{report_id}-{chunk_count}"
                cursor.execute("""
                    INSERT INTO chunks (
                        chunk_id, report_id, main_heading, page_range, 
                        text_content, extraction_status
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    chunk_id,
                    report_id,
                    chunk['main_heading'],
                    chunk['page_range'],
                    chunk['text_content'],
                    'pending_embedding'
                ))
                chunk_count += 1
            
            # Update search metadata (heading count)
            for chunk in chunks:
                heading = chunk['main_heading']
                cursor.execute("""
                    INSERT INTO search_metadata (heading, heading_count, last_updated)
                    VALUES (?, 1, ?)
                    ON CONFLICT(heading) DO UPDATE SET
                    heading_count = heading_count + 1,
                    last_updated = ?
                """, (heading, datetime.now(), datetime.now()))
            
            self.db.commit()
            
            return {
                'status': 'success',
                'report_id': report_id,
                'chunks_count': chunk_count,
                'year': metadata['year'],
                'message': f'Ingested {report_id} with {chunk_count} chunks'
            }
        
        except FileNotFoundError as e:
            return {'status': 'error', 'message': f'File not found: {e}'}
        except Exception as e:
            self.db.rollback()
            return {'status': 'error', 'message': f'Ingestion failed: {e}'}
    
    def ingest_batch(self, pdf_dir: str) -> Dict:
        """
        Ingest all PDFs from a directory.
        
        Args:
            pdf_dir: Path to directory containing PDFs
        
        Returns:
            {
                'total': 10,
                'success': 8,
                'skipped': 1,
                'errors': 1,
                'results': [...]
            }
        """
        pdf_dir = Path(pdf_dir)
        pdfs = list(pdf_dir.glob("*.pdf"))
        
        results = {
            'total': len(pdfs),
            'success': 0,
            'skipped': 0,
            'errors': 0,
            'results': []
        }
        
        for i, pdf_path in enumerate(pdfs, 1):
            print(f"[{i}/{len(pdfs)}] Ingesting {pdf_path.name}...")
            result = self.ingest_pdf(str(pdf_path))
            results['results'].append(result)
            
            if result['status'] == 'success':
                results['success'] += 1
            elif result['status'] == 'skipped':
                results['skipped'] += 1
            else:
                results['errors'] += 1
        
        return results
    
    def get_ingestion_status(self) -> Dict:
        """Get current database ingestion status."""
        cursor = self.db.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM reports")
        total_reports = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM chunks WHERE extraction_status = 'pending_embedding'")
        pending_embeddings = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM chunks WHERE extraction_status = 'embedded'")
        embedded_chunks = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT year) FROM reports")
        years = cursor.fetchone()[0]
        
        return {
            'total_reports': total_reports,
            'total_chunks': pending_embeddings + embedded_chunks,
            'pending_embeddings': pending_embeddings,
            'embedded_chunks': embedded_chunks,
            'years_covered': years
        }
    
    def close(self):
        """Close database connection."""
        if self.db:
            self.db.close()


if __name__ == "__main__":
    # Example: ingest PDFs from data/samples
    pipeline = PDFIngestionPipeline()
    
    sample_dir = Path(__file__).parent.parent / "data" / "samples"
    if sample_dir.exists():
        print(f"Ingesting PDFs from {sample_dir}")
        results = pipeline.ingest_batch(str(sample_dir))
        print(json.dumps(results, indent=2))
    else:
        print(f"Sample directory not found: {sample_dir}")
    
    print("\nDatabase Status:")
    status = pipeline.get_ingestion_status()
    print(json.dumps(status, indent=2))
    
    pipeline.close()
