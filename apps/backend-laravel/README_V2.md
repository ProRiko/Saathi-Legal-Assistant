# Backend Laravel V2 Scaffold

This folder contains a production-oriented Laravel API scaffold for Saathi V2.

## Includes
- API routes for chat, history, templates, usage
- Sanctum-ready auth controllers
- Models and migrations for normalized schema
- Chat service that persists messages and calls Python AI service
- Usage service and template generation service

## Next Setup Steps
1. Create a full Laravel app in this folder if not already bootstrapped.
2. Register policies and rate limiters in providers.
3. Install Sanctum and configure auth guards.
4. Wire storage + PDF engine (DomPDF/Snappy).
5. Add feature tests and CI pipeline.
