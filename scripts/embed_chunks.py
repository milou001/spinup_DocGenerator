#!/usr/bin/env python3
"""Generate embeddings for all pending chunks."""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.embedding import EmbeddingService
from app.db import get_db_connection

if __name__ == "__main__":
    print("🚀 Starting embedding generation via Ollama...\n")
    
    service = EmbeddingService()
    
    # Get current status
    cursor = get_db_connection().cursor()
    cursor.execute("SELECT COUNT(*) FROM chunks WHERE extraction_status = 'pending_embedding'")
    pending = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM chunks WHERE extraction_status = 'embedded'")
    embedded = cursor.fetchone()[0]
    
    print(f"Status before:")
    print(f"  Pending embeddings: {pending}")
    print(f"  Already embedded: {embedded}\n")
    
    # Embed all chunks
    results = service.embed_all_chunks(batch_size=20)
    
    print(f"\n✅ Embedding complete!")
    print(json.dumps(results, indent=2))
    
    service.close()
