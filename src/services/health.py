"""Health check and monitoring endpoints."""
from fastapi import FastAPI, HTTPException
from src.core.config import config
from src.core.llm import LLMProvider

app = FastAPI(title="Vika_Ok Health API", version="13.1.1")

llm = LLMProvider()


@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "ok",
        "version": "13.1.1",
    }


@app.get("/status")
async def detailed_status():
    """Detailed status of all components."""
    return {
        "status": "ok",
        "version": "13.1.1",
        "config": {
            "telegram_configured": bool(config.telegram_token),
            "allowed_users": len(config.allowed_ids),
            "log_level": config.log_level,
        },
        "providers": {
            "do": bool(llm.do_client),
            "groq": bool(llm.groq_client),
            "gemini": bool(llm.gemini_model),
        },
        "qdrant": {
            "host": config.qdrant_host,
            "port": config.qdrant_port,
        },
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check - fails if critical components missing."""
    is_valid, errors = config.validate()
    if not is_valid:
        raise HTTPException(status_code=503, detail={"errors": errors})

    # Check at least one LLM provider
    if not any([llm.do_client, llm.groq_client, llm.gemini_model]):
        raise HTTPException(status_code=503, detail="No LLM provider available")

    return {"status": "ready"}
