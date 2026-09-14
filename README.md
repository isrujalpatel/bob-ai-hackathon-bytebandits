# Container Congestion Predictor & Port Operations Optimiser

> **IBM BoB AI Innovation Hackathon 2026 — Team ByteBandits**
> Track: AI · Problem Statement L1 — Logistics & Ports

---

## Team

| Field | Value |
|---|---|
| **Team Name** | ByteBandits |
| **Track** | AI |
| **Team Lead** | Prince Patel — prince@example.com |
| **Members** | Prince Patel, Member 2, Member 3 |

---

## Problem Statement

Port operators at major container terminals like Los Angeles/Long Beach allocate berths and cranes manually using spreadsheets, only discovering congestion hotspots *reactively* — after vessels have already begun queuing offshore. The 2021 LA/LB backlog held over 100 ships for weeks and cost global supply chains more than $10B. No widely accessible tool connects real vessel-arrival data to proactive, shift-ready scheduling decisions.

---

## Solution

We built a full-stack system that fetches **live daily vessel-call data from the IMF PortWatch API** (real AIS-based satellite tracking of ~90,000 ships), generates a calibrated 72-hour simulated vessel schedule, runs a **rule-based congestion detector** to flag over-capacity time windows before they occur, and applies a **greedy berth/crane assignment optimiser** to minimise total vessel wait time. Results feed a **Google Gemini-powered natural-language 72-hour operations brief** that shift supervisors can act on immediately.

---

## Key Features

- **Real data anchor**: live IMF PortWatch API integration — daily vessel-call volumes from AIS satellite tracking calibrate every simulation run
- **Congestion hotspot detection**: slot-by-slot berth demand vs. capacity, flagged LOW / MEDIUM / HIGH severity with exact time windows
- **Berth & crane optimiser**: greedy earliest-available-berth algorithm assigns each vessel to a berth and crane count, outputs structured schedule table
- **AI operations brief**: Google Gemini 2.0 Flash generates a BLUF-style 72-hour plan shift supervisors can act on without any training
- **React dashboard**: interactive colour-coded congestion timeline, filterable/sortable assignment table, and the operator brief in a single view

---

## Tech Stack

| Category | Technologies |
|---|---|
| **Languages** | Python, JavaScript |
| **Frameworks** | FastAPI, React, Vite, Recharts |
| **IBM Technologies** | IBM Bob (AI coding agent — entire project built inside Bob) |
| **Data Sources** | IMF PortWatch API (real AIS data), Google Gemini 2.0 Flash API |
| **Other** | httpx, pandas, Render (backend), Vercel (frontend) |

---

## Repository Structure

```
├── src/
│   ├── backend/          ← Python FastAPI: data fetcher, congestion, optimizer, Gemini brief
│   ├── frontend/         ← React/Vite dashboard
│   ├── data/             ← Auto-created CSV cache (gitignored)
│   └── .env.example      ← Environment variable template
├── docs/
│   ├── problem-statement.md
│   ├── solution-overview.md
│   ├── architecture.md   ← Mermaid diagram + component table
│   └── setup-guide.md
├── demo/
│   ├── screenshots/
│   ├── demo-video-link.txt
│   └── live-demo-url.txt
├── presentation/
└── submission.yaml
```

---

## How to Run

```bash
# 1. Clone the repo
git clone https://github.com/your-org/bob-ai-hackathon-bytebandits.git
cd bob-ai-hackathon-bytebandits

# 2. Backend — set up Python environment
cd src/backend
pip install -r requirements.txt

# 3. Configure environment
cd ..
cp .env.example .env
# Open .env and set: GEMINI_API_KEY=<your key from aistudio.google.com>

# 4. Start the backend
cd ..   # back to repo root
uvicorn backend.main:app --app-dir src --reload --port 8000

# 5. Frontend — new terminal
cd src/frontend
npm install
npm run dev   # opens http://localhost:3000
```

Full instructions (prerequisites, troubleshooting, deployment): see [`docs/setup-guide.md`](docs/setup-guide.md).

---

## Demo

| Artifact | Link |
|---|---|
| Demo Video | [See demo/demo-video-link.txt](demo/demo-video-link.txt) |
| Live Demo | [See demo/live-demo-url.txt](demo/live-demo-url.txt) |
| Screenshots | [See demo/screenshots/](demo/screenshots/) |
| Presentation | [See presentation/](presentation/) |

---

## Known Limitations

- Per-vessel ETAs and individual berth/crane specs are **simulated** — no free public dataset provides this granularity (clearly documented in code and docs)
- Gemini API key required for AI brief generation; app falls back to a structured rule-based brief if unavailable
- Optimiser uses greedy FCFS heuristic — not globally optimal, but O(V×B), interpretable, and sufficient for 50–100 vessels
- Render free-tier backend cold-starts in ~30–60 s after 15 min of inactivity

---

## What We're Most Proud Of

The **honest data-lineage design**: we anchor every run to live IMF PortWatch AIS data and explicitly label the simulated layer — judges can see exactly what is real and what is modelled. The congestion detector and optimiser are deliberately rule-based and explainable so a port supervisor (or a judge) can follow the logic, not just trust a black-box score. The entire project was built end-to-end inside **IBM Bob**, making the AI coding agent genuinely load-bearing throughout development.

---
