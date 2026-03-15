import os
import logging
from pathlib import Path
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
except ImportError:
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except ImportError:
        logger.error("RecursiveCharacterTextSplitter not found. Install: pip install langchain-text-splitters")
        raise

from sentence_transformers import SentenceTransformer
from qdrant_manager import QdrantManager
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Migrator")

class KnowledgeMigrator:
    def __init__(self, knowledge_dir="knowledge"):
        self.knowledge_dir = Path(knowledge_dir)
        self.qdrant = QdrantManager()
        # Using the same model as in examples.py
        self.model = SentenceTransformer('distiluse-base-multilingual-cased-v2')
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=100,
            separators=["\n\n", "\n", " ", ""]
        )

    def migrate(self):
        if not self.knowledge_dir.exists():
            logger.error(f"Knowledge directory {self.knowledge_dir} not found")
            return

        # 1. Prepare collection
        self.qdrant.create_collection(vector_size=512)

        # 2. Process files
        files = list(self.knowledge_dir.glob("*.md")) + \
                list(self.knowledge_dir.glob("*.txt"))
        
        if not files:
            logger.warning("No files found in knowledge directory")
            return

        for file_path in files:
            logger.info(f"Processing {file_path.name}...")
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
                
                chunks = self.splitter.split_text(text)
                if not chunks:
                    continue
                
                embeddings = self.model.encode(chunks)
                self.qdrant.upsert_documents(chunks, embeddings, source_name=file_path.name)
                
            except Exception as e:
                logger.error(f"Error processing {file_path.name}: {e}")

        logger.info("Migration completed successfully!")

if __name__ == "__main__":
    # Ensure we are in the right directory
    os.chdir(Path(__file__).parent)
    migrator = KnowledgeMigrator(knowledge_dir="knowledge")
    migrator.migrate()
