"""Embedding generation and vector similarity search via Ollama."""

import numpy as np
import requests
import json
from typing import List, Dict
import sqlite3

from app.db import get_db_connection


class EmbeddingService:
    """Generate and search embeddings via Ollama."""
    
    def __init__(self, ollama_url: str = "http://openclaw-8ola-ollama-1:11434", model: str = "nomic-embed-text"):
        """
        Initialize embedding service.
        
        Args:
            ollama_url: Ollama API endpoint
            model: Model name (must be pulled in Ollama)
        """
        self.ollama_url = ollama_url
        self.model = model
        self.db = get_db_connection()
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text via Ollama.
        
        Args:
            text: Input text
        
        Returns:
            Embedding vector (768 dimensions for nomic-embed-text)
        """
        try:
            response = requests.post(
                f"{self.ollama_url}/api/embed",
                json={"model": self.model, "input": text},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return data["embeddings"][0]
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None
    
    def embed_all_chunks(self, batch_size: int = 10) -> Dict:
        """
        Generate embeddings for all pending chunks in database.
        
        Args:
            batch_size: Process chunks in batches
        
        Returns:
            {processed, skipped, errors, total}
        """
        cursor = self.db.cursor()
        
        # Get all pending chunks
        cursor.execute("""
            SELECT chunk_id, text_content FROM chunks 
            WHERE extraction_status = 'pending_embedding'
        """)
        
        chunks = cursor.fetchall()
        total = len(chunks)
        processed = 0
        skipped = 0
        errors = 0
        
        print(f"\n🔄 Embedding {total} chunks...")
        
        for i, (chunk_id, text_content) in enumerate(chunks, 1):
            if i % batch_size == 0:
                print(f"  [{i}/{total}] Processing batch...")
            
            try:
                # Generate embedding
                embedding = self.generate_embedding(text_content[:500])  # Limit to 500 chars
                
                if embedding:
                    # Store in database
                    cursor.execute("""
                        UPDATE chunks 
                        SET embedding = ?, extraction_status = 'embedded'
                        WHERE chunk_id = ?
                    """, (json.dumps(embedding), chunk_id))
                    
                    processed += 1
                else:
                    errors += 1
            
            except Exception as e:
                print(f"  ❌ Error on chunk {chunk_id}: {e}")
                errors += 1
        
        self.db.commit()
        
        return {
            "processed": processed,
            "skipped": skipped,
            "errors": errors,
            "total": total
        }
    
    def similarity_search(self, query: str, top_k: int = 5, year_filter: int = None) -> List[dict]:
        """
        Find similar chunks using semantic search.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            year_filter: Optional year filter
        
        Returns:
            List of {chunk_id, report_id, similarity_score, text, heading, page_range}
        """
        # Generate query embedding
        query_embedding = self.generate_embedding(query)
        if not query_embedding:
            return []
        
        # Get all embedded chunks from database
        cursor = self.db.cursor()
        
        if year_filter:
            cursor.execute("""
                SELECT c.chunk_id, c.report_id, c.embedding, c.text_content, c.main_heading, c.page_range
                FROM chunks c
                JOIN reports r ON c.report_id = r.report_id
                WHERE c.extraction_status = 'embedded' AND r.year = ?
            """, (year_filter,))
        else:
            cursor.execute("""
                SELECT chunk_id, report_id, embedding, text_content, main_heading, page_range
                FROM chunks 
                WHERE extraction_status = 'embedded'
            """)
        
        chunks = cursor.fetchall()
        
        # Compute similarities
        similarities = []
        for chunk_id, report_id, embedding_json, text, heading, page_range in chunks:
            try:
                embedding = json.loads(embedding_json)
                similarity = cosine_similarity(query_embedding, embedding)
                similarities.append({
                    'chunk_id': chunk_id,
                    'report_id': report_id,
                    'similarity_score': similarity,
                    'text': text[:200],  # Preview
                    'heading': heading,
                    'page_range': page_range
                })
            except:
                pass
        
        # Sort by similarity and return top-k
        similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
        return similarities[:top_k]
    
    def close(self):
        """Close database connection."""
        if self.db:
            self.db.close()


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.array(a)
    b = np.array(b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return float(np.dot(a, b) / (norm_a * norm_b))
