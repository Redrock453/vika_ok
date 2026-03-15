import os
import requests
import logging
import argparse
from pathlib import Path
from qdrant_manager import QdrantManager
from sentence_transformers import SentenceTransformer
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
except ImportError:
    from langchain_text_splitters import RecursiveCharacterTextSplitter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GitHubAnalyzer")

class GitHubAnalyzer:
    def __init__(self, token=None):
        self.token = token or os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
        self.headers = {"Authorization": f"token {self.token}"} if self.token else {}
        self.qdrant = QdrantManager()
        self.model = SentenceTransformer('distiluse-base-multilingual-cased-v2')
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    def run(self, repo_url, branch=None):
        parts = repo_url.rstrip("/").split("/")
        repo_path = f"{parts[-2]}/{parts[-1]}"
        api_url = f"https://api.github.com/repos/{repo_path}/contents"
        if branch: api_url += f"?ref={branch}"
        
        logger.info(f"Indexing repo: {repo_path} (branch: {branch or 'default'})")
        res = requests.get(api_url, headers=self.headers)
        if res.status_code != 200:
            return f"Error: {res.status_code} - {res.text}"
        
        contents = res.json()
        for item in contents:
            if item["type"] == "file" and any(item["name"].endswith(ext) for ext in [".py", ".md", ".txt", ".js"]):
                f_res = requests.get(item["download_url"])
                chunks = self.splitter.split_text(f_res.text)
                self.qdrant.upsert_documents(chunks, self.model.encode(chunks), source_name=f"github:{repo_path}/{item['path']}")
        
        return f"Successfully indexed {repo_path}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_url")
    parser.add_argument("--branch", default=None)
    args = parser.parse_args()
    
    analyzer = GitHubAnalyzer()
    print(analyzer.run(args.repo_url, args.branch))
