#!/bin/bash
echo '=== Проверка состояния контейнеров ==='
docker compose ps
echo ''
echo '=== Последние логи бота ==='
docker compose logs vika_bot --tail=20
echo ''
echo '=== Проверка подключения к Qdrant ==='
docker compose exec vika_bot python3 -c "
from qdrant_client import QdrantClient
client = QdrantClient(url='http://qdrant:6333')
try:
    collections = client.get_collections()
    print('Коллекции:', [c.name for c in collections.collections])
except Exception as e:
    print('Ошибка:', e)
" 2>&1 | grep -v 'level=warning'
