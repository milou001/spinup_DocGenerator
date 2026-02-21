#!/usr/bin/env python3
"""Test PDF parser with sample PDFs."""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.pdf_parser import PDFParser

def test_parser(pdf_path: str):
    """Test parser on a single PDF."""
    print(f"\n📄 Testing: {pdf_path}")
    
    try:
        parser = PDFParser(pdf_path)
        metadata, chunks = parser.get_all_chunks()
        
        print("\n✅ Metadata:")
        print(json.dumps(metadata, indent=2, ensure_ascii=False))
        
        print(f"\n✅ Chunks ({len(chunks)} total):")
        for i, chunk in enumerate(chunks[:3]):  # Show first 3
            print(f"\n  {i+1}. {chunk['main_heading']}")
            print(f"     Pages: {chunk['page_range']}")
            print(f"     Text: {chunk['text_content'][:80]}...")
        
        parser.close()
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    data_dir = Path(__file__).parent.parent / "data"
    
    # Find all PDFs in data dir
    pdfs = list(data_dir.glob("*.pdf"))
    
    if not pdfs:
        print(f"No PDFs found in {data_dir}")
        print("To test: place a PDF in data/ directory")
        sys.exit(0)
    
    success_count = 0
    for pdf in pdfs[:3]:  # Test first 3
        if test_parser(str(pdf)):
            success_count += 1
    
    print(f"\n{'='*50}")
    print(f"Results: {success_count}/{len(pdfs[:3])} PDFs parsed successfully")
