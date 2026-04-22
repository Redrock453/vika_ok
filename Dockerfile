FROM python:3.12-slim

WORKDIR /app

# System deps: ffmpeg (audio), curl (healthcheck), openssh-client (SSH to servers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg curl openssh-client && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Create SSH dir
RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["python", "run.py"]
