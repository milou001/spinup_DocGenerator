"""LLM-based document generation from search results."""

import requests
import json
from typing import List, Dict
from datetime import datetime

from app.embedding import EmbeddingService


class DocumentGenerator:
    """Generate new reports from search results using Ollama LLM."""
    
    def __init__(self, ollama_url: str = "http://openclaw-8ola-ollama-1:11434", model: str = "orca-mini"):
        """
        Initialize document generator.
        
        Args:
            ollama_url: Ollama API endpoint
            model: LLM model name (e.g., mistral, neural-chat, etc)
        """
        self.ollama_url = ollama_url
        self.model = model
    
    def generate_report(self, brief: str, search_results: List[dict], num_results: int = 5) -> Dict:
        """
        Generate a new report from user brief + search results.
        
        Args:
            brief: User's textual requirements/brief
            search_results: List of relevant chunks from semantic search
            num_results: How many search results to use
        
        Returns:
            {
                'status': 'success' | 'error',
                'report_title': '...',
                'report_content': '...',
                'source_documents': [...],
                'generation_prompt': '...'
            }
        """
        # Select top N results
        top_results = search_results[:num_results]
        
        # Build context from search results
        context = self._build_context(top_results)
        
        # Generate report via LLM
        prompt = self._build_prompt(brief, context)
        
        try:
            generated_content = self._call_ollama(prompt)
            
            return {
                'status': 'success',
                'report_title': f"Synthesized Report: {brief[:50]}",
                'report_content': generated_content,
                'source_documents': [
                    {
                        'report_id': r['report_id'],
                        'heading': r['heading'],
                        'page_range': r['page_range'],
                        'similarity': r['similarity_score']
                    }
                    for r in top_results
                ],
                'generation_timestamp': datetime.now().isoformat(),
                'num_sources': len(top_results)
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'brief': brief
            }
    
    def _build_context(self, search_results: List[dict]) -> str:
        """
        Build context string from search results.
        
        Args:
            search_results: List of {text, heading, report_id, ...}
        
        Returns:
            Formatted context block
        """
        context_parts = []
        
        for i, result in enumerate(search_results, 1):
            context_parts.append(f"""
Report {i}: {result['report_id']} - {result['heading']}
Source: Pages {result['page_range']}
Confidence: {result['similarity_score']:.2%}

{result['text'][:200]}
---
""")
        
        return "\n".join(context_parts)
    
    def _build_prompt(self, brief: str, context: str) -> str:
        """
        Build LLM prompt for report generation.
        
        Args:
            brief: User's requirements
            context: Relevant context from search results
        
        Returns:
            Full prompt for LLM
        """
        return f"""Technischer Report-Generator. Schreibe einen kurzen technischen Bericht.

Thema: {brief}

Kontext:
{context}

Schreibe einen kurzen Bericht (max 300 Worte) mit: Einleitung, Analyse, Ergebnis.
"""
    
    def _call_ollama(self, prompt: str, max_tokens: int = 300) -> str:
        """
        Call Ollama LLM to generate text.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum output tokens
        
        Returns:
            Generated text
        """
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.5,  # Lower for more consistent output
                    "top_p": 0.8,
                    "num_predict": max_tokens
                },
                timeout=300  # Longer timeout for large models
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()
        except Exception as e:
            raise Exception(f"Ollama LLM error: {e}")


if __name__ == "__main__":
    # Test
    generator = DocumentGenerator()
    
    # Mock search results
    test_results = [
        {
            'report_id': '001',
            'heading': 'Windkraftsimulation',
            'page_range': '5-7',
            'similarity_score': 0.65,
            'text': 'Die Windkraftsimulation zeigt die Belastung des Rahmens unter extremen Windbedingungen...'
        }
    ]
    
    result = generator.generate_report(
        brief="Fahrzeug mit Bruchgefahr im Rahmen unter Windbedingungen",
        search_results=test_results
    )
    
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))
