"""SQLite + json1 database schema and utilities."""

import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "docgen.db"


def init_db():
    """Initialize SQLite database with schema."""
    
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Enable json1 extension
    cursor.execute("PRAGMA compile_options;")
    
    # Table: reports (metadata)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        report_id TEXT PRIMARY KEY,
        berichtsnummer TEXT UNIQUE,
        year INTEGER,
        title TEXT,
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        file_path TEXT,
        ocr_status TEXT DEFAULT 'pending',
        metadata TEXT  -- JSON: {year, headings, etc}
    )
    """)
    
    # Table: chunks (page segments grouped by heading)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chunks (
        chunk_id TEXT PRIMARY KEY,
        report_id TEXT NOT NULL,
        main_heading TEXT,
        page_range TEXT,  -- "1-3", "5", etc
        text_content TEXT,
        embedding TEXT,  -- JSON array (1536 dims)
        extraction_status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (report_id) REFERENCES reports(report_id)
    )
    """)
    
    # Table: search_metadata (indexed by heading for fast filtering)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS search_metadata (
        id INTEGER PRIMARY KEY,
        heading TEXT UNIQUE,
        heading_count INTEGER DEFAULT 0,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Indices for faster queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_report_year ON reports(year)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunk_heading ON chunks(main_heading)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunk_report ON chunks(report_id)")
    
    conn.commit()
    conn.close()
    
    print(f"✅ Database initialized: {DB_PATH}")


def get_db_connection():
    """Get database connection."""
    return sqlite3.connect(DB_PATH)


if __name__ == "__main__":
    init_db()
