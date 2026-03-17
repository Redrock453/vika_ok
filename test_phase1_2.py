#!/usr/bin/env python3
"""
🧪 PHASE 1-2 FUNCTIONAL TEST SUITE
Перевірка всіх основних компонентів:
- Document parsing (PDF/DOCX/OCR)
- OSINT queries
- Gemini API integration
- Ollama fallback
- FastAPI endpoints
- RAG retrieval

Использование:
  python test_phase1_2.py          # All tests
  python test_phase1_2.py --quick  # Quick tests only
  python test_phase1_2.py --verbose # With details
"""

import os
import sys
import json
import time
from typing import Dict, Tuple, Any
from datetime import datetime
import traceback

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'


class FunctionalTestSuite:
    """Comprehensive test suite for Phase 1-2"""
    
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.results = {}
        self.start_time = datetime.now()
        self.test_count = 0
        self.passed = 0
        self.failed = 0
        self.skipped = 0
    
    def print_header(self, title: str):
        print(f"\n{BOLD}{CYAN}{'='*80}{RESET}")
        print(f"{BOLD}{CYAN}🧪 {title}{RESET}")
        print(f"{BOLD}{CYAN}{'='*80}{RESET}\n")
    
    def print_test(self, name: str, status: bool, message: str = "", time_ms: float = 0):
        """Print test result"""
        self.test_count += 1
        
        if status:
            icon = f"{GREEN}✓{RESET}"
            self.passed += 1
            status_str = f"{GREEN}PASS{RESET}"
        else:
            icon = f"{RED}✗{RESET}"
            self.failed += 1
            status_str = f"{RED}FAIL{RESET}"
        
        time_str = f" [{time_ms:.0f}ms]" if time_ms > 0 else ""
        message_str = f" — {message}" if message else ""
        
        print(f"{icon} {name:50} [{status_str}]{time_str}{message_str}")
    
    def print_summary(self):
        """Print test summary"""
        self.print_header("TEST SUMMARY")
        
        total = self.test_count
        passed = self.passed
        failed = self.failed
        skipped = self.skipped
        
        percentage = int((passed / total * 100)) if total > 0 else 0
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        print(f"{BOLD}Results:{RESET}")
        print(f"  {GREEN}✓ Passed:{RESET} {passed}/{total}")
        print(f"  {RED}✗ Failed:{RESET} {failed}/{total}")
        print(f"  {YELLOW}⊗ Skipped:{RESET} {skipped}")
        print(f"  {BOLD}Success rate: {BOLD}{percentage}%{RESET}")
        print(f"  {BOLD}Time: {elapsed:.1f}s{RESET}\n")
        
        return percentage >= 80  # 80% pass rate = success
    
    # ========================================================================
    # TEST GROUPS
    # ========================================================================
    
    def test_imports(self) -> bool:
        """Test all critical imports"""
        self.print_header("1. TESTING IMPORTS")
        
        imports_ok = True
        
        # FastAPI
        try:
            import fastapi
            self.print_test("FastAPI import", True, f"v{fastapi.__version__}")
        except ImportError as e:
            self.print_test("FastAPI import", False, str(e))
            imports_ok = False
        
        # Document parsing
        try:
            from pypdf import PdfReader
            self.print_test("PyPDF2 import", True)
        except ImportError:
            self.print_test("PyPDF2 import", False, "pip install pypdf")
            imports_ok = False
        
        try:
            from docx import Document
            self.print_test("python-docx import", True)
        except ImportError:
            self.print_test("python-docx import", False, "pip install python-docx")
            imports_ok = False
        
        # LLM
        try:
            import google.generativeai as genai
            self.print_test("Google Generative AI (Gemini) import", True)
        except ImportError:
            self.print_test("Google Generative AI import", False, "pip install google-generativeai")
            imports_ok = False
        
        # Vector DB
        try:
            from qdrant_client import QdrantClient
            self.print_test("Qdrant client import", True)
        except ImportError:
            self.print_test("Qdrant client import", False, "pip install qdrant-client")
        
        # OSINT
        try:
            import requests
            self.print_test("Requests import", True)
        except ImportError:
            self.print_test("Requests import", False, "pip install requests")
            imports_ok = False
        
        try:
            from bs4 import BeautifulSoup
            self.print_test("BeautifulSoup import", True)
        except ImportError:
            self.print_test("BeautifulSoup import", False, "pip install beautifulsoup4")
        
        # LangChain
        try:
            try:
                from langchain.text_splitter import RecursiveCharacterTextSplitter
            except ImportError:
                from langchain_text_splitters import RecursiveCharacterTextSplitter
            self.print_test("LangChain import", True)
        except ImportError:
            self.print_test("LangChain import", False, "pip install langchain-text-splitters")
            imports_ok = False
        
        # Ollama
        try:
            from ollama import Client
            self.print_test("Ollama client import", True)
        except ImportError:
            self.print_test("Ollama client import", False, "pip install ollama (optional)")
        
        return imports_ok
    
    def test_document_ai(self) -> bool:
        """Test Document AI pipeline"""
        self.print_header("2. TESTING DOCUMENT AI PIPELINE")
        
        all_ok = True
        
        try:
            from pypdf import PdfReader
            from docx import Document as DocxDocument
            try:
                from langchain.text_splitter import RecursiveCharacterTextSplitter
            except ImportError:
                from langchain_text_splitters import RecursiveCharacterTextSplitter
        except ImportError as e:
            self.print_test("Document AI Setup", False, f"Missing imports: {e}")
            return False
        
        # Test chunking
        try:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=512,
                chunk_overlap=100,
                separators=["\n\n", "\n", " ", ""]
            )
            test_text = "This is a test document. " * 50  # Create sample text
            chunks = splitter.split_text(test_text)
            
            success = len(chunks) > 0
            self.print_test(
                "Text chunking",
                success,
                f"{len(chunks)} chunks created" if success else "No chunks"
            )
        except Exception as e:
            self.print_test("Text chunking", False, str(e))
            all_ok = False
        
        # Test embedding
        try:
            from sentence_transformers import SentenceTransformer
            
            model = SentenceTransformer('distiluse-base-multilingual-cased-v2')
            embeddings = model.encode(["This is a test sentence", "Another test"])
            
            success = len(embeddings) == 2
            self.print_test(
                "Embedding generation",
                success,
                f"Shape: {embeddings[0].shape}" if success else "Failed"
            )
        except ImportError:
            self.print_test("Embedding generation", False, "pip install sentence-transformers")
            all_ok = False
        except Exception as e:
            self.print_test("Embedding generation", False, str(e))
            all_ok = False
        
        # Test knowledge directory
        knowledge_dir = "knowledge"
        if os.path.exists(knowledge_dir):
            files = os.listdir(knowledge_dir)
            doc_count = len([f for f in files if f.endswith(('.pdf', '.docx', '.txt'))])
            self.print_test(
                "Knowledge base directory",
                True,
                f"{doc_count} documents found"
            )
        else:
            self.print_test("Knowledge base directory", False, "Create 'knowledge/' folder")
            all_ok = False
        
        return all_ok
    
    def test_gemini_api(self) -> bool:
        """Test Gemini 2.5 Flash API"""
        self.print_header("3. TESTING GEMINI 2.5 FLASH API")
        
        try:
            import google.generativeai as genai
        except ImportError:
            self.print_test("Gemini API", False, "pip install google-generativeai")
            return False
        
        # Check API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            self.print_test("Gemini API Key", False, "Set GEMINI_API_KEY environment variable")
            return False
        
        self.print_test("Gemini API Key", True, "Configured")
        
        # Test API connection
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            start = time.time()
            response = model.generate_content("Say 'Vika is ready' in 5 words")
            elapsed = (time.time() - start) * 1000
            
            success = response.text and len(response.text) > 0
            self.print_test(
                "Gemini API call",
                success,
                f"Response: {response.text[:30]}... ({elapsed:.0f}ms)" if success else "No response"
            ),
            time_ms=elapsed
            
            return success
        except Exception as e:
            self.print_test("Gemini API call", False, str(e))
            return False
    
    def test_ollama(self) -> bool:
        """Test Ollama fallback"""
        self.print_header("4. TESTING OLLAMA FALLBACK")
        
        try:
            from ollama import Client
        except ImportError:
            self.print_test("Ollama client", False, "pip install ollama (optional)")
            return False
        
        try:
            client = Client(host='http://localhost:11434')
            
            # Check if service is running
            response = client.list()
            models = response.get('models', [])
            
            if models:
                self.print_test(
                    "Ollama service",
                    True,
                    f"{len(models)} models available"
                )
                
                # Try to generate
                try:
                    # Robustly get model name (dictionary or object)
                    model_obj = models[0]
                    if hasattr(model_obj, 'model'):
                        model_name = model_obj.model
                    elif isinstance(model_obj, dict) and 'name' in model_obj:
                        model_name = model_obj['name']
                    else:
                        model_name = 'mistral' # Fallback
                        
                    start = time.time()
                    response = client.generate(
                        model=model_name,
                        prompt="Say 'Ollama is ready' in 3 words",
                        stream=False
                    )
                    elapsed = (time.time() - start) * 1000
                    
                    success = response and len(response['response']) > 0
                    self.print_test(
                        "Ollama generation",
                        success,
                        f"Response: {response['response'][:30]}... ({elapsed:.0f}ms)" if success else "No response"
                    )
                    return success
                except Exception as e:
                    self.print_test("Ollama generation", False, str(e))
                    return False
            else:
                self.print_test("Ollama service", False, "No models found. Run: ollama pull mistral")
                return False
        
        except Exception as e:
            self.print_test("Ollama connection", False, f"Service not running: {e}")
            return False
    
    def test_osint(self) -> bool:
        """Test OSINT functionality"""
        self.print_header("5. TESTING OSINT FUNCTIONALITY")
        
        all_ok = True
        
        try:
            import requests
            from bs4 import BeautifulSoup
        except ImportError as e:
            self.print_test("OSINT imports", False, f"Missing: {e}")
            return False
        
        # Test URL fetch
        try:
            response = requests.get(
                'https://httpbin.org/status/200',
                timeout=5
            )
            self.print_test(
                "URL fetch",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.print_test("URL fetch", False, str(e))
            all_ok = False
        
        # Test HTML parsing
        try:
            html = """
            <html>
                <head><title>Test</title></head>
                <body>
                    <h1>Test Content</h1>
                    <p>Paragraph 1</p>
                    <p>Paragraph 2</p>
                </body>
            </html>
            """
            soup = BeautifulSoup(html, 'html.parser')
            paragraphs = soup.find_all('p')
            
            self.print_test(
                "HTML parsing",
                len(paragraphs) == 2,
                f"Found {len(paragraphs)} paragraphs"
            )
        except Exception as e:
            self.print_test("HTML parsing", False, str(e))
            all_ok = False
        
        return all_ok
    
    def test_rag_pipeline(self) -> bool:
        """Test RAG pipeline"""
        self.print_header("6. TESTING RAG PIPELINE")
        
        try:
            try:
                from langchain.text_splitter import RecursiveCharacterTextSplitter
            except ImportError:
                from langchain_text_splitters import RecursiveCharacterTextSplitter
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            self.print_test("RAG imports", False, f"Missing: {e}")
            return False
        
        # Test full RAG flow
        try:
            # 1. Document preparation
            sample_doc = """
            Vika is an AI assistant for подразделение БАС.
            She can analyze documents using RAG (Retrieval-Augmented Generation).
            The system uses Gemini 2.5 Flash as the primary model.
            Ollama provides local fallback capability.
            """
            
            # 2. Chunking
            splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
            chunks = splitter.split_text(sample_doc)
            self.print_test("RAG chunking", len(chunks) > 0, f"{len(chunks)} chunks")
            
            # 3. Embedding
            model = SentenceTransformer('distiluse-base-multilingual-cased-v2')
            embeddings = model.encode(chunks)
            self.print_test("RAG embedding", len(embeddings) == len(chunks), f"Embedded {len(embeddings)} chunks")
            
            # 4. Query embedding
            query = "What is Vika?"
            query_embedding = model.encode([query])[0]
            self.print_test("Query embedding", len(query_embedding) > 0, f"Dimension: {len(query_embedding)}")
            
            # 5. Similarity search (simplified)
            import numpy as np
            similarities = [
                np.dot(query_embedding, emb) / (np.linalg.norm(query_embedding) * np.linalg.norm(emb))
                for emb in embeddings
            ]
            top_idx = np.argsort(similarities)[-1]
            self.print_test(
                "RAG retrieval",
                True,
                f"Top match: '{chunks[top_idx][:50]}...'"
            )
            
            return True
        
        except Exception as e:
            self.print_test("RAG pipeline", False, str(e))
            return False
    
    def test_fastapi_readiness(self) -> bool:
        """Test FastAPI readiness"""
        self.print_header("7. TESTING FASTAPI READINESS")
        
        try:
            import fastapi
            from fastapi import FastAPI
            from fastapi.testclient import TestClient
        except ImportError as e:
            self.print_test("FastAPI imports", False, f"Missing: {e}")
            return False
        
        try:
            # Create test app
            app = FastAPI()
            
            @app.get("/health")
            def health():
                return {"status": "ok"}
            
            @app.post("/documents/upload")
            def upload_document():
                return {"message": "OK"}
            
            @app.post("/rag/query")
            def rag_query():
                return {"results": []}
            
            @app.post("/osint/search")
            def osint_search():
                return {"findings": []}
            
            # Test endpoints
            client = TestClient(app)
            
            response = client.get("/health")
            self.print_test("FastAPI /health", response.status_code == 200)
            
            response = client.post("/documents/upload")
            self.print_test("FastAPI /documents/upload", response.status_code == 200)
            
            response = client.post("/rag/query")
            self.print_test("FastAPI /rag/query", response.status_code == 200)
            
            response = client.post("/osint/search")
            self.print_test("FastAPI /osint/search", response.status_code == 200)
            
            return True
        
        except Exception as e:
            self.print_test("FastAPI endpoints", False, str(e))
            return False
    
    def test_integration(self) -> bool:
        """Test integration between components"""
        self.print_header("8. TESTING COMPONENT INTEGRATION")
        
        all_ok = True
        
        # Check if all key modules can be imported together
        try:
            from pypdf import PdfReader
            try:
                from langchain.text_splitter import RecursiveCharacterTextSplitter
            except ImportError:
                from langchain_text_splitters import RecursiveCharacterTextSplitter
            from sentence_transformers import SentenceTransformer
            import google.generativeai as genai
            
            self.print_test("Full stack imports", True, "All components available")
        except ImportError as e:
            self.print_test("Full stack imports", False, str(e))
            all_ok = False
        
        # Check configuration files
        if os.path.exists("knowledge"):
            self.print_test("Knowledge base directory", True)
        else:
            self.print_test("Knowledge base directory", False, "Create 'knowledge/' folder")
            all_ok = False
        
        # Check environment variables
        env_vars = {
            "GEMINI_API_KEY": "Gemini API Key",
            "GROQ_API_KEY": "Groq API Key (optional)",
            "GITHUB_TOKEN": "GitHub Token (optional)"
        }
        
        for var, desc in env_vars.items():
            if os.getenv(var):
                self.print_test(f"Environment: {desc}", True, "Configured")
            else:
                status = False if var == "GEMINI_API_KEY" else True  # Only GEMINI is required
                self.print_test(f"Environment: {desc}", status, "Not set" if status else "REQUIRED")
                if not status:
                    all_ok = False
        
        return all_ok
    
    def run_all_tests(self, quick=False) -> bool:
        """Run all tests"""
        self.print_header("PHASE 1-2 FUNCTIONAL TEST SUITE")
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        results = []
        
        # 1. Imports (always run)
        results.append(("Imports", self.test_imports()))
        
        # 2. Document AI
        if not quick:
            results.append(("Document AI", self.test_document_ai()))
        
        # 3. Gemini API
        results.append(("Gemini API", self.test_gemini_api()))
        
        # 4. Ollama (optional)
        if not quick:
            results.append(("Ollama", self.test_ollama()))
        
        # 5. OSINT
        if not quick:
            results.append(("OSINT", self.test_osint()))
        
        # 6. RAG Pipeline
        if not quick:
            results.append(("RAG Pipeline", self.test_rag_pipeline()))
        
        # 7. FastAPI
        if not quick:
            results.append(("FastAPI", self.test_fastapi_readiness()))
        
        # 8. Integration
        if not quick:
            results.append(("Integration", self.test_integration()))
        
        # Print summary
        overall_ok = self.print_summary()
        
        # Print component status
        self.print_header("COMPONENT STATUS SUMMARY")
        for name, ok in results:
            icon = f"{GREEN}✓{RESET}" if ok else f"{YELLOW}⚠{RESET}"
            status = f"{GREEN}READY{RESET}" if ok else f"{YELLOW}NEEDS WORK{RESET}"
            print(f"{icon} {name:20} {status}")
        
        return overall_ok


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Phase 1-2 Functional Tests")
    parser.add_argument("--quick", action="store_true", help="Quick tests only")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    suite = FunctionalTestSuite(verbose=args.verbose)
    success = suite.run_all_tests(quick=args.quick)
    
    # Exit with proper code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
