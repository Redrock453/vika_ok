from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

client = QdrantClient(url='http://localhost:6333')

# Проверяем, существует ли коллекция
try:
    collections = client.get_collections()
    if any(c.name == 'vika_knowledge' for c in collections.collections):
        print('Collection vika_knowledge already exists')
    else:
        # Создаём коллекцию
        client.create_collection(
            collection_name='vika_knowledge',
            vectors_config=VectorParams(size=512, distance=Distance.COSINE)
        )
        print('Collection vika_knowledge created successfully')
except Exception as e:
    print(f'Error: {e}')
