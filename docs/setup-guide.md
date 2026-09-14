# Setup Guide

This guide assumes a **clean clone** — follow every step in order.

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.11+ | `python --version` to check |
| Node.js | 18+ | `node --version` to check |
| npm | 9+ | bundled with Node |
| Internet access | — | Required for first IMF PortWatch fetch |
| Gemini API key | free | Get at [aistudio.google.com](https://aistudio.google.com) in ~2 min |

> **Windows users**: all commands below work in PowerShell or cmd. Use `python` instead of `python3` if needed.

---

## Step 1 — Clone the repository

```bash
git clone https://github.com/your-org/bob-ai-hackathon-bytebandits.git
cd bob-ai-hackathon-bytebandits
```

---

## Step 2 — Set up the Python backend

```bash
cd src/backend

# Create and activate a virtual environment (recommended)
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

---

## Step 3 — Configure environment variables

```bash
# From the src/ directory
cd ..
cp .env.example .env
```

Open `src/.env` in any text editor and fill in:

```
GEMINI_API_KEY=your_gemini_api_key_here   # REQUIRED for AI brief
APP_PORT=8000
APP_ENV=development
```

**How to get a free Gemini API key (2 minutes):**
1. Go to [https://aistudio.google.com](https://aistudio.google.com)
2. Sign in with any Google account
3. Click **"Get API key"** → **"Create API key"**
4. Copy and paste the key into `src/.env`

> **Without the key**: the app still runs fully — it generates a rule-based plain-text brief instead of an AI-written one.

---

## Step 4 — Start the backend

```bash
# From the repo root
cd ..    # make sure you're at bob-ai-hackathon-bytebandits/

uvicorn backend.main:app --app-dir src --reload --port 8000
```

**Verify it's working:**
```bash
curl http://localhost:8000/health
# Expected: {"status":"ok","service":"container-congestion-predictor"}
```

You can also open [http://localhost:8000/docs](http://localhost:8000/docs) to see the auto-generated API documentation.

---

## Step 5 — Start the frontend

Open a **new terminal** (keep the backend running):

```bash
cd src/frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

**Verify it's working**: you should see the dashboard with a port selector and "Run 72h Plan" button.

---

## Step 6 — Run a plan end-to-end

1. In the browser at [http://localhost:3000](http://localhost:3000), select **Port of Los Angeles**
2. Click **▶ Run 72h Plan**
3. Wait ~3–5 seconds — the backend fetches live IMF PortWatch data, runs the congestion model, and generates the assignment plan
4. You should see:
   - A colour-coded congestion timeline (green/yellow/orange/red bars)
   - A berth assignment table with all vessels
   - A 72-hour operations brief (AI-generated if Gemini key is set, rule-based otherwise)

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `GEMINI_API_KEY` | Recommended | `""` | Google Gemini API key for AI brief generation |
| `APP_PORT` | No | `8000` | Backend server port |
| `APP_ENV` | No | `development` | `development` or `production` |
| `CORS_ORIGINS` | No | `http://localhost:3000,...` | Comma-separated allowed frontend origins |
| `VITE_API_URL` | No (frontend) | `""` | Backend URL for the React app (used in Vercel deploy) |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'fastapi'` | venv not activated or deps not installed | Activate venv: `.venv\Scripts\Activate.ps1`, then `pip install -r requirements.txt` |
| `uvicorn: command not found` | uvicorn not on PATH | Use `python -m uvicorn backend.main:app --app-dir src ...` |
| Backend starts but `/api/plan` returns 503 | IMF PortWatch API unreachable | Check internet; the app falls back to CSV cache if one exists from a previous run |
| `No data returned for port 'Los Angeles'` | Port name not matching PortWatch format | Try `Los Angeles` exactly (case-sensitive) |
| Dashboard loads but shows "Failed to fetch" | Backend not running on port 8000 | Start backend first; confirm `curl http://localhost:8000/health` works |
| Gemini brief shows fallback text | `GEMINI_API_KEY` not set or invalid | Check `.env` file in `src/`; get key from [aistudio.google.com](https://aistudio.google.com) |
| `npm run dev` fails on Node version | Node < 18 | Install Node 18+ from [nodejs.org](https://nodejs.org) |
| Port 3000 already in use | Another process | Change port: `npm run dev -- --port 3001` |

---

## Deployment (Render + Vercel)

See [`docs/architecture.md`](architecture.md#deployment-architecture) for the full deployment diagram.

**Backend — Render (free Web Service):**
1. Connect your GitHub repo to [render.com](https://render.com)
2. New → Web Service → select repo
3. Build command: `pip install -r src/backend/requirements.txt`
4. Start command: `uvicorn backend.main:app --app-dir src --host 0.0.0.0 --port 10000`
5. Add environment variable: `GEMINI_API_KEY` = your key
6. Deploy — note the `https://your-service.onrender.com` URL

**Frontend — Vercel (free Hobby tier):**
1. Connect repo at [vercel.com](https://vercel.com)
2. Root directory: `src/frontend`
3. Add environment variable: `VITE_API_URL` = `https://your-service.onrender.com`
4. Deploy — note the `https://your-app.vercel.app` URL

**After both are live:**
- Add the Vercel URL to `CORS_ORIGINS` in Render's environment variables
- Put the Vercel URL in `demo/live-demo-url.txt`
- Hit `https://your-service.onrender.com/health` once before recording the demo to warm up the cold-start

---

## Data Cache Location

The backend auto-creates `src/data/portwatch_los_angeles.csv` (and similar for other ports) on first run. This cache is used for offline operation and to avoid hammering the API. It is refreshed automatically when > 24 hours old. The `src/data/` directory is `.gitignored` — never commit these files.
