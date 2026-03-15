# 🐳 QDRANT SETUP GUIDE - VIKA AI

## 📊 OVERVIEW
Qdrant is a high-performance vector database used to provide Vika with **Persistent Memory**. Unlike the current in-memory RAG, Qdrant allows documents to be stored on disk and retrieved instantly even after a system restart.

---

## 🚀 1. DOCKER DEPLOYMENT
To run Qdrant locally, use the following Docker command:

```bash
docker run -p 6333:6333 -p 6334:6334 \
    -v qdrant_storage:/qdrant/storage:z \
    qdrant/qdrant
```

### Key Parameters:
- `-p 6333:6333`: REST API port (used by `qdrant-client`).
- `-p 6334:6334`: gRPC port (high-performance).
- `-v qdrant_storage:/qdrant/storage`: Persistent volume for your data.

---

## 🛠️ 2. PYTHON INTEGRATION
Replace the current `numpy` similarity search with the official `qdrant-client`.

### Installation
```bash
pip install qdrant-client
```

### Connection & Collection Setup
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# Initialize client
client = QdrantClient("localhost", port=6333)

# Create collection (only once)
collection_name = "vika_knowledge"

client.recreate_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(size=512, distance=Distance.COSINE),
)
```

### Upserting Documents
```python
from qdrant_client.models import PointStruct

points = [
    PointStruct(
        id=idx,
        vector=embedding.tolist(),
        payload={"text": chunk_text, "source": "manual.pdf"}
    )
    for idx, (embedding, chunk_text) in enumerate(zip(embeddings, chunks))
]

client.upsert(
    collection_name=collection_name,
    points=points
)
```

### Searching
```python
search_result = client.search(
    collection_name=collection_name,
    query_vector=query_embedding.tolist(),
    limit=3
)

for hit in search_result:
    print(f"Score: {hit.score:.4f} | Text: {hit.payload['text'][:100]}...")
```

---

## 🔍 3. WEB INTERFACE (DASHBOARD)
Once Qdrant is running, you can access the interactive dashboard at:
👉 **[http://localhost:6333/dashboard](http://localhost:6333/dashboard)**

Use the dashboard to:
- Monitor collection health.
- Manually run search queries.
- Inspect document payloads.

---

## 🎖️ NEXT STEPS
1. Verify Docker installation.
2. Start the Qdrant container.
3. Run the migration script (to be provided in Day 1 of Phase 3).

*Created 15 березня 2026*
*For в/ч А7022 | Позывной БАС*
