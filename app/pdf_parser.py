"""PDF parsing, OCR, TOC extraction, and page chunking."""

from pathlib import Path
from typing import List, Dict, Tuple
import pdfplumber
import re


class PDFParser:
    """Parse technical PDFs and extract metadata + chunks."""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        self.pdf = None
        self.num_pages = 0
        self._load_pdf()
    
    def _load_pdf(self):
        """Load PDF using pdfplumber."""
        self.pdf = pdfplumber.open(self.pdf_path)
        self.num_pages = len(self.pdf.pages)
    
    def extract_metadata(self) -> Dict:
        """
        Extract metadata from PDF (filename, properties, first page).
        
        Returns:
            {
                'berichtsnummer': 'REP-2023-001',
                'year': 2023,
                'title': 'Bruchanalyse Fahrzeugrahmen',
                'filename': 'report_001.pdf'
            }
        """
        filename = self.pdf_path.stem
        
        # Extract year from filename or metadata
        year_match = re.search(r'20\d{2}', filename)
        year = int(year_match.group(0)) if year_match else 2023
        
        # Extract report number from filename
        report_match = re.search(r'(\d{3,})', filename)
        berichtsnummer = report_match.group(0) if report_match else filename
        
        # Get PDF metadata
        pdf_meta = self.pdf.metadata or {}
        title = pdf_meta.get('Title', filename)
        
        return {
            'berichtsnummer': berichtsnummer,
            'year': year,
            'title': title,
            'filename': self.pdf_path.name,
            'num_pages': self.num_pages,
        }
    
    def extract_toc(self) -> List[Tuple[str, int]]:
        """
        Extract Table of Contents (headings and page ranges).
        
        Strategy:
        - Look for typical TOC in first few pages
        - Identify main headings by keywords
        - Return list of (heading, start_page)
        
        Returns:
            List of (heading, start_page) tuples
        """
        toc = []
        
        # Heuristic: scan first 5 pages for TOC patterns
        for page_num in range(min(5, self.num_pages)):
            page = self.pdf.pages[page_num]
            text = page.extract_text()
            
            if text and any(keyword in text.lower() for keyword in ['inhalt', 'inhaltsverzeichnis', 'contents', 'table of']):
                # Found TOC page(s)
                toc_text = text
                # Simple pattern: "1. Heading ............... 3"
                matches = re.findall(r'^(\d+\.\s+)(.+?)\s+(\d+)$', toc_text, re.MULTILINE)
                for match in matches:
                    heading = match[1].strip()
                    page = int(match[2])
                    toc.append((heading, page - 1))  # 0-indexed
        
        return toc
    
    def chunk_by_heading(self, toc: List[Tuple[str, int]] = None) -> List[Dict]:
        """
        Split PDF into page ranges grouped by main heading.
        
        If TOC is not provided, use simple heuristics (large text = heading).
        
        Returns:
            List of {
                'main_heading': 'Bruchanalyse',
                'page_range': '1-3',
                'pages': [0, 1, 2],
                'text_content': '...'
            }
        """
        chunks = []
        
        if not toc:
            # Fallback: treat each page as a chunk
            for page_num in range(self.num_pages):
                page = self.pdf.pages[page_num]
                text = page.extract_text() or ""
                
                # Try to find heading in first few lines
                heading = text.split('\n')[0][:50] if text else f"Page {page_num + 1}"
                
                chunks.append({
                    'main_heading': heading,
                    'page_range': str(page_num + 1),
                    'pages': [page_num],
                    'text_content': text,
                })
            return chunks
        
        # Use TOC to group pages by heading
        for i, (heading, start_page) in enumerate(toc):
            # Find end page (next heading or last page)
            end_page = toc[i + 1][1] if i + 1 < len(toc) else self.num_pages
            
            # Extract text from all pages in range
            text_parts = []
            pages_in_range = []
            
            for page_num in range(start_page, end_page):
                if page_num < self.num_pages:
                    page = self.pdf.pages[page_num]
                    text = page.extract_text() or ""
                    text_parts.append(text)
                    pages_in_range.append(page_num)
            
            chunks.append({
                'main_heading': heading,
                'page_range': f"{start_page + 1}-{end_page}",
                'pages': pages_in_range,
                'text_content': '\n---PAGE_BREAK---\n'.join(text_parts),
            })
        
        return chunks
    
    def get_all_chunks(self) -> Tuple[Dict, List[Dict]]:
        """
        Extract metadata and all chunks from PDF.
        
        Returns:
            (metadata_dict, chunks_list)
        """
        metadata = self.extract_metadata()
        toc = self.extract_toc()
        chunks = self.chunk_by_heading(toc if toc else None)
        
        return metadata, chunks
    
    def close(self):
        """Close PDF file."""
        if self.pdf:
            self.pdf.close()


# Example usage
if __name__ == "__main__":
    import json
    
    # Test with sample PDF (create or use existing)
    sample_pdf = Path(__file__).parent.parent / "data" / "sample.pdf"
    
    if sample_pdf.exists():
        parser = PDFParser(str(sample_pdf))
        metadata, chunks = parser.get_all_chunks()
        
        print("Metadata:")
        print(json.dumps(metadata, indent=2, ensure_ascii=False))
        print("\nChunks:")
        for i, chunk in enumerate(chunks):
            print(f"\n{i+1}. {chunk['main_heading']} ({chunk['page_range']})")
            print(f"   Text preview: {chunk['text_content'][:100]}...")
        
        parser.close()
    else:
        print(f"Sample PDF not found at {sample_pdf}")
        print("To test: place a PDF in data/sample.pdf and run this script")
