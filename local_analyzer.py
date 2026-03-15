import os
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
logger = logging.getLogger("LocalAnalyzer")

class LocalAnalyzer:
    def __init__(self):
        self.qdrant = QdrantManager()
        self.model = SentenceTransformer('distiluse-base-multilingual-cased-v2')
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\nclass ", "\ndef ", "\n", " ", ""]
        )

    def analyze_dir(self, dir_path):
        """Анализирует локальную директорию и загружает в Qdrant"""
        base_path = Path(dir_path)
        if not base_path.exists():
            logger.error(f"Путь не найден: {dir_path}")
            return False

        logger.info(f"Анализ директории: {base_path.absolute()}")
        
        # Рекурсивный обход
        for file_path in base_path.rglob("*"):
            # Пропускаем папки и лишние файлы
            if not file_path.is_file(): continue
            if any(part in file_path.parts for part in [".git", "node_modules", "__pycache__", "venv"]): continue
            
            # Только текстовые и кодовые файлы
            if not file_path.suffix in [".py", ".md", ".txt", ".js", ".html", ".css", ".json"]: continue

            logger.info(f"Анализ файла: {file_path.relative_to(base_path)}")
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                
                chunks = self.splitter.split_text(text)
                if chunks:
                    embeddings = self.model.encode(chunks)
                    self.qdrant.upsert_documents(
                        chunks, 
                        embeddings, 
                        source_name=f"local:{base_path.name}/{file_path.relative_to(base_path)}"
                    )
            except Exception as e:
                logger.error(f"Ошибка при анализе файла {file_path.name}: {e}")
        
        logger.info(f"Анализ директории {base_path.name} завершен!")
        return True

if __name__ == "__main__":
    # Анализируем проект BAS-SUPERGROK
    analyzer = LocalAnalyzer()
    analyzer.analyze_dir(r"C:\Users\admin\BAS-SUPERGROK")
