# Vika_Ok — Production TODO

## ✅ Done
- [x] Refactored to modular structure (src/core, src/handlers, src/services)
- [x] LLM retry + fallback chain (DO → Groq → Gemini, 3 retries each)
- [x] Thread-safe history manager
- [x] Config centralized in src/core/config.py
- [x] RAG service isolated
- [x] Web search service isolated
- [x] Task scheduler isolated
- [x] Docker + docker-compose with health checks
- [x] Proper logging throughout
- [x] Telegram bot handler with audio transcription

## 🔴 Next (Critical)
- [ ] Rate limit handling — add exponential backoff per provider
- [ ] Graceful shutdown (signal handlers)
- [ ] Test on real VPS

## 🟡 Important
- [ ] .env.example update
- [ ] README rewrite (Ukrainian)
- [ ] CI/CD (GitHub Actions → SSH deploy)
- [ ] Version tags
