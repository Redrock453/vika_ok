# AGENTS.md - VIKA_OK Coding Guide

## Project Overview

VIKA_OK is a bilingual (Russian/English) AI assistant with smart LLM routing, RAG memory, and self-learning capabilities. Built as a monorepo with Python backend and React/Next.js frontend.

## Build, Test & Lint Commands

### Python Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Run main agent
python agent.py

# Run agent with query
python agent.py --query "your question"

# Run signal bot
python signal_bot_vika.py

# Run tests (Phase 1-2)
python test_phase1_2.py
python test_phase1_2.py --quick  # Quick tests only
python test_phase1_2.py --verbose # Detailed output

# Run integration test (Phase 3)
python test_phase3_integration.py

# Run migrations
python migrate_to_qdrant.py

# Run local analyzer
python local_analyzer.py

# Run GitHub analyzer
python github_analyzer.py

# Run bridge (OSINT)
python signal_bridge.py
```

### Frontend (Next.js/React)
```bash
# Navigate to frontend directory if it exists
cd frontend  # (Check if this directory exists in the repo)

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

### Qdrant Management
```bash
# Start Qdrant container (if using Docker)
docker run -d -p 6333:6333 -p 6334:6334 -v qdrant_storage:/qdrant/storage qdrant/qdrant

# Run Qdrant manager in test mode
python qdrant_manager.py
```

## Python Code Style Guidelines

### Imports
- Import standard library modules first (`os`, `sys`, `logging`, `json`)
- Import third-party packages second (`requests`, `numpy`, `qdrant_client`)
- Import local modules last (`from agent import VikaOk`, etc.)
- Group imports: standard library → third-party → local
- Use absolute imports for local modules

```python
# Good
import os
import logging
from pathlib import Path

import requests
from qdrant_client import QdrantClient

from agent import VikaOk

# Bad
from agent import VikaOk
import os
```

### Formatting
- 4 spaces per indentation level (no tabs)
- Maximum line length: 120 characters
- Blank lines: 2 between top-level definitions, 1 between methods
- Import each module on its own line

### Type Annotations
- Use type hints for function parameters and return values
- Optional types with `Optional[T]` or `T | None`
- Use standard types (`str`, `int`, `bool`, `List`, `Dict`, etc.)
- Import typing module when needed

```python
# Good
def ask(self, query: str) -> str:
    """Execute query through routing system."""
    q_low: str = query.lower().strip()

# Bad
def ask(self, query):
    return query.lower().strip()
```

### Naming Conventions
- Classes: PascalCase (`VikaOk`, `QdrantManager`, `FunctionalTestSuite`)
- Functions/methods: snake_case (`_ask_groq`, `scan_environment`, `run_all_tests`)
- Private methods: leading underscore (`_ask_ollama`)
- Constants: UPPER_SNAKE_CASE (`VERSION = 'v11.2'`, `LOG_DIR`, `BASE_DIR`)
- Protected attributes: single underscore (`_embedding_model`, `env_info`)
- Protected classes: leading underscore (`_BaseHandler`)

```python
# Good
class VikaOk:
    def __init__(self):
        self._embedding_model = None
        self.env_info = {}
    
    def scan_environment(self) -> dict:
        return {}

# Bad
class vika_ok:
    def __init__(self):
        self.EmbeddingModel = None
        self.EnvInfo = {}
    
    def scan_environment(self):
        return {}
```

### Error Handling
- Use try-except for critical operations
- Log errors with appropriate logging levels (ERROR, WARNING)
- Return meaningful default values or None on failure
- Never swallow exceptions silently
- Use `logging.getLogger(__name__)` for module-specific logging

```python
# Good
try:
    from qdrant_manager import QdrantManager
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    logging.warning('Qdrant not available')

try:
    res = self.qdrant.search(vec, limit=3)
except Exception as e:
    logging.error(f'Search failed: {e}')
    return []
```

### Logging
- Configure logging at module level
- Use `logging.getLogger(__name__)` for context
- Log levels: DEBUG (development), INFO (normal), WARNING (warnings), ERROR (errors)
- Include timestamps in logs
- Use Unicode emojis for status messages (🚀, ✅, ❌, ⚠️)

```python
# Good
import logging
logger = logging.getLogger(__name__)

logger.info("🚀 Starting Vika agent...")
logger.warning("⚠️ Qdrant service not running")
logger.error("❌ Connection failed: {error}")
```

### Docstrings
- Use triple double quotes `"""` for all docstrings
- Include one-line summary, parameters, and return value
- Follow Google or NumPy style (prefer NumPy for Python)
- Language: Match the project language (Russian/English)

```python
# Good
def ask(self, query: str) -> str:
    """
    Execute query through smart LLM routing system.

    Parameters
    ----------
    query : str
        User's question or command.

    Returns
    -------
    str
        AI-generated response from selected model.
    """
```

### String Handling
- Use f-strings for string formatting (Python 3.6+)
- Use `json.dumps()` for JSON serialization
- Use `pathlib.Path` for file operations instead of os.path
- Handle encoding explicitly with utf-8 when reading/writing files
- Use `strip()` when cleaning strings

```python
# Good
path = Path(__file__).parent
response = model.generate_content(f'{prompt}\nUser: {query}')
text = stdout.decode('utf-8', errors='ignore').strip()

# Bad
path = os.path.dirname(__file__)
response = model.generate_content(prompt + "\nUser: " + query)
text = stdout.decode()
```

### File Operations
- Use `pathlib.Path` for all file path operations
- Use `Path.mkdir(exist_ok=True)` for creating directories
- Use `Path.exists()` instead of `os.path.exists()`
- Always use `with` statements for file context managers
- Use `Path.parent` and `Path.name` for path components

```python
# Good
base_dir = Path(__file__).parent
log_dir = base_dir / 'logs'
log_dir.mkdir(exist_ok=True)

with open(log_file, 'w', encoding='utf-8') as f:
    f.write(data)

# Bad
base_dir = os.path.dirname(__file__)
log_dir = base_dir + '/logs'
os.makedirs(log_dir)

with open(log_file, 'w') as f:
    f.write(data)
```

## React/Next.js Code Style Guidelines

### Component Structure
- Use functional components with hooks
- Use descriptive function names
- Group imports alphabetically
- Use PascalCase for component names

```typescript
// Good
import { useState } from 'react'

export function VikaDashboard() {
  const [count, setCount] = useState(0)
  
  return <div>Count: {count}</div>
}

// Bad
import { useState } from "react";

function VikaDashboard() {
  const count = useState(0);
  return <div>{count}</div>;
}
```

### Hooks Usage
- Use `useRef` for mutable values that don't trigger re-renders
- Use `useEffect` for side effects
- Use TypeScript interfaces for type safety

```typescript
const buttonRef = useRef<HTMLButtonElement>(null)

useEffect(() => {
  // Side effect
}, [dependency])
```

### Styling
- Use Tailwind CSS classes (based on imports)
- Use semantic naming for components
- Group related styles together

```typescript
<Card className="p-4 space-y-4">
  <CardHeader>
    <CardTitle>AI Models</CardTitle>
  </CardHeader>
</Card>
```

## Environment Setup

### Required Environment Variables
```bash
# Required
GEMINI_API_KEY=your_gemini_api_key

# Optional but recommended
GROQ_API_KEY=your_groq_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=vika_knowledge

# For Signal bot
SIGNAL_NUMBER=+1234567890
MASTER_SIGNAL_NUMBER=+1234567890
CIPHER_KEY=your_encryption_key

# For GitHub analysis
GITHUB_TOKEN=your_github_token
```

### Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate on Linux/Mac
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate
```

## Project Structure
```
vika_ok/
├── agent.py              # Main AI agent with routing
├── signal_bot_vika.py    # Signal messenger bot
├── qdrant_manager.py     # Qdrant vector DB manager
├── test_phase1_2.py      # Functional tests (Phase 1-2)
├── test_phase3_integration.py  # Integration tests (Phase 3)
├── examples.py           # Usage examples
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (not in git)
├── .env.example          # Environment template
├── src/
│   └── app/
│       └── page.tsx      # React/Next.js frontend
├── knowledge/            # Document knowledge base
├── logs/                 # Application logs
└── bin/                  # Signal CLI binaries
```

## Testing Strategy

### Unit Tests
- Test individual functions and methods
- Use fixtures for testing with mocked data
- Test error conditions and edge cases

### Integration Tests
- Test module interactions
- Test API integrations (Gemini, Qdrant, OpenRouter)
- Test end-to-end workflows

### Test Commands
```bash
# Run all tests
python test_phase1_2.py

# Quick tests (imports + critical paths)
python test_phase1_2.py --quick

# Verbose output
python test_phase1_2.py --verbose

# Check component status
python test_phase1_2.py | grep "COMPONENT STATUS"
```

## Code Review Checklist

- [ ] Type hints used appropriately
- [ ] Error handling with logging
- [ ] Docstrings included
- [ ] Imports organized correctly
- [ ] No magic numbers (use constants)
- [ ] Code follows naming conventions
- [ ] File paths use pathlib.Path
- [ ] Logging configured and used
- [ ] Security: No hardcoded credentials
- [ ] Environment variables used for config
- [ ] Test coverage for new features
- [ ] Bilingual comments and strings (if applicable)
- [ ] No commented-out code
- [ ] No TODOs without issue numbers
- [ ] Consistent formatting (4 spaces, 120 char limit)
- [ ] No unnecessary dependencies
- [ ] Proper error messages for users

## Common Pitfalls

- **Swallowing exceptions**: Always log or handle exceptions
- **Hardcoded paths**: Use `pathlib.Path` and environment variables
- **Direct API calls**: Use wrapper functions
- **Missing logging**: Add logging for debugging
- **Ignoring encoding**: Always specify utf-8 for text files
- **Not checking None**: Always validate None values
- **Mixing languages**: Be consistent with Python code (English) and comments (Russian/English)
- **No type hints**: Use typing for better IDE support and readability
- **Magic numbers**: Extract to constants

## Performance Considerations

- Cache expensive operations (embeddings, API calls)
- Use async/await for I/O operations
- Implement rate limiting for API calls
- Use vector embeddings for fast similarity search
- Optimize chunk size for RAG pipeline (512-1000 chars recommended)

## Security Best Practices

- Never commit API keys or credentials
- Use environment variables for sensitive data
- Validate and sanitize all user inputs
- Use encryption for sensitive data (Signal bot uses Fernet)
- Implement rate limiting
- Use HTTPS for all API calls
- Validate SSL certificates

## Bilingual Documentation

- Python code comments: English (technical terms)
- User-facing strings: Russian (main audience)
- Code variables: English (industry standard)
- Documentation: Bilingual or according to context
- Keep UI text in Russian for better UX

## Additional Resources

- Test Guide: `TEST_GUIDE.md`
- Environment Template: `.env.example`
- Gemini API: https://ai.google.dev/
- Qdrant Docs: https://qdrant.tech/
- Sentence Transformers: https://www.sbert.net/

---

*Last Updated: 2026-03-21*
*Version: v11.2-SMART-ROUTING*
