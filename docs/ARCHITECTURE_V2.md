# Saathi V2 Architecture

## Runtime Topology
Frontend (React/Blade) -> Laravel API Gateway -> Python AI Service

## Responsibility Split
- Laravel:
  - Authentication (Sanctum)
  - Business logic
  - DB writes/reads
  - Template management + PDF generation
  - Usage and billing limits
- Python:
  - AI chat completion
  - Legal document analysis
  - Query classification

## Key Security Controls
- Per-user isolation at query level (`user_id` scoped access)
- No global in-memory conversation state
- Service-to-service HMAC signatures
- Laravel rate limiting on chat/document endpoints

## Primary APIs
- POST /api/chat
- GET /api/history
- POST /api/template/generate
- GET /api/usage

## Python Internal APIs
- POST /ai/chat
- POST /ai/analyze
- POST /ai/classify
- GET /health
