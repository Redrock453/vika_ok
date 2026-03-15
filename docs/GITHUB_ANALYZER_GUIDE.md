# 📁 GITHUB ANALYZER - VIKA AI

## 📊 OVERVIEW
The GitHub Analyzer is Vika's tool for deep intelligence gathering from codebases and technical documentation. It enables Vika to understand complex project structures, analyze code for security or logic, and ingest documentation directly from version control systems.

---

## 🚀 1. SETUP & AUTHENTICATION
Vika uses the GitHub REST API (v3) to interact with repositories. You must provide a **Personal Access Token (PAT)**.

### Create a PAT:
1. Go to **Settings -> Developer Settings -> Personal access tokens**.
2. Select **Generate new token (classic)**.
3. Grant `repo` (Full control of private repositories) and `read:org` scopes.
4. Add the token to your `.env` file:
   ```bash
   GITHUB_PAT=your_token_here
   ```

---

## 🛠️ 2. CORE FUNCTIONALITY
The analyzer performs recursive repository traversal to ingest files into Vika's RAG system.

### Recursive File Ingestion
```python
import requests
import base64

def fetch_repo_files(repo_name, path=""):
    url = f"https://api.github.com/repos/{repo_name}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_PAT}"}
    
    response = requests.get(url, headers=headers)
    items = response.json()
    
    for item in items:
        if item["type"] == "file" and item["name"].endswith((".py", ".md", ".js")):
            content = fetch_file_content(item["url"])
            process_file(item["path"], content)
        elif item["type"] == "dir":
            fetch_repo_files(repo_name, item["path"])

def fetch_file_content(file_url):
    headers = {"Authorization": f"token {GITHUB_PAT}"}
    resp = requests.get(file_url, headers=headers)
    return base64.b64decode(resp.json()["content"]).decode("utf-8")
```

---

## 🏗️ 3. ANALYSIS FLOW
1. **Fetch:** Recursively pull files from target repository.
2. **Chunk:** Split code and documentation into manageable blocks.
3. **Embed:** Create vector representations of the technical content.
4. **Store:** Save the vectors in **Qdrant** for persistent access.

---

## 🎖️ NEXT STEPS (DAY 4)
1. Configure GitHub PAT.
2. Implement the recursive repository parser.
3. Test Vika's ability to summarize a complex codebase (e.g., this project).

*Created 15 березня 2026*
*For в/ч А7022 | Позывной БАС*
