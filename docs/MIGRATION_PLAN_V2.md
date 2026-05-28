# Saathi V2 Migration Plan (Laravel + Python Microservices)

## Phase 0 - Hardening Existing Monolith
1. Remove global `conversation_history` usage.
2. Remove duplicate routes and duplicate error handlers.
3. Freeze new feature development in Flask monolith.

## Phase 1 - Stand Up Laravel Core
1. Create models, migrations, and Sanctum auth.
2. Implement `/api/chat`, `/api/history`, `/api/template/generate`, `/api/usage`.
3. Enforce per-user ownership via policies.

## Phase 2 - Extract Python AI Service
1. Keep only `/ai/chat`, `/ai/analyze`, `/ai/classify`, `/health`.
2. Remove auth/database/static frontend code from Python.
3. Add internal signature verification.

## Phase 3 - Integrate Services
1. Implement Laravel `AIClient` with HMAC signed requests.
2. Store user message before AI call and assistant reply after AI call.
3. Add usage counters and audit logs.

## Phase 4 - Template Migration
1. Move templates to Laravel table.
2. Render + generate PDF in Laravel service layer.
3. Decommission template generation in Flask monolith.

## Phase 5 - Cutover
1. Route frontend only to Laravel APIs.
2. Backfill data from SQLite into Postgres.
3. Keep old app read-only for rollback window.
4. Shut down monolith after stability window.
