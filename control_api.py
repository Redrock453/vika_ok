from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import json
import os

app = FastAPI(title="Vika Control API - Grok Edition")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.getenv("CONTROL_API_KEY", "changeme")

def check_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

class ExecRequest(BaseModel):
    cmd: str

@app.get("/health")
async def health():
    return {"status": "alive", "message": "Grok control ready"}

@app.get("/docker-ps")
async def docker_ps():
    try:
        result = subprocess.run(["docker", "ps", "-a"], capture_output=True, text=True, timeout=10)
        return {"output": result.stdout.strip()}
    except Exception as e:
        return {"error": str(e)}

@app.get("/logs/{service}")
async def get_logs(service: str, lines: int = 100):
    try:
        result = subprocess.run(["docker", "logs", "--tail", str(lines), service], capture_output=True, text=True, timeout=15)
        return {"service": service, "logs": result.stdout.strip()}
    except Exception as e:
        return {"error": str(e)}

@app.get("/git-branches")
async def git_branches():
    try:
        result = subprocess.run(["git", "branch", "-a"], cwd="/root/vika_ok", capture_output=True, text=True)
        return {"branches": result.stdout.strip()}
    except Exception as e:
        return {"error": str(e)}

@app.post("/restart-bot")
async def restart_bot():
    try:
        subprocess.run(["docker", "restart", "vika_bot"], check=True)
        return {"status": "vika_bot restarted successfully"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/qdrant-health")
async def qdrant_health():
    try:
        result = subprocess.run(["curl", "-s", "http://127.0.0.1:6333/healthz"], capture_output=True, text=True)
        return json.loads(result.stdout)
    except Exception as e:
        return {"error": str(e)}

@app.post("/exec")
async def exec_cmd(req: ExecRequest, x_api_key: str = Header(...)):
    check_key(x_api_key)
    try:
        result = subprocess.run(
            req.cmd, shell=True,
            capture_output=True, text=True,
            timeout=30, cwd="/root/vika_ok"
        )
        return {
            "cmd": req.cmd,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"error": "timeout"}
    except Exception as e:
        return {"error": str(e)}
