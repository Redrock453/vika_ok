import os
import requests
import logging
from pathlib import Path
from qdrant_manager import QdrantManager
from sentence_transformers import SentenceTransformer
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
except ImportError:
    from langchain_text_splitters import RecursiveCharacterTextSplitter

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GitHubAnalyzer")

class GitHubAnalyzer:
    def __init__(self, token=None):
        self.token = token or os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
        self.headers = {"Authorization": f"token {self.token}"} if self.token else {}
        self.qdrant = QdrantManager()
        self.model = SentenceTransformer('distiluse-base-multilingual-cased-v2')
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\nclass ", "\ndef ", "\n", " ", ""]
        )

    def get_repo_structure(self, repo_url):
        """Получает структуру репозитория через GitHub API"""
        # Преобразуем URL (например, https://github.com/user/repo -> user/repo)
        parts = repo_url.rstrip("/").split("/")
        repo_path = f"{parts[-2]}/{parts[-1]}"
        
        api_url = f"https://api.github.com/repos/{repo_path}/contents"
        logger.info(f"Анализ репозитория: {repo_path}")
        
        try:
            response = requests.get(api_url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json(), repo_path
            else:
                logger.error(f"Ошибка API: {response.status_code} - {response.text}")
                return None, repo_path
        except Exception as e:
            logger.error(f"Ошибка подключения: {e}")
            return None, repo_path

    def analyze_file(self, file_info, repo_name):
        """Скачивает и анализирует отдельный файл"""
        if file_info["type"] != "file":
            return
        
        # Пропускаем бинарные файлы
        if not any(file_info["name"].endswith(ext) for ext in [".py", ".md", ".txt", ".js", ".html", ".css", ".json"]):
            return

        logger.info(f"Анализ файла: {file_info['path']}")
        try:
            content_res = requests.get(file_info["download_url"], timeout=10)
            if content_res.status_code == 200:
                text = content_res.text
                chunks = self.splitter.split_text(text)
                if chunks:
                    embeddings = self.model.encode(chunks)
                    self.qdrant.upsert_documents(
                        chunks, 
                        embeddings, 
                        source_name=f"github:{repo_name}/{file_info['path']}"
                    )
        except Exception as e:
            logger.error(f"Ошибка при анализе файла {file_info['name']}: {e}")

    def run(self, repo_url):
        """Запуск полного цикла анализа"""
        contents, repo_name = self.get_repo_structure(repo_url)
        if not contents:
            return False
        
        # Рекурсивный обход (упрощенно для первого уровня)
        for item in contents:
            if item["type"] == "file":
                self.analyze_file(item, repo_name)
            elif item["type"] == "dir":
                # Здесь можно добавить рекурсию для глубокого анализа
                logger.info(f"Найдена директория: {item['path']} (пропуск в демо-режиме)")
        
        logger.info(f"Анализ репозитория {repo_name} завершен!")
        return True

if __name__ == "__main__":
    # Тестовый запуск на публичном репозитории, если токен не задан
    analyzer = GitHubAnalyzer()
    test_repo = "https://github.com/qdrant/qdrant-client"
    analyzer.run(test_repo)
