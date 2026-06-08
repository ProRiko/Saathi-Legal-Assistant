# 🏛️ Saathi Legal Assistant

> AI-powered legal guidance, document templates, and compliance calculators crafted for Indian law, prepared for **Vercel** deployment, and now defaulting to Anthropic Claude Haiku with Gemini fallback.

[![Deploy to Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/ProRiko/Saathi-Legal-Assistant)

## 🔗 Quick Links

- **Live Demo (Vercel)**: https://saathi-legal-assistant.vercel.app
- **Landing Experience**: `landing.html` (static HTML served by Flask)
- **Blueprint**: `vercel.json` (routes the whole Flask app through a Python serverless function)

## ✨ Feature Highlights

- 🤖 **AI Legal Copilot** – Anthropic Claude Haiku (default) chat with optional Gemini fallback, multi-language mirroring, intent detection, memory, and guardrails.
- ⚠️ **Legal Notice Generator** – Advocate-style notices (salary delay, rent default, consumer complaint, cheque bounce) rendered as PDFs.
- 📄 **Agreement Templates** – Ready-to-sign rent agreements, NDAs, freelance contracts, offer letters, and sale-of-goods drafts.
- 🧮 **Compliance Calculators** – Notice period, overtime & working hours, maternity benefits, and consumer compensation estimators.
- 📋 **Case Tracker & Legal Help Directory** – Static tools for case logging plus curated legal aid resources.
- 📚 **Guide Library & Onboarding** – Dedicated guides + landing onboarding that route users to the right tool in two clicks.
- 🛡️ **Trust Footer & Support Escalations** – Shared footer highlights consent, manual review paths, and human escalation info on every surface.
- 🚀 **SEO + PWA Ready** – JSON-LD metadata, sitemap/robots, new maskable icons, and app shortcuts for install prompts.
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

## 🔍 SEO, PWA & Trust Upgrades

- **Metadata pass**: canonical URLs, Open Graph/Twitter cards, and JSON-LD (`WebApplication`, `CollectionPage`, `FAQPage`) on every public page.
- **Discovery aids**: `sitemap.xml` and `robots.txt` now ship with fresh links to landing, tools, guides, calculators, and chat.
- **Guide hub**: `legal-guides.html` plus three deep-dive pages route to calculators/notices with contextual CTAs.
- **Shared trust footer**: support email/WhatsApp, compliance badges, and quick links are injected site-wide.
- **PWA polish**: refreshed `manifest.json`, maskable + square SVG icons, and app shortcuts (Chat, Notices, Calculators).
- **Consent-first analytics**: `analytics.js` only fires events after the consent modal sets `saathi_consent=yes`, posting to `/api/event` which logs into `audit_logs`.

## 🧱 Architecture Overview

| Layer | Tech | Notes |
|-------|------|-------|
| Backend | Flask (`app_production.py`) | Single entrypoint with chat, PDF generation, calculators, security, and static file serving. |
| Templates | ReportLab | Reusable `create_pdf_document` helper streams advocate-ready PDFs. |
| Frontend | Static HTML/CSS/JS (`landing.html`, `legal_*.html`) | Hosted by Flask; optional React prototype lives under `frontend/`. |
| Data | `use_cases/legal_questions.json`, optional MongoDB | Conversational context logging + canned FAQ prompts. |
| Deployment | Vercel (serverless) | `vercel.json` and `api/index.py` route the Flask app through a Python function. |

## 🛠️ Local Development

### Prerequisites
- Python 3.12+
- Node 18+ (only if you plan to work inside `frontend/` React prototype)
- An Anthropic API key (Claude Haiku) for the default chat provider.
- (Optional) A Gemini API key (Google AI Studio) if you want a fallback provider.

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
| `MODEL_PROVIDER` | `claude` (default) or `gemini` to force a specific provider. |
| `ANTHROPIC_API_KEY` | Required for Anthropic Claude Haiku (default chat). |
| `CLAUDE_MODEL` | Defaults to `claude-3-5-haiku-20241022`. |
| `GEMINI_API_KEY` | Optional fallback (used when provider is `gemini` or Claude is unavailable). |
| `GEMINI_MODEL` | Defaults to `gemini-2.5-flash`. |
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

## ☁️ Deploy to Vercel

1. Push your fork to GitHub.
2. Import the GitHub repo in Vercel or click **Deploy to Vercel** above.
3. Keep the project root as-is so Vercel sees `vercel.json` and the `api/` directory.
4. Set the environment variables:

| Key | Value / Notes |
|-----|---------------|
| `MODEL_PROVIDER` | Usually `claude` (defaults automatically); set to `gemini` only if forcing fallback. |
| `ANTHROPIC_API_KEY`, `CLAUDE_MODEL` | Anthropic Claude Haiku credentials (default chat provider). |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | Optional fallback Gemini access; keep the API key secret. |
| `SECRET_KEY` | Strong random string. |
| `ALLOWED_ORIGINS` | Public domain(s) for CORS. |
| `MONGODB_URI`, `MONGO_DB_NAME`, `MONGO_COLLECTION_NAME` | Optional; required only if you enable persistent conversation logging. |
| `SAATHI_STORAGE_DIR` | Optional writable directory for local SQLite and consent logs during testing. |

5. Deploy. Once healthy, Vercel assigns `https://<project>.vercel.app`.
6. Hit `/health` or `/version` to confirm the instance is responding before sharing publicly.

> 📝 The Flask app still runs locally with `python app_production.py`; Vercel uses the serverless wrapper in `api/index.py`.

### Configuring CORS & Allowed Origins

- `ALLOWED_ORIGINS` accepts a comma-separated list (e.g., `https://saathi.example.com,https://admin.example.com`).
- Use `*` during local development, but **never** in production—list each domain that will host the HTML.
- The frontend now surfaces an explicit CORS hint if it cannot talk to the Flask API: “Add <origin> to ALLOWED_ORIGINS.” Use that origin string verbatim when updating your env vars.
- Redeploy Vercel after changing the variable so the function picks up the new whitelist.

## 📄 API Reference Snapshot

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/chat` | POST | Provider-agnostic conversational replies (Anthropic Claude by default) with optional multilingual output. |
| `/api/legal-notices` | GET | Returns metadata for each notice template. |
| `/notices/<slug>` | GET | Streams PDF notice download. |
| `/api/agreements` | GET | Lists agreement templates with tags and descriptions. |
| `/agreements/<slug>` | GET | Streams PDF agreement download. |
| `/api/calculators/notice-period` | POST | Computes recommended notice days based on company type/tenure. |
| `/api/calculators/work-hours` | POST | Flags overtime and calculates double-rate payout. |
| `/api/calculators/maternity-benefit` | POST | Estimates payable weeks/days and eligibility under MB Act. |
| `/api/calculators/consumer-compensation` | POST | Suggests consumer dispute compensation package. |
| `/api/event` | POST | Lightweight, consent-gated analytics sink (page views, calculator usage, CTA taps). |
| `/health`, `/version` | GET | Lightweight health/version checks for monitoring. |

## 📁 Key Files

- `app_production.py` – Flask app, calculators, PDF dictionaries, rate limiting, and route handlers.
- `legal_notices.html`, `agreement_templates.html`, `legal_calculators.html` – Feature-specific landing pages.
- `landing.html` – Primary marketing and onboarding surface.
- `legal-guides.html` + `*-guide.html` – Long-form explainer content that links to calculators and notices.
- `vercel.json` – Vercel routing config for the Flask app.
- `api/index.py` – Vercel Python entrypoint that exposes the Flask WSGI app.
- `requirements.txt` – Python dependencies (ReportLab, Flask, Gunicorn, etc.).
- `analytics.js` – Consent-aware tracker that posts to `/api/event`.
- `sitemap.xml` & `robots.txt` – Search crawling aids now deployed alongside the app.
- `assets/icons/saathi-icon.svg` (and `-maskable.svg`) – PWA icons referenced by `manifest.json`.

## 🔒 Privacy & Legal Notice

- ✅ No accounts or personal-data storage.
- ✅ HTTPS via Vercel.
- ✅ Rate limiting + security headers guard abuse.
- ⚠️ AI answers are informational only; always consult a qualified advocate before taking legal action.

> **Disclaimer**: Saathi Legal Assistant provides general legal information only. It is not a substitute for professional legal advice. Always consult a qualified attorney for guidance specific to your case.

---

*Built with ❤️ for India 🇮🇳 — now ready for a Vercel deployment flow while keeping the local Flask workflow intact.*
