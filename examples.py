#!/usr/bin/env python3
"""
💡 PHASE 1-2 USAGE EXAMPLES
Примеры того, как использовать все компоненты

Используй ці приклади для тестування функціональності
"""

import os
import json
from typing import List


# ============================================================================
# EXAMPLE 1: GEMINI API USAGE
# ============================================================================

def example_gemini_api():
    """Пример 1: Використання Gemini API"""
    print("\n" + "="*80)
    print("EXAMPLE 1: GEMINI 2.5 FLASH API")
    print("="*80 + "\n")
    
    try:
        import google.generativeai as genai
    except ImportError:
        print("❌ Missing google-generativeai. Install: pip install google-generativeai")
        return
    
    # Get API key from environment
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set. Set environment variable first.")
        return
    
    # Configure API
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    print("📍 Connecting to Gemini 2.5 Flash...")
    
    # Example 1: Simple question
    print("\n1️⃣  Simple Question:")
    response = model.generate_content("What is Strategic Intelligence AI?")
    print(f"Q: What is Strategic Intelligence AI?")
    print(f"A: {response.text[:200]}...")
    
    # Example 2: Code analysis
    print("\n2️⃣  Code Analysis:")
    code = """
    def analyze_document(doc_path):
        with open(doc_path) as f:
            text = f.read()
        return text.split()
    """
    response = model.generate_content(f"Analyze this Python code:\n{code}")
    print(f"A: {response.text[:200]}...")
    
    # Example 3: Multi-turn conversation
    print("\n3️⃣  Multi-turn Conversation:")
    chat = model.start_chat(history=[])
    
    response1 = chat.send_message("Who is Vika?")
    print(f"Q: Who is Vika?")
    print(f"A: {response1.text[:100]}...")
    
    response2 = chat.send_message("What are her main features?")
    print(f"Q: What are her main features?")
    print(f"A: {response2.text[:100]}...")
    
    print("\n✓ Gemini API working correctly!")


# ============================================================================
# EXAMPLE 2: DOCUMENT AI PIPELINE
# ============================================================================

def example_document_ai():
    """Пример 2: Document AI Pipeline"""
    print("\n" + "="*80)
    print("EXAMPLE 2: DOCUMENT AI PIPELINE")
    print("="*80 + "\n")
    
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("❌ Missing dependencies. Install: pip install langchain sentence-transformers")
        return
    
    # Sample document
    sample_doc = """
    Vika is an AI agent developed for подразделение БАС.
    She can analyze documents using RAG (Retrieval-Augmented Generation).
    The system uses Gemini 2.5 Flash as the primary LLM.
    Ollama provides local fallback capability.
    """
    Key features:
    - Document parsing (PDF, DOCX, TXT)
    - OCR for scanned documents
    - OSINT automation
    - RAG-based retrieval
    - Signal Bot integration
    
    Phase 1-2 includes:
    - Document upload and analysis
    - OSINT queries
    - Gemini API integration
    - Local LLM fallback
    """
    
    print("📄 Sample document loaded")
    print(f"   Length: {len(sample_doc)} characters\n")
    
    # Step 1: Chunking
    print("1️⃣  TEXT CHUNKING:")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=150,
        chunk_overlap=30,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = splitter.split_text(sample_doc)
    print(f"   Created {len(chunks)} chunks")
    for i, chunk in enumerate(chunks[:3], 1):
        print(f"   Chunk {i}: {chunk[:60]}...")
    
    # Step 2: Embedding
    print("\n2️⃣  EMBEDDING GENERATION:")
    model = SentenceTransformer('distiluse-base-multilingual-cased-v2')
    embeddings = model.encode(chunks)
    print(f"   Embedded {len(embeddings)} chunks")
    print(f"   Embedding dimension: {len(embeddings[0])}")
    print(f"   First embedding (first 5 values): {embeddings[0][:5]}")
    
    # Step 3: Query and Retrieval
    print("\n3️⃣  QUERY AND RETRIEVAL:")
    query = "What is Vika?"
    query_embedding = model.encode([query])[0]
    
    # Calculate similarities
    import numpy as np
    similarities = []
    for emb in embeddings:
        similarity = np.dot(query_embedding, emb) / (
            np.linalg.norm(query_embedding) * np.linalg.norm(emb) + 1e-10
        )
        similarities.append(similarity)
    
    # Get top-3 results
    top_indices = np.argsort(similarities)[-3:][::-1]
    print(f"   Query: '{query}'")
    print(f"   Top results:")
    for i, idx in enumerate(top_indices, 1):
        print(f"   {i}. Score: {similarities[idx]:.3f} — {chunks[idx][:60]}...")
    
    print("\n✓ Document AI pipeline working correctly!")


# ============================================================================
# EXAMPLE 3: OSINT
# ============================================================================

def example_osint():
    """Пример 3: OSINT функциональность"""
    print("\n" + "="*80)
    print("EXAMPLE 3: OSINT FUNCTIONALITY")
    print("="*80 + "\n")
    
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        print("❌ Missing requests or beautifulsoup4. Install: pip install requests beautifulsoup4")
        return
    
    # Example 1: HTTP request
    print("1️⃣  HTTP REQUEST:")
    try:
        response = requests.get('https://httpbin.org/json', timeout=5)
        print(f"   URL: https://httpbin.org/json")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Example 2: HTML parsing
    print("\n2️⃣  HTML PARSING:")
    html_content = """
    <html>
        <head>
            <title>OSINT Example Page</title>
            <meta name="description" content="Example page for OSINT testing">
        </head>
        <body>
            <h1>Company Information</h1>
            <div class="info">
                <p>Founded: 2020</p>
                <p>Location: Ukraine</p>
                <p>Focus: AI Development</p>
            </div>
            <div class="contacts">
                <email>info@example.com</email>
            </div>
        </body>
    </html>
    """
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    title = soup.find('title').text if soup.find('title') else "N/A"
    description = soup.find('meta', {'name': 'description'})
    description_content = description.get('content') if description else "N/A"
    paragraphs = soup.find_all('p')
    
    print(f"   Title: {title}")
    print(f"   Description: {description_content}")
    print(f"   Found {len(paragraphs)} paragraphs:")
    for p in paragraphs:
        print(f"   - {p.text}")
    
    print("\n✓ OSINT functionality working correctly!")


# ============================================================================
# EXAMPLE 4: FASTAPI ENDPOINTS
# ============================================================================

def example_fastapi():
    """Пример 4: FastAPI endpoints"""
    print("\n" + "="*80)
    print("EXAMPLE 4: FASTAPI ENDPOINTS")
    print("="*80 + "\n")
    
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
    except ImportError:
        print("❌ Missing fastapi. Install: pip install fastapi")
        return
    
    # Create test app
    app = FastAPI()
    
    @app.get("/health")
    def health_check():
        return {
            "status": "healthy",
            "components": {
                "document_ai": "ready",
                "gemini": "ready",
                "osint": "ready"
            }
        }
    
    @app.post("/documents/upload")
    def upload_document(filename: str, content: str):
        return {
            "status": "success",
            "file": filename,
            "chunks": len(content.split()),
            "embeddings": "generated"
        }
    
    @app.post("/rag/query")
    def rag_query(query: str, top_k: int = 5):
        return {
            "query": query,
            "results": [
                {"text": "Result 1", "score": 0.95},
                {"text": "Result 2", "score": 0.87},
                {"text": "Result 3", "score": 0.78}
            ]
        }
    
    @app.post("/osint/search")
    def osint_search(url: str):
        return {
            "url": url,
            "findings": {
                "title": "Example title",
                "description": "Example description",
                "paragraphs": 3,
                "emails": 1
            }
        }
    
    # Test endpoints
    client = TestClient(app)
    
    print("1️⃣  GET /health:")
    response = client.get("/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
    
    print("\n2️⃣  POST /documents/upload:")
    response = client.post("/documents/upload?filename=test.pdf&content=sample content here")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
    
    print("\n3️⃣  POST /rag/query:")
    response = client.post("/rag/query?query=What+is+Vika?&top_k=3")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
    
    print("\n4️⃣  POST /osint/search:")
    response = client.post("/osint/search?url=https://example.com")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
    
    print("\n✓ FastAPI endpoints working correctly!")


# ============================================================================
# EXAMPLE 5: OLLAMA FALLBACK
# ============================================================================

def example_ollama():
    """Пример 5: Ollama fallback"""
    print("\n" + "="*80)
    print("EXAMPLE 5: OLLAMA FALLBACK")
    print("="*80 + "\n")
    
    try:
        from ollama import Client
    except ImportError:
        print("❌ Missing ollama. Install: pip install ollama")
        print("   (This is optional - Gemini API is primary)")
        return
    
    try:
        client = Client(host='http://localhost:11434')
        
        print("📍 Connecting to Ollama...")
        
        # List available models
        response = client.list()
        models = response.get('models', [])
        
        if models:
            print(f"   Available models: {len(models)}")
            for model in models[:3]:
                print(f"   - {model['name']}")
            
            # Try to generate
            print(f"\n💬 Generating with Ollama...")
            model_name = models[0]['name']
            response = client.generate(
                model=model_name,
                prompt="What is Strategic Intelligence AI?",
                stream=False
            )
            print(f"   Model: {model_name}")
            print(f"   Response: {response['response'][:200]}...")
            print("\n✓ Ollama fallback working correctly!")
        else:
            print("   ⚠️  No models found")
            print("   Run: ollama pull mistral")
    
    except Exception as e:
        print(f"   ⚠️  Ollama not running: {e}")
        print("   This is optional. Gemini API is primary.")


# ============================================================================
# EXAMPLE 6: COMPLETE RAG WORKFLOW
# ============================================================================

def example_rag_workflow():
    """Пример 6: Complete RAG workflow"""
    print("\n" + "="*80)
    print("EXAMPLE 6: COMPLETE RAG WORKFLOW")
    print("="*80 + "\n")
    
    try:
        import google.generativeai as genai
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("❌ Missing dependencies")
        return
    
    # Setup
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set")
        return
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=50)
    embedding_model = SentenceTransformer('distiluse-base-multilingual-cased-v2')
    
    # Documents
    documents = [
        "Vika is an AI assistant for подразделение БАС. She specializes in document analysis and OSINT.",
        "The system uses Gemini 2.5 Flash as the primary LLM with Ollama as fallback.",
        "Phase 1-2 includes document parsing, OSINT, and RAG retrieval.",
        "Phase 3 will add Qdrant, Signal Bot, and GitHub analyzer."
    ]
    
    print("📚 RAG WORKFLOW STEPS:\n")
    
    # Step 1: Document processing
    print("1️⃣  Document Processing:")
    chunks = []
    for doc in documents:
        doc_chunks = splitter.split_text(doc)
        chunks.extend(doc_chunks)
    print(f"   Processed {len(documents)} documents into {len(chunks)} chunks")
    
    # Step 2: Embedding
    print("\n2️⃣  Embedding:")
    embeddings = embedding_model.encode(chunks)
    print(f"   Created {len(embeddings)} embeddings (dim: {len(embeddings[0])})")
    
    # Step 3: Query processing
    print("\n3️⃣  Query Processing:")
    query = "What is Vika and what does she do?"
    query_embedding = embedding_model.encode([query])[0]
    print(f"   Query: '{query}'")
    
    # Step 4: Retrieval
    print("\n4️⃣  Retrieval:")
    import numpy as np
    similarities = [
        np.dot(query_embedding, emb) / (np.linalg.norm(query_embedding) * np.linalg.norm(emb) + 1e-10)
        for emb in embeddings
    ]
    top_indices = np.argsort(similarities)[-3:][::-1]
    
    context = "\n".join([chunks[i] for i in top_indices])
    print(f"   Retrieved top-3 relevant chunks:")
    for i, idx in enumerate(top_indices, 1):
        print(f"   {i}. {chunks[idx][:60]}... (score: {similarities[idx]:.3f})")
    
    # Step 5: LLM Response
    print("\n5️⃣  LLM Response:")
    prompt = f"""Using this context, answer the question:

Context:
{context}

Question: {query}"""
    
    response = model.generate_content(prompt)
    print(f"   {response.text}")
    
    print("\n✓ Complete RAG workflow executed successfully!")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run all examples"""
    print("\n" + "="*80)
    print("💡 PHASE 1-2 USAGE EXAMPLES")
    print("="*80)
    
    print("\nChoose which example to run:")
    print("1. Gemini API")
    print("2. Document AI Pipeline")
    print("3. OSINT")
    print("4. FastAPI Endpoints")
    print("5. Ollama Fallback")
    print("6. Complete RAG Workflow")
    print("0. Run all")
    
    choice = input("\nEnter your choice (0-6): ").strip()
    
    if choice == "1":
        example_gemini_api()
    elif choice == "2":
        example_document_ai()
    elif choice == "3":
        example_osint()
    elif choice == "4":
        example_fastapi()
    elif choice == "5":
        example_ollama()
    elif choice == "6":
        example_rag_workflow()
    elif choice == "0":
        example_gemini_api()
        example_document_ai()
        example_osint()
        example_fastapi()
        example_ollama()
        example_rag_workflow()
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
