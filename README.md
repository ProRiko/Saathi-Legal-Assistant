# 🏛️ Saathi Legal Assistant

> AI-powered legal guidance, document templates, and compliance calculators crafted for Indian law and deployed on **Render**.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://dashboard.render.com/deploy?repo=https://github.com/ProRiko/Saathi-Legal-Assistant)

## 🔗 Quick Links

- **Live Demo (Render)**: https://saathi-legal-assistant.onrender.com
- **Landing Experience**: `landing.html` (static HTML served by Flask)
- **Blueprint**: `render.yaml` (Render auto-detects build/start commands and env vars)

## ✨ Feature Highlights

- 🤖 **AI Legal Copilot** – Gemini-powered chat (multi-language) with intent detection, memory, and guardrails.
- ⚠️ **Legal Notice Generator** – Advocate-style notices (salary delay, rent default, consumer complaint, cheque bounce) rendered as PDFs.
- 📄 **Agreement Templates** – Ready-to-sign rent agreements, NDAs, freelance contracts, offer letters, and sale-of-goods drafts.
- 🧮 **Compliance Calculators** – Notice period, overtime & working hours, maternity benefits, and consumer compensation estimators.
- 📋 **Case Tracker & Legal Help Directory** – Static tools for case logging plus curated legal aid resources.
- 🌐 **Responsive Landing Page** – Accessible on mobile/desktop with device diagnostics, language selector, and quick actions.

## 🏛️ Legal Areas Covered

| Category | Examples |
|----------|----------|
| 🏠 Property Law | Landlord-tenant disputes, security deposits, rent issues |
| 💼 Employment Law | Salary disputes, wrongful termination, workplace rights |
| 👨‍👩‍👧‍👦 Family Law | Marriage, divorce, custody, domestic issues |
| 🛍️ Consumer Rights | Defective products, refunds, warranty claims |
| ⚖️ Criminal Law | Arrests, bail, false accusations, police matters |
| 📄 Contract Law | Agreements, breaches, terms and conditions |
| 🏛️ Civil Law | Damages, compensation, negligence cases |

## 📦 Product Modules

### 1. AI Legal Copilot
- Routes: `/api/chat`, `/chat.html`
- Inline language choice (English + 8 Indian languages) with response mirroring.
- Rate-limited endpoints and security middleware.

### 2. Legal Notice Generator
- UI: `legal_notices.html`
- API: `GET /api/legal-notices`, `GET /notices/<slug>`
- Notices (salary not paid, rent default, consumer complaint, cheque bounce) rendered through ReportLab for advocate-ready PDFs.

### 3. Agreement Templates
- UI: `agreement_templates.html`
- API: `GET /api/agreements`, `GET /agreements/<slug>`
- Templates stored as dictionaries in `app_production.py`; editing copy or adding tags is a quick metadata update.

### 4. Compliance Calculators
- UI: `legal_calculators.html`
- APIs:
	- `POST /api/calculators/notice-period`
	- `POST /api/calculators/work-hours`
	- `POST /api/calculators/maternity-benefit`
	- `POST /api/calculators/consumer-compensation`
- Calculator cards perform validation, format INR outputs, and summarize compliance notes.

### 5. Auxiliary Tools
- `case_tracker.html` for manual case logging.
- `legal_help.html` to surface legal aid centers, NGOs, and courts.
- `language_selection.html` plus device diagnostics for accessibility.

## 🧱 Architecture Overview

| Layer | Tech | Notes |
|-------|------|-------|
| Backend | Flask (`app_production.py`) | Single entrypoint with chat, PDF generation, calculators, security, and static file serving. |
| Templates | ReportLab | Reusable `create_pdf_document` helper streams advocate-ready PDFs. |
| Frontend | Static HTML/CSS/JS (`landing.html`, `legal_*.html`) | Hosted by Flask; optional React prototype lives under `frontend/`. |
| Data | `use_cases/legal_questions.json`, optional MongoDB | Conversational context logging + canned FAQ prompts. |
| Deployment | Render (free plan) | `render.yaml` configures build/start commands and env vars. |

## 🛠️ Local Development

### Prerequisites
- Python 3.12+
- Node 18+ (only if you plan to work inside `frontend/` React prototype)
- A Gemini API key (Google AI Studio) for chat completion.

### Setup Steps
```bash
git clone https://github.com/ProRiko/Saathi-Legal-Assistant.git
cd Saathi-Legal-Assistant
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.template .env
```

Fill the `.env` with at least:

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini key used by the chat + calculators. |
| `GEMINI_MODEL` | Defaults to `gemini-1.5-flash`. |
| `SECRET_KEY` | Flask session secret. |
| `ALLOWED_ORIGINS` | CORS whitelist (use `*` for development). |
| `MONGODB_URI` / `MONGO_DB_NAME` / `MONGO_COLLECTION_NAME` | Optional logging store. |

Then start the server:

```bash
python app_production.py
```

Visit `http://127.0.0.1:5000/` for the landing page. Static calculators/notices pages can be accessed directly (e.g., `/legal-calculators.html`).

### Optional React Frontend
```bash
cd frontend
npm install
npm start
```
Proxy API calls to `http://127.0.0.1:5000` as needed.

## 🧪 Smoke Tests

Use Python's bytecode compilation to catch syntax issues before deploying:

```bash
python -m compileall app_production.py
```

Add your preferred linters/test suites as needed.

## ☁️ Deploy to Render

1. Push your fork to GitHub.
2. Click **Deploy to Render** above (or create a new Web Service in the Render dashboard pointing to this repo).
3. Render will auto-read `render.yaml`, pre-filling:
	 - Build: `pip install -r requirements.txt`
	 - Start: `gunicorn --config gunicorn.conf.py app_production:app`
	 - Region: Singapore (free plan)
4. Set the environment variables:

| Key | Value / Notes |
|-----|---------------|
| `PYTHON_VERSION` | `3.11.9` (avoids wheel issues on Render's default Python 3.13). |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | Gemini access; keep the API key secret. |
| `SECRET_KEY` | Strong random string. |
| `ALLOWED_ORIGINS` | Public domain(s) for CORS. |
| `MONGODB_URI`, `MONGO_DB_NAME`, `MONGO_COLLECTION_NAME` | Optional; required only if you enable persistent conversation logging. |

5. Deploy. Once healthy, Render assigns `https://<service>.onrender.com`. Update the README's Live Demo link with the generated domain.
6. Hit `/health` or `/version` to confirm the instance is responding before sharing publicly.

> 📝 The `render.yaml` also works as infrastructure-as-code if you prefer `render blueprint deploy` workflows.

### Configuring CORS & Allowed Origins

- `ALLOWED_ORIGINS` accepts a comma-separated list (e.g., `https://saathi.example.com,https://admin.example.com`).
- Use `*` during local development, but **never** in production—list each domain that will host the HTML.
- The frontend now surfaces an explicit CORS hint if it cannot talk to the Flask API: “Add <origin> to ALLOWED_ORIGINS.” Use that origin string verbatim when updating your env vars.
- Restart the Render service (or your local server) after changing the variable so Flask reloads the whitelist.

## 📄 API Reference Snapshot

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/chat` | POST | Gemini-powered conversational replies with optional multilingual output. |
| `/api/legal-notices` | GET | Returns metadata for each notice template. |
| `/notices/<slug>` | GET | Streams PDF notice download. |
| `/api/agreements` | GET | Lists agreement templates with tags and descriptions. |
| `/agreements/<slug>` | GET | Streams PDF agreement download. |
| `/api/calculators/notice-period` | POST | Computes recommended notice days based on company type/tenure. |
| `/api/calculators/work-hours` | POST | Flags overtime and calculates double-rate payout. |
| `/api/calculators/maternity-benefit` | POST | Estimates payable weeks/days and eligibility under MB Act. |
| `/api/calculators/consumer-compensation` | POST | Suggests consumer dispute compensation package. |
| `/health`, `/version` | GET | Lightweight health/version checks for monitoring. |

## 📁 Key Files

- `app_production.py` – Flask app, calculators, PDF dictionaries, rate limiting, and route handlers.
- `legal_notices.html`, `agreement_templates.html`, `legal_calculators.html` – Feature-specific landing pages.
- `landing.html` – Primary marketing and onboarding surface.
- `render.yaml` – Render IaC blueprint.
- `requirements.txt` – Python dependencies (ReportLab, Flask, Gunicorn, etc.).

## 🔒 Privacy & Legal Notice

- ✅ No accounts or personal-data storage.
- ✅ HTTPS via Render.
- ✅ Rate limiting + security headers guard abuse.
- ⚠️ AI answers are informational only; always consult a qualified advocate before taking legal action.

> **Disclaimer**: Saathi Legal Assistant provides general legal information only. It is not a substitute for professional legal advice. Always consult a qualified attorney for guidance specific to your case.

---

*Built with ❤️ for India 🇮🇳 — now running on Render's free tier so anyone can deploy a full-fledged legal companion at zero cost.*
